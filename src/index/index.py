#!/usr/bin/env python

"""
written by Leonardo D'Alonzo - leonardo.dalonzo@gmail.com

version of 2008/12/23
version of 2008/12/26
version of 2009/01/06
"""

__author__ = "Leonardo D'Alonzo (leonardo.dalonzo@gmail.com)"
__version__ = '2009-03-17'

import codecs
import datetime
import heapq
import math
import re
import threading
import pageRank

from pdfparser import PDFPaperParser
import common.stringdiff
import storage
import common.nlp
from core.core import PDFResource
from core.core import Paper
from core.core import Author

class CitationGraphAnalizerThread(threading.Thread):
    
    def __init__(self, peerStatus):
        pass

class Index():
    
    def __init__(self, titleIndex, abstractIndex, bodyIndex):
        
        self.__knownResources = storage.KnownResources()
        self.__knownAuthors = storage.KnownAuthors()
        self.__knownPapers = storage.KnownPapers()
        
        #self.__abstractDictionary = storage.Dictionary('abstract')
        #self.__titleDictionary = storage.Dictionary('title')
        #self.__bodyDictionary = storage.Dictionary('body')
        
        self.__titleDictionary = titleIndex#storage.Dictionary('title')
        self.__abstractDictionary = abstractIndex#storage.Dictionary('abstract')
        self.__bodyDictionary = bodyIndex#storage.Dictionary('body')
        
        self.__indexesUpdated = threading.Event()
        self.__indexesUpdated.set()
        
        #self.__indexesUpdatedCondition = threading.Condition()
        
        self.__pageRankVector = {}
        
        self.__condition = threading.Condition()
        
    def getIndexes(self):
        #print "[%s] waiting for index updating..." % threading.currentThread().getName()
        self.__indexesUpdated.wait()
        self.__indexesUpdated.clear()
        
        #print "[%s] index updated! waiting for acquiring condition..." % threading.currentThread().getName()
        
        self.__condition.acquire()
        
        #print "[%s] condition acquired!" % threading.currentThread().getName()
        
        titleIndex = self.__titleDictionary
        abstractIndex = self.__abstractDictionary
        bodyIndex = self.__bodyDictionary
        
        self.__condition.release()
        
        return (titleIndex, abstractIndex, bodyIndex)
    
    
    def submitPDF(self, pdfFileURL):
        
        #print "[%s] file %s submitted... waiting for condition..." % (threading.currentThread().getName(), pdfFileURL)
        self.__condition.acquire()
        print "\n[%s] file _%s_ submitted. Analyzing..." % (threading.currentThread().getName(), pdfFileURL)
        try:
            pdfFile = PDFResource(pdfFileURL)
            if self.__knownResources.contains(pdfFile.sha1):
                print "[%s] The file %s is already known." % (threading.currentThread().getName(), pdfFileURL)
                self.__condition.release()
                return None

            self.__knownResources.add(pdfFile.sha1, pdfFile)
            
            pdfParser = PDFPaperParser.PDFPaperParserHtml()
            pdfParser.feed(pdfFileURL)
            
            if pdfParser.title:
                
                paper = Paper(pdfParser.title)                
                    
                paper.addResource(pdfFile)#???
                paper.urn = pdfFile.sha1 #TODO
                
                if self.__knownPapers.contains(paper.urn):
                    print "[%s] The paper with the title '%s' is already known." % (threading.currentThread().getName(), pdfParser.title)
                    self.__condition.release()
                    return None
                else:
                    self.__knownPapers.add(paper.urn, paper)
                    print "[%s] '%s' added to index" % (threading.currentThread().getName(), paper.title)
                    
                if len(paper.title)>0:
                    self.indexText(paper, paper.title, self.__titleDictionary)
                else:
                    print "[%s] ERROR Unable to index the title of '%s'" % (threading.currentThread().getName(), paper.title)                    
                
                if pdfParser.authors:
                    for authorName in pdfParser.authors:
                        if not self.__knownAuthors.contains(authorName):
                            self.__knownAuthors.add( Author(authorName) )
                            
                        author = self.__knownAuthors.get(authorName)
                        
                        author.addPaper(paper)
                        paper.addAuthor(author)
                        
                if pdfParser.bibliography:
                    paper.bibliography = pdfParser.bibliography
                
                if pdfParser.abstract:
                    paper.abstract = pdfParser.abstract
                    if len(paper.abstract)>0:
                        self.indexText(paper, paper.abstract, self.__abstractDictionary)
                    else:
                        print "[%s] ERROR Unable to index the abstract of '%s'" % (threading.currentThread().getName(), paper.title)
                        
                if pdfParser.bodyText:
                    if len(pdfParser.bodyText)>0:
                        #pass
                        self.indexText(paper, pdfParser.bodyText, self.__bodyDictionary)
                        
                #print "[%s] I have updated the index. Setting flag..." % threading.currentThread().getName()
                self.__indexesUpdated.set()
                
                #print "[%s] releasing condition" % threading.currentThread().getName()        
                self.__condition.release()
                
                #self.buildCitationsLinks() ##The reference graph is updated every time a paper is added
                self.buildCitGraphAndAnalyze()
                return paper
            
            else:
                print "[%s] Unable to retrieve enough metadata from %s. It will not be indexed." % (threading.currentThread().getName(), pdfFileURL)
                self.__condition.release()
                return None

        except:# KeyboardInterrupt:
            print "[%s] There was an exception on analyzing %s" % (threading.currentThread().getName(), pdfFileURL)
            self.__condition.release()
            return None
        
    def howManyPapers(self):
        return len(self.__knownPapers.keys())
        
    def buildCitGraphAndAnalyze(self):
        self.__buildCitationsLinks()
        
        try:
            PRVector = self.calculatePageRank()
            
            listOfPaperIDs = self.getListOfPaperIDs()
        
            self.__pageRankVector = {}
            counter = 0
            for paperID in listOfPaperIDs:
                self.__pageRankVector[paperID] = PRVector[counter]
                counter += 1
        except:
            print "[%s] Unable to calculate PageRank..." % (threading.currentThread().getName())
            
        
            
    def logAbstractTermByDocMatrix__DEPRECATED(self):
        (docVector, termVector, tdocMatrix) = self.__abstractDictionary.getTermByDocMatrix()
        
        matrixString = ''
        for row in tdocMatrix:
            rowString = ','.join(['%.5f' % wij for wij in row])
            rowString += '\n'
            matrixString += rowString
            
        docVectorString = ','.join(['%s' % docID for docID in docVector])
        termVectorString = ','.join(['%s' % term for term in termVector])
        
        now = '../logs/' + re.sub('\s','_', '%s' % datetime.datetime.now())
                
        logFileName = '%s-termByDoc-matrix.data' % now
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(matrixString)
        
        logFileName = '%s-docVector.data' % now
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(docVectorString)
        
        logFileName = '%s-termVector.data' % now
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(termVectorString)
        
    def logAllTermByDocMatrix(self):
        self.__logTermByDocMatrix(self.__titleDictionary)
        self.__logTermByDocMatrix(self.__abstractDictionary)
        self.__logTermByDocMatrix(self.__bodyDictionary)
        
    def __logTermByDocMatrix(self, dictionary):
        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        
        matrixString = ''
        for row in tdocMatrix:
            rowString = ','.join(['%.5f' % wij for wij in row])
            rowString += '\n'
            matrixString += rowString
            
        docVectorString = ','.join(['%s' % docID for docID in docVector])
        termVectorString = ','.join(['%s' % term for term in termVector])
        
        now = '../logs/' + re.sub('\s','_', '%s' % datetime.datetime.now())
        now = re.sub(':','-', '%s' % now)
                
        logFileName = '%s-termByDoc-matrix_%s.data' % (now, dictionary.name)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(matrixString)
        
        logFileName = '%s-docVector_%s.data' % (now, dictionary.name)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(docVectorString)
        
        logFileName = '%s-termVector_%s.data' % (now, dictionary.name)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(termVectorString)
        
        
    def __buildCitationsLinks(self):

        self.__condition.acquire()
        print "[%s] Building citation graph on a set of %d papers..." % (threading.currentThread().getName(), len(self.__knownPapers.keys()))
        DEBUG_counter = 0
        DEBUG_citationStringsAnalyzed = 0
        DEBUG_citationStringsTotal = 0
        DEBUG_time_start = datetime.datetime.now()
        
        for paperURN in self.__knownPapers.keys():
            paper = self.__knownPapers.get(paperURN)
            
            if hasattr(paper, 'bibliography'):
                for reference in paper.bibliography.getReferences():
                    DEBUG_citationStringsTotal += 1
                    if not hasattr(reference, 'describe'):
                        citedPaper = self.lookForCitedPaper(reference)
                        DEBUG_citationStringsAnalyzed += 1
                        if citedPaper:
                            reference.setDescribe(citedPaper)
                            citedPaper.addCitingPaper(paper)
                            print "[%s] Indexed reference: '%s' --> '%s' (now is cited by %d)" % (threading.currentThread().getName(), paper.title, citedPaper.title, len(citedPaper.getCitingPapers()))                
                            DEBUG_counter += 1
                          
 
        DEBUG_time_job = datetime.datetime.now() - DEBUG_time_start         
        #print "[%s] Citation graph built in %d seconds. %d reference strings analyzed. Added %d new edges." % (threading.currentThread().getName(), DEBUG_time_job.seconds, DEBUG_citationStringsAnalyzed, DEBUG_counter)
        self.__knownPapers.committ()#FIXME
        self.__condition.release()
        print "[%s] Citation graph built in %d seconds. %d reference strings analyzed. Added %d new edges." % (threading.currentThread().getName(), DEBUG_time_job.seconds, DEBUG_citationStringsAnalyzed, DEBUG_counter)
                
    def lookForCitedPaper__DEPRECATED(self, reference):
        threshold = 15
        
        if hasattr(reference, 'title'):
            results = {}
            for paperURN in self.__knownPapers.keys():
                paper = self.__knownPapers.get(paperURN)
                editDistance = common.stringdiff.levenshtein(reference.title, paper.title)
                if editDistance < threshold:
                    results[paper] = editDistance
                    
            best = heapq.nsmallest(1, results.iteritems(), heapq.itemgetter(1))
            if len(best)>0:
                bestPaper = best[0][0]
                reference.setDescribe(bestPaper)  
                return bestPaper
            
        return None
    
    def lookForCitedPaper___DEPRECATED__20090402(self, reference):
        if hasattr(reference, 'title'):
            print "\n_______REFERENCE _%s_" % reference.title
            
            query = common.nlp.filter_punctuation_from_words(re.split('\s', reference.title.lower()))
            query = common.nlp.remove_hypens_from_words(query)
            
            #resultSet = self.queryAll(query, 0.90, 3)
            resultSet = self.queryTitle(query, 3)
            
            if len(resultSet)>0:
                
                
                
                
                
                bestScore = resultSet[0][1]
                
                print "    bestScore is %.3f (%s)" % (bestScore, resultSet[0][0].title)
                
                if bestScore>0.40:
                            
                    wordsInTheCandidate = common.nlp.filter_punctuation_from_words( re.split('\s', resultSet[0][0].title.lower()) )
                    wordsInTheCandidate = common.nlp.remove_hypens_from_words(wordsInTheCandidate)
                    
                    numOfOverlappingWords = float(0)
                    
                    for word in wordsInTheCandidate:
                        if word in query:
                            numOfOverlappingWords += 1 
                    
                    overlapRatio = numOfOverlappingWords / float( len(wordsInTheCandidate) )
                    
                    #print wordsInTheCandidate
                    #print query
                    
                    
                    #if hasattr(reference, 'authors'):
                    #    print "Authors reference are %s" % reference.authors
                    #if hasattr(resultSet[0][0], 'authors'):
                        #authorsList = resultSet[0][0].authors
                    #    authorsNames = [author.name for author in resultSet[0][0].authors]
                    #    print "Paper authors are %s" % authorsNames
                    
                    if overlapRatio > 0.85:
                        print "[%s] (%f, %f) _%s_ ~ _%s_" % (threading.currentThread().getName(), resultSet[0][1], overlapRatio, reference.title, resultSet[0][0].title)
                        return resultSet[0][0]


    def lookForCitedPaper(self, reference):
        if hasattr(reference, 'title'):
            #print "\n_______REFERENCE _%s_" % reference.title
            
            query = common.nlp.filter_punctuation_from_words(re.split('\s', reference.title.lower()))
            query = common.nlp.remove_hypens_from_words(query)
            
            resultSet = self.queryAll(query, 0.90, 5)
            #resultSet = self.queryTitle(query, 3)
            
            refine = {}
            for result in resultSet:
                
                (currentPaper, currentScore, pageRank) = result
                
                wordsInTheCandidate = common.nlp.filter_punctuation_from_words( re.split('\s', currentPaper.title.lower()) )
                wordsInTheCandidate = common.nlp.remove_hypens_from_words(wordsInTheCandidate)
                
                numOfOverlappingWords = float(0)
                    
                for word in wordsInTheCandidate:
                    if word in query:
                        numOfOverlappingWords += 1 
                
                overlapRatio = numOfOverlappingWords / float( len(wordsInTheCandidate) )
                
                refine[currentPaper] = overlapRatio
                
            if len( refine.keys() )>0:
                
                bestRefined = heapq.nlargest(1, refine.iteritems(), heapq.itemgetter(1))
                
                (bestPaper, bestScore) = bestRefined.pop()
                
                #print "    bestOverlapScore is %.3f (%s)" % (bestScore, bestPaper.title)
                
                if bestScore > 0.85:
                    print "[%s] (%f) _%s_ ~ _%s_" % (threading.currentThread().getName(), bestScore, reference.title, bestPaper.title)
                    return bestPaper
                else:
                    pass
                    #print "not enough %.3f" % bestScore
        return None
                    
    
    
    def indexText(self, document, textToIndex, index):
        #print "Indexing text _%s_ in the %s..." % (textToIndex, index.name)
        
        #listOfWordsToIndex = common.nlp.filterWords(textToIndex)
        listOfWordsToIndex = common.nlp.filterWords__V2(textToIndex)
        ####listOfWordsToIndex = common.nlp.stemWords(listOfWordsToIndex)
        print "[%s] Indexing %d words in the %s..." % (threading.currentThread().getName(), len(listOfWordsToIndex), index.name)
        ii = {}
        for word in listOfWordsToIndex:
            if ii.has_key(word):
                ii[word] += 1
            else:
                ii[word] = 1
                
        time_start = datetime.datetime.now()
        for term in ii.keys():
            frequency = ii[term]
            index.addTerm(term, document, frequency)
        index.committ() ##FIXME
        time_end = datetime.datetime.now()
        time_job = time_end - time_start
        print "[%s] %d words inserted into the %s dictionary. It took %d s, %d us" % (threading.currentThread().getName(), len(listOfWordsToIndex), index.name, time_job.seconds, time_job.microseconds)
            
        #print "[%s] calculating global idf for the collection of %d documents in the %s index..." % (threading.currentThread().getName(), len(self.__knownPapers.keys()), index.name)
        
        time_start = datetime.datetime.now()
        
        index.updateIDF( len(self.__knownPapers.keys()) )
        
        time_end = datetime.datetime.now()
        time_job = time_end - time_start
        
        #self.logAbstractTermByDocMatrix() ##FIXME
        
        #print "[%s] Global idf computed in %d s, %d us" % (time_job.microseconds)
        print "[%s] Global idf for %d documents in the %s index computed in %d s, %d us" % (threading.currentThread().getName(), len(self.__knownPapers.keys()), index.name, time_job.seconds, time_job.microseconds)
        
    def getListOfPaperIDs(self):
        listOfPaperIDs = [paperID for paperID in self.__knownPapers.keys()]
        #print "keys is _%s_" % self.__knownPapers.keys()
        #print "lopID is _%s_" % listOfPaperIDs
        listOfPaperIDs.sort()
        #print "ordered list is _%s_" % listOfPaperIDs
        return listOfPaperIDs
        
        
    def buildAdjacencyMatrix(self):
        
        listOfPaperIDs = self.getListOfPaperIDs()
            
        #print "LIST OF PAPERS:"
        counter = 1
        #print listOfPaperIDs
        for paperID in listOfPaperIDs:
            title = self.__knownPapers.get(paperID).title
            if len(title) > 50:
                title = title[:50] + "..."
            #print "%d\t%s\t%s" % (counter, paperID, title)
            counter += 1
        #print "\n"
        
        adjacencyMatrix = []
        for paperID in listOfPaperIDs:
            paper = self.__knownPapers.get(paperID)
            
            citedBy = paper.getCitingPapers()
            row = []
            for paperID in listOfPaperIDs:
                if paperID in citedBy:
                    row.append(-1)
                else:
                    row.append(0)
            adjacencyMatrix.append(row)
            #print row
        
        #print adjacencyMatrix
        
        return (listOfPaperIDs, adjacencyMatrix)
        
        
    def calculatePageRank(self, alpha=0.85):
        
        def __transposed(lists):
            if not lists:
                return []
            return map(lambda *row: list(row), *lists)
        
        def __outGoingLinksMatrix(adjacencyMatrix):
            transposed = __transposed(adjacencyMatrix)
            rowNum = 0
            for row in transposed:
                column = 0
                for element in row:
                    if element == -1:
                        transposed[rowNum][column] = 1
                    column += 1
                rowNum += 1
            return transposed
        
        def __buildLinkMatrix(adjacencyMatrix):
            transposed = __transposed(adjacencyMatrix)
            rowNum = 0
            linkMatrix = []
            for row in transposed:
                column = 0
                nodeLinks = []
                for element in row:
                    if element == -1:
                        transposed[rowNum][column] = 1
                        nodeLinks.append(column)
                    column += 1
                rowNum += 1
                linkMatrix.append(nodeLinks)
            return linkMatrix
            

        print "[%s] calculating PageRank..." % threading.currentThread().getName()
        
        (listOfPaperIDs, adjacencyMatrix) = self.buildAdjacencyMatrix()
        if not len(listOfPaperIDs) > 0:
            raise Exception
        
        #for i in range(len(listOfPaperIDs)):
            #print "%s\t\t%s" % (listOfPaperIDs[i], adjacencyMatrix[i])
            
        linksList = __buildLinkMatrix(adjacencyMatrix)
        
        #example of graph from figure 21.4 of Introduction to Information Retrieval
        #should return eq. 21.6
        #linksList = [[2],[1,2],[0,2,3],[3,4],[6],[5,6],[3,4,6]]
        #alpha = 0.86
        
        (incomingLinks, numLinks, leafNodes) = pageRank.transposeLinkMatrix(linksList)
        #print "DEBUG IncomingLinks = _%s_" % incomingLinks
        #print "DEBUG numLinks = _%s_" % numLinks
        #print "DEBUG leafNodes = _%s_" % leafNodes
        
        tstart = datetime.datetime.now()
        pageRankVector = pageRank.pageRank(linksList, alpha)
        tend = datetime.datetime.now()
        delta = tend - tstart
        
        sum = float(0)
        for element in pageRankVector:
            sum += element
            
        print "[%s] PageRank vector computed in %d s, %s us" % (threading.currentThread().getName(), delta.seconds, delta.microseconds)
        #print "alpha=%.2f, PR=_%s_, norm=%.2f" % (alpha, pageRankVector, sum)
            
        #Method 2
        #print "peterbe algorithm"
        #outGoingLinks = __outGoingLinksMatrix(adjacencyMatrix)
        #for row in outGoingLinks:
        #    print row
        #pr = peterbePageRank.PageRanker(0.86, outGoingLinks)
        #pr.improve_guess(100)
        #print pr.getPageRank()
        
        return pageRankVector
    
    #----------------
    #SEARCH FUNCTIONS
    #----------------
    
    def getCitingPapers(self, paperURN):
        if self.__knownPapers.contains(paperURN):
            paper = self.__knownPapers.get(paperURN)
            citingPapers = paper.getCitingPapers()
            #print "%s %s is cited by %d" % (paper.urn, paper.title, len(citingPapers))
            return [self.__knownPapers.get(paperURN) for paperURN in citingPapers]
        
    def searchForAuthors(self, authorQuery):
        if not len(authorQuery) > 0:
            return None
        authorQuery = authorQuery[0]
        
        resultSet = []
        for authorURN in self.__knownAuthors.keys():
            author = self.__knownAuthors.get(authorURN)
            #print author.name
            if authorQuery in [name.lower() for name in re.split('\s', author.name)]:
                writtenPapers = author.getWrittenPapers()
                #print "%s wrote %d papers" %(author.name, len(writtenPapers))
                for paper in writtenPapers:
                    #print "%s, %d citations" % (paper.title, paper.getCitingPapers())
                    #print "%s %s is cited by %d" % (paper.urn, paper.title, len(paper.getCitingPapers()))
                    if not resultSet.__contains__(paper):
                        resultSet.append(paper)
                    
        return resultSet
    
    def computeSimilarity__DEPRECATED(self, docJ={}, docK={}):
        
        #Normalization of vectors
        sumJ = 0
        for component in docJ.keys():
            sumJ += math.pow( docJ[component], 2 )
        normDocJ = math.sqrt(sumJ)
        
        sumK = 0
        for component in docK.keys():
            sumK += math.pow( docK[component], 2 )
        normDocK = math.sqrt(sumK)
        
        for component in docJ.keys():
            docJ[component] = float(docJ[component]) / float(normDocJ)
            
        for component in docK.keys():
            docK[component] = float(docK[component]) / float(normDocK)
            
        dotProduct = 0
        for component in docJ.keys():
            if component in docK.keys():
                dotProduct += docJ[component]*docK[component]
        
        similarity = float(dotProduct)
        return similarity
        
    def queryIDF__DEPRECATED(self, query=[]):
        
        #def computeSimilarity
        
        print "[%s] Searching for documents that are relevant to the query %s" % (threading.currentThread().getName(), query)
        resultSet = {}
        for term in query:
            if self.__abstractDictionary.contains(term):
                print "\n[%s] The dictionary contains the term _%s_" % (threading.currentThread().getName(), term)
                postingFile = self.__abstractDictionary.getPostingFile(term)
                for docID in postingFile.keys():                    
                    if not resultSet.has_key(docID):
                        resultSet[docID] = float(0)
                    resultSet[docID] += postingFile[docID][1]
                    print "[%s] doc _%s_ w=%f\tDocScore=%f" % (threading.currentThread().getName(), docID, postingFile[docID][1], resultSet[docID])
                    
        k = 10
        topK = heapq.nlargest(k, resultSet.iteritems(), heapq.itemgetter(1))
        #print "Found %d results" % len(topK)
        
        res = []
        for item in topK:
            paperURN = item[0]
            #print "paperURN %s has a similarity of %f" % (paperURN, item[1])
            paper = self.__knownPapers.get(paperURN)
            res.append((paper, item[1]))
        return res
    
    def __queryDictionary__BUGGED_OLD(self, query, dictionary):
        
        resultSet = {}
        for term in query:
            if dictionary.contains(term):
                #print "\n[%s] The dictionary %s contains the term _%s_" % (threading.currentThread().getName(), dictionary.name, term)
                postingFile = dictionary.getPostingFile(term)
                for docID in postingFile.keys():
                    if not resultSet.has_key(docID):
                        resultSet[docID] = float(0)
                    resultSet[docID] += postingFile[docID][1]
                    #print "[%s] doc _%s_ w=%f\tDocScore=%f" % (threading.currentThread().getName(), docID, postingFile[docID][1], resultSet[docID])
                    
        return resultSet
    
    
    def __queryDictionary__BUGGED(self, query, dictionary):
        
        resultSet = {}
        for term in query:
            if dictionary.contains(term):
                #print "\n[%s] The dictionary %s contains the term _%s_" % (threading.currentThread().getName(), dictionary.name, term)
                postingFile = dictionary.getPostingFile(term)
                for docID in postingFile.keys():
                    if not resultSet.has_key(docID):
                        resultSet[docID] = float(0)
                    resultSet[docID] += postingFile[docID][1]
                    #print "[%s] doc _%s_ w=%f\tDocScore=%f" % (threading.currentThread().getName(), docID, postingFile[docID][1], resultSet[docID])
                    
        return resultSet
    
    def __queryDictionary(self, query, dictionary):
        
        queryWeights = {}
        for queryTerm in query:
            queryWeights[queryTerm] = float(0)
            
        for term in query:
            if dictionary.contains(term):
                postingFile = dictionary.getPostingFile(term)
                Ni = len( postingFile.keys() )
                idf = math.log( float(len(self.__knownPapers.keys())) / float(Ni) )
                queryWeights[term] += idf#tf supposed = 1
                
        queryNorm = float(0)
        for queryTerm in query:
            queryNorm += math.pow(queryWeights[queryTerm],2)
        queryNorm = math.sqrt(queryNorm)
        
        ###ONLY FOR DEBUGGING ISSUES
        #print "\t\tQuery norm=%.2f"%queryNorm
        #print "\t\tqueryWeights= _%s_\n" % queryWeights
        if queryNorm>0:
            accumulaPeso = float(0)
            for qt in queryWeights.keys():
                if queryWeights[qt]>0:
                    peso = queryWeights[qt]/queryNorm
                    accumulaPeso += peso*peso
                    #print "%s --> (%.3f)" % (qt, peso)
            #print "   norm is %.3f (in dictionary _%s_)" % (math.sqrt(accumulaPeso), dictionary.name)
             
            
        resultSet = {}    
        for term in query:
            if dictionary.contains(term):
                postingFile = dictionary.getPostingFile(term)   
                for docID in postingFile.keys():
                    if not resultSet.has_key(docID):
                        resultSet[docID] = float(0)
                    #print "term=_%s_, w=%.2f" % (term, postingFile[docID][1])
                    if not queryNorm==0:
                        resultSet[docID] += postingFile[docID][1]*(queryWeights[term]/queryNorm)
        #print resultSet
        return resultSet    
    
    def __queryZones__DEPRECATED(self, query=[]):
        
        resultSet = {}
        
        alpha = 0.6
        beta = 0.4
        
        resultSetA = self.__queryDictionary(query, self.__titleDictionary)
        resultSetB = self.__queryDictionary(query, self.__abstractDictionary)
        
        for docID in resultSetA:
            resultSet[docID] = resultSetA[docID] * alpha
            
        for docID in resultSetB:
            
            if not resultSet.has_key(docID):
                resultSet[docID] = float(0)
                
            resultSet[docID] += resultSetB[docID] * beta
            
        return resultSet
    
    def computeTopKResults__DEPRECATED(self, resultSet, numOfResults=10):
        k = numOfResults
        topK = heapq.nlargest(k, resultSet.iteritems(), heapq.itemgetter(1))
        
        res = []
        for item in topK:
            paperURN = item[0]
            #print "paperURN %s has a similarity of %f" % (paperURN, item[1])
            paper = self.__knownPapers.get(paperURN)
            res.append((paper, item[1]))
        return res
    
    def computeTopKResults(self, resultSet, numOfResults=10):
        k = numOfResults
        topK = heapq.nlargest(k, resultSet.iteritems(), heapq.itemgetter(1))
        
        res = []
        for item in topK:
            paperURN = item[0]
            #print "paperURN %s has a similarity of %f" % (paperURN, item[1])
            paper = self.__knownPapers.get(paperURN)
              
            pagerank = -1
            if self.__pageRankVector.has_key(paperURN):
                pagerank = self.__pageRankVector[paperURN]
            
            res.append((paper, item[1], pagerank))
        return res
    
    def queryTitle(self, query=[], numOfResults=10):
        
        #print "[%s] Searching in the title for %s" % (threading.currentThread().getName(), query)
        
        resultSet = self.__queryDictionary(query, self.__titleDictionary)
        return self.computeTopKResults(resultSet, numOfResults)
    
    def queryAbstract(self, query=[]):
        
        print "[%s] Searching in the abstract for %s" % (threading.currentThread().getName(), query)
        
        resultSet = self.__queryDictionary(query, self.__abstractDictionary)
        return self.computeTopKResults(resultSet)
    
    def queryAll(self, query=[], alpha=0.6, numOfResults=10, printDEBUG=True):
        
        #print "[%s] Searching everywhere for %s" % (threading.currentThread().getName(), query)
        
        resultSet = {}
        
        beta = 1 - alpha
        
        resultSetA = self.__queryDictionary(query, self.__titleDictionary)
        resultSetB = self.__queryDictionary(query, self.__abstractDictionary)
        
        for docID in resultSetA:
            resultSet[docID] = resultSetA[docID] * alpha
            
        for docID in resultSetB:
            
            if not resultSet.has_key(docID):
                resultSet[docID] = float(0)
                
            resultSet[docID] += resultSetB[docID] * beta
            
        return self.computeTopKResults(resultSet, numOfResults)
    
    def queryAll_fullText(self, query=[], alpha=0.6, numOfResults=10, printDEBUG=True):
        
        #print "[%s] Searching everywhere for %s" % (threading.currentThread().getName(), query)
        
        #score = alpha * score_title + beta * score_abstract * gamma * score_body
        #alpha + beta + gamma = 1
        
        alpha = float(0.40)
        beta = float(0.35)
        gamma = 1 - (alpha + beta)
        
        resultSet = {}
        
        beta = 1 - alpha
        
        resultSetA = self.__queryDictionary(query, self.__titleDictionary)
        resultSetB = self.__queryDictionary(query, self.__abstractDictionary)
        resultSetC = self.__queryDictionary(query, self.__bodyDictionary)
        
        for docID in resultSetA:
            resultSet[docID] = resultSetA[docID] * alpha
            
        for docID in resultSetB:
            if not resultSet.has_key(docID):
                resultSet[docID] = float(0)
                
            resultSet[docID] += resultSetB[docID] * beta
            
        for docID in resultSetC:
            if not resultSet.has_key(docID):
                resultSet[docID] = float(0)
                
            resultSet[docID] += resultSetC[docID] * gamma
            
        return self.computeTopKResults(resultSet, numOfResults)
                