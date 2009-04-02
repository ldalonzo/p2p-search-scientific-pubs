import re

def filterExtraSpaces(text):
    ret = re.sub('^[\s]+', '', text) #removes spaces from the beginning
    ret = re.sub('[\s]+$', '', ret)  #removes spaces from the end
    ret = re.sub('[\s]+', ' ', ret)  #normalize multiple spaces to 1
    return ret

def removeCarriageReturns(text):
    text = re.sub('\n', ' ', text)
    return text

def splitRawReferencesToSingleReferences(rawReferencesText):
    """The function try to split the whole raw reference text
    into single text references looking for styles.
    
    ACM style
    e.g. 1. Davenport, T., DeLong, D. and Beers, M. 1998. Successful knowledge
            management projects. Sloan Management Review, 39 (2). 43-57.
    
    IEEE style
    e.g. [1] T. Davenport, D. DeLong, and M. Beers, "Successful knowledge
         management projects," Sloan Management Review, vol. 39, no. 2, pp. 43-57, 1998.
         
    """
    
    def __splitUsingGivenSeparator(refRegExp):
        
        referenceMatch = re.finditer(refRegExp, rawReferencesText)
        if referenceMatch:
        
            startpos = [reference.start() for reference in referenceMatch]
            referenceSpan = [(pos,startpos[startpos.index(pos)+1]-1) for pos in startpos if startpos.index(pos)<len(startpos)-1]
            if len(referenceSpan)>0:
                referenceSpan.append((referenceSpan[len(referenceSpan)-1][1]+1,len(rawReferencesText)))
                
                referenceList = []
                candidateReferenceList = [rawReferencesText[spanpos[0]:spanpos[1]] for spanpos in referenceSpan]
                for reference in candidateReferenceList:
                    if len(reference)>350:
                        break
                    referenceList.append(reference)
    
                referenceList = [removeCarriageReturns(ref) for ref in referenceList]
                referenceList = [filterExtraSpaces(ref) for ref in referenceList]
                
                if len(referenceList)>0:
                    return referenceList
    
        return None
        
    
    ieeeRegExp = '[\s]*\[[0-9]{1,2}\]'
    acmRegExp = '[ ]{1,}[\s]*[0-9]{1,2}\.[\s]+[A-Z]'
    
    ieeeStyle = re.split(ieeeRegExp, rawReferencesText)
    acmStyle = re.split(acmRegExp, rawReferencesText)
    
    if ieeeStyle and not acmStyle:
        refRegExp = ieeeRegExp
    elif not ieeeStyle and acmStyle:
        refRegExp = acmRegExp
    elif ieeeStyle and acmStyle:
        if len(ieeeStyle)>len(acmStyle):
            refRegExp = ieeeRegExp
        elif len(ieeeStyle)<len(acmStyle):
            refRegExp = acmRegExp
        else:
            return None
    else:
        return None
    
    return __splitUsingGivenSeparator(refRegExp)

def filterCitations(rawReferencesText):
    referenceStringList = splitRawReferencesToSingleReferences(rawReferencesText)
    if referenceStringList:
        return referenceStringList
    return None
