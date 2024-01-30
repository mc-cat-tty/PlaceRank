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
from dataclasses import dataclass
from operator import index
from placerank.views import ResultView, QueryView
from abc import ABC, abstractmethod
from whoosh.analysis.analyzers import CompositeAnalyzer
from whoosh.scoring import WeightingModel
from whoosh.searching import Results
from whoosh.index import Index
from typing import List
from whoosh.qparser import QueryParser


class IRModel(ABC):
    def __init__(
        self,
        query_expansion_service: QueryExpansionService,
        preprocessing_pipeline: CompositeAnalyzer,
        retrieval_model: RetrievalModel
    ):
        self._tolerant_retrieval_service = query_expansion_service
        self._preprocessing_pipeline = preprocessing_pipeline
        self._retrieval_model = retrieval_model

    
    @abstractmethod
    def search(self, query: QueryView) -> List[ResultView]:
        ...

class IRModelDumb(IRModel):
    def search(self, query):
        return self._retrieval_model.search(query)

class QueryExpansionService(ABC):
    """
    A service that implements a query expansion service.
    Exposes the `expand` method.
    """

    @abstractmethod
    def expand(query: str) -> str:
        ...


class NoQueryExpansionService(QueryExpansionService):
    """
    A mock object that does nothing on the query
    """
    def expand(query: str) -> str:
        return query


class RetrievalModel(ABC):
    def __init__(self, index: Index, weighting_model: WeightingModel):
        self._index = index
        self._weighting_model = weighting_model

    @abstractmethod
    def search(self, query: str) -> Results:
        ...

class RetrievalModelDumb(RetrievalModel):
    def search(self, query: QueryView) -> List[ResultView]:
        parser = QueryParser("neighborhood_overview", self._index.schema)
        query = parser.parse(query.textual_query)
        with self._index.searcher() as s:
            return [ResultView(**hit) for hit in s.search(query)]