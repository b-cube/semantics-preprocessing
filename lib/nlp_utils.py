import re
import HTMLParser
from lib.utils import flatten
import langid

'''
nlp prep methods
'''


def normalize_keyword_text(keyword_string):
    '''
    this is the very basic regex-based normalization. we
    know that keywords are handled in a variety of ways even
    in standards that support multiple term elements. we also
    know that the nlp tokenizers, etc, won't parse strings
    correctly using certain delimiters (they are not standard
    punctuation in those ways).

    unescape any html bits (thanks gcmd!)

    delimiters: , ; > | + :
        (ignore space-delimited strings - let the tokenizers
            manage that)
        (we are also going to actually just ignore the commas as well)
    '''
    if not keyword_string:
        return

    hp = HTMLParser.HTMLParser()
    keyword_string = hp.unescape(keyword_string)

    simple_pattern = r'[;|>+:]'
    return re.sub(simple_pattern, ',', keyword_string)


def collapse_to_bag(data_blob, exclude_urls=True):
    '''
    for our * description dicts, create a basic
    text blob

    if exclude_urls: ignore endpoint urls
    '''
    _url_keys = ['url']
    excludes = _url_keys if exclude_urls else []

    # TODO: run the generator
    bag_of_words = flatten(data_blob, excludes)

    return ' '.join(bag_of_words)


def is_english(test_string):
    '''
    using langid.py, check if the detected lang is 'en'

    note: currently no clear bar for the confidence value
    returned, we are simply going with 'en' regardless
    and we are going to leave the stopwords in just to
    give the classifier more text to use
    '''
    language, confidence = langid.classify(test_string)
    return language == 'en'
