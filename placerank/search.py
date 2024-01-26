"""
This module implements different strategies of search for a given index.
"""

from whoosh.searching import Results
from whoosh.qparser import MultifieldParser
from whoosh.scoring import TF_IDF, BM25F, FunctionWeighting, Frequency, WeightingModel, WeightScorer
from typing import Set


def boolean_search(ix, query: str) -> set[int]:
    """
    Performs a boolean search on the given index. Only sets that "crispy" match with the
    query are returned.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher() as searcher:
        res = searcher.search(q, scored=False, sortedby=None)
        return res.docs()


class Indicator(WeightingModel):
    def scorer(self, searcher, fieldname, text, qf=1):
        return WeightScorer(1)

def __binary_scoring(searcher, fieldname, text, matcher):
    frequency = Indicator().scorer(searcher, fieldname, text).score(matcher)
    return frequency 


def vector_boolean_search(ix, query: str) -> set[int]:
    """
    Performs a vector space search on the given index using cosine similarity with boolean
    scoring of terms.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher(weighting=FunctionWeighting(__binary_scoring)) as searcher:
        res = searcher.search(q)
        return [int(r.get("id")) for r in res]


def vector_tfidf_search(ix, query: str) -> set[int]:
    """
    Score using TF-IDF.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher(weighting=TF_IDF) as searcher:
        res = searcher.search(q)
        return [int(r.get("id")) for r in res]
    

def vector_bm25_search(ix, query: str) -> set[int]:
    """
    Score using BM25.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher(weighting=BM25F) as searcher:
        res = searcher.search(q)
        return [int(r.get("id")) for r in res]


def index_search(ix, query: str, strategy = None) -> list[int]:
    """
    Performs index search for a given query and returns an ordered list of document IDs.
    With no strategy, this performs a default TF-IDF scoring on retrieval.

    TODO: move to a ranked list of results, opposed to a set.
    """

    return vector_tfidf_search(ix, query)


def main():
    from whoosh.index import open_dir

    ix = open_dir("index/naive")
    print(*vector_boolean_search(ix, "manhattan"))

if __name__ == "__main__":
    main()
