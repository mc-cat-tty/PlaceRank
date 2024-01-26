"""
Module to test performance of an index against predefined queries.
"""

import json


class BenchmarkQuery:
    """
    Representation of a benchmark query. Provides access to the UIN, textual query,
    relevant set, required sentiments and room type as fields.
    """

    def __init__(self, row_dict):
        self.__dict__.update(**row_dict)

    def __repr__(self):
        return f"<BenchmarkQuery {self.uin}, {self.query}, {self.room_type}, {self.relevant}, {self.sentiments}"


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

    def __init__(self, bm_dataset_path: str = "validation"):
        """
        Creates a Benchmark object that hold the benchmark dataset,
        i.e. a collection of queries and expected relevant documents.

        :bm_dataset_path: path of the benchmark dataset directory
        """

        pass


def main():
    """
    Test program for benchmark loading.
    """

    with open("validation/benchmark.json") as fp:
        dset = BenchmarkDataset(fp)

    print(dset.queries)

if __name__ == "__main__":
    main()