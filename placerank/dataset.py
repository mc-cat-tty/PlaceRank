from placerank.logic_views import InsideAirbnbSchema
from sentimentModule.sentiment import GoEmotionsClassifier
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, Index
from whoosh.analysis import Analyzer
import requests
import io
import os
import csv
import gzip
import sys
from collections import defaultdict
import pickle
from operator import itemgetter
from itertools import islice
from datetime import datetime

LINK = "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz"
REVIEWS_LINK = "http://data.insideairbnb.com/united-states/ma/cambridge/2023-12-26/data/reviews.csv.gz"

BATCH_SIZE = 10000

def download_dataset_source(storage: io.StringIO, link = LINK) -> io.StringIO:
    """
    Download data of InsideAirbnb and unpacks it in memory.
    """

    r = requests.get(link)
    
    if not r.ok:
        raise ConnectionError(f"Error retrieving the dataset source. Server returned status code {r.status}")
    
    with io.BytesIO(r.content) as gz_response:
        with gzip.GzipFile(mode="r:gz", fileobj=gz_response) as gz:
            for line in gz:
                storage.write(line.decode()) #TODO: reimplement using less memory

    storage.seek(0)
    return storage


def create_index(index_dir: str, schema: Schema) -> Index:
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    ix = create_in(index_dir, schema)

    return ix


def populate_index(index_dir: str, analyzer: Analyzer = None):
    schema = InsideAirbnbSchema(analyzer)
    ix = create_index(index_dir, schema)

    with io.StringIO() as storage, ix.writer() as writer:
        download_dataset_source(storage)

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
    Returns up to the first 512 characters of the comment.
    """
    return comment[:512]


def build_reviews_index(link: str = REVIEWS_LINK):
    reviews_index = defaultdict(list)

    sent = GoEmotionsClassifier()

    with open("reviews", "r+") as storage, open("reviews.pickle", "bw") as fp:
        download_dataset_source(storage, link)

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


if __name__ == "__main__":
    #populate_index(sys.argv[1])
    build_reviews_index()

    #with open("reviews", "r") as fp:
    #    a = ReviewsDict(fp)

    #    x = islice(a, 200)
    #    print(*[b for b in x], sep="\n")
