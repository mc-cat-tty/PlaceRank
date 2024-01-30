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
from whoosh.scoring import WeightingModel
from whoosh.index import Index
from whoosh.scoring import BM25F
from whoosh import qparser
from typing import List, Type

from placerank.views import ResultView, QueryView
from placerank.query_expansion import QueryExpansionService

class IRModel(ABC):
    def __init__(
        self,
        spell_corrector: Type[SpellCorrectionService],
        query_expander: QueryExpansionService,
        index: Index,
        weighting_model: WeightingModel = BM25F,
    ):
        self.spell_corrector = spell_corrector(self)
        self.query_expander = query_expander
        self.index = index
        self.weighting_model = weighting_model

    def get_query_parser(self, query: QueryView) -> qparser.QueryParser:
        return qparser.MultifieldParser([i.name.lower() for i in query.search_fields], self.index.schema)
    
    def search(self, query: QueryView) -> List[ResultView]:
        parser = self.get_query_parser(query)
        query = parser.parse(query.textual_query)
        with self.index.searcher(weighting = self.weighting_model) as s:
            hits = [ResultView(**hit) for hit in s.search(query)]

        return hits

class SpellCorrectionService(ABC):
    def __init__(self, ir_model: IRModel):
        self._ir_model = ir_model

    @abstractmethod
    def correct(self, query: str) -> str:
        ...

class NoSpellCorrection(SpellCorrectionService):
    def correct(self, query: str) -> str:
        return query

class WhooshSpellCorrection(SpellCorrectionService):
    def correct(self, query: QueryView) -> str:
        parser = self._ir_model.get_query_parser(query)
        parsed_query = parser.parse(query.textual_query)
        
        with self._ir_model.index.searcher() as s:
            corrected_query = s.correct_query(parsed_query, query.textual_query)

        return corrected_query.string