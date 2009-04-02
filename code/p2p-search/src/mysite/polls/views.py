
from django.http import HttpResponse

import datetime
import codecs
import xmlrpclib
import math

from django.template import Context, loader
from mysite.polls.models import Choice

from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from xml.dom import minidom
import re

from forms_test import ContactForm

def getProxyPeerServer():
    
    logFileName = '../tmp/peerAddress.txt'
    logFile = codecs.open(logFileName, 'r', 'utf-8', errors='ignore')
    peerProxyAddress =  "%s" % logFile.read()
    logFile.close()
    
    server = xmlrpclib.ServerProxy(peerProxyAddress)
    return server
    

class Paper():
    def __init__(self):
        self.title = ''

def startSearch(request):
    
    server = getProxyPeerServer()
    name = server.getName()
    
    numOfDocs = server.getNumOfIndexedDocuments()
    
    centroidTagClouds = server.getClusterCentroidApproximation()
        
    largestWeight = float(0)
    smallestWeight = float(1)
    for term in centroidTagClouds.keys():
        if centroidTagClouds[term] > largestWeight:
            largestWeight = float( centroidTagClouds[term] )
        if centroidTagClouds[term] < smallestWeight:
            smallestWeight = float( centroidTagClouds[term] )

    largestFontSize = 26
    smallestFontSize = 6
    
    deltaFontSize = float(largestFontSize - smallestFontSize) 
    deltaWeight = largestWeight - smallestWeight

    tagCloud = []
    if deltaWeight>0:
        orderedSet = centroidTagClouds.keys()
        orderedSet.sort()
        for term in orderedSet:
            tag = {}
            amount = float( (centroidTagClouds[term]-smallestWeight)/deltaWeight )
            target = smallestFontSize + deltaFontSize * amount

            tag['term'] = term
            tag['size'] = math.ceil( target )
            tagCloud.append(tag)

    pageContext = {'name':name, 'docs':numOfDocs, 'tagCloud':tagCloud}
        
    rss = server.getClusterRss()
    if rss:
        pageContext['rss'] = "%.2f" % rss
    
    approx = server.getClusterApproxRatio()
    if approx:
        approx = approx*100
        pageContext['approx'] = "%.3f" % approx
        
        
    tasteBuddies = server.getTasteBuddiesDjango()
    buddyList = []
    for buddyName in tasteBuddies.keys():
        buddyContextData = {}
        buddyContextData['name'] = buddyName
        (address, port, sim) = tasteBuddies[buddyName]
        buddyContextData['address'] = address
        buddyContextData['port'] = port
        buddyContextData['sim'] = "%.4f" % (sim*100)
        buddyList.append(buddyContextData)
        
    if len(buddyList)>0:
        pageContext['buddies'] = buddyList
        pageContext['numOfBuddies'] = len(buddyList)

    server = getProxyPeerServer()
    recommendations = server.getRecommendationDjango()
    
    recommendationResults = []
    for reco in recommendations.keys():
        results = parseResult( recommendations[reco].encode('utf-8') )
        recommendationResults.append( {'buddy':reco, 'resultSet': results, 'lenResultSet':len(results)} )
        
    if len(recommendationResults) > 0:
        pageContext['recommendations'] = recommendationResults
    
    t = loader.get_template('polls/search.html')
    c = Context(pageContext)
    return HttpResponse(t.render(c))

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/thanks/')
        
    else:
        form = ContactForm()
            
    return render_to_response('contact.html', {'form':form})

def parseResult(xmlData):
    resultSet = []
    try:
        xmlDoc = minidom.parseString(xmlData)
        resultElements = xmlDoc.getElementsByTagName('result')
        for resultNode in resultElements:
            paper = {}
            for title in resultNode.getElementsByTagName('title'):
                paper['title'] = unicode(title.firstChild.data)
                
            authors = []
            for authorsNode in resultNode.getElementsByTagName('authors'):
                for authorNode in authorsNode.getElementsByTagName('author'):
                    authors.append(unicode(authorNode.firstChild.data))
            paper['authors'] = ', '.join(authors)
            
            for abstractNode in resultNode.getElementsByTagName('abstract'):
                paper['abstract'] = abstractNode.firstChild.data
            
            for citedByNode in resultNode.getElementsByTagName('citedby'):
                numOfCitingPapers = int(citedByNode.firstChild.data)
                if numOfCitingPapers != 0:
                    paper['citedBy'] = citedByNode.firstChild.data
                
            for paperURNNode in resultNode.getElementsByTagName('urn'):
                paperURN = paperURNNode.firstChild.data
                paperURN = re.sub("\s", '', paperURN)
                paper['urn'] = paperURN
                
            for similarityNode in resultNode.getElementsByTagName('similarity'):
                similarityScore = float(similarityNode.firstChild.data)
                similarityScorePercentage = similarityScore * 100
                paper['similarity'] = "VSM similarity ~%d%% (%.3f)" % (similarityScorePercentage, similarityScore)
                
            for pageRankNode in resultNode.getElementsByTagName('pagerank'):
                pageRank = float(pageRankNode.firstChild.data)
                pageRankPercentage = pageRank * 100
                paper['pagerank'] = "PageRank ~%d%% (%.4f)" % (pageRankPercentage, pageRank)
                
            for resourceNode in resultNode.getElementsByTagName('resource'):
                resourceURL = resourceNode.firstChild.data
                paper['resourceURL'] = "file://" + re.sub('^[\s]*', '', resourceURL)
                
            resultSet.append(paper)
    except:
        print "eccezione!"
    
    return resultSet
    
def query(request):
    
    authors = request.POST['author']
    
    server = getProxyPeerServer()
    response = server.search(authors)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)

    t = loader.get_template('polls/results.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', authors),
                 'lunghezza' : lunghezza})

    return HttpResponse(t.render(c))

def queryIDF(request):
    
    query = request.POST['searchAtLeast']
    server = getProxyPeerServer()
    response = server.searchTopK(query)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    t = loader.get_template('polls/resultsIDF.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', query),
                 'lunghezza' : lunghezza})
    
    return HttpResponse(t.render(c))

def queryTitle(request):
    query = request.POST['searchAtLeast']
    server = getProxyPeerServer()
    response = server.searchTitle(query)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    t = loader.get_template('polls/resultsIDF.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', query),
                 'lunghezza' : lunghezza})
    
    return HttpResponse(t.render(c))

def queryAbstract(request):
    query = request.POST['searchAtLeast']
    server = getProxyPeerServer()
    response = server.searchAbstract(query)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    t = loader.get_template('polls/resultsIDF.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', query),
                 'lunghezza' : lunghezza})
    
    return HttpResponse(t.render(c))

def queryAll(request):
    query = request.POST['searchAtLeast']
    server = getProxyPeerServer()
    response = server.searchAll(query)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    t = loader.get_template('polls/resultsIDF.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', query),
                 'lunghezza' : lunghezza})
    
    return HttpResponse(t.render(c))

def searchCloud(request, keyword):
    query = keyword
    
    server = getProxyPeerServer()

    startTime = datetime.datetime.now()

    response = server.searchAll(query)

    response_utf8 = response.encode('utf-8')

    jobTime = datetime.datetime.now() - startTime
    jobTimeString = "%d.%d" % (jobTime.seconds, jobTime.microseconds)
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    pageContext = {'resultSet': results, 'query': re.split('\s', query), 'lunghezza' : lunghezza}
    pageContext['jobTime'] = jobTimeString
    pageContext['lenLocalResults'] = len(results)
    pageContext['peerName'] = server.getName()

    t = loader.get_template('polls/localsearchresults.html')
    c = Context(pageContext)

    return HttpResponse(t.render(c))

def search_newVersion(request):
    query = request.POST['queryText']
    server = getProxyPeerServer()
    response = ''

    startTime = datetime.datetime.now()

    region = request.POST['textRegion']
    if region=='title':
        response = server.searchTitle(query)
        
    elif region=='abstract':
        response = server.searchAbstract(query)
        
    else:
        response = server.searchAll_FullText(query)

    jobTime = datetime.datetime.now() - startTime

    response_utf8 = response.encode('utf-8')

    jobTimeString = "%d.%d" % (jobTime.seconds, jobTime.microseconds)
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    pageContext = {'resultSet': results, 'query': re.split('\s', query), 'lunghezza' : lunghezza}
    pageContext['jobTime'] = jobTimeString
    pageContext['lenLocalResults'] = len(results)
    pageContext['peerName'] = server.getName()

    t = loader.get_template('polls/localsearchresults.html')
    c = Context(pageContext)

    return HttpResponse(t.render(c))

def p2pKeywordSearch(request):
    query = request.POST['queryText']
    server = getProxyPeerServer()

    response = ''
    
    startTime = datetime.datetime.now()
    response = server.searchAll(query)
    jobTime = datetime.datetime.now() - startTime    
    jobTimeString = "%d.%d" % (jobTime.seconds, jobTime.microseconds)
    
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    pageContext = {'resultSet': results, 'query': re.split('\s', query), 'lunghezza' : lunghezza}
    pageContext['jobTime'] = jobTimeString
    pageContext['lenLocalResults'] = len(results)
    pageContext['peerName'] = server.getName()
    
    p2pResponses = server.p2pSearch(query)
    p2pContextResults = []
    if len( p2pResponses.keys() )>0:
        for buddyName in p2pResponses.keys():
            (jobTimeString, xmlResult) = p2pResponses[buddyName]
            
            resultProperties = {}
            resultProperties['buddyName'] = buddyName
            resultProperties['searchTime'] = jobTimeString
            resultProperties['peerResults'] = parseResult( xmlResult.encode('utf-8') )
            resultProperties['lenPeerResults'] = len(resultProperties['peerResults'])
            p2pContextResults.append(resultProperties)

    if len(p2pContextResults)>0:
        pageContext['p2pResults'] = p2pContextResults

    t = loader.get_template('polls/p2psearchresults.html')
    c = Context(pageContext)
    return HttpResponse(t.render(c))

def queryAll_FullText(request):
    query = request.POST['searchAtLeast']
    server = getProxyPeerServer()
    response = server.searchAll_FullText(query)
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)
    
    t = loader.get_template('polls/resultsIDF.html')
    c = Context({'resultSet': results,
                 'query': re.split('\s', query),
                 'lunghezza' : lunghezza})
    
    return HttpResponse(t.render(c))
    
def getCitedBy(request, paperURN):
    
    print "paperURN is _%s_" % paperURN
    
    server = getProxyPeerServer()
    response = server.getCitingPapers(paperURN)
    
    response_utf8 = response.encode('utf-8')
    
    results = parseResult(response_utf8)
    lunghezza = len(results)

    t = loader.get_template('polls/results.html')
    c = Context({'resultSet': results,
                 'lunghezza' : lunghezza})

    return HttpResponse(t.render(c))

