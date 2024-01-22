"""
This file is a kind of configuration file, where preprocessing strategies are
defined and one of them can be chosen for the entire project as a default.
"""

from whoosh.analysis import *
from typing import Generator
import nltk

class LemmaFilter(Filter):
    def __init__(self):
        self.__lemmatizerFn = nltk.WordNetLemmatizer().lemmatize
    
    def __call__(self, tokens: list[Token]) -> Generator[Token, None, None]:
        tags = nltk.pos_tag([t.text for t in tokens])
        
        for token, tag in zip(tokens, tags):
            if not token.stopped:
                token.text = self.__lemmatizerFn(token.text, tag)
            yield token

ANALYZER_NAIVE = RegexTokenizer() | LowercaseFilter() | StopFilter()
ANALYZER_STEMMER = RegexTokenizer() | LowercaseFilter() | StopFilter() | StemFilter()
ANALYZER_LEMMATIZER = RegexTokenizer() | LowercaseFilter() | LemmaFilter() | StopFilter()  # Not working, cause tokens is a generator

def getDefaultAnalyzer() -> Analyzer:
  return ANALYZER_LEMMATIZER

if __name__ == "__main__":
    nltk.download("wordnet")
    nltk.download('averaged_perceptron_tagger')

    analyzer = getDefaultAnalyzer()
    preproc = lambda s: print(*[t.text for t in analyzer(s)], sep='\n')
    preproc(u"This is an amazing Whoosh experience, I'm loving it")