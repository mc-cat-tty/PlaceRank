"""
Cooked models ready to ship
"""

from whoosh.index import Index, open_dir
from whoosh.query import *
from whoosh.qparser import QueryParser, syntax
from whoosh.qparser.plugins import MultifieldPlugin
from typing import Type, Tuple, List

from placerank.views import *
from placerank.ir_model import *
from placerank.query_expansion import *
from placerank.sentiment import *
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



def main():
    idx = open_dir(INDEX_DIR)
    sentiment_model = UnionIRModel(NoSpellCorrection, NoQueryExpansion(), idx, AdvancedSentimentWeightingModel(REVIEWS_INDEX))
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