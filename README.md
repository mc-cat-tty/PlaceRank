# PlaceRank

Search engine for AirBnB listings.

Final assignment of the "Gestione dell'informazione" course at University of Modena and Reggio Emilia. Academic year 2023-2024.

## Bringup
In order to enjoy our not-so-SOTA search engine, the average user needs to run the following command in a shell where the Python interpreter is available:
```bash
# INSTALL DEPENDENCIES
python3 -m pip install -r requirements.txt

# DOWNLOAD DATASET, CREATE INDEX, DOWNLOAD WORDNET AND BERT MODEL
python3 -m setup
```

Please, be aware that `bert-large-uncased-whole-word-masking` can take up to 1.5 Gb of disk space and 30 min to download.

For experienced user, we suggest to firstly crate a virtual environment, where all packages will be installed; then follow the above procedure:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Usage
### TUI
```bash
python3 -m placerank
```

### Benchmarks

The Benchmark module is designed to test the performance of an index against predefined queries. It includes functionality to load a benchmark dataset, test an index against the queries, and compute various evaluation metrics such as recall, precision, precision at ranking r, average precision, mean average precision, F1 score, and the E-measure.

To use the Benchmark module, follow these steps:

Create a Benchmark object:

```python
bench = Benchmark()
```

Open the index:

```python
ix = open_dir("index/benchmark")
```

Test the benchmark against the index. This is required to compute different metrics on the benchmark.

```python
bench.test_against(ix)
```

Print or use the computed metrics by using the object methods:

```python
print(bench.precision())
print(bench.recall())
print(bench.precision_at_r())
print(bench.precision_at_recall_levels())
print(bench.average_precision())
print(bench.mean_average_precision())
print(bench.f1())
print(bench.e())
```

Calling the module `placerank.benchmark` from the command line computes all of the metrics above for the "index/benchmark" index, which is an inverted index built on InsideAirbnb Cambridge listings.

### Reviews

The reviews dataset is used to compute the sentiment metric for each listing. Recent reviews have a major weight on the score than older ones.

To compute sentiment for each review, use the function `build_reviews_index` of `placerank.dataset` to build the dataset of reviews.
The function initializes a defaultdict where keys are listing IDs, and values are lists of tuples containing review information.

The dataset will be saved in a `reviews.pickle` file, to load it call the function `load_reviews_index`.

## Contributors
 - Corradini Giulio
 - Mecatti Francesco
 - Stano Antonio
