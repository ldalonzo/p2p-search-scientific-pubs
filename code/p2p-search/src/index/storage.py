import cPickle
import math
import threading

class Persistence():
    
    def __init__(self):
        self.repositoryDirectory = '../repo/'
    
    def save(self, pickledDataFile, objectsList):
        returnValue = False
        fileName = self.repositoryDirectory + pickledDataFile
        try:
            output = open(fileName, 'wb')
            try:
                for object in objectsList:
                    cPickle.dump(object, output)
                returnValue = True
            except:
                print "[%s] Unable to save index data to %s" % (threading.currentThread().getName(), fileName)
            finally:
                output.close()
        except:
            print "[%s] Unable to open %s on saving index data" % (threading.currentThread().getName(), fileName)
        return returnValue
    
    def restore(self, pickledDataFile):
        restoredObject = None
        try:
            fileName = self.repositoryDirectory + pickledDataFile
            input = open(fileName, 'rb')
            try:
                restoredObject = cPickle.load(input)                    
            except:
                print "[%s] Unable to restore index data." % threading.currentThread().getName()
                exit(-1)
            finally:
                input.close()
        except:
            print "[%s] Unable to open %s. No data will be restored." % (threading.currentThread().getName(), pickledDataFile)            
        return restoredObject
    
class KnownResources(Persistence):
    
    def __init__(self):
        Persistence.__init__(self)
        self.__pickledFileName = 'resources.pickle'
        
        self.__knownResources = {}
        
        knownResources = self.restore(self.__pickledFileName)
        if knownResources:
            print "[%s] KnownResources restored. It contains %d entries." % (threading.currentThread().getName(), len(knownResources.keys()))
            self.__knownResources = knownResources
        
    def contains(self, sha1):
        if self.__knownResources.has_key(sha1):
            return True
        return False
    
    def add(self, resourceKey, resource):
        if not self.__knownResources.has_key(resourceKey):
            self.__knownResources[resourceKey] = resource
            self.save(self.__pickledFileName, [self.__knownResources])
    
class KnownAuthors(Persistence):
    
    def __init__(self):
        Persistence.__init__(self)
        self.__pickledFileName = 'authors.pickle'
        
        self.__knownAuthors = {}
        
        knownAuthors = self.restore(self.__pickledFileName)
        if knownAuthors:
            print "[%s] KnownAuthors restored. It contains %d entries." % (threading.currentThread().getName(), len(knownAuthors.keys()))
            self.__knownAuthors = knownAuthors
    
    def contains(self, authorName):
        if self.__knownAuthors.has_key(authorName):
            return True
        return False
    
    def add(self, author):
        if self.__knownAuthors.has_key(author.name):
            return False
        self.__knownAuthors[author.name] = author
        self.save(self.__pickledFileName, [self.__knownAuthors])
        return True
    
    def get(self, author):
        if self.__knownAuthors.has_key(author):
            return self.__knownAuthors[author]
        return None
    
    def keys(self):
        return self.__knownAuthors.keys()
    
class KnownPapers(Persistence):
    
    def __init__(self):
        Persistence.__init__(self)
        self.__pickledFileName = 'papers.pickle'
        self.__knownPapers = {}

        knownPapers = self.restore(self.__pickledFileName)
        if knownPapers:
            print "[%s] knownPapers restored. It contains %d entries." % (threading.currentThread().getName(), len(knownPapers.keys()))
            self.__knownPapers = knownPapers

    def committ(self):
        self.save(self.__pickledFileName, [self.__knownPapers])
        
    def contains(self, paperURN):
        if self.__knownPapers.has_key(paperURN):
            return True
        return False
    
    def add(self, paperURN, paper):
        if self.__knownPapers.has_key(paperURN):
            return False
        self.__knownPapers[paperURN] = paper
        self.save(self.__pickledFileName, [self.__knownPapers])
        return True
    
    def get(self, paperURN):
        if self.__knownPapers.has_key(paperURN):
            return self.__knownPapers[paperURN]
    
    def keys(self):
        return self.__knownPapers.keys()
    
class Dictionary(Persistence):
    def __init__(self, dictionaryName):
        Persistence.__init__(self)
        
        self.name = dictionaryName
        self.__pickledFileName = dictionaryName + '.pickle'
        
        
        self.__dictionary = {}
        
        dictionary = self.restore(self.__pickledFileName)
        if dictionary:
            print "[%s] dictionary '%s' restored. It contains %d entries." % (threading.currentThread().getName(), self.name, len(dictionary.keys()))
            self.__dictionary = dictionary
            
        self.__condition = threading.Condition()
            
    def contains(self, term):
        if self.__dictionary.has_key(term):
            return True
        return False
    
    def addTerm(self, term, document, frequency):
        
        self.__condition.acquire()
        
        docID = document.urn
        
        if self.__dictionary.has_key(term):
            postingFile = self.__dictionary[term]
            
            if not postingFile.has_key(docID):
                #(frequency, weight)
                postingFile[docID] = (frequency, 0)
            else:
                print "[%s EXCEPTION] inconsistency error: docID %s is already present in the posting file of the word %s" % (threading.currentThread().getName(), docID, term)
        else:
            self.__dictionary[term] = {docID: (frequency, 0)}
            
        self.__condition.release()

    def committ(self):
        self.save(self.__pickledFileName, [self.__dictionary])
            
    def getPostingFile(self, term):
        self.__condition.acquire()
        
        if self.__dictionary.has_key(term):
            self.__condition.release()
            return self.__dictionary[term]
        
        self.__condition.release()
        return None
    
    def getTermByDocMatrix(self):
        
        self.__condition.acquire()
        
        invertedIndex = self.__dictionary.keys()
        invertedIndex.sort()
        
        #building the list of all doc IDS
        listOfDocumentIDs = []
        for term in invertedIndex:
            postingFile = self.__dictionary[term]
            for docID in postingFile.keys():
                if not docID in listOfDocumentIDs:
                    listOfDocumentIDs.append(docID)
                    
        listOfDocumentIDs.sort()
        
        docVector = listOfDocumentIDs
        termVector = []
        tdocMatrix = []
        for term in invertedIndex:
            row = []
            termVector.append(term)
            postingFile = self.__dictionary[term]
            for docID in docVector:
                if docID in postingFile.keys():
                    (tf, wij) = postingFile[docID] 
                    row.append(wij)
                else:
                    row.append(0)
            tdocMatrix.append(row)
            
        self.__condition.release()
            
        return (docVector, termVector, tdocMatrix)
            
        
    def updateIDF(self, docsInTheCollection):
        
        doc_cumulative_weight = {}
        
        for term in self.__dictionary.keys():
            postingFile = self.__dictionary[term]
            
            # Number of docs in the collection in which the term ti appears
            Ni = len( postingFile.keys() )
            idf = math.log( float(docsInTheCollection) / float(Ni) )
            
            for docID in postingFile.keys():
                tf = postingFile[docID][0]
                w_ij = tf*idf
                postingFile[docID] = (tf, w_ij)
                
                if not doc_cumulative_weight.has_key(docID):
                    doc_cumulative_weight[docID] = float(0)
                doc_cumulative_weight[docID] += w_ij * w_ij#math.pow(w_ij, 2)
                
        # Normalizing
        for term in self.__dictionary.keys():
            postingFile = self.__dictionary[term]
            for docID in postingFile.keys():
                (termFreq, weight) = postingFile[docID]
                if doc_cumulative_weight[docID]>0:
                    normalizedWeight = weight / math.sqrt( doc_cumulative_weight[docID] )
                    postingFile[docID] = (termFreq, normalizedWeight)
                    
        self.save(self.__pickledFileName, [self.__dictionary])
