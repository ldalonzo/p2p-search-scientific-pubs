#!/usr/bin/env python

import codecs
import datetime
import hashlib
import os
import popen2
import re
import threading
from xml.dom import minidom

from core.core import Bibliography
from core.core import Reference

class ParsCitWrapper(threading.Thread):
    
    def __init__(self, reference):
        threading.Thread.__init__(self)
        self.__referenceString = reference.rawString
        self.__reference = reference
    
    def run(self):
        try:
            tempCitationFile = '../tmp/rawcit-%s.txt' % hashlib.sha1(self.__referenceString).hexdigest()

            fsock = codecs.open(tempCitationFile, 'w', encoding='utf-8', errors='ignore')
            fsock.write(self.__referenceString)
            fsock.close()

            child = popen2.Popen3('perl ../lib/parscit-080917/bin/parseRefStrings.pl %s' % tempCitationFile, True)
            
            xmlData = ''
            for line in child.fromchild:
                xmlData = xmlData + line
                
            exitCode = os.WEXITSTATUS( child.wait() )
            os.system('rm %s' % tempCitationFile)
            
            if exitCode==0:
                xmlData = re.sub('&', 'and', xmlData)  
        
                try:
                    xmlDoc = minidom.parseString(xmlData)
                
                    citationElements = xmlDoc.getElementsByTagName('citation')
                    for citationNode in citationElements:
                        
                        for title in citationNode.getElementsByTagName('title'):
                            self.__reference.title = unicode(title.firstChild.data)
                        
                        authors = citationNode.getElementsByTagName('author')
                        if len(authors)>0:
                            self.__reference.authors = [author.firstChild.data for author in authors]
                            
                        for booktitle in citationNode.getElementsByTagName('booktitle'):
                            self.__reference.booktitle = booktitle.firstChild.data
                            
                        for pages in citationNode.getElementsByTagName('pages'):
                            self.__reference.pages = pages.firstChild.data
                            
                        for date in citationNode.getElementsByTagName('date'):
                            node = date.firstChild
                            if node:
                                self.__reference.date = date.firstChild.data
                except:
                    pass
            else:
                pass
        except (OSError):
            pass

class ReferenceStringsParser():
    
    def __init__(self):
        pass
    
    def feed_mt(self, referencesList):
        bibliography = Bibliography()
        
        listOfThreads = []
        for referenceString in referencesList:
            if not re.search('\.$', referenceString):
                referenceString += '.'
            reference = Reference(referenceString)
            bibliography.addReference(reference)
            parsCitThread = ParsCitWrapper(reference)
            listOfThreads.append(parsCitThread)
            parsCitThread.start()
            
        for thread in listOfThreads:
            thread.join()
            
        return bibliography
    
    def feed(self, referencesList):
        
        bibliography = Bibliography()
        for referenceString in referencesList:
            if not re.search('\.$', referenceString):
                referenceString += '.'
            
            xmlData = self.parseReferenceString(referenceString)
            if xmlData:
                reference = self.parseXmlReference(xmlData, Reference(referenceString))
                bibliography.addReference(reference)
            
        return bibliography
        
    def parseReferenceString(self, referenceString):
        try:
            tempCitationFile = '../tmp/rawCitations.txt'
            fsock = codecs.open(tempCitationFile, 'w', encoding='utf-8', errors='ignore')
            fsock.write(referenceString)
            fsock.close()
            
            child = popen2.Popen3('perl -CSD ../lib/parscit-080917/bin/parseRefStrings.pl %s' % tempCitationFile, True)
            
            xmlCitations = ''
            for line in child.fromchild:
                xmlCitations = xmlCitations + line
                
            exitCode = os.WEXITSTATUS( child.wait() )
            os.system('rm %s' % tempCitationFile)
            
            if exitCode==0:
                return xmlCitations
            else:
                return None
            
        except (OSError):
            print "OS ERROR!"
            
    def parseXmlReference(self, xmlData, reference):
        """Given the xml output provided by the parseRefString.pl tool,
        returns a Reference object with the attributes retrieved from
        the parsed reference string"""

        xmlData = re.sub('&', 'and', xmlData)

        citationsList = []
        try:
            xmlDoc = minidom.parseString(xmlData)
        
            citationElements = xmlDoc.getElementsByTagName('citation')
            for citationNode in citationElements:
                citation = {}
                
                for title in citationNode.getElementsByTagName('title'):
                    reference.title = unicode(title.firstChild.data)

                authors = citationNode.getElementsByTagName('author')
                if len(authors)>0:
                    reference.authors = [author.firstChild.data for author in authors]

                for booktitle in citationNode.getElementsByTagName('booktitle'):
                    reference.booktitle = booktitle.firstChild.data

                for pages in citationNode.getElementsByTagName('pages'):
                    reference.pages = pages.firstChild.data

                for date in citationNode.getElementsByTagName('date'):
                    node = date.firstChild
                    if node:
                        reference.date = date.firstChild.data

                return reference
        except:
            print "[EXCEPTION] There was an error on parsing the reference strings."

if __name__ == '__main__':
    
    parser = ReferenceStringsParser()
    
    referencesList = []
    referencesList.append('[1] http://sf.net/projects/pingpong-abc')
    referencesList.append('[2] http://www.kijkonderzoek.nl')
    referencesList.append('[3] E. Adar and B. A. Huberman. Free riding on gnutella. Technical report, Xerox PARC, August 2000.')
    referencesList.append('[4] N. Borch. Social peer-to-peer for social people. In The International Conf. on Internet Technologies and Applications , Sep 2005.')
    referencesList.append('[5] J. S. Breese, D. Heckerman, and C. Kadie. Empirical analysis of predictive algorithms for collaborative filtering. In Proc. of UAI , 1998.')
    referencesList.append('[6] A. Broder and M. Mitzenmacher. Network applications of bloom filters: A survey. In 40th Conference on Communication, Control, and Computing , 2002')
    referencesList.append('[7] N. Christin, A.S. Weigand, and J. Chuang. Content availibility, pollution and poisoning. In ACM E-Commerce Conference . ACM, June 2005')
    referencesList.append('[8] A. Fast, D. Jensen, and B. N. Levine. Creating social networks to improve peer-to-peer networking. In 11th ACM SIGKDD , Aug 2005')
    
    time_start = datetime.datetime.now()
    bibliography = parser.feed(referencesList)
    time_job = datetime.datetime.now() - time_start
    print "[Sequential version] Completed in %d seconds\n-----------------------" % time_job.seconds
    for ref in bibliography.getReferences():
        print "\n%s" % ref.rawString
        if hasattr(ref, 'title'):
            print "TITLE: %s" % ref.title
        if hasattr(ref, 'authors'):
            print "AUTHORS: %s" % ref.authors
        
    time_start = datetime.datetime.now()
    bibliography = parser.feed_mt(referencesList)
    time_job = datetime.datetime.now() - time_start
    print "[Multithreaded version] Completed in %d seconds\n-----------------------" % time_job.seconds
    for ref in bibliography.getReferences():
        print "\n%s" % ref.rawString
        if hasattr(ref, 'title'):
            print "TITLE: %s" % ref.title
        if hasattr(ref, 'authors'):
            print "AUTHORS: %s" % ref.authors