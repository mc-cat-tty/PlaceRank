"""
Cooked models ready to ship
"""

from whoosh.scoring import WeightingModel, BM25F
from whoosh.index import Index, open_dir
from typing import Type, Tuple, List

from placerank.views import ResultView, QueryView, ReviewsIndex, SearchFields
from placerank.ir_model import IRModel, NoSpellCorrection, SentimentRanker, SpellCorrectionService
from placerank.query_expansion import NoQueryExpansion, QueryExpansionService
from placerank.config import INDEX_DIR, REVIEWS_INDEX

class SentimentAwareIRModel(IRModel):
    def __init__(
        self,
        spell_corrector: Type[SpellCorrectionService],
        query_expander: QueryExpansionService,
        index: Index,
        sentiment_ranker: SentimentRanker,
        weighting_model: WeightingModel = BM25F,
    ):
        super().__init__(spell_corrector, query_expander, index, weighting_model)
        self.sentiment_ranker = sentiment_ranker

    def search(self, query: QueryView, **kwargs) -> Tuple[List[ResultView], int]:
        sentiment = {k: 1 for k in query.sentiment_tags.split(" ")}
        limit = kwargs.get('limit', None)
        kwargs['limit'] = None
        docs, dlen = super().search(query, **kwargs)
        sent_ranked_docs = self.sentiment_ranker.rank(docs, sentiment)[:limit]

        return (sent_ranked_docs, dlen)

def main():
    idx = open_dir(INDEX_DIR)
    model = SentimentAwareIRModel(NoSpellCorrection, NoQueryExpansion(), idx, SentimentRanker(REVIEWS_INDEX))
    print(
        model.search(QueryView(
            textual_query = u'apartment in manhattan',
            sentiment_tags = 'joy',
            search_fields = SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
        ))
    )

if __name__ == "__main__":
    main()