#!/usr/bin/env python

import re

#SUBSTITUTE LIGATURES WITH SINGLE CHARS
def remove_strange_chars(text): 
    text = re.sub(u'ﬁ', 'fi', text)
    text = re.sub(u'ﬂ', 'fl', text)
    text = re.sub(u'ﬀ', 'ff', text)
    text = re.sub(u'ﬃ', 'ffi', text)
    return text