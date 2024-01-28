"""
Module to test performance of an index against predefined queries.
"""

from placerank.search import index_search
from whoosh.index import open_dir
import json

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

    def __repr__(self):
        return f"<BenchmarkQuery {self.uin}, {self.text}, {self.room_type}, {self.relevant}, {self.sentiments}"


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


    def test_against(self, ix):
        """
        Tests the benchmark against a given index.
        This is the first call needed to compute different measures.
        """
        
        # Produce a list of (query, retrieve_results)
        self.__results = [
            (q, index_search(ix, q.text)) for q in self.__dset.queries
        ]

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
        get_precisions = lambda x: [p for p, _ in zip(*x)]

        return mean(get_precisions(self._compute_p_at_recall(relevant, answer)))
    
    def average_precision(self):
        return [
            (q, self._compute_average_precision(q.relevant, ans)) for q, ans in self.__results
        ]
    
    def mean_average_precision(self):
        return mean([p for q, p in self.average_precision()])


def main():
    """
    Test program for benchmark loading.
    """

    bench = Benchmark()
    ix = open_dir("index/benchmark")

    bench.test_against(ix)
    
    for (query, results), (_q, precision), (__q, recall) in zip(bench.results, bench.precision(), bench.recall()):
        print(f"{query.text} {results} p:{precision} r:{recall}")

    print(bench.precision_at_r())
    print(bench.precision_at_recall_levels())
    #print(bench.average_precision())

if __name__ == "__main__":
    main()