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

    def __init__(self, fp):
        self.csvdictreader = csv.DictReader(fp)

    def __todate(self, s: str):
        return datetime.strptime(s, "%Y-%m-%d")
    
    def __iter__(self):
        sortedreviews = sorted(self.csvdictreader, key=lambda x: (int(x.get("listing_id") ), x.get("date") ), reverse=True)
        mapped_to_dict = map(
            lambda comment: {"listing_id": int(comment.get("listing_id")), "date": self.__todate(comment.get("date")), "id": comment.get("id")},
            sortedreviews
        )

        return mapped_to_dict


def preprocess_comment(comment: str) -> str:
    """
    Returns up to the first 512 characters of the comment.
    """
    return comment[:512]


def build_reviews_index(link: str = REVIEWS_LINK):
    reviews_index = defaultdict(list)

    sent = GoEmotionsClassifier()

    with open("reviews", "r+") as storage, open("reviews.pickle", "bw") as fp:
        #download_dataset_source(storage, link)

        print("Downloaded dataset")

        dset = csv.DictReader(storage)

        with open("reviews", "r") as comments_storage:
            comments_set = csv.DictReader(comments_storage)
            comments = map(preprocess_comment, map(itemgetter("comments"), comments_set))

            while True:
                next_comments = islice(comments, 10000)
                next_sentiment = sent.classify_texts(list(next_comments))

                if not next_sentiment:
                    break

                for row, sentiment in zip(dset, next_sentiment):
                    print(row["id"])
                    reviews_index[int(row["listing_id"])].append((int(row["id"]), row["date"], sentiment))

        pickle.dump(reviews_index, fp)


if __name__ == "__main__":
    #populate_index(sys.argv[1])
    #build_reviews_index()
    with open("reviews", "r+") as storage:
        r = ReviewsDict(storage)
        first10 = islice(r, 10)

        for x in first10:
            print(x)

