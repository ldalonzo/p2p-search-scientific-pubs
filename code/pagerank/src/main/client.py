#!/usr/bin/env python

import index.index
import os
import threading
import time
import re

from index import presentation

import datetime
import SimpleXMLRPCServer

class Indexer(threading.Thread):
    
    def __init__(self, index, name='indexer'):
        threading.Thread.__init__(self)
        self.setName(name)
        
        self.__index = index
        self.__directoryToIndexList = []
        self.__directoryToIndexList.append('/home/leo/workspace/bibliography/thesis')

    def run(self):
        print "[%s] Indexer is running..." % threading.currentThread().getName()
        self._set_daemon()
        try:
            for directory in self.__directoryToIndexList:
                for fileName in self.listDirectory(directory):
                    self.__index.submitPDF(fileName)

            self.__index.buildCitationsLinks()
            self.__index.createDotCode()

        except KeyboardInterrupt:
            exit()
    
    def listDirectory(self, directory):
        file_ext_list = ['.pdf']
        file_list = [os.path.normcase(f) for f in os.listdir(directory)]
        file_list = [os.path.join(directory,f) for f in file_list if os.path.splitext(f)[1] in file_ext_list]
        return file_list
    
class SearchServerMethodsInterface():
    
    def __init__(self, index):
        self.__index = index
        
    def search(self, searchQuery):
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
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryTitle(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchAbstract(self, searchQuery):
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryAbstract(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
    def searchAll(self, searchQuery):
        queryTerms = re.split('\s', searchQuery)
        resultSet = self.__index.queryAll(queryTerms)
        return presentation.encodeResultAsXml_IDF(resultSet)
    
class SearchServer(threading.Thread):
    
    def __init__(self, index, address = ('localhost', 9000)):
        threading.Thread.__init__(self)
        self.setName('searchServer')
        
        self.__address = address
        self.__server = SimpleXMLRPCServer.SimpleXMLRPCServer(self.__address)
        self.__server.allow_reuse_address = True
        self.__server.register_instance( SearchServerMethodsInterface(index) )
    
    def run(self):
        print "[%s] Server is running at http://%s:%s/" % (threading.currentThread().getName(), self.__address[0], self.__address[1])
        try:
            self.__server.serve_forever()
        except KeyboardInterrupt:
            exit()


if __name__ == '__main__':

    DEBUG=False
    
    if DEBUG:
        
        for c in range(10):
            for d in range(6):
                print "%d, %d" %(c,d)
                if c==d:
                    print "breaking..."
                    break
    
    else:
        myIndex = index.index.Index()
        
        
        server = SearchServer(myIndex)
        indexer = Indexer(myIndex)
        
        server.start()
        indexer.start()
        
        time_start = datetime.datetime.now()
        try:
            while(True):
                time.sleep(1000)

        except KeyboardInterrupt:
            time_end = datetime.datetime.now()
            time_job = time_end - time_start
            
            time_sec = time_job.seconds
            minutes = time_job.seconds/60
            seconds = time_sec - 60*minutes
            
            
            print "\nMy job lasts %d minutes, %d seconds." % (minutes, seconds)
            print "I'm leaving... see you next time!"
            exit()