#!/usr/bin/env python

import codecs
import heapq
import math
import os
import popen2
import re
import sgmllib
import threading
import datetime

import citationParser
import filter
import referenceStringsParser

class PDFPaperParser():
    
    def __init__(self):
        self.title = None
        self.authors = None
        self.abstract = None
        self.bodyText = None
        self.bibliography = None
        self.fulltext = None
    
    def feed(self, pdfFileURL):
        pass
    
class PDFPaperParserHtml(PDFPaperParser):
    
    def __init__(self):
        PDFPaperParser.__init__(self)
    
    def feed(self, pdfFileURL):
        
        self.__init__()
        
        htmlContent = self.convertPdfToHtml(pdfFileURL)
        if not self.checkContentForPaper(htmlContent):
            print ""
            raise Exception('Not a paper')
        
        print "[%s] parsing html..." % threading.currentThread().getName()
        htmlparser = Pdf2HtmlParser()
        timeStart = datetime.datetime.now()
        
        htmlparser.feed(htmlContent)
        
        timeJob = datetime.datetime.now() - timeStart
        timeJobString = "%d.%d" % ( timeJob.seconds, timeJob.microseconds )
        print "[%s] html parsed, it tooks %s seconds" % (threading.currentThread().getName(), timeJobString)

        metadata = htmlparser.getMetadata(True)
        if metadata:
            
            if metadata.has_key('title'):
                if metadata['title']:
                    self.title = metadata['title']
            if metadata.has_key('authors'):
                if metadata['authors']:
                    self.authors = metadata['authors']
            if metadata.has_key('abstract'):
                if metadata['abstract']:
                    self.abstract = metadata['abstract']
            if metadata.has_key('bodyText'):
                if metadata['bodyText']:
                    self.bodyText = metadata['bodyText']
            if metadata.has_key('references'):
                if metadata['references']:
                    self.bibliography = metadata['references']
        else:
            raise Exception('No metadata')

    def checkContentForPaper(self, text_content=''):
        score = float(0)
        threshold = float(1.99)
        
        if re.search('abstract', text_content[:3000], re.IGNORECASE):
            score +=2
        elif re.search('summary', text_content[:3000], re.IGNORECASE):
            score +=2
        elif re.search('abstract', text_content, re.IGNORECASE):
            score +=1
        elif re.search('summary', text_content, re.IGNORECASE):
            score +=1
        
        #Sometimes the first letter is capitalized or it is draw using another special
        #font so the tool pdftotext return the word without the first letter
        if re.search('introduction', text_content, re.IGNORECASE):
            score +=1
        elif re.search('ntroduction', text_content, re.IGNORECASE):
            score +=0.5
            
        if re.search('conclusion', text_content, re.IGNORECASE):
            score +=1
        elif re.search('onclusion', text_content, re.IGNORECASE):
            score +=0.5
            
        if re.search('references', text_content, re.IGNORECASE):
            score +=1
        elif re.search('eferences', text_content, re.IGNORECASE):
            score +=1.5
        elif re.search('bibliography', text_content, re.IGNORECASE):
            score +=1
        if score > threshold:
            return True
        else:
            return False
    
    def convertPdfToHtml(self, pdfFileURN):
        """Uses the external tool pdftohtml to perform the conversion from
        the original pdf file format to the target html. The goal of the
        resulting file is to resemble the visual aspect of the pdf rendered file        
        """
        try:
            tempHtmlFile = 'temp.html'

            timeStart = datetime.datetime.now()
            child = popen2.Popen3('../lib/pdftohtml-0.36 -c -i -q -noframes -enc UTF-8 %s %s' % (pdfFileURN, tempHtmlFile.split('.')[0]), True)
            
            print "[%s] waiting for pdftohtml..." % threading.currentThread().getName()
            exitCode = os.WEXITSTATUS( child.wait() )
            timeJob = datetime.datetime.now() - timeStart
            timeJobString = "%d.%d" % (timeJob.seconds, timeJob.microseconds)
            if exitCode == 0:
                fsock = codecs.open(tempHtmlFile, 'r', 'utf-8', errors='ignore')
                try:
                    htmlContent = filter.remove_strange_chars( fsock.read() )
                finally:
                    os.system('rm %s' % tempHtmlFile)
                    fsock.close()
                    print "[%s] pdftohtml tooks %s seconds for conversion. Html length is about %d chars." % ( threading.currentThread().getName(), timeJobString, len(htmlContent) )
                    #print "[%s] htmlContent is long %d chars" % (threading.currentThread().getName(), len(htmlContent))
                    return htmlContent
            else:
                print "[%s] Error on converting pdf to html. Exit code was %d." % (threading.currentThread().getName(), exitCode)
                raise Exception('pdftohtml error')
        except (IOError, OSError):
            raise Exception('unable to perform the html conversion')
        
class Pdf2HtmlParser(sgmllib.SGMLParser):
    
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        
        self.__current_page = 0
        self.__currentTextProperties = {}
        
        self.__currentRetrievalStage = 'IDLE'
        
        self.__titleTextProperties = {}
        self.__authorsTextProperties = {}
        self.__abstractTextProperties = {}
        self.__rawReferences = ""
        
        self.__fontsFace = {}
        self.__top3LargestFonts = []
        
        self.__title = ''
        self.__authors = []
        self.__abstract = ''
        self.__bodyText = ''
        
        self.__breakLine = ''
        
        self.MAX_ABSTRACT_PAGE = 4
        
    
    def debug(self, functionName, message):
        debugMode = False
        if debugMode == True:
            print "[DEBUG %s] % s" % (functionName, message)

    def filterTitleText(self, text):
        if text.isupper():
            text = text.title()
        return text
    
    def filterExtraSpaces(self, text):
        ret = re.sub('^[\s]+', '', text) #removes spaces from the beginning
        ret = re.sub('[\s]+$', '', ret)  #removes spaces from the end
        ret = re.sub('[\s]+', ' ', ret)  #normalize multiple spaces to 1
        return ret
    
    def filterAuthors(self, text):
        authorTextMaxLenght = 35#27
        ban_words = ['Berkeley', 'College', 'Computer', 'Department', 'Engineering', 'IEEE', 'Institute',
                     'Laboratory', 'Member', 'Microsoft', 'Netherlands','Project', 'Report', 'Research',
                     'School', 'Science', 'Technology', 'Universit']
        regexp_ban_words = "|".join(ban_words)
        if (not re.search('[0-9]+|@|&', text) and (not re.search(regexp_ban_words, text)) ):
            
            text = re.sub(',[\s]*$', '', text)
            
            list = [possible_author for possible_author in re.split('[\s]*,|[\n]+|[\s]+and[\s]+|^[\s]*and[\s]+|[\s]+AND[\s]+', text) if len(possible_author)<authorTextMaxLenght]
            
            filtered_list_1 = [item for item in list if len(item)>0]
            
            for item in filtered_list_1:
                single_words = [word for word in re.split('[\s]*', item) if len(word)>0]
                if len(single_words)<2 or len(single_words)>3:
                    return None
                elif ((not re.search('^[A-Z]', single_words[0])) or (not re.search('^[A-Z]', single_words[len(single_words)-1]))):
                    return None
                    
            filtered_list_2 = [item for item in filtered_list_1 if re.search('[\w]+|[A-Z]. [\w]+', item)]
                    
            if len(filtered_list_2)==0:
                pass
            else:
                return [self.filterExtraSpaces(item) for item in filtered_list_2]

        return None

    def getMetadata(self, ReferenceAnalysis=True):
        def __filterAbstractText(text):
            m = re.search('^[\s]*Abstract[\s]*|^[\s]*Summary[\s]*', text, re.IGNORECASE)
            if m:
                text = text[m.span()[1]:]
            search_for_first_capital_letter = re.search('[A-Z]', text)
            if search_for_first_capital_letter:
                text = text[search_for_first_capital_letter.span()[0]:]
            return text

        def __normalizePunctuation(text):
            text = re.sub('\*$', '', text)
            text = re.sub(' :', ':', text)
            text = re.sub(' ,', ',', text)
            return text
        
        metadata = {}
        if len(self.__title) > 0:
            title = self.filterExtraSpaces(self.__title)
            title = __normalizePunctuation(title)
            title = self.filterTitleText(title)
            if re.search('[\w]+', title):
                metadata['title'] = title  
                
        if len(self.__authors) > 0:
            authors = [__normalizePunctuation(self.filterExtraSpaces(author)) for author in self.__authors]
            metadata['authors'] = [self.filterTitleText(author) for author in authors]
             
        if len(self.__abstract) > 0:
            abstract = self.filterExtraSpaces(self.__abstract)
            abstract = __normalizePunctuation(abstract)
            abstract = __filterAbstractText(abstract)
            if re.search('[\w]+', abstract):
                metadata['abstract'] = abstract
                
        if len(self.__bodyText) > 0:
            bodyText = self.filterExtraSpaces(self.__bodyText)
            bodyText = __normalizePunctuation(bodyText)
            if re.search('[\w]+', bodyText):
                metadata['bodyText'] = bodyText
                
        if len(self.__rawReferences)>0:
            self.__rawReferences = re.sub('^.{,4}[\s]+References', '', self.__rawReferences, 1)

            references = citationParser.filterCitations(self.__rawReferences)
            if references and len(references) and ReferenceAnalysis>0:
                refStringsParser = referenceStringsParser.ReferenceStringsParser()
                metadata['references'] = refStringsParser.feed(references)
        
        if len(metadata.keys())>0:
            return metadata
        
    def reset(self):
        sgmllib.SGMLParser.reset(self)
        
    def start_b(self, attrs):
        self.__currentTextProperties['bold'] = True
        
    def end_b(self):
        self.__currentTextProperties['bold'] = False
        
    def start_br(self, attrs):
        self.__breakLine += ' '

    def start_div(self, attrs):
        properties = re.split(';', attrs[0][1])
        if properties[0] == 'position:absolute':
            properties_top = re.split(':', properties[1])
            if properties_top[0] == 'top' and re.search('^[0-9]+', properties_top[1]):
                self.__currentTextProperties['top'] = int(properties_top[1])
        else:
            self.__currentTextProperties['top'] = -1
        
    def start_span(self, attrs):
        for tuple in attrs:
            if tuple[0] == 'class':
                self.__currentTextProperties['font'] = tuple[1]
    
    def handle_data(self, text):
        def __checkTopPositionForTitleLine():
            maxTitleTopPosition = 225#200
            if self.__currentTextProperties['top'] < maxTitleTopPosition:
                return True
            return False
        
        def __checkTopPositionForAuthorLine():
            maxSpaceBetweenTitleAndAuthors = 180
            if self.__titleTextProperties.has_key('top') and self.__currentTextProperties['top']>0:
                if self.__currentTextProperties['top'] - self.__titleTextProperties['top'] < maxSpaceBetweenTitleAndAuthors:
                    return True
            elif self.__currentTextProperties['top']<200:
                return True
            
            return False
        
        def __canBeATitleLine(text):
            if __checkTopPositionForTitleLine():
                if self.__currentTextProperties['font'] in self.__top3LargestFonts:
                    if re.search('[A-Z]+', text, re.IGNORECASE):
                        return True
    
                titleFontSizeTolerance = 2
                currentFontSize = self.__fontsFace[self.__currentTextProperties['font']]
                largestFontSize = self.__fontsFace[self.__top3LargestFonts[0]]
                if largestFontSize-currentFontSize < titleFontSizeTolerance:
                    return True
                else:
                    return False
            
        def __canConsiderTitleCompleted(text):
            if self.__currentTextProperties.has_key('font') and self.__titleTextProperties.has_key('font'):
                if self.__currentTextProperties['font'] != self.__titleTextProperties['font']:
                    if re.search('[A-Z]+', self.__title, re.IGNORECASE) and text == '\n':
                        return True
            
        def __canBeAnAuthorLine(text):
            if __checkTopPositionForAuthorLine():
                titleFontTolerance = 1
                
                if self.__titleTextProperties.has_key('font'):
                    titleFontSize = self.__fontsFace[self.__titleTextProperties['font']]
                    currentFontSize = self.__fontsFace[self.__currentTextProperties['font']]
                    difference = titleFontSize - currentFontSize
                    if difference > titleFontTolerance:
                        return True
                    elif difference > 0 and self.filterAuthors(text):
                        return True
                
            return False
            
        def __canBeTheAbstract(text):
            if self.__current_page < self.MAX_ABSTRACT_PAGE:
                if re.search('^[\s]*[A]?bstract[\s]*|^[\s]*[S]?ummary', text, re.IGNORECASE):
                    return True
            return False
        
        def __canBeANewSection(text, threshold=1):
            if self.__current_page > 0 and re.search('[\w]+', text): #TODO
                if self.__currentTextProperties.has_key('medium_font-size') and self.__currentTextProperties.has_key('font'):
                    currentFontSize = self.__fontsFace[self.__currentTextProperties['font']]
                    difference = currentFontSize - self.__currentTextProperties['medium_font-size'] 
                    if difference > threshold:
                        return True
            return False
                
        def __canBeTheReferences(text):
            if self.__current_page > 0: #TODO
                if __canBeANewSection:            
                    if re.search('^[\s]*[R]?eferences', text, re.IGNORECASE):
                        return True
                    elif re.search('^[\s]*[B]?ibliography', text, re.IGNORECASE):
                        return True
                    elif re.search('^.{,3}[\s]+References', text, re.IGNORECASE):
                        return True
                    else:
                        return False
            return False
        
        def __canStopTheReferences(text):
            if __canBeANewSection(text, 2):
                return True
            return False
        
        def __canStopAbstract(text):
            if len(self.__abstract)>3000:
                return True
                
            if self.__abstractTextProperties.has_key('medium_font-size') and self.__currentTextProperties.has_key('font'):
                fontSizeThreshold = 1
                difference = self.__fontsFace[self.__currentTextProperties['font']] - self.__abstractTextProperties['medium_font-size']
                if re.search('\.[\s]*$', self.__abstract) and difference > fontSizeThreshold:
                    return True
                elif difference > 2 * fontSizeThreshold:
                    return True

            if re.search('\.[\s]*$', self.__abstract) and re.search('^[\s]*Key[\s]*word|Introduction|^[\s]*Index[\s]+terms', text, re.IGNORECASE):
                return True
            elif re.search('^Introduction|^ntroduction', text, re.IGNORECASE):
                return True
            
            return False
            
        def __calcAverageTextProperties(currentText, averageTextProperties):
            """It uses EWMA filtering for calculating the font size of the abstract section.
            This is cause because in certain papers the abstract text doesn't have the same
            font face name, although their size are so close.
            
            This information about the medium value will be used by the algorithm which
            (try) to locate the end of the abstract section, i.e. when a text with a font face
            larger than a specified threshold from the medium value will be encountered."""
            if self.__currentTextProperties.has_key('font'):
                if not averageTextProperties.has_key('medium_font-size'):
                    averageTextProperties['medium_font-size'] = self.__fontsFace[self.__currentTextProperties['font']]

                alpha = 0.80
                temp_value = 0
                h = float(len(currentText)/10)
                if h > 0:
                    alpha_h = math.pow(alpha, h)
                    temp_value = float(alpha_h * averageTextProperties['medium_font-size'])
                    alpha_sum = float(1 - math.pow(alpha,h))
                    new_value = temp_value + alpha_sum * self.__fontsFace[self.__currentTextProperties['font']]
                    return new_value
            else:
                pass
            
        def __getFutureState(text):
            if self.__currentRetrievalStage == 'IDLE':
                """Current state of the FSM is IDLE
                """
                if self.__current_page == 0:
                    self.debug('__getFutureState', 'IDLE -> IDLE (current page = 0)')
                    return 'IDLE'
                else:
                    if __canBeTheAbstract(text) and len(self.__abstract)==0:
                        self.debug('__getFutureState' , 'IDLE -> ABSTRACT (can be the abstract)')
                        return 'ABSTRACT'
                    elif __canBeTheReferences(text) and len(self.__rawReferences)==0:
                        self.__breakLine = ''
                        self.debug('__getFutureState' , 'IDLE -> REFERENCES')
                        return 'REFERENCES'
                    elif __canBeATitleLine(text) and len(self.__title)==0:
                        self.debug('__getFutureState' , 'IDLE -> TITLE')
                        return 'TITLE'
                
                
                return 'IDLE'
                
            elif self.__currentRetrievalStage == 'TITLE':
                """Current state of the FSM is TITLE
                """
                if self.__current_page<3:
                    if __canBeTheAbstract(text):
                        return 'ABSTRACT'
                    elif __canBeAnAuthorLine(text):
                        return 'AUTHORS'
                    elif __canConsiderTitleCompleted(text):
                        return 'AUTHORS'
                    else:
                        return 'TITLE'
                     
                return 'IDLE'
            
            elif self.__currentRetrievalStage == 'AUTHORS':
                """Current state of the FSM is AUTHORS
                """
                if self.__current_page<3:
                    if __canBeTheAbstract(text):
                        return 'ABSTRACT'
                    if __checkTopPositionForAuthorLine():
                        return 'AUTHORS'
                    else:
                        return 'WAIT_FOR_ABSTRACT'

                return 'IDLE'
            
            elif self.__currentRetrievalStage == 'WAIT_FOR_ABSTRACT':
                if self.__current_page<4: #3
                    if __canBeTheAbstract(text):
                        return 'ABSTRACT'
                    else:
                        return 'WAIT_FOR_ABSTRACT'

                return 'IDLE'

            elif self.__currentRetrievalStage == 'ABSTRACT':
                """Current state of the FSM is ABSTRACT
                """
                if __canStopAbstract(text):
                    self.debug('__getFutureState' , 'ABSTRACT -> IDLE')
                    return 'IDLE'
                else:
                    self.debug('__getFutureState' , 'ABSTRACT -> ABSTRACT')
                    return 'ABSTRACT'
                    
                return 'IDLE'
                
            elif self.__currentRetrievalStage == 'REFERENCES':
                """Current state of the FSM is REFERENCES
                """
                self.debug('__getFutureState' , 'REFERENCES -> REFERENCES')
                
                if __canStopTheReferences(text):
                    return 'IDLE'
                else:
                    return 'REFERENCES'
            else:
                pass
        
        def __takeAction(text):
            
            def __removeHypensAndNormalizeWhiteSpaces(stackText, rawText, removeLineBreak=True):
                
                """Remove hyphens and normalize white spaces"""
                if len(self.__breakLine)>0 and removeLineBreak:
                    if re.search('\.[\s]*$', stackText):
                        rawText = "\n%s" % rawText
                    else:
                        rawText = " %s" % rawText
                    self.__breakLine = ''
                
                if re.search('[a-z]+-[\s]*$', stackText):
                    if re.search('^[\s]+', rawText):
                        rawText = re.sub('^[\s]+', '', rawText)

                    stackText = re.sub('-[\s]*$', '', stackText) + rawText
                    stackText = re.sub('[\s]+$', '', stackText)
                elif re.search('\n$', self.__abstract):
                    stackText = re.sub('\n$', ' ', stackText) + rawText
                else:
                    stackText += " %s" % rawText
                    
                return stackText
            
            if self.__currentRetrievalStage == 'TITLE':
                if __canBeATitleLine(text):
                    self.__title += " %s" % text
                    if not self.__titleTextProperties.has_key('font'):
                        self.__titleTextProperties['font'] = self.__currentTextProperties['font']
                        self.__titleTextProperties['top'] = self.__currentTextProperties['top']
                else:
                    pass
            elif self.__currentRetrievalStage == 'AUTHORS':
                authors = self.filterAuthors(text)
                if authors:
                    for item in authors:
                        if item not in self.__authors:
                            self.__authors.append(item)

            elif self.__currentRetrievalStage == 'ABSTRACT':
                self.__abstract = __removeHypensAndNormalizeWhiteSpaces(self.__abstract, text)
                mediumFontSize = __calcAverageTextProperties(text, self.__abstractTextProperties)
                if mediumFontSize:
                    self.__abstractTextProperties['medium_font-size'] = mediumFontSize

            elif self.__currentRetrievalStage == 'REFERENCES':
                """Current retrieval stage is REFERENCES
                """
                self.__rawReferences = __removeHypensAndNormalizeWhiteSpaces(self.__rawReferences, text, True)#False
            else:
                self.__bodyText = __removeHypensAndNormalizeWhiteSpaces(self.__bodyText, text) 
            
        if self.__currentTextProperties.has_key('font') and self.__current_page>0:
            mediumFontSize = __calcAverageTextProperties(text, self.__currentTextProperties)
            if mediumFontSize:
                self.__currentTextProperties['medium_font-size'] = mediumFontSize 
            self.__currentRetrievalStage = __getFutureState(text)
            __takeAction(text)

    def handle_comment(self, text):
        if re.search('\.ft[0-9]+', text):
            stili = re.split('}', text)
            for entry in stili:
                res1 = re.search('.ft[0-9]+', entry)
                res2 = re.search('{font-size:', entry)
                res3 = re.search('px;', entry)
                if (res1 and res2 and res3):
                    self.__fontsFace[entry[res1.span()[0]+1:res1.span()[1]]] = int(entry[res2.span()[1]:res3.span()[0]])
                    
            self.__top3LargestFonts = [font[0] for font in heapq.nlargest(3, self.__fontsFace.iteritems(), heapq.itemgetter(1))]

        elif re.search('Page[\s]+[0-9]+', text):
            res1 = re.search('Page[\s]+[0-9]+', text).span()
            res2 = re.search('Page[\s]+', text).span()
            pagenum = text[res2[1]:res1[1]]
            self.__current_page = int(pagenum)

if __name__ == '__main__':
    
    pdfFileURN = '../demodata/tribler.pdf'
    
    parser = PDFPaperParserHtml()
    parser.feed(pdfFileURN)
    
    print parser.title
    print parser.authors
    print parser.abstract
    print parser.bibliography