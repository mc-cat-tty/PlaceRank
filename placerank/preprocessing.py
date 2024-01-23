"""
This file is a kind of configuration file, where preprocessing strategies are
defined and one of them can be chosen for the entire project as a default.
"""

import nltk
import copy
from nltk.corpus import wordnet
from whoosh.analysis import *
from typing import Generator
from operator import attrgetter

class LemmaFilter(Filter):
    def __init__(self):
        self.__lemmatizerFn = nltk.WordNetLemmatizer().lemmatize
    
    @staticmethod
    def to_wordnet_pos(tag: str):
        """
        Make treebank POS tags compliant with WordNet POS tags.
        """
        if tag.startswith('J'):
            return wordnet.ADJ
        elif tag.startswith('V'):
            return wordnet.VERB
        elif tag.startswith('N'):
            return wordnet.NOUN
        elif tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN
    
    def __call__(self, tokens: Generator[Token, None, None]) -> Generator[Token, None, None]:
        tokens = list(map(copy.copy, tokens))  # Inefficiently consumes the whole generator to have an integral view over the text field
        tokens_text = list(map(attrgetter("text"), tokens))
        tags = list(zip(*nltk.pos_tag(tokens_text)))[1]
        tags_wn = map(self.to_wordnet_pos, tags)
        
        for token, tag in zip(tokens, tags_wn):
            if not token.stopped:
                token.text = self.__lemmatizerFn(token.text, tag)
            yield token

ANALYZER_NAIVE = RegexTokenizer() | LowercaseFilter() | StopFilter()
ANALYZER_STEMMER = RegexTokenizer() | LowercaseFilter() | StopFilter() | StemFilter()
ANALYZER_LEMMATIZER = RegexTokenizer() | LowercaseFilter() | (LemmaFilter() | StopFilter())

def getDefaultAnalyzer() -> Analyzer:
  return ANALYZER_LEMMATIZER

if __name__ == "__main__":
    nltk.download("wordnet")
    nltk.download('averaged_perceptron_tagger')

    analyzer = getDefaultAnalyzer()
    preproc = lambda s: print(*[t.text for t in analyzer(s)], sep='\n')
    preproc(u"I was walking, while a programmer was programming a program") # test passed
