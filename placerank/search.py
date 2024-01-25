"""
This module implements different strategies of search for a given index.
"""

from whoosh.searching import Results
from whoosh.qparser import MultifieldParser
from whoosh.scoring import TF_IDF, BM25F
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


def vector_tfidf_search(ix, query: str) -> set[int]:
    """
    Score using TF-IDF.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher(weighting=TF_IDF) as searcher:
        res = searcher.search(q)
        return res.docs()
    

def vector_bm25_search(ix, query: str) -> set[int]:
    """
    Score using BM25.
    """

    parser = MultifieldParser(fieldnames=ix.schema.logicview.keys(), schema=ix.schema)
    q = parser.parse(query)

    with ix.searcher(weighting=BM25F) as searcher:
        res = searcher.search(q)
        return res.docs()


def main():
    from whoosh.index import open_dir

    ix = open_dir("index/naive")
    print(*vector_tfidf_search(ix, "flat manhattan"))

if __name__ == "__main__":
    main()
