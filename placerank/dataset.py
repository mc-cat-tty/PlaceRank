from placerank.views import DocumentLogicView
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, Index
import requests
import io
import os
import csv
import gzip
import pydash

LINK = "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz"
CACHE_FILE = "datasets/listings.csv"

def cached_download(filename: str):
    def decorator(download_function):
        def inner(storage: io.StringIO):
            if not os.path.isfile(filename):
                storage = download_function(storage)
                with open(filename, 'w') as cache: print(storage.getvalue(), file=cache)
            else:
                with open(filename, 'r') as cache: storage = io.StringIO(cache.read())
            return storage
        return inner
    return decorator

@cached_download(CACHE_FILE)
def download_dataset_source(storage: io.StringIO) -> io.StringIO:
    """
    Download data of InsideAirbnb and unpacks it in memory.
    """

    r = requests.get(LINK)
    
    if not r.ok:
        raise ConnectionError(f"Error retrieving the dataset source. Server returned status code {r.status}")
    
    with io.BytesIO(r.content) as gz_response:
        with gzip.GzipFile(mode="r:gz", fileobj=gz_response) as gz:
            for line in gz:
                storage.write(line.decode()) #TODO: reimplement using less memory

    storage.seek(0)
    return storage


def create_index(index_dir: str) -> Index:
    schema = DocumentLogicView.get_schema()

    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    ix = create_in(index_dir, schema)

    return ix


def populate_index(index_dir: str):
    ix = create_index(index_dir)

    with io.StringIO() as storage, ix.writer() as writer:
        storage = download_dataset_source(storage)

        dset = csv.DictReader(storage)

        for row in dset:
            writer.add_document(**DocumentLogicView(row))

    ix.close()


def load_page(id: int) -> DocumentLogicView:
    """
    TODO: optimize using in-memory dataset
    """
    with open(CACHE_FILE, 'r') as listings:
        return DocumentLogicView(
            pydash.chain(csv.DictReader(listings.readlines()))
                .filter(lambda r: int(r['id']) == id)
                .value()
                .pop()
        )


if __name__ == "__main__":
    populate_index("index")
