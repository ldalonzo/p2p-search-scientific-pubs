#!/usr/bin/env python

import codecs
import datetime
import heapq
import index.index
import os
import re
import SimpleXMLRPCServer
import threading
import time
import xmlrpclib
import sys
import index.storage
import clustering.cluster

from index import presentation

class Recommender(threading.Thread):
    
    def __init__(self, peerStatus):
        threading.Thread.__init__(self)
        self.setName('recommender')
        
        self.__peerStatus = peerStatus
        
        self.__bornTime = None
        self.__activated = True
        
    def shutdown(self):
        self.__activated = False
        
    def run(self):
        self.__bornTime = datetime.datetime.now()
        print "[%s] (%s) Hello!" % (threading.currentThread().getName(), self.__bornTime)
        while(self.__activated):

            buddies = self.__peerStatus.getTasteBuddies()
            queryTerms = self.__peerStatus.getPeerProfile().getClusterCentroidApprox().keys()
            recommendations = {}
            for buddyName in buddies.keys():
                
                (buddyAddress, buddyPort, buddyProxyPeerServer, buddySim) = buddies[buddyName]
                print "[%s] contacting taste buddy %s@%s:%s for discover recommendation (using %d terms for profile)..." % (threading.currentThread().getName(), buddyName, buddyAddress, buddyPort, len(queryTerms) )
                
                try:
                    numOfItemToRecommend = 2
                    #queryTerms = ['networks', 'overlays']
                    resultXml = buddyProxyPeerServer.getRecommendations(self.__peerStatus.getName(), queryTerms, numOfItemToRecommend)
                    print "[%s] The buddy %s@%s:%s recommends to me some interesting things..." % (threading.currentThread().getName(), buddyName, buddyAddress, buddyPort)
                    if len(resultXml)>0:
                        recommendations[buddyName] = resultXml
                except KeyboardInterrupt:
                    print "[%s] Unable to contact %s@%s:%s" % (threading.currentThread().getName(), buddyName, buddyAddress, buddyPort)

            self.__peerStatus.setRecommendation(recommendations)

class BuddyCast(threading.Thread):
    
    def __init__(self, peerStatus, superPeerProxy):
        threading.Thread.__init__(self)
        self.setName('buddyCast')
        
        self.__peerStatus = peerStatus
        
        self.__superPeer = superPeerProxy
        self.__bornTime = 0
        
        self.__activated = True
        
    def shutdown(self):
        self.__activated = False
        
    def run(self):
        self.__bornTime = datetime.datetime.now()
        print "[%s] (%s) Hello!" % (threading.currentThread().getName(), self.__bornTime)
        
        name = self.__peerStatus.getName()
        
        while(self.__activated):
            peerProfile = self.__peerStatus.getPeerProfileForBuddyCast()
            stemmedProfile = peerProfile.getClusterCentroidApproxStemmed()

            try:
                print "\n[%s] posting your profile (%d keywords) to the superpeer@%s" % (threading.currentThread().getName(), len(stemmedProfile.keys()), self.__superPeer)                
                self.__superPeer.postPeerProfile(name, stemmedProfile)

            except OSError:
                print "[%s] unable to post! superpeer unreachable!" % threading.currentThread().getName()

            time.sleep(10)

class Clusterizer(threading.Thread):
    
    def __init__(self, peerStatus, superPeerProxy):
        threading.Thread.__init__(self)
        self.setName('clusterizer')
        
        self.__peerStatus = peerStatus
        
        self.__superPeer = superPeerProxy
        self.__bornTime = 0
        
        self.__activated = True
        
    def shutdown(self):
        print "[%s] shutting down..." % threading.currentThread().getName()
        self.__activated = False
        
    def run(self):
        self.__bornTime = datetime.datetime.now()
        print "[%s] (%s) Hello!" % (threading.currentThread().getName(), self.__bornTime)
        
        while(self.__activated):
            
            approxTerms = 50
            approxTermsStemmed = 30
            
            print "[%s] waiting for dictionary changes..." % threading.currentThread().getName()
            ## getIndex is blocking
            ## it is triggered to the index update (i.e. new document submission)
            (titleDictionary, abstractDictionary, bodyDictionary) = self.__peerStatus.getIndex().getIndexes()
            
            cl = clustering.cluster.Clusterizer()

            try:
                result = cl.computeClusterCentroid(abstractDictionary)

                if not result:
                    print "[%s] unable to cluster the index" % threading.currentThread().getName()
                    continue

                (rss, clusterCentroid) = result
                print "[%s] abstract cluster centroid quality RSS = %.2f" % (threading.currentThread().getName(), rss)

                (approximationRatio, centroidApproximation) = cl.computeCentroidApproximation(clusterCentroid, approxTerms)
                
                top7PeerProfile = heapq.nlargest(7, centroidApproximation.iteritems(), heapq.itemgetter(1))
                for res in top7PeerProfile:
                    (term, weight) = res
                    print "\t(%.4f)\t%s" % (weight, term)
                print "\t( .... )\t..."
                
                (approximationRatioStemmed, centroidApproximationStemmed) = cl.computeCentroidApproximationStemmed(clusterCentroid, approxTermsStemmed)
                print "[%s] your profile has been approximated by %d keywords (%.3f%% of the centroid norm)" % (threading.currentThread().getName(), len( centroidApproximationStemmed.keys() ), approximationRatioStemmed*100 )

                peerProfile = self.__peerStatus.getPeerProfileAndModify()
                peerProfile.setClusterCentroid( rss, clusterCentroid )
                peerProfile.setClusterCentroidApprox( approximationRatio, centroidApproximation )            
                peerProfile.setClusterCentroidApproxStemmed( approximationRatioStemmed, centroidApproximationStemmed )
                self.__peerStatus.committPeerProfileModifications()

            except:
                print "\n[%s] There was an error on clustering!" % threading.currentThread().getName()

        print "[%s] See you next time!" % threading.currentThread().getName()
        
class PeerProfile():
    def __init__(self):
        
        self.__rss = None
        self.__clusterCentroid = {}
        
        self.__centroidApproximation = {}
        self.__approximationRatio = 0
        
        self.__centroidApproximationStemmed = {}
        self.__approximationRatioStemmed = 0
        
    def getClusterCentroidApprox(self):
        return self.__centroidApproximation
    
    def getClusterCentroidApproxStemmed(self):
        return self.__centroidApproximationStemmed
    
    def setClusterCentroid(self, rss, clusterCentroid):
        self.__rss = rss
        self.__clusterCentroid = clusterCentroid
        
    def getRss(self):
        return self.__rss
    
    def getApproximationRatioStemmed(self):
        return self.__approximationRatioStemmed
        
    def setClusterCentroidApprox(self, approximationRatio, centroidApproximation):
        self.__approximationRatio = approximationRatio
        self.__centroidApproximation = centroidApproximation
        
    def setClusterCentroidApproxStemmed(self, approximationRatioStemmed, centroidApproximationStemmed ):
        self.__approximationRatioStemmed = approximationRatioStemmed
        self.__centroidApproximationStemmed = centroidApproximationStemmed

class Indexer(threading.Thread):
    
    def __init__(self, index, name='indexer'):
        threading.Thread.__init__(self)
        self.setName(name)
        self.__condition = threading.Condition()
        self.__index = index

        self.__filesToIndex = []
        for directory in self.directoriesToIndex():
            self.addDirectory(directory)
        
        self.__bornTime = 0
        self.__active = True
        
    def shutdown(self):
        self.__active = False
        
    def directoriesToIndex(self):
        dirs = []

        dirs.append('/home/leo/workspace/bibliography/thesis')

        return dirs
        
    def addDirectory(self, directory):
        
        file_ext_list = ['.pdf']
        file_list = [os.path.normcase(f) for f in os.listdir(directory)]
        file_list = [os.path.join(directory,f) for f in file_list if os.path.splitext(f)[1] in file_ext_list]
    
        self.__condition.acquire()
        
        for file in file_list:
            self.__filesToIndex.append(file)
        self.__condition.release()
    
    def addFile (self, fileName):
        self.__condition.acquire()
        self.__filesToIndex.append(fileName)
        self.__condition.release()
        
    def run(self):
        self.__bornTime = datetime.datetime.now()
        print "[%s] (%s) Hello!" % (threading.currentThread().getName(), self.__bornTime)

        self.__index.buildCitGraphAndAnalyze()
        while (self.__active):
            self.__index.buildCitGraphAndAnalyze()

            while len(self.__filesToIndex)>0:
                print "[%s] I have more %d files to analyze..." % (threading.currentThread().getName(), len(self.__filesToIndex))
                self.__condition.acquire()
                fileName = self.__filesToIndex.pop()
                self.__index.submitPDF(fileName)
                self.__condition.release()
                   
            time.sleep(60)
        print "[%s] See you next time!" % threading.currentThread().getName()

class Peer:
    def __init__(self, peerName, index):
        self.__name = peerName
        self.__index = index
        
        self.__buddies = {}
        self.__buddiesUpdated = threading.Event()
        
        self.__recommendations = {}
        
        self.__peerProfile = PeerProfile()
        self.__peerProfileUpdated = threading.Event()
        
        self.__condition = threading.Condition()
        
    def getName(self):
        return self.__name
    
    def getIndex(self):
        return self.__index
    
    def getPeerProfileForBuddyCast(self):
        
        self.__peerProfileUpdated.wait()
        self.__peerProfileUpdated.clear()
        
        self.__condition.acquire()
        peerProfile = self.__peerProfile
        self.__condition.release()
        return peerProfile
    
    def getPeerProfile(self):
        self.__condition.acquire()
        peerProfile = self.__peerProfile
        self.__condition.release()
        return peerProfile
        
    def getTasteBuddiesDjango(self):
        self.__condition.acquire()
        buddies = self.__buddies
        self.__condition.release()
        
        
        buddiesDjango = {}
        
        for buddyName in buddies.keys():
            (buddyAddress, buddyPort, buddyProxyPeerServer, buddySim) = buddies[buddyName]
            buddiesDjango[buddyName] = (buddyAddress, buddyPort, buddySim)

        return buddiesDjango

    def getRecommendationDjango(self):
        self.__condition.acquire()
        recommendations = self.__recommendations
        self.__condition.release()

        return recommendations

    def setRecommendation(self, recommendations):
        self.__condition.acquire()
        self.__recommendations = recommendations

        self.__condition.release()
        
    def getPeerProfileAndModify(self):
        self.__condition.acquire()
        return self.__peerProfile
    
    def committPeerProfileModifications(self):
        self.__peerProfileUpdated.set()
        self.__condition.release()
        return True
    
    def getClusterCentroidApproximation(self):
        self.__condition.acquire()
        capprox = self.__peerProfile.getClusterCentroidApprox()
        self.__condition.release()
        return capprox
    
    def getClusterRss(self):
        self.__condition.acquire()
        rss = self.__peerProfile.getRss()
        self.__condition.release()
        return rss
    
    def getClusterApproxRatio(self):
        self.__condition.acquire()
        
        approxRatio = self.__peerProfile.getApproximationRatioStemmed()
        
        self.__condition.release()
        return approxRatio
    
    def getNumOfIndexedDocuments(self):
        return self.__index.howManyPapers()
    
    def setPeerProfile________DEPRECATED(self, peerProfile):
        self.__condition.acquire()
        self.__profile = peerProfile
        self.__condition.release()
    
    def isAlive(self):
        print "[%s] peer '%s' is still connected to the p2p network!" % (threading.currentThread().getName(), self.__name) 
        return True
    
    def getTasteBuddies(self):
        
        self.__buddiesUpdated.wait()
        self.__buddiesUpdated.clear()
        
        self.__condition.acquire()
        tasteBuddies = self.__buddies
        self.__condition.release()
        return tasteBuddies
    
    def setTasteBuddies(self, tasteBuddiesList):
        print "[%s] %s are now taste friend with:" % ( threading.currentThread().getName(), self.__name )
        self.__condition.acquire()

        self.__buddies = {}
        for buddyTuple in tasteBuddiesList:
            (buddyName, buddySim, buddyAddress, buddyPort) = buddyTuple

            print "\t%s@%s:%s (%.4f)" % (buddyName, buddyAddress, buddyPort, buddySim)
            
            buddyPeerServerCompleteAddress = "http://%s:%s" % (buddyAddress, buddyPort)
            buddyProxyPeerServer = xmlrpclib.ServerProxy(buddyPeerServerCompleteAddress, allow_none=True)
            
            self.__buddies[buddyName] = (buddyAddress, buddyPort, buddyProxyPeerServer, buddySim)
            
        self.__buddiesUpdated.set()
            
        self.__condition.release()
        return True
    
    def ping(self):
        return True
    
    def getRecommendations(self, requestPeerName, searchQuery, numOfItemToRecommend):
        print "\n[%s] peer %s asked me to recommend him some of my contents..." % (threading.currentThread().getName(), requestPeerName)
        
        result = self.__index.queryTitle(searchQuery, numOfItemToRecommend)
        print "[%s] I recommend %d documents to peer %s.  " % (threading.currentThread().getName(), len(result), requestPeerName)
        ## xmlrpc doesn't allow marshalling recursive dictionaries!!!!
        return presentation.encodeResultAsXml_IDF(result)
    
    def p2pSearch(self, searchQuery):
        self.__condition.acquire()
        buddies = self.__buddies
        self.__condition.release()
        
        p2pSearchResults = {}
        
        for buddyName in buddies.keys():
            (buddyAddress, buddyPort, buddyProxyPeerServer, buddySim) = buddies[buddyName]
                
            startTime = datetime.datetime.now()
            xmlResult = buddyProxyPeerServer.searchAll_FullText(searchQuery, 4)
            jobTime = datetime.datetime.now() - startTime
            jobTimeString = "%s.%s" % (jobTime.seconds, jobTime.microseconds)
            p2pSearchResults[buddyName] = (jobTimeString, xmlResult)

        return p2pSearchResults

    def search(self, searchQuery):
        searchQuery = searchQuery.lower()
        resultSet = self.__index.searchForAuthors(re.split("\s", searchQuery))
        return presentation.encodeResultAsXml(resultSet)
    
    def getCitingPapers(self, citedPaperURN):
        resultSet = self.__index.getCitingPapers(citedPaperURN)
        return presentation.encodeResultAsXml(resultSet)
    
    def searchTopK__DEPRECATED(self, searchQuery):
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryIDF(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchTitle(self, searchQuery):
        searchQuery = searchQuery.lower()
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryTitle(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchAbstract(self, searchQuery):
        searchQuery = searchQuery.lower()
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryAbstract(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchAll(self, searchQuery):
        searchQuery = searchQuery.lower()
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryAll(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchAll_FullText(self, searchQuery, maxResults=10):
        searchQuery = searchQuery.lower()
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryAll_fullText(queryTerms, 0.6, maxResults)
        return presentation.encodeResultAsXml_IDF(resultSet)

class PeerServer(threading.Thread):
    
    def __init__(self, peerStatus, peerAddress, peerPort):    
        threading.Thread.__init__(self)
        self.setName('peerServer')
        
        self.__peerStatus = peerStatus
        
        self.__peerAddress = peerAddress
        self.__peerPort = peerPort
        
        self.__bornTime = 0
        self.__activated = True
        
        self.__peerServer = None
        
    def __writePeerServerRunningAddressForDjango(self):
        peerAddressString = 'http://%s:%s' % (self.__peerAddress, self.__peerPort)
        logFileName = '../tmp/peerAddress.txt'
        logFile = codecs.open(logFileName, 'w', 'utf-8', errors='ignore')
        logFile.write(peerAddressString)
        logFile.close()
        
    def shutdown(self):
        self.__activated = False

    def run(self):
        self.__bornTime = datetime.datetime.now()
        print "[%s] Hello @%s!" % (threading.currentThread().getName(), self.__bornTime)

        self.__peerServer = SimpleXMLRPCServer.SimpleXMLRPCServer((self.__peerAddress, self.__peerPort))
        self.__peerServer.allow_reuse_address = True
        self.__peerServer.allow_none = True
        self.__peerServer.register_instance(self.__peerStatus)
        
        print "[%s] Peer %s@%s:%s joined the p2p network... " % (
                                                                 threading.currentThread().getName(),
                                                                 self.__peerStatus.getName(),
                                                                 self.__peerAddress,
                                                                 self.__peerPort)
        
        self.__writePeerServerRunningAddressForDjango()
        
        while(self.__activated): 
            self.__peerServer.handle_request()

        print "[%s] See you next time!" % threading.currentThread().getName()
    
    def __init__(self, spAddress, spPort):
        
        self.__superPeerAddress = spAddress
        self.__superPeerPort = spPort
        
        self.__proxyServer = self.__setupConnection(self.__superPeerAddress, self.__superPeerPort)
        
    def __setupConnection(self, address, port):
        superPeerAddress = "http://%s:%s" % (address, port)
        spProxy = xmlrpclib.ServerProxy(superPeerAddress)

    def getProxy(self):
        return self.__proxyServer

if __name__ == '__main__':
    
    peerName = 'leo'
    peerAddress = 'localhost'
    superPeerAddress = 'localhost'
    superPeerPort = 15000

    for argument in sys.argv:
        
        if re.search('alias=', argument):
            peerName = re.split('=', argument)[1]
            
        elif re.search('^ip=', argument):
            peerAddress = re.split('=', argument)[1]
            
        elif re.search('^sip=', argument):
            superPeerAddress = re.split('=', argument)[1]

    superPeerProxy = xmlrpclib.ServerProxy( "http://%s:%s" % (superPeerAddress, superPeerPort) )
    indexerProcess = None
    peerServerProcess = None
    clusteringProcess = None
    
    try:
        titleDictionary = index.storage.Dictionary('title')
        abstractDictionary = index.storage.Dictionary('abstract')
        bodyDictionary = index.storage.Dictionary('body')

        peerIndex = index.index.Index(titleDictionary, abstractDictionary, bodyDictionary)

        print "\n[%s] starting indexer process..." % threading.currentThread().getName()        
        indexerProcess = Indexer(peerIndex)
        indexerProcess.start()

    except:
        print "fatal! exiting..."
        exit()
        
    peerStatus = Peer(peerName, peerIndex)
    
    ##### try to retrieve the port and set up the server
    try:
        peerPort = superPeerProxy.registerPeer(peerName, peerAddress)
        if peerPort>0:
            #print "setting up"
            
            ## setting up peerServer
            print "\n[%s] starting server process..." % threading.currentThread().getName()
            peerServerProcess = PeerServer(peerStatus, peerAddress, peerPort)
            peerServerProcess.start()
            
            ## starting clusterizer
            print "\n[%s] starting cluster process..." % threading.currentThread().getName()
            clusteringProcess = Clusterizer(peerStatus, superPeerProxy)
            clusteringProcess.start()
            
            print "\n[%s] starting recommender process..." % threading.currentThread().getName()
            recommenderProcess = Recommender(peerStatus)
            recommenderProcess.start()
            
            print "\n[%s] starting buddyCast process..." % threading.currentThread().getName()
            buddyCastProcess = BuddyCast(peerStatus, superPeerProxy)
            buddyCastProcess.start()

        else:
            print "eccezione"
            raise Exception()
    except:
        print "[%s] Unable to join the p2p network (superPeer unreachable)" % threading.currentThread().getName()

    try:
        while(True):
            time.sleep(5000)
    except KeyboardInterrupt:
        print "[%s] Shutting down..." % threading.currentThread().getName()

        if indexerProcess:
            indexerProcess.shutdown()
            indexerProcess.join(4)
        
        if clusteringProcess:
            clusteringProcess.shutdown()
            clusteringProcess.join(4)
        
        if peerServerProcess:
            peerServerProcess.shutdown()
            peerServerProcess.join(4)
            
        if recommenderProcess:
            recommenderProcess.shutdown()
            recommenderProcess.join(4)
            
        if buddyCastProcess:
            buddyCastProcess.shutdown()
            buddyCastProcess.join(4)
            
        print "[%s] Bye bye." % threading.currentThread().getName()
