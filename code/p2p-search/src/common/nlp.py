#!/usr/bin/env python

import re
import porterStemmer

def filter_punctuation_from_words___DEPRECATED(list_of_words):
    """Remove punctuation from words.
       
       Given a list of words from a text, returns a list
       of words without any punctuation mark.
    """
    list_of_filtered_words = []
    for word in list_of_words:
        if re.search('\.$', word):
            filtered_word = re.sub('\.$', '', word)
        elif re.search('\,$', word):
            filtered_word = re.sub('\,$', '', word)
        elif re.search(';$', word):
            filtered_word = re.sub(';', '', word)
        elif re.search('\:$', word):
            filtered_word = re.sub('\:$', '', word)
        elif re.search('^\([a-z]*\)$', word):
            filtered_word = re.sub('^\(', '', word)
            filtered_word = re.sub('\)$', '', filtered_word)
        elif re.search('^\(', word):
            filtered_word = re.sub('^\(', '', word)
        elif re.search('\)$', word):
            filtered_word = re.sub('\)$', '', word)
        else:
            filtered_word = word
        list_of_filtered_words.append(filtered_word)
        #print "%s\t\t->\t%s" % (word, filtered_word)
    return list_of_filtered_words

def filterOutPunctuation(listOfWords):
    listOfCleanWords = []
    
    for word in listOfWords:
        if re.search('[a-z]{2,}', word, re.IGNORECASE):#filter out words with less than 2 alphabetic characters
            word = re.sub('\.', '', word)
            word = re.sub('\,', '', word)
            word = re.sub('\;', '', word)
            word = re.sub('\:', '', word)
            word = re.sub("\'", '', word)
            word = re.sub('\(', '', word)
            word = re.sub('\)', '', word)
            word = re.sub('"', '', word)
            word = re.sub('^-', '', word)
            word = re.sub('-$', '', word)
            word = re.sub('\?', '', word)
            word = re.sub('‘', '', word)
            word = re.sub('’', '', word)
            
            if len(word)>0:
                listOfCleanWords.append(word)

    return listOfCleanWords

def filter_punctuation_from_words(list_of_words):
    """Remove punctuation from words.
       
       Given a list of words from a text, returns a list
       of words without any punctuation mark.
    """
    list_of_filtered_words = []
    for word in list_of_words:
        if re.search('\.$', word):
            filtered_word = re.sub('\.$', '', word)
        elif re.search('\,$', word):
            filtered_word = re.sub('\,$', '', word)
        elif re.search(';$', word):
            filtered_word = re.sub(';', '', word)
        elif re.search('\:$', word):
            filtered_word = re.sub('\:$', '', word)
        elif re.search('^\([a-z]*\)$', word):
            filtered_word = re.sub('^\(', '', word)
            filtered_word = re.sub('\)$', '', filtered_word)
        elif re.search('^\(', word):
            filtered_word = re.sub('^\(', '', word)
        elif re.search('\)$', word):
            filtered_word = re.sub('\)$', '', word)
        else:
            filtered_word = word
        list_of_filtered_words.append(filtered_word)

    return list_of_filtered_words

def remove_hypens_from_words(list_of_words):

    list_of_filtered_words = []
    for word in list_of_words:
        if re.search('\-', word):
            list_of_filtered_words.extend( re.split('\-', word) )
        else:
            list_of_filtered_words.append(word)
            
    return list_of_filtered_words

def filter_stop_words(list_of_words_in_the_line):
    
    stop_words=[
            'am', 'ii', 'iii', 'per', 'po', 're', 'a', 'about', 'above', 'across',
            'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone',
            'along', 'already', 'also', 'although', 'always', 'am', 'among',
            'amongst', 'amoungst', 'amount', 'an', 'and', 'another', 'any',
            'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around',
            'as', 'at', 'back', 'be', 'became', 'because', 'become', 'becomes',
            'becoming', 'been', 'before', 'beforehand', 'behind', 'being',
            'below', 'beside', 'besides', 'between', 'beyond', 'bill', 'both',
            'bottom', 'but', 'by', 'can', 'cannot', 'cant', 'con', 'could',
            'couldnt', 'cry', 'describe', 'detail', 'do', 'done', 'down', 'due',
            'during', 'each', 'eg', 'eight', 'either', 'eleven', 'else',
            'elsewhere', 'empty', 'enough', 'even', 'ever', 'every', 'everyone',
            'everything', 'everywhere', 'except', 'few', 'fifteen', 'fifty',
            'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 'formerly',
            'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get',
            'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her',
            'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers',
            'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'i',
            'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it',
            'its', 'itself', 'keep', 'last', 'latter', 'latterly', 'least',
            'less', 'made', 'many', 'may', 'me', 'meanwhile', 'might', 'mill',
            'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much', 'must',
            'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless',
            'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not',
            'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
            'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our',
            'ours', 'ourselves', 'out', 'over', 'own', 'per', 'perhaps',
            'please', 'pre', 'put', 'rather', 're', 'same', 'see', 'seem',
            'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 'should',
            'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some',
            'somehow', 'someone', 'something', 'sometime', 'sometimes',
            'somewhere', 'still', 'such', 'take', 'ten', 'than', 'that', 'the',
            'their', 'them', 'themselves', 'then', 'thence', 'there',
            'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these',
            'they', 'thick', 'thin', 'third', 'this', 'those', 'though', 'three',
            'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too',
            'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under',
            'until', 'up', 'upon', 'us', 'very', 'via', 'was', 'we', 'well',
            'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where',
            'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon',
            'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever',
            'whole', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without',
            'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves',
            ]
    
    filtered_line = []
    for word in list_of_words_in_the_line:
        if word in stop_words:
            pass
        else:
             filtered_line.append(word)
             
    return filtered_line 

def filterWords_____DEPRECATED(textToIndex):
    """Before build the inverted index, the words from the raw text
    must be located and filtered (e.g. for remove punctuation)"""
    list_of_words_from_raw_text = re.split('\s', textToIndex)
    list_of_words = filter_punctuation_from_words(list_of_words_from_raw_text)
    
    """The words to be index are boiled down to lower case""" 
    list_of_words_to_index = [word.lower() for word in list_of_words]
    
    """Filter stop-words"""
    list_of_words_to_index = filter_stop_words(list_of_words_to_index)
    return list_of_words_to_index

def filterWords(textToIndex):
    """Before build the inverted index, the words from the raw text
    must be located and filtered (e.g. for remove punctuation)"""
    list_of_words_from_raw_text = re.split('\s', textToIndex)
    list_of_words = filter_punctuation_from_words(list_of_words_from_raw_text)
    
    """The words to be index are boiled down to lower case""" 
    list_of_words_to_index = [word.lower() for word in list_of_words]
    
    """Filter stop-words"""
    list_of_words_to_index = filter_stop_words(list_of_words_to_index)
    return list_of_words_to_index

def filterWords__V2(textToIndex):
    """Before build the inverted index, the words from the raw text
    must be located and filtered (e.g. for remove punctuation)"""
    listOfWordsToIndex = filterOutPunctuation([word.lower() for word in re.split('\s', textToIndex)])
    return filter_stop_words(listOfWordsToIndex)

def stemWords(listOfWords):
    ps = porterStemmer.PorterStemmer()
    listOfStemmedWords = [ps.stem(word, 0, len(word)-1) for word in listOfWords]
    return listOfStemmedWords
