#!/usr/bin/env python

import threading
import codecs
import datetime
import fcntl
import math
import re
import socket
import struct
import sys
import time
import xmlrpclib

import SimpleXMLRPCServer

def printLog(message):
    print message
    logFileName = 'superpeer.log'
    logFile = codecs.open(logFileName, 'a', 'utf-8', errors='ignore')
    message = "[%s]__" % datetime.datetime.now() + message + "\n"
    logFile.write(message)
    logFile.close()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    
def getPastTimeString(startTime):
    now = datetime.datetime.now()
    diff = now-startTime
    
    days = diff.days
    hours = diff.seconds / 3600
    minutes =  (diff.seconds - (hours*3600))/60
    seconds = diff.seconds - (hours*3600) - (minutes*60)

    return "%d days, %.2d:%.2d:%.2d s" % (days, hours, minutes, seconds)

class Pinger(threading.Thread):
    
    def __init__(self, network):
        threading.Thread.__init__(self)
        self.setName('pinger')
        self.__network = network
        
        self.__shutdown = False
        
    def shutdown(self):
        self.__shutdown = True
        
    def run(self):
        while(not self.__shutdown):
            
            time.sleep(60)
            
            peerAddresses = self.__network.getPeers()
            if len( peerAddresses.keys() )>0:
                printLog("\n[%s] pinging %d peers in the network..." % (threading.currentThread().getName(), len( peerAddresses.keys() ) ) )
                for peerName in peerAddresses.keys():
                    (peerAddress, peerPort, proxyPeerServer) = peerAddresses[peerName]
                    printLog("[%s] trying to contact %s@%s:%s" % (threading.currentThread().getName(), peerName, peerAddress, peerPort))
                    try:
                        response = proxyPeerServer.isAlive()
                        if response:
                            print "[%s] peer %s@%s:%s is still alive." % (threading.currentThread().getName(), peerName, peerAddress, peerPort)
                        else:
                            raise Exception()
                    except:
                        printLog("[%s ERROR] unable to contact %s@%s:%s"  % (threading.currentThread().getName(), peerName, peerAddress, peerPort))
                        self.__network.removePeer(peerName)
            else:
                print "[%s] No peers in the network..." % threading.currentThread().getName()

class BuddyCast(threading.Thread):
    def __init__(self, threadName, peerName, peerProxy, buddyList):
        
        threading.Thread.__init__(self)
        self.setName(threadName)
        
        self.__peerProxy = peerProxy
        self.__buddyList = buddyList
        self.__peerName = peerName
        
    def __run_DEBUG(self):
        print "\n[%s] attempting to contact %s@%s for updating his taste buddies..." % (threading.currentThread().getName(), self.__peerName, self.__peerProxy)
        
        for buddyData in self.__buddyList:
            (buddyName, buddyAddress, buddyPort, buddySim) = buddyData
            print "\t (%.4f) %s@%s" % (buddySim, buddyName, buddyProxy)
        time.sleep(3)

    def run(self):
        DEBUG = False
        
        if DEBUG:
            self.__run_DEBUG()
        else:
            
            print "\n[%s] attempting to contact %s@%s for updating his taste buddies..." % (threading.currentThread().getName(), self.__peerName, self.__peerProxy)
            
            dataToBeTransmitted = []
            for buddyData in self.__buddyList:
                (buddyName, buddyAddress, buddyPort, buddySim) = buddyData
                print "\t (%.4f) %s@%s:%s" % (buddySim, buddyName, buddyAddress, buddyPort)
                dataToBeTransmitted.append( (buddyName, buddySim, buddyAddress, buddyPort) )

            try:
                result = self.__peerProxy.setTasteBuddies(dataToBeTransmitted)
                print "[%s] friendships of %s@%s have been updated." % (threading.currentThread().getName(), self.__peerName, self.__peerProxy)
            except:# KeyboardInterrupt:
                print "[%s ERROR] Unable to contact %s@%s. Friendships not updated." % (threading.currentThread().getName(), self.__peerName, self.__peerProxy)

class BuddyBuilder(threading.Thread):
    
    def __init__(self, network):
        threading.Thread.__init__(self)
        self.setName('buddyBuilder')
        self.__network = network
        
        self.__maxNumOfBuddies = 2
        
    def shutdown(self):
        pass ##TODO
        
    def __calculateFriendships(self, similarityMatrix, matrixBase, maxNumOfBuddies=2):
        
        print "[%s] calculating friendships (each peer has at most %d taste buddies)..." % (threading.currentThread().getName(),
                                                                                            maxNumOfBuddies)

        buddiesAdjacencyList = []
        rowCount = 0
        for row in similarityMatrix:
            
            rowBuddies = [rowCount]
            while( len(rowBuddies)<=maxNumOfBuddies ):
            
                (bestValue, bestIndex) = (0, -1)
                columnCount = 0
                for column in row:
                    if columnCount in rowBuddies:
                        pass
                    else:
                        if column > bestValue:
                            bestValue = column
                            bestIndex = columnCount
                    columnCount += 1
                            
                if bestIndex<0:
                    break
                else:
                    rowBuddies.append(bestIndex)
                    
            rowBuddies.pop(0) #remove itself to its buddies

            buddiesAdjacencyList.append(rowBuddies)
            rowCount += 1
            
        return buddiesAdjacencyList#tasteBuddies

    def __computeFriendshipsAndSpreadOut(self, similarityMatrix, matrixBase, maxNumOfBuddies=2):
        
        tasteBuddiesAdjacencyList = self.__calculateFriendships(similarityMatrix, matrixBase, maxNumOfBuddies)
        self.__printTasteBuddiesAdjacencyMatrix(tasteBuddiesAdjacencyList, matrixBase)
        self.__printTasteBuddiesSimAdjacencyMatrix(similarityMatrix, tasteBuddiesAdjacencyList, matrixBase)
        
        peersInTheNetwork = self.__network.getPeers()
        spreadBuddyDict = {} # {'peerName':[(buddyName_1, buddyProxy_1, similarity_1), ..., (buddyName_K, buddyProxy_K, similarity_K) ]}
        
        numberOfFriendships = 0
        numberOfAlonePeers = 0
        
        peerBuddyID = 0
        for peerBuddies in tasteBuddiesAdjacencyList:
            peerName = matrixBase[peerBuddyID]
            if peersInTheNetwork.has_key(peerName):
                
                (peerAddress, peerPort, proxyPeerServer) = peersInTheNetwork[peerName]

                #list made of tuple like the following:
                #(buddyName, buddyAddress, buddyPort, buddySim)
                buddiesProxies = []
                for buddyID in peerBuddies:
                    
                    buddyName = matrixBase[buddyID]
                    if peersInTheNetwork.has_key(peerName):
                        (buddyAddress, buddyPort, proxyBuddyServer) = peersInTheNetwork[buddyName]
                        
                        similarityValue = similarityMatrix[peerBuddyID][buddyID]
                        buddiesProxies.append((buddyName, buddyAddress, buddyPort, similarityValue))

                    else:
                        print "[%s] the buddy %s is no longer connected to the p2p network" % (
                                                                    threading.currentThread().getName(),
                                                                    buddyName)
                         
                if len(buddiesProxies)>0:
                    spreadBuddyDict[peerName] = buddiesProxies
                    numberOfFriendships += len(buddiesProxies)

                else:
                    numberOfAlonePeers += 1
                    pass

            else:
                print "[%s] the peer %s is no longer connected to the p2p network" % (threading.currentThread().getName(), peerName)

            peerBuddyID += 1
           
        timeStart = datetime.datetime.now() 
        threadList = []
        threadCounter = 0
        for peerName in spreadBuddyDict.keys():
            name = threading.currentThread().getName() + '-TH_%.2d' % threadCounter

            (peerAddress, peerPort, proxyPeerServer) = peersInTheNetwork[peerName]

            buddyPeers = spreadBuddyDict[peerName]

            bcThread = BuddyCast(name, peerName, proxyPeerServer, buddyPeers)
            bcThread.start()
            threadList.append(bcThread)
            
            threadCounter += 1
            
        for bcThread in threadList:
            bcThread.join(10)

        timeEnd = datetime.datetime.now()
        job = timeEnd - timeStart
        ###FIXME there's some problem with the next line...
        print "\n[%s] %d peers in the network, %d are alone, %d have friends for a total of %d friendships." % (threading.currentThread().getName(), len(peersInTheNetwork), numberOfAlonePeers, len(peersInTheNetwork)-numberOfAlonePeers, numberOfFriendships)
        print "[%s] friendships updated in %d s, %d us." % (threading.currentThread().getName(), job.seconds, job.microseconds)

    def __printTasteBuddiesAdjacencyMatrix(self, tasteBuddiesAdjList, matrixBase):
        print "[%s] Taste buddies adjacency matrix:" % threading.currentThread().getName()
        tasteBuddiesAdjMatrix = []
        
        rowCount = 0
        for peer in tasteBuddiesAdjList:
            
            rowString = '\t%s\t' % matrixBase[rowCount]
            for i in range( len(matrixBase) ):
                if i in peer:
                    rowString += '1  '
                else:
                    rowString += '0  '
            print rowString
            rowCount += 1
            
    def __printTasteBuddiesSimAdjacencyMatrix(self, similarityMatrix, tasteBuddiesAdjList, matrixBase):
        print "[%s] Taste buddies similarity adjacency matrix:" % threading.currentThread().getName()
        tasteBuddiesSimAdjMatrix = []
        
        rowCount = 0
        for peer in tasteBuddiesAdjList:
            
            rowString = '\t%s\t' % matrixBase[rowCount]
            for i in range( len(matrixBase) ):
                if i in peer: 
                    rowString += '%.4f  ' % similarityMatrix[rowCount][i]
                else:
                    rowString += '0       '
            print rowString
            rowCount += 1
        
    def run(self):
        while(True):
            
            ##blocking
            (similarityMatrix, matrixBase) = self.__network.getPeerProfilesMatrix()
            self.__computeFriendshipsAndSpreadOut(similarityMatrix, matrixBase, self.__maxNumOfBuddies)

class P2PNetwork():
    
    def __init__(self):
        self.__basePeerPort = 16200
        self.__knownPeers = {} ## {'peerName': (peerAddress, peerPort, proxyPeerServer)}
        self.__knownHosts = {}
        
        self.__condition = threading.Condition()
        self.__bornTime = datetime.datetime.now()
        self.__peerProfiles = {}
        self.__peerProfileMatrixBase = []
        self.__peerProfileMatrix = []
        self.__peerProfileMatrixUpdated = threading.Event()
        
    def getPeerProfilesMatrix(self):
        self.__peerProfileMatrixUpdated.wait()
        self.__peerProfileMatrixUpdated.clear()
        self.__condition.acquire()
        returnValue = (self.__peerProfileMatrix, self.__peerProfileMatrixBase)
        self.__condition.release()
        return returnValue

    def getPeers(self):
        self.__condition.acquire()
        knownPeers = self.__knownPeers
        self.__condition.release()
        return knownPeers
    
    def hasPeers(self):
        if len(self.__knownPeers.keys())>0:
            return True
        return False
    
    def getUpTime(self):
        return getPastTimeString(self.__bornTime)
    
    def sayHello(self):
        printLog("[%s] Hello world! I'm the server! I'm up for %s" % (threading.currentThread().getName(), self.getUpTime())) 
    
    def removePeer(self, peerName):
        self.__condition.acquire()
        
        if self.__knownPeers.has_key(peerName):
            (peerAddress, peerPort, proxyPeerServer) = self.__knownPeers[peerName]
            del self.__knownPeers[peerName]
            if self.__peerProfiles.has_key(peerName):
                del self.__peerProfiles[peerName]
            printLog("[%s] Peer '%s' that was running @%s:%s left the p2p network. Now it has %d peers" % (threading.currentThread().getName(), peerName, peerAddress, peerPort, len(self.__knownPeers.keys())))
            
            if self.__knownHosts[peerAddress] == 1:
                del self.__knownHosts[peerAddress]
            elif self.__knownHosts[peerAddress] > 1:
                self.__knownHosts[peerAddress] -= 1
            else:
                printLog("[%s] SUPERPEER PANIC!!!! Inconsistency problem!!!!" % threading.currentThread().getName())
                self.__condition.release()
                exit()            
        else:
            printLog("[%s] SUPERPEER PANIC!!!! Inconsistency problem!!!!" % threading.currentThread().getName())
            self.__condition.release()
            exit()

        self.__condition.release()

    def registerPeer(self, peerName, peerAddress):

        printLog("\n[%s] %s@%s requested to join the p2p network..." % (threading.currentThread().getName(), peerName, peerAddress))
        self.__condition.acquire()
        if self.__knownPeers.has_key(peerName):
            printLog("[%s ERROR] there's already a peer named %s..." % (threading.currentThread().getName(), peerName))
            
            self.__condition.release()
            return False
        
        numOfNextPort = 0
        if self.__knownHosts.has_key(peerAddress):
            self.__knownHosts[peerAddress] += 1
        else:
            self.__knownHosts[peerAddress] = 1
                
        numOfPeersAtThatAddress = self.__knownHosts[peerAddress]
        peerPort = self.__basePeerPort + numOfPeersAtThatAddress

        proxyPeerServerCompleteAddress = "http://%s:%s" % (peerAddress, peerPort)
        proxyPeerServer = xmlrpclib.ServerProxy(proxyPeerServerCompleteAddress, allow_none=True)

        self.__knownPeers[peerName] = (peerAddress, peerPort, proxyPeerServer)

        printLog("[%s] Peer '%s'@%s:%d joined the p2p network which has %d peers" % (threading.currentThread().getName(), peerName, peerAddress, peerPort, len(self.__knownPeers.keys())))
        
        self.__condition.release()
        return peerPort
    
    def postPeerProfile(self, peerName, peerProfile):
        
        if self.__knownPeers.has_key(peerName):
            (peerAddress, peerPort, proxyPeerServer) = self.__knownPeers[peerName]
            
            printLog("[%s] %s@%s:%s posted its profile (%d keywords)..." % (threading.currentThread().getName(),
                                                       peerName,
                                                       peerAddress,
                                                       peerPort, len(peerProfile.keys()) ))
            
            self.__condition.acquire()
            self.__peerProfiles[peerName] = peerProfile
            self.__condition.release()
            
            self.__calculatePeerProfileSimilarities()
            
        else:
            printLog("[%s WARNING] peer '%s' posted its profile but it is not in the network..." %(
                                    threading.currentThread().getName(),
                                    peerName))
            
    def __calculatePeerProfileSimilarities(self):
        
        self.__condition.acquire()
        
        self.__peerProfileMatrix = []
        self.__peerProfileMatrixBase = self.__peerProfiles.keys()
        
        self.__peerProfileMatrixBase.sort()
        
        rowCounter = 0
        for peerNameProfileRow in self.__peerProfileMatrixBase:
            matrixRow = []
            peerProfileA = self.__peerProfiles[peerNameProfileRow]
            
            for peerNameProfileCol in self.__peerProfileMatrixBase:
                peerProfileB = self.__peerProfiles[peerNameProfileCol]
                
                similarity = self.__calculateSimilarities(peerProfileA, peerProfileB)
                matrixRow.append(similarity)
                
            rowCounter += 1
            self.__peerProfileMatrix.append(matrixRow)

        print "[%s] Profiles similarity matrix:" % threading.currentThread().getName()
        counter = 0
        for row in self.__peerProfileMatrix:
            string = "\t%s\t" % self.__peerProfileMatrixBase[counter]
            for entry in row:
                string += "%.3f  " % entry
            print string
            counter += 1

        self.__peerProfileMatrixUpdated.set()

        self.__condition.release()

    def __calculateSimilarities(self, profileA, profileB):
        profileANorm = float(0)
        for term in profileA:
            profileANorm += math.pow(profileA[term], 2)
        profileANorm = math.sqrt(profileANorm)
        profileBNorm = float(0)
        for term in profileB:
            profileBNorm += math.pow(profileB[term], 2)
        profileBNorm = math.sqrt(profileBNorm)

        ## compute cosine similarity
        cosineSimilarity = float(0)
        for term in profileA:
            if term in profileB.keys():
                termAWeight = profileA[term]
                termBWeight = profileB[term]
                cosineSimilarity += termAWeight * termBWeight

        profilesNorm = profileANorm * profileBNorm
        cosineSimilarity = cosineSimilarity / profilesNorm
                
        return cosineSimilarity

class SuperPeerServer(threading.Thread):
    
    def __init__(self, superPeerAddress, superPeerPort, p2pNetwork):
        threading.Thread.__init__(self)
        self.setName('superPeerServer')
        self.__status = p2pNetwork
        self.__superPeerAddress = superPeerAddress
        self.__superPeerPort = superPeerPort
        
        self.__shutdown = False
        
    def shutdown(self):
        self.__shutdown = True
        
    def run(self):
        try:
            timeStart = datetime.datetime.now()

            server = SimpleXMLRPCServer.SimpleXMLRPCServer( (self.__superPeerAddress, self.__superPeerPort) )
            server.allow_none = True
            server.allow_reuse_address = True
            server.register_instance(self.__status)
            printLog("\n[%s] Hello! Superpeer is running @ http://%s:%s..." % (threading.currentThread().getName(), self.__superPeerAddress, self.__superPeerPort))

            while(not self.__shutdown):
                server.handle_request()
            print "[%s] Bye bye." % threading.currentThread().getName()
            
        except IOError:
            printLog("[%s] Unable to discover %s ip address" % (threading.currentThread().getName(), interfaceName) )
            exit()

if __name__ == '__main__':
    interfaceName = None

    for argument in sys.argv:
        
        if re.search('if=', argument):
            interfaceName = re.split('=', argument)[1]
            
    if not interfaceName:
        print "\nUsage: python superpeer.py if=IFNAME"
        print "\n\tIFNAME: network adapter interface name (e.g. eth0)\n"
        exit()

    OPTION = 2

    if OPTION == 2:
        net = P2PNetwork()
        
        try:
            superPeerAddress = get_ip_address(interfaceName)
            superPeerPort = 15000
            superPeerServerProcess = SuperPeerServer(superPeerAddress, superPeerPort, net)
            superPeerServerProcess.start()
            
            pingerProcess = Pinger(net)
            pingerProcess.start()
            
            bbProcess = BuddyBuilder(net)
            bbProcess.start()
            
            while(True): ###FIXME
                time.sleep(5000)
        except KeyboardInterrupt:
            print "[%s] shutting down..." % threading.currentThread().getName()
            
            superPeerServerProcess.shutdown()
            pingerProcess.shutdown()
            bbProcess.shutdown()
            
            print "[%s] waiting for threads..."  % threading.currentThread().getName()
            superPeerServerProcess.join(5)
            pingerProcess.join(5)
            bbProcess.join(5)
            
            print "[%s] Bye bye" % threading.currentThread().getName()
            
        except:
            print "[%s] ECCEZIONE!!!!" % threading.currentThread().getName()

    elif OPTION==0:
        superPeer = SuperPeerServer(interfaceName)
        superPeer.start()
        timeStart = datetime.datetime.now()
        try:
            pass
        except KeyboardInterrupt:
            superPeer.shutdownSuperPeer()
            timeEnd = datetime.datetime.now()
            timeJob = timeEnd - timeStart
            time_sec = timeJob.seconds
            minutes = timeJob.seconds/60
            seconds = time_sec - 60*minutes
            print "\n[%s] my job took %d minutes, %d seconds. I'm leaving... see you next time!" % (threading.currentThread().getName(), minutes, seconds)
            exit()