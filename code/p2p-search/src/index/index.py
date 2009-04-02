#!/usr/bin/env python

__author__ = "Leonardo D'Alonzo"
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
        self.__titleDictionary = titleIndex
        self.__abstractDictionary = abstractIndex
        self.__bodyDictionary = bodyIndex
        self.__indexesUpdated = threading.Event()
        self.__indexesUpdated.set()
        self.__pageRankVector = {}
        self.__condition = threading.Condition()

    def getIndexes(self):
        self.__indexesUpdated.wait()
        self.__indexesUpdated.clear()
        self.__condition.acquire()

        titleIndex = self.__titleDictionary
        abstractIndex = self.__abstractDictionary
        bodyIndex = self.__bodyDictionary

        self.__condition.release()

        return (titleIndex, abstractIndex, bodyIndex)

    def submitPDF(self, pdfFileURL):
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
                    
                paper.addResource(pdfFile)
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
                        self.indexText(paper, pdfParser.bodyText, self.__bodyDictionary)

                self.__indexesUpdated.set()
                self.__condition.release()
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

                    if overlapRatio > 0.85:
                        print "[%s] (%f, %f) _%s_ ~ _%s_" % (threading.currentThread().getName(), resultSet[0][1], overlapRatio, reference.title, resultSet[0][0].title)
                        return resultSet[0][0]

    def lookForCitedPaper(self, reference):
        if hasattr(reference, 'title'):
            query = common.nlp.filter_punctuation_from_words(re.split('\s', reference.title.lower()))
            query = common.nlp.remove_hypens_from_words(query)
            resultSet = self.queryAll(query, 0.90, 5)

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

                if bestScore > 0.85:
                    print "[%s] (%f) _%s_ ~ _%s_" % (threading.currentThread().getName(), bestScore, reference.title, bestPaper.title)
                    return bestPaper
                else:
                    pass

        return None

    def indexText(self, document, textToIndex, index):
        listOfWordsToIndex = common.nlp.filterWords__V2(textToIndex)
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

        time_start = datetime.datetime.now()

        index.updateIDF( len(self.__knownPapers.keys()) )

        time_end = datetime.datetime.now()
        time_job = time_end - time_start

        print "[%s] Global idf for %d documents in the %s index computed in %d s, %d us" % (threading.currentThread().getName(), len(self.__knownPapers.keys()), index.name, time_job.seconds, time_job.microseconds)

    def getListOfPaperIDs(self):
        listOfPaperIDs = [paperID for paperID in self.__knownPapers.keys()]
        listOfPaperIDs.sort()

        return listOfPaperIDs

    def buildAdjacencyMatrix(self):
        listOfPaperIDs = self.getListOfPaperIDs()
        counter = 1

        for paperID in listOfPaperIDs:
            title = self.__knownPapers.get(paperID).title
            if len(title) > 50:
                title = title[:50] + "..."
            counter += 1

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

        linksList = __buildLinkMatrix(adjacencyMatrix)

        (incomingLinks, numLinks, leafNodes) = pageRank.transposeLinkMatrix(linksList)

        tstart = datetime.datetime.now()
        pageRankVector = pageRank.pageRank(linksList, alpha)
        tend = datetime.datetime.now()
        delta = tend - tstart
        
        sum = float(0)
        for element in pageRankVector:
            sum += element
            
        print "[%s] PageRank vector computed in %d s, %s us" % (threading.currentThread().getName(), delta.seconds, delta.microseconds)

        return pageRankVector

    def getCitingPapers(self, paperURN):
        if self.__knownPapers.contains(paperURN):
            paper = self.__knownPapers.get(paperURN)
            citingPapers = paper.getCitingPapers()
            return [self.__knownPapers.get(paperURN) for paperURN in citingPapers]

    def searchForAuthors(self, authorQuery):
        if not len(authorQuery) > 0:
            return None
        authorQuery = authorQuery[0]
        
        resultSet = []
        for authorURN in self.__knownAuthors.keys():
            author = self.__knownAuthors.get(authorURN)

            if authorQuery in [name.lower() for name in re.split('\s', author.name)]:
                writtenPapers = author.getWrittenPapers()
                for paper in writtenPapers:
                    if not resultSet.__contains__(paper):
                        resultSet.append(paper)

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
                queryWeights[term] += idf

        queryNorm = float(0)
        for queryTerm in query:
            queryNorm += math.pow(queryWeights[queryTerm],2)
        queryNorm = math.sqrt(queryNorm)

        if queryNorm>0:
            accumulaPeso = float(0)
            for qt in queryWeights.keys():
                if queryWeights[qt]>0:
                    peso = queryWeights[qt]/queryNorm
                    accumulaPeso += peso*peso

        resultSet = {}
        for term in query:
            if dictionary.contains(term):
                postingFile = dictionary.getPostingFile(term)   
                for docID in postingFile.keys():
                    if not resultSet.has_key(docID):
                        resultSet[docID] = float(0)

                    if not queryNorm==0:
                        resultSet[docID] += postingFile[docID][1]*(queryWeights[term]/queryNorm)
        
        return resultSet

    def computeTopKResults(self, resultSet, numOfResults=10):
        k = numOfResults
        topK = heapq.nlargest(k, resultSet.iteritems(), heapq.itemgetter(1))
        
        res = []
        for item in topK:
            paperURN = item[0]
            paper = self.__knownPapers.get(paperURN)

            pagerank = -1
            if self.__pageRankVector.has_key(paperURN):
                pagerank = self.__pageRankVector[paperURN]
            
            res.append((paper, item[1], pagerank))
        return res
    
    def queryTitle(self, query=[], numOfResults=10):

        resultSet = self.__queryDictionary(query, self.__titleDictionary)
        return self.computeTopKResults(resultSet, numOfResults)
    
    def queryAbstract(self, query=[]):
        print "[%s] Searching in the abstract for %s" % (threading.currentThread().getName(), query)
        
        resultSet = self.__queryDictionary(query, self.__abstractDictionary)
        return self.computeTopKResults(resultSet)
    
    def queryAll(self, query=[], alpha=0.6, numOfResults=10, printDEBUG=True):
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
