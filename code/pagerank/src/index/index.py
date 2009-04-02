#!/usr/bin/env python

import codecs
import datetime
import heapq
import math
import re
import threading
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
                                pass
                            else:
                                reference.setDescribe(citedPaper)
                                citedPaper.addCitingPaper(paper)
                                DEBUG_counter += 1
 
        DEBUG_time_job = datetime.datetime.now() - DEBUG_time_start         
        print "[%s] Citation graph built in %d s, %d us. %d reference analyzed. Added %d more edges." % (threading.currentThread().getName(), DEBUG_time_job.seconds, DEBUG_time_job.microseconds, DEBUG_citationStringsAnalyzed, DEBUG_counter)

        self.__knownPapers.committ()#FIXME
        self.__condition.release()
          
    def buildAdjacencyMatrix(self):
        listOfPaperIDs = [paperID for paperID in self.__knownPapers.keys()]
        listOfPaperIDs.sort()

        counter = 1
        for paperID in listOfPaperIDs:
            title = self.__knownPapers.get(paperID).title
            if len(title) > 50:
                title = title[:50] + "..."
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

        return (listOfPaperIDs, adjacencyMatrix)

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

        visualPR = []
        for PR_entry in pageRankVector:
            visualPR_entry = PR_entry*PR_scaleFactor
            visualPR.append(visualPR_entry)

        visualPR_log = []
        for PR_entry in pageRankVector:
            visualPR_entry = math.log(PR_entry/PR_smallest)
            visualPR_log.append(visualPR_entry)
            
        PR_largest_log = float(0)
        for PR_entry in visualPR_log:
            if PR_entry > PR_largest_log:
                PR_largest_log = PR_entry
                
        LPR_maxScaleValue = float(0.60)
        LPR_scaleFactor = LPR_maxScaleValue/PR_largest_log

        LOGvisualPR = []
        for item in visualPR_log:
            entry = item*LPR_scaleFactor
            LOGvisualPR.append(entry)

        code = "digraph citation_graph {\n"
        colorScheme = 'ylgnbu9'
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
            pageRankVisual =  LOGvisualPR[paperIndex-1]
            if not (title[len(title)-2] == '\\' and title[len(title)-1] == 'n'):
                title += '\\n'
            title += "%.4f" % pageRankValue
            colorScale = math.ceil(pageRankVisual*10)+1
            code += "%d [label=\"%s\", fillcolor=%d];  // node %s\n" % (paperIndex, "[" + paperID + "]\\n" + title, colorScale, paperID)
            paperIndex +=1
            
        code += "\n/* Edges */\n"
        rowIndex = 0
        for row in adjacencyMatrix:
            toEdge = rowIndex
            
            columnIndex = 0
            for edge in row:
                if edge == -1:
                    fromEdge = columnIndex
                    code += "%s->%s;\n" %((fromEdge+1), (toEdge+1))
                columnIndex +=1
            
            rowIndex +=1
        code += "}\n"
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

        linksList = __buildLinkMatrix(adjacencyMatrix)

        (incomingLinks, numLinks, leafNodes) = pageRank.transposeLinkMatrix(linksList)

        tstart = datetime.datetime.now()
        pageRankVector = pageRank.pageRank(linksList, alpha)
        tend = datetime.datetime.now()
        delta = tend - tstart
        
        sum = float(0)
        for element in pageRankVector:
            sum += element
            
        print "PageRank vector computed in %d s, %s us" % (delta.seconds, delta.microseconds)
        print "alpha=%.2f, PR=_%s_, norm=%.2f" % (alpha, pageRankVector, sum)
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
                        numOfOverlappingWords = float(0)
                        for word in wordsInTheCandidate:
                            if word in query:
                                numOfOverlappingWords += 1
                        if not wordsInTheCandidate == 0:
                            overlapRatio = numOfOverlappingWords / float( len(wordsInTheCandidate) )
                            
                        refineResultSet[paper] = overlapRatio

            if len(refineResultSet.keys())>0:
                bestResultOverlap = heapq.nlargest(1, refineResultSet.iteritems(), heapq.itemgetter(1))
                (bestPaper, titleOverlapRatio) = bestResultOverlap[0]

                if titleOverlapRatio > 0.85:
                    return bestPaper
                else:
                    pass

            return None

    def indexText(self, document, textToIndex, index):
        listOfWordsToIndex = common.nlp.filterWords(textToIndex)

        ii = {}
        for word in listOfWordsToIndex:
            if ii.has_key(word):
                ii[word] += 1
            else:
                ii[word] = 1

        for term in ii.keys():
            frequency = ii[term]
            index.addTerm(term, document, frequency)
            
        print "[%s] calculating global idf for the collection of %d documents in the %s index..." % (threading.currentThread().getName(), len(self.__knownPapers.keys()), index.name)
        
        time_start = datetime.datetime.now()
        
        index.updateIDF( len(self.__knownPapers.keys()) )
        
        time_end = datetime.datetime.now()
        time_job = time_end - time_start
        
        print "Computation time is %d microseconds" % time_job.microseconds
    
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
                queryWeights[term] += idf#tf supposed = 1
                
        queryNorm = float(0)
        for queryTerm in query:
            queryNorm += math.pow(queryWeights[queryTerm],2)
        queryNorm = math.sqrt(queryNorm)

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
            res.append((paper, item[1]))
        return res
    
    def queryTitle(self, query=[]):
        resultSet = self.__queryDictionary(query, self.__titleDictionary)
        return self.computeTopKResults(resultSet)
    
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
