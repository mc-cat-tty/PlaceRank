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
ANALYZER_LEMMATIZER = RegexTokenizer() | LowercaseFilter() | LemmaFilter() | StopFilter()


def getDefaultAnalyzer() -> Analyzer:
  """
  Factory function to return the default corpus analyzer for the project.
  To edit the default for the entire project, change the returned object below by selecting
  another one (for example ANALYZER_NAIVE), or specify your own.

  This function is used by :py:`~placerank.logic_views.DocumentLogicView` when defining schema
  for the inverted index.
  """

  return ANALYZER_LEMMATIZER


def main():
    nltk.download("wordnet")
    nltk.download('averaged_perceptron_tagger')

    analyzer = getDefaultAnalyzer()
    preproc = lambda s: print(*[t.text for t in analyzer(s)], sep='\n')
    preproc(u"This is an amazing Whoosh experience, I'm loving it")

if __name__ == "__main__":
    main()
