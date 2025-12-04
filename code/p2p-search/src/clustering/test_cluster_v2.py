import numpy
import math
import heapq
import Pycluster
import re
import datetime
import codecs

#import clustering.cluster

import index.storage
import common.porterStemmer

class Cluster___DEPRECATED():
    
    def __init__(self, documentVector, documentClusterVector):
        
        self.__documentVector = documentClusterVector
        self.__documentClusterVector = documentClusterVector
        
        self.__rss = self.__computeResidualSumOfSquares()
        
    def __computeResidualSumOfSquares(self):
        pass
    
    def __computeClusterCentroid(self):
        pass

#Class centroid
class BestTerms____DEPRECATED():
    
    def __init__(self, termVector, clusterCentroid):
        
        self.__termVector = termVector
        self.__clusterCentroid = clusterCentroid
        
        self.__accumulatorOfBestTerms = []
        
    def approximate(self):
        approximation = {}
        
        k=10
        bestTerms = self.__getKBestStemmedTerms(k)
        if bestTerms:
            for tuple in bestTerms:
                (term, weight) = tuple
                approximation[term] = float(weight)
                
        return approximation     
    
    def __getNextBestTerm(self):
        
        nextBestWeight = 0
        i_position = None
        for i in range( len(self.__clusterCentroid) ):
            if i in self.__accumulatorOfBestTerms:
                pass
            else:
                if self.__clusterCentroid[i] > nextBestWeight:
                    nextBestWeight = self.__clusterCentroid[i]
                    i_position = i
                    
        self.__accumulatorOfBestTerms.append(i_position)
        
        if i_position and nextBestWeight > 0:
            return (self.__termVector[i_position], self.__clusterCentroid[i_position])
                    
        return (None, None)
                    
    def __getNextKBestTerms(self, k):
        bestTerms = []
        for i in range(k):
            (term, weight) = self.__getNextBestTerm()
            if term and weight:
                bestTerms.append( (term,weight) )
            else:
                break
        if len(bestTerms) > 0:
            return bestTerms
        else:
            return None
        
    def __getKBestStemmedTerms(self, k):
        
        ps = common.porterStemmer.PorterStemmer()
        listOfStemmedTerms = []
        
        bestTerms = []
        approxNorm = float(0)
        numOfCollapsed = 0
        while len(listOfStemmedTerms) < k:
            (term, weight) = self.__getNextBestTerm()
            if term and weight:
                stemmedTerm = ps.stem(term, 0, len(term)-1)
                if len(stemmedTerm)>1 and not (stemmedTerm in listOfStemmedTerms):
                    listOfStemmedTerms.append(stemmedTerm)
                    bestTerms.append( (stemmedTerm, weight) )
                else:
                    numOfCollapsed += 1
                    #incrementa conteggio duplicati
                    pass
                #incrementa conteggio approssimazione norma
                approxNorm += math.pow(weight, 2)
            else:
                break
            
        #verifica che la norma sia 1:
        acc = float(0)
        for termW in self.__clusterCentroid:
            acc += math.pow(termW, 2)
        print "Original norm was %.4f" % math.sqrt(acc)
        
        if len(self.__termVector)>0 and acc>0 and len(bestTerms)>0:
                
            
            
            approximationRatio = math.sqrt(approxNorm)/math.sqrt(acc)
            
            approximatedTermsRatio = float( len(bestTerms) )/ len(self.__termVector)
            
            print "Approximated with %d (%d) terms. %d%% - %.4f." % (
                                                                    len(bestTerms),
                                                                    len(bestTerms) + numOfCollapsed,
                                                                    approximatedTermsRatio*100,
                                                                    approximatedTermsRatio)
            print "Norm approximation: %d%% (%.4f)" % (
                                               approximationRatio*100,
                                               approximationRatio)
            return (bestTerms)
        else:
            return None
              

class Clusterizer___DEPRECATED():
    
    def __init__(self, titleIndex, abstractIndex, bodyIndex):
        self.__titleDictionary = titleIndex
        self.__abstractDictionary = abstractIndex
        self.__bodyDictionary = bodyIndex
    
    def something(self, dictionary):
        #(docVector, termVector, tdocMatrix) = self.__abstractDictionary.getTermByDocMatrix()
        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        print "dictionary %s" % dictionary.name
        print "termVector has %d terms" % len(termVector)
        
        print "tdocMatrix %d X %d" % (len(termVector), len(docVector))
        
    def getFirstKTerms(self, clusterCentroid, termVector, k):
        pass
        
    def clusterCentroid(self, dictionary, clusterId = None):
        # @param clusterId Vector of integers showing to which cluster each element belongs.
        # If clusterid is not given, then all elements are assumed to belong to the same
        # cluster.
        
        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        
        centroid = []
        for i in range(len(termVector)):
            centroid.append(float(0))
            
        i = 0
        for row in tdocMatrix:
            for column in row:
                centroid[i] += float( column )
            i += 1
                
        #for i in range(len(docVector)):
        #    print "doc%d Norm = %.3f" % (i, math.sqrt(acc[i]))
        
        accumulator = float(0)
        for i in range( len(termVector) ):
            centroid[i] = centroid[i]/float(len(docVector))
            accumulator += math.pow(centroid[i], 2)
        centroidNorm = math.sqrt(accumulator)
        print "cluster norm is %.4f" % centroidNorm
        
        for i in range( len(termVector) ):
            centroid[i] = centroid[i]/centroidNorm
            
        accumulator = float(0)
        for i in range( len(termVector) ):
            accumulator += math.pow(centroid[i], 2)
        centroidNorm = math.sqrt(accumulator)
        print "cluster norm (hopefully) is %.4f" % centroidNorm
        
        #normalizing centroid
        

         
            
        
        data = numpy.array(tdocMatrix)
        mask = None
        
        # Specifies whether the arithmetic mean (method=='a') or the median (method=='m')
        # is used to calculate the cluster center.
        method = 'a'
        
        # Determines if row or column clusters are being considered. If transpose==0, then
        # we are considering clusters rows. If transpose==1, then we are considering
        # clusters of columns (i.e. document vectors).
        transpose = 1
        
        (cdata, cmask) = Pycluster.clustercentroids(data, mask, clusterId, method, transpose)
        
        print "clusterCentroid length = %d" % len(cdata)
        
        cdataNorm = float(0)
        for component in cdata:
            cdataNorm += math.pow(component, 2)
        cdataNorm = math.sqrt(cdataNorm)
        
        for i in range( len(cdata) ):
            cdata[i] = cdata[i]/cdataNorm
            
        #for i in range( len(cdata) ):
            #print "%.4f ---> (%.4f)\t\t%s" % (cdata[i], centroid[i], termVector[i])
            
        
        
       # for row in tdocMatrix:
       #     print row
            
        ## calculation on Residual Sum of Squares            
        distanceVectors = [float(0) for i in range( len(docVector) )]
        
        i = 0
        for row in tdocMatrix:
            j = 0
            for entry in row:
                #print "(%.2d,%.2d) %.4f" % (i,j, cdata[i])
                entryDistance = math.pow( entry - cdata[i], 2)
                #print "\t%.4f ---> diff = %.4f" % (tdocMatrix[i][j], entryDistance )
                distanceVectors[j] += entryDistance
                j += 1
            i += 1
            
        rss = float(0)
        for distance in distanceVectors:
            rss += distance
        
        print "______________\nResidual Sum of Squares"    
        print "RSS = %.4f" % rss
        
        ##naive implementation
#        print "______________\nmethod A"
#        k=3
#        largestTermsWeights = heapq.nlargest(k, cdata)
#        for i in range( len(cdata) ):
#            if cdata[i] in largestTermsWeights:
#                print "%.2d (%.4f) --> (%s)" % (i, cdata[i], termVector[i])
        
#        print "______________\nmethod B"        
        cluster_centroid = [float(entry) for entry in cdata]
#        bt = BestTerms(termVector, cluster_centroid)
#        resultSetTerms = bt.__getNextKBestTerms(10)
#        for tuple in resultSetTerms:
#            
#            porter = common.porterStemmer.PorterStemmer()
#            word = tuple[0]
#            sword = porter.stem(word, 0, len(word)-1)
#            
#            print "(%.3f) %s --> %s" % (tuple[1], tuple[0], sword)
            
        
        print "______________\nmethod stemmed"    
        bt2 = BestTerms(termVector, cluster_centroid)
        resultSetTerms = bt2.approximate()
        for term in resultSetTerms.keys():
            print "(%.3f) %s" % (resultSetTerms[term], term)
            
        
        
class Clusterizer():
    
    def __init__(self):
        pass
    
    def __mergeTdocWithCentroids(self, tdocMatrix, clusterCentroids):
        
        clusterCentroidsMatrix = []
        for clusterCentroidsID in clusterCentroids.keys():
            clusterCentroids[clusterCentroidsID]
            
        clusterIDs = clusterCentroids.keys()
        clusterIDs.sort()
        print "cluster IDs = _%s_" % clusterIDs
            
        
        
        newMatrix = []
        
        rowCounter = 0
        for row in tdocMatrix:
            
            for clusterID in clusterIDs:
                row.append( float( clusterCentroids[clusterID][rowCounter] ) )
                
            newMatrix.append(row)
            rowCounter += 1
        
        return newMatrix
    
    def __logMatrix(self, matrix, docVector, termVector, dicname):
        
        matrixString = ''
        for row in matrix:
            rowString = ','.join(['%.5f' % wij for wij in row])
            rowString += '\n'
            matrixString += rowString
            
        docVectorString = ','.join(['%s' % docID for docID in docVector])
        termVectorString = ','.join(['%s' % term for term in termVector])
        
        fileName = '../logs/' + re.sub('\s','_', '%s' % datetime.datetime.now())
        fileName = re.sub(':','-', '%s' % fileName)
                
        logFileName = '%s-termByDoc-matrix_%s.data' % (fileName, dicname)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(matrixString)
        
        logFileName = '%s-docVector_%s.data' % (fileName, dicname)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(docVectorString)
        
        logFileName = '%s-termVector_%s.data' % (fileName, dicname)
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(termVectorString)
    
    def __normalizeVector(self, vectorToNormalize):
        
        accumulator = float(0)
        for entry in vectorToNormalize:
            accumulator += math.pow(entry, 2)
            
        originalNorm = math.sqrt(accumulator)
        print "Original norm was %.4f" % originalNorm
        
        normalizedVector = []
        
        for entry in vectorToNormalize:
            normalizedEntry = entry/originalNorm
            normalizedVector.append(normalizedEntry)
            
        ##check
        accumulator = float(0)
        for entry in normalizedVector:
            accumulator += math.pow(entry, 2)
            
        newNorm = math.sqrt(accumulator)
        print "Normalized norm is %.4f" % newNorm
            
        return normalizedVector
    
    def __computeClusterCentroids(self, tdocMatrix, clusterIDList):
                       
        ##compute cluster centroid
        data = numpy.array(tdocMatrix)
        mask = None
        
        # Specifies whether the arithmetic mean (method=='a') or the median (method=='m')
        # is used to calculate the cluster center.
        method = 'a'
        
        # Determines if row or column clusters are being considered. If transpose==0, then
        # we are considering clusters rows. If transpose==1, then we are considering
        # clusters of columns (i.e. document vectors).
        transpose = 1
        
        (cdata, cmask) = Pycluster.clustercentroids(data, mask, clusterIDList, method, transpose)
        
        print cdata
        
        
        
        clusterCentroids = {}
        clusterCentroidsNormalized = {}
        for clusterID in clusterIDList:
            if not clusterCentroids.has_key(clusterID):
                clusterCentroids[clusterID] = []
                clusterCentroidsNormalized[clusterID] = []
        
        for row in cdata:
            columnCounter = 0
            for entry in row:
                clusterCentroids[columnCounter].append(entry)
                columnCounter += 1
                
        for clusterID in clusterCentroids.keys():
            
            clusterCentroidsNormalized[clusterID] = self.__normalizeVector(clusterCentroids[clusterID])
            
        return clusterCentroidsNormalized
                
                        


                
        
    def printIndexStats(self, dictionary):
        
        
        
        
        #######################################################################
        #######################################################################
        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        print "Dictionary %s" % dictionary.name        
        print "\t termVector has %d terms" % len(termVector)
        print "\t tdocMatrix %d X %d" % (len(termVector), len(docVector))
        
        print docVector
        
        
        """
        clusters[nameOfDocumentID] = numberOfDocuments
        example:
           leo     4
           frank   5
           johan   2
        """
                
        clusters = {}
        for docID in docVector:
            #(name, docNumber) = re.split('-', docID)
            name="biblio"
            if not clusters.has_key(name):
                clusters[name] = 0
            clusters[name] += 1
        
        """
        Assigns an integer to each cluster name
        example:
            leo     0
            frank   1
            johan   2
        """
        counter = 0
        clustersIDs = {}
        for clusterName in clusters.keys():
            if not clustersIDs.has_key(clusterName):
                clustersIDs[clusterName] = counter
                counter += 1
                
        """
        clusterIDList assigns each document in the docVector to a cluster
        by naming each cluster using an integer
        """
        clusterIDList = []
        for docID in docVector:
            #(name, docNumber) = re.split('-', docID)
            name="biblio"
            clusterIDList.append( clustersIDs[name] )
            
        print clusterIDList
        
        clusterCentroids = self.__computeClusterCentroids(tdocMatrix, clusterIDList)
        
        tdocExtended = self.__mergeTdocWithCentroids(tdocMatrix, clusterCentroids)
        
        self.__logMatrix(tdocExtended, docVector, termVector, dictionary.name)
        
        

            
            
        #################################################################
        #clusterCentroidNormalized
        #ccacNormalized[clusterCentroidsID]
        #################################################################    
        
            
        
#        matrixString = ''
#        for row in tdocMatrix:
#            rowString = ','.join(['%.5f' % wij for wij in row])
#            rowString += '\n'
#            matrixString += rowString
#            
#        docVectorString = ','.join(['%s' % docID for docID in docVector])
#        termVectorString = ','.join(['%s' % term for term in termVector])
#        
#        now = '../logs/' + re.sub('\s','_', '%s' % datetime.datetime.now())
#        now = re.sub(':','-', '%s' % now)
#                
#        logFileName = '%s-termByDoc-matrix_%s.data' % (now, dictionary.name)
#        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
#        logFile.write(matrixString)
#        
#        logFileName = '%s-docVector_%s.data' % (now, dictionary.name)
#        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
#        logFile.write(docVectorString)
        
#        logFileName = '%s-termVector_%s.data' % (now, dictionary.name)
#        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
#        logFile.write(termVectorString)
#        
        
        
        
    def logTermByDocMatrix(self, dictionary):
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
        
    def computeCentroidApproximation(self, clusterCentroid, numOfTerms):
        
        centroidNorm = float(0)
        for term in clusterCentroid.keys():
            #print "\t%.4f\t%s" % ( clusterCentroid[term], term )
            centroidNorm += math.pow(clusterCentroid[term], 2)
            
        print "centroid Norm is %.4f" % math.sqrt( centroidNorm )
        
        bestTerms = heapq.nlargest(numOfTerms, clusterCentroid.iteritems(), heapq.itemgetter(1))
        approximationNorm = float(0)
        centroidApproximation = {}
        for item in bestTerms:
            (term, weight) = item
            centroidApproximation[term] = float(weight)
            #print "\t%.4f\t%s" % (weight, term)
            approximationNorm += math.pow(weight, 2)
        
        print "centroid approximation norm is %.4f" % math.sqrt( approximationNorm)
            
        if (approximationNorm > 0) and (centroidNorm > 0):
            centroidNorm = math.sqrt(centroidNorm)
            approximationNorm = math.sqrt(approximationNorm)
            approximationRatio = ( approximationNorm / centroidNorm )
            
            return (approximationRatio, centroidApproximation)
        
        return None
    
    def computeCentroidApproximationStemmed(self, clusterCentroid, numOfTerms):
        
        centroidNorm = float(0)
        for term in clusterCentroid.keys():
            #print "\t%.4f\t%s" % ( clusterCentroid[term], term )
            centroidNorm += math.pow(clusterCentroid[term], 2)
        
        bestTerms = heapq.nlargest(len( clusterCentroid.keys() ), clusterCentroid.iteritems(), heapq.itemgetter(1))
        approximationNorm = float(0)
        centroidApproximation = {}
        stemmedTerms = []
        ps = common.porterStemmer.PorterStemmer()
        for item in bestTerms:
            (term, weight) = item
                        
            stemmedTerm = ps.stem(term, 0, len(term)-1)
            if len(stemmedTerm)>0:
                stemmedTerms.append(stemmedTerm)
            
            if not centroidApproximation.has_key(stemmedTerm):
                centroidApproximation[stemmedTerm] = float(0)
                
            centroidApproximation[stemmedTerm] += float(weight)
            approximationNorm += math.pow(weight, 2)
            
            if not ( len( centroidApproximation.keys() ) < numOfTerms ):
                break
            
        if (approximationNorm > 0) and (centroidNorm > 0):
            centroidNorm = math.sqrt(centroidNorm)
            approximationNorm = math.sqrt(approximationNorm)
            approximationRatio = ( approximationNorm / centroidNorm )
            
            return (approximationRatio, centroidApproximation)
        
        return None
        
    def computeClusterCentroid(self, dictionary, clusterID=None, numOfDimensions=None ):
        
        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        
        #print tdocMatrix
        
        data = numpy.array(tdocMatrix)
        mask = None
        
        # Specifies whether the arithmetic mean (method=='a') or the median (method=='m')
        # is used to calculate the cluster center.
        method = 'a'
        
        # Determines if row or column clusters are being considered. If transpose==0, then
        # we are considering clusters rows. If transpose==1, then we are considering
        # clusters of columns (i.e. document vectors).
        transpose = 1
        
        (cdata, cmask) = Pycluster.clustercentroids(data, mask, clusterID, method, transpose)
        
        cdataNorm = float(0)
        for component in cdata:
            cdataNorm += math.pow(component, 2)
        cdataNorm = math.sqrt(cdataNorm)
        
        if not (cdataNorm>0):
            return None
        
        for i in range( len(cdata) ):
            cdata[i] = cdata[i]/cdataNorm
            
        ## calculation on Residual Sum of Squares            
        distanceVectors = [float(0) for i in range( len(docVector) )]
        
        i = 0
        for row in tdocMatrix:
            j = 0
            for entry in row:
                #print "(%.2d,%.2d) %.4f" % (i,j, cdata[i])
                entryDistance = math.pow( entry - cdata[i], 2)
                #print "\t%.4f ---> diff = %.4f" % (tdocMatrix[i][j], entryDistance )
                distanceVectors[j] += entryDistance
                j += 1
            i += 1
            
        rss = float(0)
        for distance in distanceVectors:
            rss += distance
                
        clusterCentroid = {}
        for i in range( len(termVector) ):
            clusterCentroid[ termVector[i] ] = float( cdata[i] )
        
        return (rss, clusterCentroid)

   
if __name__ == '__main__':
    
    titleDictionary = index.storage.Dictionary('title')
    abstractDictionary = index.storage.Dictionary('abstract')
    bodyDictionary = index.storage.Dictionary('body')
    
    cl = Clusterizer()

    cl.printIndexStats(abstractDictionary)
    #cl.printIndexStats(titleDictionary)
    