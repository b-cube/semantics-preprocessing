import re
import HTMLParser
from lib.utils import flatten
import langid
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import WordListCorpusReader
from nltk.stem.wordnet import WordNetLemmatizer
from itertools import chain


_corpus_root = 'lib/corpus'


'''
nlp prep methods
'''


def normalize_subjects(subjects, do_split=False, return_unique=True):
    '''
    for some set of extracted keyword/tag/subject strings,
    normalize the strings to split on delimiters, handle some
    phrase definitions, clean up a bit of whitespace

    subjects is extracted from the service description generally
    '''
    if not subjects:
        return

    normalized_subjects = []
    for subject in subjects:
        if not subject:
            # skip any empty tag
            continue
        normalized = normalize_keyword_text(subject)
        normalized_subjects += [n.strip() for n in normalized.split(',')] \
            if do_split else [normalized]

    return list(set(normalized_subjects)) if return_unique else normalized_subjects


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

    # unescape
    hp = HTMLParser.HTMLParser()
    keyword_string = hp.unescape(keyword_string)

    # replace underscores (assume these are NOT delimiters
    #    but phrase concatenators)
    underscore_pattern = r'[_]'
    keyword_string = re.sub(underscore_pattern, ' ', keyword_string)

    punctuation_pattern = r'[;|>+:=+]'
    return re.sub(punctuation_pattern, ',', keyword_string)


def remove_punctuation(text):
    '''
    remove any punctuation from the text (for
        bag of words to be just words)
    '''
    simple_pattern = r'[;|>+:=.,()/?!]'
    return re.sub(simple_pattern, ' ', text)


def split_words(text):
    ''' '''
    simple_pattern = r'[/:.]'
    return re.split(simple_pattern, text)


def remove_stopwords(text):
    '''
    remove any known english stopwords from a
    piece of text (bag of words or otherwise)
    '''
    _stopwords = set(stopwords.words('english'))
    words = word_tokenize(text)
    return ' '.join([w for w in words if w not in _stopwords and w])


def remove_mimetypes(text):
    '''
    do this before something like tokenize or the
    resplit option will split the mimetypes to not
    be recognizable as such anymore
    '''
    mimetypes = WordListCorpusReader(_corpus_root, 'mimetypes.txt')
    words = [w.replace('+', '\+') for w in mimetypes.words()]

    pttn = re.compile('|'.join(words))
    return pttn.sub('', text)


def extract_mimetypes(text, do_replace=True):
    '''
    pull a list of mimetypes from some text feature

    return a list of mimetypes in the text block and
    the text, without mimetypes or unmodified
    '''
    mimetypes = WordListCorpusReader(_corpus_root, 'mimetypes.txt')

    found_mimetypes = [w for w in mimetypes.words() if w in text]

    if do_replace:
        text = remove_mimetypes(text)

    return found_mimetypes, text


def tokenize_text(text, resplit=True):
    '''
    tokenize to words
    if resplit, split words (we find things like
        Profiles/Sounders so maybe those should
        be separated)
    tag with parts of speech
    '''
    # TODO: note this might not always be the required step!
    # tokenize [(u'used', 'VBN'), (u'navigation', 'NN')]
    words = word_tokenize(text)
    words = list(
        chain.from_iterable(
            [split_words(w) for w in words]
        )
    ) if resplit else words
    return nltk.pos_tag(words)


def extract_by_pos(tokenized_text, parts_of_speech):
    '''
    sneetches on beaches...
    '''
    # pull out the parts of speech if subsetting else return the terms
    return [t[0] for t in tokenized_text if t[1] in parts_of_speech] \
        if parts_of_speech else [t[0] for t in tokenized_text]


def lemmatize_words(words):
    lem = WordNetLemmatizer()
    return [lem.lemmatize(w) for w in words]


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
