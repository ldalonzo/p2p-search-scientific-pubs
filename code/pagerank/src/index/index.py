#!/usr/bin/env python

"""
written by Leonardo D'Alonzo - leonardo.dalonzo@gmail.com

version of 2008/12/23
version of 2008/12/26
version of 2009/01/06
"""

import codecs
import datetime
import heapq
import math
import re
import threading

import peterbePageRank

import os

from pdfparser import PDFPaperParser
import common.stringdiff
import storage
import pageRank
import common.nlp
from core.core import PDFResource
from core.core import Paper
from core.core import Author

class Index():
    
    def __init__(self):
        
        self.__knownResources = storage.KnownResources()
        self.__knownAuthors = storage.KnownAuthors()
        self.__knownPapers = storage.KnownPapers()
        
        self.__abstractDictionary = storage.Dictionary('abstract')
        self.__titleDictionary = storage.Dictionary('title')
        
        self.__condition = threading.Condition()
        
    def submitPDF_DEBUG(self):
        self.indexText(None, "", self.__titleDictionary)
        self.__queryDictionary(['mob', 'zero-configuration', 'high-throughput', 'grid', 'multicasting', 'applications', 'tribler'], self.__titleDictionary)
    
    def submitPDF(self, pdfFileURL):
        
        self.__condition.acquire()
        print "[%s] %s submitted. Analyzing..." % (threading.currentThread().getName(), pdfFileURL)
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
                        pass
                        #self.indexText(paper, paper.abstract, self.__abstractDictionary)
                    else:
                        print "[%s] ERROR Unable to index the abstract of '%s'" % (threading.currentThread().getName(), paper.title)
                    
                if pdfParser.fulltext:
                    paper.fulltext = pdfParser.fulltext
                    
                self.__condition.release()
                self.buildCitationsLinks() ##The reference graph is updated every time a paper is added
                return paper
            
            else:
                print "[%s] Unable to retrieve enough metadata from %s. It will not be indexed." % (threading.currentThread().getName(), pdfFileURL)
                self.__condition.release()
                return None

        except (OSError):
            print "[%s] There was an exception on analyzing %s" % (threading.currentThread().getName(), pdfFileURL)
            self.__condition.release()
            return None
        
    #def clearCitationsLinks(self):
        
        
    def buildCitationsLinks(self):

        self.__condition.acquire()
        print "[%s] Building citation graph on a set of %d papers..." % (threading.currentThread().getName(), len(self.__knownPapers.keys()))
        DEBUG_counter = 0
        DEBUG_citationStringsAnalyzed = 0
        DEBUG_citationStringsTotal = 0
        DEBUG_numOfDocuments = len(self.__knownPapers.keys())
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
                            if paper.urn == citedPaper.urn:
                                #print "DEBUG autoreference! skipping..."
                                pass
                            else:
                                reference.setDescribe(citedPaper)
                                citedPaper.addCitingPaper(paper)
                                #print "[%s] Indexed reference: '%s' --> '%s' (now is cited by %d)" % (threading.currentThread().getName(), paper.title, citedPaper.title, len(citedPaper.getCitingPapers()))                
                                DEBUG_counter += 1
                          
 
        DEBUG_time_job = datetime.datetime.now() - DEBUG_time_start         
        print "[%s] Citation graph built in %d s, %d us. %d reference analyzed. Added %d more edges." % (threading.currentThread().getName(), DEBUG_time_job.seconds, DEBUG_time_job.microseconds, DEBUG_citationStringsAnalyzed, DEBUG_counter)
        
        #logString = "%d, %d, %d, %d\n" % (DEBUG_numOfDocuments, DEBUG_citationStringsTotal, DEBUG_citationStringsAnalyzed, DEBUG_time_job.microseconds)
        #logFileName = 'citgraph-stats_k1.txt'
        #logFile = codecs.open(logFileName, 'a', 'utf-8', errors='ignore')
        #logFile.write(logString)
        #logFile.close()
        self.__knownPapers.committ()#FIXME
        self.__condition.release()
          
    def buildAdjacencyMatrix(self):
                
        listOfPaperIDs = [paperID for paperID in self.__knownPapers.keys()]
        listOfPaperIDs.sort()
            
        #print "LIST OF PAPERS:"
        counter = 1
        for paperID in listOfPaperIDs:
            title = self.__knownPapers.get(paperID).title
            if len(title) > 50:
                title = title[:50] + "..."
            #print "%d\t%s\t%s" % (counter, paperID, title)
            counter += 1
        print "\n"
        
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
            
            #for citingPaperURN in citedBy:
            #    print citingPaperURN
                
            
            
            
#            if hasattr(paper, 'bibliography'):
#                for reference in paper.bibliography.getReferences():
#                    citedPaperURN = reference.getTarget()
#                    if citedPaperURN:
#                        print citedPaperURN
#                    else:
#                        print "NO target"

    def dotCode(self, listOfPaperIDs, adjacencyMatrix):
        
        pageRankVector = self.calculatePageRank(adjacencyMatrix, 0.85)
        
        PR_largest = float(0)
        PR_smallest = float(1)
        for PR_entry in pageRankVector:
            if PR_entry > PR_largest:
                PR_largest = PR_entry
            if PR_entry < PR_smallest:
                PR_smallest = PR_entry
        PR_delta = PR_largest-PR_smallest
        
        PR_maxScaleValue = float(0.45)
        PR_scaleFactor = PR_maxScaleValue/PR_largest
        #print "deltaPR=%.2f, scale_factor=%.2f" % (PR_delta, PR_scaleFactor) 
        
        visualPR = []
        for PR_entry in pageRankVector:
            visualPR_entry = PR_entry*PR_scaleFactor
            visualPR.append(visualPR_entry)
        #print "visualPR = _%s_" % visualPR
        
        
        visualPR_log = []
        #log_scale_factor = 
        for PR_entry in pageRankVector:
            visualPR_entry = math.log(PR_entry/PR_smallest)
            visualPR_log.append(visualPR_entry)
            
        PR_largest_log = float(0)
        for PR_entry in visualPR_log:
            if PR_entry > PR_largest_log:
                PR_largest_log = PR_entry
                
        LPR_maxScaleValue = float(0.60)
        LPR_scaleFactor = LPR_maxScaleValue/PR_largest_log
        #print "deltaPR=%.2f, scale_factor=%.2f" % (PR_delta, PR_scaleFactor) 
        
        LOGvisualPR = []
        for item in visualPR_log:
            entry = item*LPR_scaleFactor
            LOGvisualPR.append(entry)
            
        #print "visualPR_log = _%s_" % visualPR_log
        
        code = "digraph citation_graph {\n"
        
        #colorScheme = 'spectral10'
        #colorScheme = 'set310'
        #colorScheme = 'oranges9'
        colorScheme = 'ylgnbu9'
        #colorScheme = 'pubugn9'
        
        
        
        
        code += "graph [margin=0, ratio=.8, sep=.10, overlap=false, splines=true, ranksep=""0.2""];\n"
        code += 'node [colorscheme=%s, fontname="Times-Roman-Oblique", style=filled, fillcolor=\"#def5ff\", fontsize=40];\n' % colorScheme
        code += "edge [arrowhead=normal, arrowsize=3];\n"
        
        code += "\n/* Nodes */\n"
        paperIndex = 1
        for paperID in listOfPaperIDs:
            title = self.__knownPapers.get(paperID).title
            if len(title) > 22:
                title = title[:22] + "..."
            if len(title) > 10:
                spl = re.split('[\s]+', title)
                title=''
                line = ''
                for word in spl:
                    line += "%s" % word
                    if len(line)>7:
                        #line += "\\n"
                        title += "%s\\n" % line
                        line = ''
                    else:
                        line += " "
                title += line
            pageRankValue = pageRankVector[paperIndex-1]
                #pageRankVisual =  visualPR[paperIndex-1]
            pageRankVisual =  LOGvisualPR[paperIndex-1]
            #print "ultimo carattere = _%s_" % title[len(title)-1]
            if not (title[len(title)-2] == '\\' and title[len(title)-1] == 'n'):
                title += '\\n'
            title += "%.4f" % pageRankValue
            #title += "%d" % int(pageRankValue*1000)
                        
            #B [label="The boss"]      // node B
            colorScale = math.ceil(pageRankVisual*10)+1
            code += "%d [label=\"%s\", fillcolor=%d];  // node %s\n" % (paperIndex, "[" + paperID + "]\\n" + title, colorScale, paperID)
            paperIndex +=1
            
        code += "\n/* Edges */\n"
        rowIndex = 0
        for row in adjacencyMatrix:
            toEdge = rowIndex#listOfPaperIDs[rowIndex]
            
            columnIndex = 0
            for edge in row:
                if edge == -1:
                    fromEdge = columnIndex#listOfPaperIDs[columnIndex]
                    
                    #B->E [label="commands", fontcolor=darkgreen] // edge B->E
                    #code += "%s->%s // edge %s->%s\n" %(fromEdge, toEdge, fromEdge, toEdge)
                    code += "%s->%s;\n" %((fromEdge+1), (toEdge+1))
                columnIndex +=1
            
            rowIndex +=1
            
        code += "}\n"
        #print code
        return code
    
    def createDotCode(self):
        (listOfPaperIDs, adjacencyMatrix) = self.buildAdjacencyMatrix()
        code = self.dotCode(listOfPaperIDs, adjacencyMatrix)
        
        logFileName = 'citgraph.dot'
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(code)
        logFile.close()
        
        logFileName = 'adjmatrix.txt'
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        
        for row in adjacencyMatrix:
            for edge in row:
                line = "%d " % edge
                logFile.write(line)
            line = "\n"
            logFile.write(line)
        logFile.close()
        
    def calculatePageRank(self, adjacencyMatrix=None, alpha=0.85):
        
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
            

        print "Calculating PageRank..."
        
        (listOfPaperIDs, adjacencyMatrix) = self.buildAdjacencyMatrix()
        
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
            
        print "PageRank vector computed in %d s, %s us" % (delta.seconds, delta.microseconds)
        print "alpha=%.2f, PR=_%s_, norm=%.2f" % (alpha, pageRankVector, sum)
            
        #Method 2
        #print "peterbe algorithm"
        #outGoingLinks = __outGoingLinksMatrix(adjacencyMatrix)
        #for row in outGoingLinks:
        #    print row
        #pr = peterbePageRank.PageRanker(0.86, outGoingLinks)
        #pr.improve_guess(100)
        #print pr.getPageRank()
        
        return pageRankVector
                
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
    
    def lookForCitedPaper(self, reference):
        if hasattr(reference, 'title'):
            
            #print "____________\nAnalyzing _%s_" % reference.title
            
            query = common.nlp.filter_punctuation_from_words(re.split('\s', reference.title.lower()))
            query = common.nlp.remove_hypens_from_words(query)
            
            KSizeOfFilterSet = 5
            filterResultSet = self.queryAll(query, 0.95, KSizeOfFilterSet)
            filterResultSetDictionary = {}
            refineResultSet = {}
            if len(filterResultSet)>0:
                for result in filterResultSet:
                    (paper,score) = result
                    
                    filterResultSetDictionary[paper] = score
                    
                    if score > 0.20:
                        wordsInTheCandidate = common.nlp.filter_punctuation_from_words( re.split('\s', paper.title.lower()) )
                        wordsInTheCandidate = common.nlp.remove_hypens_from_words(wordsInTheCandidate)
                        #print wordsInTheCandidate
                        #print query
                        numOfOverlappingWords = float(0)
                        for word in wordsInTheCandidate:
                            if word in query:
                                numOfOverlappingWords += 1
                        if not wordsInTheCandidate == 0:
                            overlapRatio = numOfOverlappingWords / float( len(wordsInTheCandidate) )
                            
                        refineResultSet[paper] = overlapRatio
                        
            
                        
            if len(refineResultSet.keys())>0:
                #print "refine resultset = _%s_" % refineResultSet
                bestResultOverlap = heapq.nlargest(1, refineResultSet.iteritems(), heapq.itemgetter(1))
                (bestPaper, titleOverlapRatio) = bestResultOverlap[0]
                #print "bestResultOverlap = %s" % bestResultOverlap
                #print  bestResultOverlap[0]
                #print "overlap=%.2f" % overlapRatio
                
                if titleOverlapRatio > 0.85:
                    #print "EUREKA!!!! (score=%f, overlap=%f) _%s_ ---> _%s_" % (filterResultSetDictionary[bestPaper], titleOverlapRatio, reference.title, bestPaper.title)
                    return bestPaper
                else:
                    #print "I'm sorry: overlapRatio is only %.2f" % titleOverlapRatio
                    pass
            
            return None
                        
                        
#                k = numOfResults
#                
#        
#                
#                
#                bestScore = resultSet[0][1]
#                
#                if bestScore>0.21:#0.60:
#                            
#                    wordsInTheCandidate = common.nlp.filter_punctuation_from_words( re.split('\s', resultSet[0][0].title.lower()) )
#                    wordsInTheCandidate = common.nlp.remove_hypens_from_words(wordsInTheCandidate)
#                    
#                    numOfOverlappingWords = float(0)
##                    
#                    for word in wordsInTheCandidate:
#                        if word in query:
#                            numOfOverlappingWords += 1 
#                    
#                    overlapRatio = numOfOverlappingWords / float( len(wordsInTheCandidate) )
                    
                    #print wordsInTheCandidate
                    #print query
                    
                    
                    
                    
                    #if hasattr(reference, 'authors'):
                    #    print "Authors reference are %s" % reference.authors
                    #if hasattr(resultSet[0][0], 'authors'):
                        #authorsList = resultSet[0][0].authors
                    #    authorsNames = [author.name for author in resultSet[0][0].authors]
                    #    print "Paper authors are %s" % authorsNames
                    
#                    if overlapRatio > 0.85:
#                        print "(score=%f, overlap=%f) _%s_ ---> _%s_" % (resultSet[0][1], overlapRatio, reference.title, resultSet[0][0].title)
#                        return resultSet[0][0]
#                    else:
#                        #print "\nNOLINK (%f, %f) _%s_ ---> _%s_" % (resultSet[0][1], overlapRatio, reference.title, resultSet[0][0].title)
#                        #return resultSet[0][0]
#                        print " overlap < TH=0.85 (score=%f, overlap=%f) _%s_(REF) ---> _%s_(docTITLE)" % (resultSet[0][1], overlapRatio, reference.title, resultSet[0][0].title)
#                        return None
                    
                    
    
    
    def indexText(self, document, textToIndex, index):
        #print "Indexing text _%s_ in the %s..." % (textToIndex, index.name)
        
        listOfWordsToIndex = common.nlp.filterWords(textToIndex)
        
        #print "list of words = _%s_" % listOfWordsToIndex
        
        ii = {}
        for word in listOfWordsToIndex:
            if ii.has_key(word):
                ii[word] += 1
            else:
                ii[word] = 1
        
        #print ii.keys()        
        
        for term in ii.keys():
            #print "sono qui! term=_%s_, len_ii=%d" % (term, len(ii.keys()) )
            frequency = ii[term]
            index.addTerm(term, document, frequency)
            
        print "[%s] calculating global idf for the collection of %d documents in the %s index..." % (threading.currentThread().getName(), len(self.__knownPapers.keys()), index.name)
        
        time_start = datetime.datetime.now()
        
        index.updateIDF( len(self.__knownPapers.keys()) )
        
        time_end = datetime.datetime.now()
        time_job = time_end - time_start
        
        print "Computation time is %d microseconds" % time_job.microseconds
    
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
        #print "Query norm=%.2f"%queryNorm
        #print "queryWeights= _%s_" % queryWeights
            
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
    
    def computeTopKResults(self, resultSet, numOfResults=10):
        k = numOfResults
        topK = heapq.nlargest(k, resultSet.iteritems(), heapq.itemgetter(1))
        
        res = []
        for item in topK:
            paperURN = item[0]
            #print "paperURN %s has a similarity of %f" % (paperURN, item[1])
            paper = self.__knownPapers.get(paperURN)
            res.append((paper, item[1]))
        return res
    
    def queryTitle(self, query=[]):
        
        #print "[%s] Searching in the title for %s" % (threading.currentThread().getName(), query)
        
        resultSet = self.__queryDictionary(query, self.__titleDictionary)
        return self.computeTopKResults(resultSet)
    
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
            #print resultSet
            
        return self.computeTopKResults(resultSet, numOfResults)
                