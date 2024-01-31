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
import re


class LemmaFilter(Filter):
    """
    This class implements a lemmatization filter: it normalize each token
    to a well-defined reference thesaurus - aka WordNet
    It follows the Whoosh fashion of defining preprocessing stages as filters.
    """

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
        tokens = [t.copy() for t in tokens]    # Consumes the whole generator
        tokens_text = [t.text for t in tokens]
        tags = list(zip(*nltk.pos_tag(tokens_text)))

        if tags:
            tags_wn = map(self.to_wordnet_pos, tags[1])
        
            for token, tag in zip(tokens, tags_wn):
                if not token.stopped:
                    token.text = self.__lemmatizerFn(token.text, tag)
                yield token


class RemoveBreakFilter(Filter):
    def __call__(self, tokens):
        for t in tokens:
            if not re.match("br", t.text):            
                yield t


ANALYZER_NAIVE = RegexTokenizer() | RemoveBreakFilter() | LowercaseFilter() | StopFilter()
ANALYZER_STEMMER = RegexTokenizer() | RemoveBreakFilter() | LowercaseFilter() | StopFilter() | StemFilter()
ANALYZER_LEMMATIZER = RegexTokenizer() | RemoveBreakFilter() | LowercaseFilter() | LemmaFilter() | StopFilter()


def get_default_analyzer() -> Analyzer:
  """
  Factory function to return the default corpus analyzer for the project.
  To edit the default for the entire project, change the returned object below by selecting
  another one (for example ANALYZER_NAIVE), or specify your own.

  This function is used by :py:`~placerank.views.DocumentLogicView` when defining schema
  for the inverted index.
  """

  return ANALYZER_NAIVE

def setup():
    nltk.download("wordnet")
    nltk.download('averaged_perceptron_tagger')

def main():
    setup()
    
    analyzer = get_default_analyzer()
    preproc = lambda s: print(*[t.text for t in analyzer(s)], sep='\n')
    preproc(u"This is an amazing Whoosh experience, I'm loving it")

if __name__ == "__main__":
    main()
