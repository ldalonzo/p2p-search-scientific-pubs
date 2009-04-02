import xml.dom.minidom

def encodeResultAsXml(resultSet = []):
    xmlDoc = xml.dom.minidom.Document()
    
    results = xmlDoc.createElement('results')
    xmlDoc.appendChild(results)
    
    for paper in resultSet:
        result = xmlDoc.createElement('result')
        results.appendChild(result)
        
        paperURN = xmlDoc.createElement('urn')
        paperURN.appendChild(xmlDoc.createTextNode(paper.urn))#FIXME
        #print "_%s_" % paper.FIXME__paperURN
        result.appendChild(paperURN)
        
        title = xmlDoc.createElement('title')
        title.appendChild(xmlDoc.createTextNode(paper.title))
        result.appendChild(title)
        
        authors = xmlDoc.createElement('authors')
        result.appendChild(authors)
        
        for author in paper.getAuthors():
            authorNode = xmlDoc.createElement('author')
            authorNode.appendChild(xmlDoc.createTextNode(author.getName()))
            authors.appendChild(authorNode)
            
        if hasattr(paper, 'abstract'):
            abstractNode = xmlDoc.createElement('abstract')
            abstractText = '[%d] - %s' % (len(paper.abstract), paper.abstract)

            abstractNode.appendChild(xmlDoc.createTextNode(abstractText))
            result.appendChild(abstractNode)
            
        citedBy = xmlDoc.createElement('citedby')
        numOfCitations = "%d" % len(paper.getCitingPapers())
        citedBy.appendChild(xmlDoc.createTextNode(numOfCitations))
        result.appendChild(citedBy)
        
    retValue = xmlDoc.toprettyxml(indent="  ")

    return retValue

def encodeResultAsXml_IDF(resultSet = []):
    xmlDoc = xml.dom.minidom.Document()
    
    results = xmlDoc.createElement('results')
    xmlDoc.appendChild(results)
    
    for tuple in resultSet:
        
        paper = tuple[0]
        similarityScoreText = "%f" % tuple[1]
        
        result = xmlDoc.createElement('result')
        results.appendChild(result)
        
        paperURN = xmlDoc.createElement('urn')
        paperURN.appendChild(xmlDoc.createTextNode(paper.urn))#FIXME
        result.appendChild(paperURN)

        resource = xmlDoc.createElement('resource')
        resURL = paper.getResources()[0].resourceURL
        resource.appendChild(xmlDoc.createTextNode(resURL))
        result.appendChild(resource)

        similarity = xmlDoc.createElement('similarity')
        similarity.appendChild(xmlDoc.createTextNode(similarityScoreText))
        result.appendChild(similarity)
        
        title = xmlDoc.createElement('title')
        title.appendChild(xmlDoc.createTextNode(paper.title))
        result.appendChild(title)
        
        authors = xmlDoc.createElement('authors')
        result.appendChild(authors)
        
        for author in paper.getAuthors():
            authorNode = xmlDoc.createElement('author')
            authorNode.appendChild(xmlDoc.createTextNode(author.getName()))
            authors.appendChild(authorNode)
            
        if hasattr(paper, 'abstract'):
            abstractNode = xmlDoc.createElement('abstract')
            abstractText = '[%d] - %s' % (len(paper.abstract), paper.abstract)

            abstractNode.appendChild(xmlDoc.createTextNode(abstractText))
            result.appendChild(abstractNode)
            
        citedBy = xmlDoc.createElement('citedby')
        numOfCitations = "%d" % len(paper.getCitingPapers())
        citedBy.appendChild(xmlDoc.createTextNode(numOfCitations))
        result.appendChild(citedBy)
        
    retValue = xmlDoc.toprettyxml(indent="  ")
    
    return retValue
