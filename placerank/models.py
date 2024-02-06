"""
Cooked models ready to ship
"""

from email.parser import Parser
import pydash
from whoosh.scoring import WeightingModel, BM25F
from whoosh.index import Index, open_dir
from whoosh.query import *
from whoosh.qparser import QueryParser, syntax
from whoosh.qparser.plugins import MultifieldPlugin
from typing import Type, Tuple, List

from placerank.views import ResultView, QueryView, ReviewsIndex, SearchFields
from placerank.ir_model import IRModel, NoSpellCorrection, SentimentRanker, SpellCorrectionService, WhooshSpellCorrection
from placerank.query_expansion import NoQueryExpansion, QueryExpansionService, ThesaurusQueryExpansion
from placerank.config import HF_CACHE, INDEX_DIR, REVIEWS_INDEX

class MultifieldUnionPlugin(MultifieldPlugin):
    def do_multifield(self, parser, group):
        ast = super().do_multifield(parser, group)
        lin_ast = [n for n in ast]
        return syntax.OrGroup(lin_ast)


class UnionIRModel(IRModel):
    def get_query_parser(self, query: QueryView) -> QueryParser:
        p = QueryParser(None, self.index.schema)
        mfp = MultifieldUnionPlugin([f.name.lower() for f in query.search_fields])
        p.add_plugin(mfp)
        return p


class SentimentAwareIRModel(UnionIRModel):
    def __init__(
        self,
        spell_corrector: Type[SpellCorrectionService],
        query_expander: QueryExpansionService,
        index: Index,
        sentiment_ranker: SentimentRanker,
        weighting_model: WeightingModel = BM25F
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
    sentiment_model = SentimentAwareIRModel(NoSpellCorrection, NoQueryExpansion(), idx, SentimentRanker(REVIEWS_INDEX))
    sentiment_res = sentiment_model.search(
        QueryView(
            textual_query = u'apartment in manhattan',  # Stopwords like 'in' are removed
            sentiment_tags = 'joy',
            search_fields = SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
        )
    )[1]

    union_model = UnionIRModel(NoSpellCorrection, NoQueryExpansion(), idx)
    union_model.set_autoexpansion(False)
    qe_res = union_model.search(
        QueryView(
            textual_query = u'cheap stay',
            search_fields = SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
        ),
    )[1]

    print(f"{sentiment_res=} {qe_res=}")

if __name__ == "__main__":
    main()