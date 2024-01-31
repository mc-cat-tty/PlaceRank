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
from placerank.views import ResultView, QueryView, ReviewsIndex
from abc import ABC, abstractmethod
from whoosh.analysis.analyzers import CompositeAnalyzer
from whoosh.scoring import WeightingModel
from whoosh.searching import Results
from whoosh.index import Index
from typing import List
from whoosh.qparser import QueryParser
import math
from operator import itemgetter


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


class QueryExpansionMock(QueryExpansionService):
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
            return [ResultView(**dict(hit) | {"score": hit.score}) for hit in s.search(query)]
        
class SentimentRanker:
    def __init__(self):
        self.__reviews_index = ReviewsIndex()

    @staticmethod
    def __cosine_similarity(doc: dict, query: dict):
        """
        Cosine similarity
        """
        
        d_norm = math.sqrt(sum(v for v in doc.values()))
        q_norm = math.sqrt(sum(v for v in query.values()))

        num = sum(doc[k]*query[k] for k in (doc.keys() & query.keys()))

        return num / (d_norm * q_norm)
    
    def __score(self, doc, sentiment):
        return SentimentRanker.__cosine_similarity(self.__get_sentiment_for(doc), sentiment) * doc.score
    
    def __get_sentiment_for(self, doc):
        return self.__reviews_index.get_sentiment_for(int(doc.id))

    def rank(self, docs: List[ResultView], sentiment) -> List[ResultView]:
        sim_docs = map(lambda d: (d, self.__score(d, sentiment)), docs)
        return list(map(itemgetter(0), sorted(sim_docs, key=itemgetter(1), reverse=True) ) )
    

if __name__ == "__main__":
    results = [ResultView(470330, 0, 0, 0.2), ResultView(267652, 0, 0, 0.9), ResultView(321014, 0, 0, 0.11)]
    sentiment = {'optimism': 1, 'approval': 1}

    a = SentimentRanker()
    ranked = a.rank(results, sentiment)
    for r in ranked:
        print(r.id)