"""
Module to test performance of an index against predefined queries.
"""

from placerank.ir_model import *
from placerank.models import *
from placerank.config import *
from placerank.query_expansion import *
from whoosh.scoring import TF_IDF
from whoosh.index import open_dir
import json
from operator import itemgetter

def mean(l):
    if len(l) > 0:
        return sum(l) / len(l)
    return 0

class BenchmarkQuery:
    """
    Representation of a benchmark query. Provides access to the UIN, textual query,
    relevant set, required sentiments and room type as fields.
    """

    def __init__(self, row_dict):
        self.__dict__.update(**row_dict)

    def __str__(self):
        return f"<BenchmarkQuery {self.text}>"


class BenchmarkDataset:
    """
    Helper class to open and decode the benchmark dataset in JSON.
    A BenchmarkDataset is a list of BenchmarkQuery objects.
    """

    def __init__(self, fp):
        """
        :fp: file pointer to the dataset
        """

        self.queries = json.load(fp, object_hook=BenchmarkDataset.row_object_decoder)

    @staticmethod
    def row_object_decoder(dict_repr):
        """
        Decodes a benchmark query encoded as a JSON row into a BenchmarkQuery object.
        """

        if "uin" in dict_repr:
            return BenchmarkQuery(dict_repr)
        return dict_repr


class Benchmark:

    def __init__(self, bm_dataset_path: str = "validation/benchmark.json"):
        """
        Creates a Benchmark object that hold the benchmark dataset,
        i.e. a collection of queries and expected relevant documents.

        :bm_dataset_path: path of the benchmark dataset directory
        """

        with open(bm_dataset_path) as fp:
            self.__dset = BenchmarkDataset(fp)


    def test_against(self, ir_model):
        """
        Tests the benchmark against a given index.
        This is the first call needed to compute different measures.
        """
        
        # Produce a list of (query, retrieve_results)
        self.__results = [
            (q, ir_model.search(
                QueryView(
                    textual_query=q.text,
                    sentiment_tags=" ".join(q.sentiments),
                    search_fields=SearchFields.DESCRIPTION | SearchFields.NEIGHBORHOOD_OVERVIEW | SearchFields.NAME
                )
            )[0]) for q in self.__dset.queries
        ]

        self.__results = [(q, [int(a.id) for a in answer]) for q, answer in self.__results]

        self.results = self.__results
        #TODO: remove self.results. Now permits inspection of the object without debugger

    def _compute_set_recall(self, relevant, answer):
        """
        Returns the recall using set theory for a given answer and relevant list (or set)
        """
        return len(set(relevant) & set(answer)) / len(relevant)
    
    def _compute_set_precision(self, relevant, answer):
        """
        Returns the precision using set theory for a given answer and relevant list (or set)
        """
        if len(answer) > 0:
            return len(set(relevant) & set(answer)) / len(answer)
        
        return 0

    def recall(self):
        return [
            (q, self._compute_set_recall(q.relevant, ans)) for q, ans in self.__results
        ]
    
    def precision(self):
        return [
            (q, self._compute_set_precision(q.relevant, ans))
            for q, ans in self.__results
        ]
    
    def _compute_precision_at_r(self, relevant, answer):
        """
        Compute precision at ranking r for slices of increasing length of the ans list of answered documents.
        """
        ndocs = len(answer)

        return [(self._compute_set_precision(relevant, answer[:i]), self._compute_set_recall(relevant, answer)) for i in range(1, ndocs+1)]
    
    def precision_at_r(self):
        return [
            (q, [self._compute_precision_at_r(q.relevant, ans)]) for q, ans in self.__results
        ]
    
    def _compute_p_at_recall(self, relevant, answer):
        """
        Computes precision at different levels of recall for a given query.
        """

        p_at_r = self._compute_precision_at_r(relevant, answer)
        p_at_recall = p_at_r[:1]

        for prev, curr in zip(p_at_r, p_at_r[1:]):
            if prev[1] < curr[1]:   # if recall increases
                p_at_recall.append(curr)

        return p_at_recall
    
    def precision_at_recall_levels(self):
        return [
            (q, self._compute_p_at_recall(q.relevant, ans)) for q, ans in self.__results
        ]
    
    def _compute_average_precision(self, relevant, answer):
        """
        TODO: debug
        """
        get_precisions = lambda x: [p for p, _ in x]

        p_at_recall = self._compute_p_at_recall(relevant, answer)
        return mean(get_precisions(p_at_recall))
    
    def average_precision(self):
        return [
            (q, self._compute_average_precision(q.relevant, ans)) for q, ans in self.__results
        ]
    
    def mean_average_precision(self):
        return mean([p for q, p in self.average_precision()])
    
    def _harmonic_mean(self, p, r, p_weight=1, r_weight=1):
        if p > 0 and r > 0:
            return (p_weight + r_weight) / (p_weight/p + r_weight/r)
        else:
            return 0

    def f1(self):
        precisions = [p[1] for p in self.precision()]
        recalls = [r[1] for r in self.recall()]

        return [
            (q, self._harmonic_mean(p, r))
            for q, p, r in zip(self.__results, precisions, recalls)
        ]
    
    def e(self, b=1.5):
        precisions = [p[1] for p in self.precision()]
        recalls = [r[1] for r in self.recall()]

        return [
            (q, 1 - self._harmonic_mean(p, r, 1, b**2))
            for q, p, r in zip(self.__results, precisions, recalls)
        ]
    
    def mean_f1(self):
        return mean([f1 for q, f1 in self.f1()])

    def test_and_print(bench, model):
        bench.test_against(model)
        for (query, results), (_q, precision), (__q, recall) in zip(bench.__results, bench.precision(), bench.recall()):
            print(f"\t{query.text} {len(results)} results p:{precision} r:{recall}")

        print(*[f"\tF1 {q[0].text}: {score}" for q, score in bench.f1()], sep="\n")
        print(f"\tF1 Mean: {bench.mean_f1()}")
        print(f"\tMAP: {bench.mean_average_precision()}")
        print()


def main():
    """
    Test program for benchmark loading.
    """

    bench = Benchmark()

    idx = open_dir(INDEX_DIR)
    base_model = IRModel(NoSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx)

    print("Model 1 - Base model (terms in AND)")
    bench.test_and_print(base_model)


    print("Model 2 - With query expansion")
    base_model.set_autoexpansion(True)
    bench.test_and_print(base_model)


    print("Model 3 - OR terms model (overcoming of whoosh scoring)")
    or_terms_model = UnionIRModel(NoSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx, TF_IDF)
    bench.test_and_print(or_terms_model)


    print("Model 4 - OR terms model with query expansion")
    or_terms_model.set_autoexpansion(True)
    bench.test_and_print(or_terms_model)


    print("Model 5 - OR terms model with LLM query expansion")
    llm_expanded = UnionIRModel(NoSpellCorrection, LLMQueryExpansion(HF_CACHE), idx, TF_IDF)
    llm_expanded.set_autoexpansion(True)
    bench.test_and_print(llm_expanded)


    print("Model 6 - OR terms model with BM25F")
    or_terms_model = UnionIRModel(NoSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx)
    bench.test_and_print(or_terms_model)


    print("Model 7 - OR terms model with BM25F and query expansion")
    or_terms_model.set_autoexpansion(True)
    bench.test_and_print(or_terms_model)


    print("Model 8 - OR terms model with BM25F and LLM query expansion")
    llm_expanded = UnionIRModel(NoSpellCorrection, LLMQueryExpansion(HF_CACHE), idx)
    llm_expanded.set_autoexpansion(True)
    bench.test_and_print(llm_expanded)


    print("Model 9 - Sentiment Analysis")
    sentiment_model = SentimentAwareIRModel(NoSpellCorrection, NoQueryExpansion(), idx, SentimentRanker(REVIEWS_INDEX))
    bench.test_against(sentiment_model)
    bench.test_and_print(sentiment_model)


    print("Model 10 - Sentiment Analysis with wordnet query expansion")
    sentiment_model = SentimentAwareIRModel(NoSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx, SentimentRanker(REVIEWS_INDEX))
    sentiment_model.set_autoexpansion(True)
    bench.test_and_print(sentiment_model)


if __name__ == "__main__":
    main()