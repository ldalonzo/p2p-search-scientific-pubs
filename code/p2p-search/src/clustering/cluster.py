import numpy
import math
import heapq
import Pycluster

import common.porterStemmer

class Clusterizer():
    def __init__(self):
        pass

    def printIndexStats(self, dictionary):

        (docVector, termVector, tdocMatrix) = dictionary.getTermByDocMatrix()
        print "Dictionary %s" % dictionary.name        
        print "\t termVector has %d terms" % len(termVector)
        print "\t tdocMatrix %d X %d" % (len(termVector), len(docVector))
        
    def computeCentroidApproximation(self, clusterCentroid, numOfTerms):
        centroidNorm = float(0)
        for term in clusterCentroid.keys():
            centroidNorm += math.pow(clusterCentroid[term], 2)

        bestTerms = heapq.nlargest(numOfTerms, clusterCentroid.iteritems(), heapq.itemgetter(1))
        approximationNorm = float(0)
        centroidApproximation = {}
        for item in bestTerms:
            (term, weight) = item
            centroidApproximation[term] = float(weight)
            approximationNorm += math.pow(weight, 2)
            
        if (approximationNorm > 0) and (centroidNorm > 0):
            centroidNorm = math.sqrt(centroidNorm)
            approximationNorm = math.sqrt(approximationNorm)
            approximationRatio = ( approximationNorm / centroidNorm )
            
            return (approximationRatio, centroidApproximation)
        
        return None

    def computeCentroidApproximationStemmed(self, clusterCentroid, numOfTerms):
        
        centroidNorm = float(0)
        for term in clusterCentroid.keys():
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
                entryDistance = math.pow( entry - cdata[i], 2)
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
