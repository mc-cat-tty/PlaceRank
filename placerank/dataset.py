from placerank.sentiment import GoEmotionsClassifier
from placerank.views import InsideAirbnbSchema, DocumentView
import placerank.config as config
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, Index
from whoosh.analysis import Analyzer
import requests
import io
import os
import sys
import csv
import gzip
import sys
from collections import defaultdict
import pickle
from operator import itemgetter
from itertools import islice
from datetime import datetime
import pydash
import argparse
from config import *

def download_dataset(url: str, storage: io.StringIO) -> io.StringIO:
    """
    Download data of InsideAirbnb and unpacks it in memory.
    """

    r = requests.get(url)
    
    if not r.ok:
        raise ConnectionError(f"Error retrieving the dataset source. Server returned status code {r.status}")

    with io.BytesIO(r.content) as gz_response:
        with gzip.GzipFile(mode="r:gz", fileobj=gz_response) as gz:
            for line in gz:
                storage.write(line.decode()) #TODO: reimplement using less memory

    storage.seek(0)
    return storage


def get_dataset(local_file: str, remote_url: str, storage: io.StringIO) -> io.StringIO:
    """
    Proxy method that writes the downloaded content to file, if passed; otherwise it keeps an in-memory representation of the dataset.
    If just a local file is passed, the dataset is loaded from that file.
    """
    if not remote_url and (not local_file or not os.path.isfile(local_file)):
        raise RuntimeError("Invalid local file and no remote source. Please provide at least one valid argument.")

    if remote_url:
        storage = download_dataset(remote_url, storage)

        if local_file:
            with open(local_file, 'w') as f:
                print(storage.getvalue(), file = f)
        return storage
    
    with open(local_file, 'r') as f:
        storage = io.StringIO(f.read())
    return storage


def create_index(index_dir: str, schema: Schema) -> Index:
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    ix = create_in(index_dir, schema)

    return ix


def populate_index(index_dir: str, local_file: str, remote_url: str = None, analyzer: Analyzer = None):
    """
    This function builds the inverted index of the provided dataset.
    If no local_file is passed, the dataset is downloaded straight from the remote_url.
    If just the local_file is passed, the dataset is loaded from there.
    If both argumetns are passed, the dataset is downloaded and stored in the local_file, then the
    inverted index is created.
    """
    schema = InsideAirbnbSchema(analyzer)
    ix = create_index(index_dir, schema)

    with io.StringIO() as ram_storage, ix.writer() as writer:
        storage = get_dataset(local_file, remote_url, ram_storage)

        dset = csv.DictReader(storage)

        for row in dset:
            writer.add_document(**schema.get_document_logic_view(row))

    ix.close()


class ReviewsDict:
    """
    Represent a Reviews file as a dictionary. Decodes CSV, preprocess text for BERT compatibility and
    filter the latest 10 reviews for each listing.
    """

    LAST_REVIEWS = 10

    def __init__(self, fp):
        self.csvdictreader = csv.DictReader(fp)
        self.__iterobj = None
        self.__last_id = 0
        self.__counter = 0

    @staticmethod
    def __todate(s: str):
        return datetime.strptime(s, "%Y-%m-%d")
    
    def __filter_first(self, row):
        if row.get("listing_id") != self.__last_id:
            self.__last_id = row.get("listing_id")
            self.__counter = 0

        if self.__counter < self.LAST_REVIEWS:
            self.__counter += 1
            
            return True

        return False
    
    def __iter__(self):
        if self.__iterobj:
            return self.__iterobj
        
        converted_types = map(lambda x: x | {"listing_id": int(x["listing_id"]), "id": int(x["id"]), "date": ReviewsDict.__todate(x["date"])}, self.csvdictreader)
        sortedreviews = sorted(converted_types, key=lambda x: (x.get("listing_id"), x.get("date") ), reverse=True)
        self.__iterobj = filter(self.__filter_first, sortedreviews)

        return self.__iterobj


def preprocess_comment(comment: str) -> str:
    """
    Returns up to the first 500 characters of the comment.
    """
    return comment[:500]


def build_reviews_index(link: str = REVIEWS_URL):
    reviews_index = defaultdict(list)

    sent = GoEmotionsClassifier()

    with io.StringIO() as storage, open(config.REVIEWS_INDEX, "bw") as fp:
        get_dataset(config.REVIEWS_DATASET_CACHE_FILE, link, storage)

        print("Downloaded dataset")

        dset = ReviewsDict(storage)

        while True:
            nextbatch = [r for r in islice(dset, BATCH_SIZE)]
            
            if not nextbatch:
                break

            comments = map(preprocess_comment, map(itemgetter("comments"), nextbatch))
            sentiments = sent.classify_texts(list(comments))

            for row, sentiment in zip(nextbatch, sentiments):
                print(row.get("id"))
                reviews_index[int(row["listing_id"])].append((int(row["id"]), row["date"], sentiment))

        pickle.dump(reviews_index, fp)


def load_page(local_dataset: str, id: str) -> DocumentView:
    """
    TODO: optimize using in-memory dataset
    """
    with open(local_dataset, 'r') as listings:
        return DocumentView.from_record(
            pydash.chain(csv.DictReader(listings.readlines()))
                .filter(lambda r: r['id'] == id)
                .value()
                .pop()
        )


class ReviewsDatabase:
    def __init__(self, filename):
        if ".pickle" in filename:
            with open(filename, "rb") as fp:
                self.db = pickle.load(fp)

        else:
            self.db = defaultdict(list)

            with open(filename, "r") as fp:
                reader = ReviewsDict(fp)
                for row in reader:
                    self.db[row.get("listing_id")].append((row.get("id"), row.get("date"), row.get("comments")))

            with open(config.REVIEWS_DB, "wb") as fp:
                pickle.dump(self.db, fp)


def main():
    parser = argparse.ArgumentParser(
        prog = "Placerank dataset downloader and indexer",
        description = "Convenience module to download and index a InsideAirBnb dataset"
    )

    parser.add_argument('-i', '--index-directory', required = True, help = 'Directory in which the index is created')
    parser.add_argument('-l', '---local-file', required = True, help = 'Path to local file. Download destination if dataset is not there, otherwise used as a local cache')
    parser.add_argument('-r', '--remote-url', help = 'Source URL from which the dataset is downloaded. Omit it if you want to use the local copy on your disk.')
    parser.add_argument('-j', '--review-index', action = "store_true", help = 'Build the reviews index.')
    
    args = parser.parse_args(sys.argv[1:])  # Exclude module itself from arguments list

    if args.review_index:
        build_reviews_index(config.REVIEWS_URL)

    populate_index(args.index_directory, args.local_file, args.remote_url)


if __name__ == "__main__":
    main()
