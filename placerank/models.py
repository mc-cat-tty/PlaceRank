"""
Cooked models ready to ship
"""

from placerank.ir_model import IRModel, SentimentRanker, SpellCorrectionService
from placerank.query_expansion import QueryExpansionService
from whoosh.scoring import WeightingModel, BM25F
from whoosh.index import Index
from placerank.views import ResultView, QueryView, ReviewsIndex
from typing import Type, Tuple, List

class SentimentAwareIRModel(IRModel):
    def __init__(
        self,
        spell_corrector: Type[SpellCorrectionService],
        query_expander: QueryExpansionService,
        index: Index,
        weighting_model: WeightingModel = BM25F,
        sentiment_ranker = SentimentRanker
    ):
        super().__init__(spell_corrector, query_expander, index, weighting_model)
        self.sentiment = sentiment_ranker()

    def search(self, query: QueryView, **kwargs) -> Tuple[List[ResultView], int]:
        sentiment = {k: 1 for k in query.sentiment_tags.split(" ")}
        docs, dlen = super().search(query, **kwargs)
        sent_ranked_docs = self.sentiment_ranker.rank(docs, sentiment)

        return (sent_ranked_docs, dlen)