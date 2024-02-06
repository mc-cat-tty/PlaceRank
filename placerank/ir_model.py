"""
This module contains the definition of a `IRModel`, aka a search engine stack:
    - preprocessing
        - lexer
        - [parser]
        - stopwords filtering
        - [stemming | lemmatization]
        - [Q-gram generation]
    - [query expansion | lexical substitution | soundex]
    - [tolerant] retrieval
        - model. Eg.:
            - BIM
            - BM25
            - vector space model
            - W2V
        - weighting strategy. Eg.:
            - binary
            - TF-IDF
    - [ranking]
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import math
import pydash
from enum import auto
from operator import itemgetter
from whoosh.scoring import WeightingModel
from whoosh.index import Index
from whoosh.scoring import BM25F
from whoosh.query import Term
from whoosh import qparser
from typing import List, Tuple, Type

from placerank.views import ResultView, QueryView, ReviewsIndex
from placerank.query_expansion import QueryExpansionService
from placerank.sentiment import BaseSentimentWeightingModel
from placerank import config

class IRModel(ABC):
    def __init__(
        self,
        spell_corrector: Type[SpellCorrectionService],
        query_expander: QueryExpansionService,
        index: Index,
        weighting_model: WeightingModel = BM25F(),
        connector: str = 'AND'
    ):
        self.spell_corrector = spell_corrector(self)
        self.query_expander = query_expander
        self.index = index
        self.weighting_model = weighting_model
        self._autoexpansion = False
        self.connector = connector

    def get_query_parser(self, query: QueryView) -> qparser.QueryParser:
        return qparser.MultifieldParser([f.name.lower() for f in query.search_fields], self.index.schema)
    
    def set_autoexpansion(self, autoexpansion: bool):
        self._autoexpansion = autoexpansion

    def search(self, query: QueryView, **kwargs) -> Tuple(List[ResultView], int):
        if isinstance(self.weighting_model, BaseSentimentWeightingModel):
            self.weighting_model.set_user_sentiment(query.sentiment_tags)

        expanded_query = self.query_expander.expand(query.textual_query, connector = self.connector)

        parser = qparser.QueryParser('room_type', self.index.schema)
        room_type = parser.parse(query.room_type) if query.room_type else None

        parser = self.get_query_parser(query)
        query = parser.parse(expanded_query if self._autoexpansion else query.textual_query)

        with self.index.searcher(weighting = self.weighting_model) as s:
            hits = s.search(query, filter = room_type, **kwargs)
            tot = len(hits)
            results = [ResultView(**dict(hit) | {"score": hit.score}) for hit in hits]

        return (results, tot)


class SpellCorrectionService(ABC):
    def __init__(self, ir_model: IRModel):
        self._ir_model = ir_model

    @abstractmethod
    def correct(self, query: QueryView) -> str:
        ...

class NoSpellCorrection(SpellCorrectionService):
    def correct(self, query: QueryView) -> str:
        return query.textual_query

class WhooshSpellCorrection(SpellCorrectionService):
    def correct(self, query: QueryView) -> str:
        parser = self._ir_model.get_query_parser(query)
        parsed_query = parser.parse(query.textual_query)
        
        with self._ir_model.index.searcher() as s:
            corrected_query = s.correct_query(parsed_query, query.textual_query)

        return corrected_query.string
        

# if __name__ == "__main__":
#     results = [ResultView(470330, 0, 0, 0.2), ResultView(267652, 0, 0, 0.9), ResultView(321014, 0, 0, 0.11)]
#     sentiment = {'optimism': 1, 'approval': 1}

#     a = SentimentRanker(config.REVIEWS_INDEX)
#     ranked = a.rank(results, sentiment)
#     for r in ranked:
#         print(r.id)