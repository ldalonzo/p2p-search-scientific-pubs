"""
core.py

written by Leonardo D'Alonzo

version of 22/12/2008
"""

import hashlib
import os

class Paper():
    """Class Paper"""
    
    def __init__(self, title):
        
        self.urn = None
        
        self.title = title
        
        self.authors = []
        self.__citedBy = []
        self.__resources = []
        
    def addAuthor(self, author):
        if not self.authors.__contains__(author):
            self.authors.append(author)
            
    def getAuthors(self):
        return self.authors
    
    def addCitingPaper(self, citingPaper):
        if not self.__citedBy.__contains__(citingPaper.urn):
            self.__citedBy.append(citingPaper.urn)
            
    def addResource(self, resource):
        if not self.__resources.__contains__(resource):
            self.__resources.append(resource)
            
    def getResources(self):
        return self.__resources
            
    def getCitingPapers(self):
        return self.__citedBy

class Author():
    """Class Author"""
    
    def __init__(self, name):
        self.name = name
        self.__writtenPapers = []
        
    def addPaper(self, paper):
        if self.__writtenPapers.count(paper) == 0:
            self.__writtenPapers.append(paper)
            return True
        return None
    
    def getWrittenPapers(self):
        return self.__writtenPapers
    
    def getName(self):
        return self.name

class Bibliography():
    """Class Bibliography"""
    
    def __init__(self):
        self.__references = []
    
    def addReference(self, reference):
        self.__references.append(reference)
        
    def getReferences(self):
        return self.__references

class Reference():
    """Class Reference"""
    
    def __init__(self, rawString):
        self.rawString = rawString
    
    def setDescribe(self, paper):
        self.describe = paper.urn

class PDFResource():
    
    def __init__(self, URL):
        self.resourceURL = URL

        (path, filename) = os.path.split(URL)
        (name, extension) = os.path.splitext(filename)
        self.sha1 = "%s" % name

    def __shaChecksum(self):
        content = ''
        try:
            fsock = open(self.resourceURL)
            while True:
                buffer = fsock.read(4096)
                if buffer == "":
                    break
                content += buffer
            fsock.close()
            checksum = hashlib.sha1(content).hexdigest()
            return checksum
        except (OSError):
            return None

class Context():
    pass