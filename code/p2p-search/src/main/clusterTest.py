import index.index
import index.storage
import clustering.cluster

if __name__ == '__main__':
    
    titleDictionary = index.storage.Dictionary('title')
    abstractDictionary = index.storage.Dictionary('abstract')
    bodyDictionary = index.storage.Dictionary('body')

    peerIndex = index.index.Index(titleDictionary, abstractDictionary, bodyDictionary)
    
    cl = clustering.cluster.Clusterizer()
    
    cl.printIndexStats(titleDictionary)
    cl.printIndexStats(abstractDictionary)
    cl.printIndexStats(bodyDictionary) 
    
    (rss, clusterCentroid) = cl.computeClusterCentroid(titleDictionary)
    
    print "RSS = %.4f" % rss
    
    dimCounter = 1
    for term in clusterCentroid.keys():
        print "\t(%.2d)\t%.4f\t%s" % (dimCounter, clusterCentroid[term], term)
        dimCounter += 1
    
    print "__"
    
    (approximationRatio, centroidApproximation) = cl.computeCentroidApproximation(clusterCentroid, 7)
    print "centroid approximation is %.4f" % approximationRatio
    dimCounter = 1
    for term in centroidApproximation.keys():
        print "\t(%.2d)\t%.4f\t%s" % (dimCounter, centroidApproximation[term], term)
        dimCounter += 1
        
    print "__"
    (approximationRatio, centroidApproximation) = cl.computeCentroidApproximationStemmed(clusterCentroid, 9)
    print "centroid approximation is %.4f" % approximationRatio
    dimCounter = 1
    for term in centroidApproximation.keys():
        print "\t(%.2d)\t%.4f\t%s" % (dimCounter, centroidApproximation[term], term)
        dimCounter += 1

