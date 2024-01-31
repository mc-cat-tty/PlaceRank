"""
Cooked models ready to ship
"""

from whoosh.scoring import WeightingModel, BM25F
from whoosh.index import Index, open_dir
from whoosh.query import *
from typing import Type, Tuple, List

from placerank.views import ResultView, QueryView, ReviewsIndex, SearchFields
from placerank.ir_model import IRModel, NoSpellCorrection, SentimentRanker, SpellCorrectionService, WhooshSpellCorrection
from placerank.query_expansion import NoQueryExpansion, QueryExpansionService, ThesaurusQueryExpansion
from placerank.config import HF_CACHE, INDEX_DIR, REVIEWS_INDEX

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

class UnionIRModel(IRModel):
    def get_query_parser(self, query: QueryView):
        return Or([Term(f.name.lower(), ) for f in query.search_fields for w in query.textual_query.split()])

def main():
    idx = open_dir(INDEX_DIR)
    sentiment_model = SentimentAwareIRModel(NoSpellCorrection, NoQueryExpansion(), idx, SentimentRanker(REVIEWS_INDEX))
    sentiment_res = sentiment_model.search(
        QueryView(
            textual_query = u'apartment in manhattan',  # Stopwords like 'in' are removed
            sentiment_tags = 'joy',
            search_fields = SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
        )
    )[1]

    qe_model = IRModel(NoSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx)
    qe_model.set_autoexpansion(True)
    qe_res = qe_model.search(
        QueryView(
            textual_query = u'apartment in manhattan',
            search_fields = SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
        ),
    )[1]

    print(f"{sentiment_res=} {qe_res=}")

if __name__ == "__main__":
    main()