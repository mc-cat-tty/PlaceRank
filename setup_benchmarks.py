from placerank import (
    preprocessing,
    dataset,
    query_expansion
)
from placerank.config import *

DATASET_URL = "http://data.insideairbnb.com/united-states/ma/cambridge/2023-12-26/data/listings.csv.gz"
REVIEWS_URL = "http://data.insideairbnb.com/united-states/ma/cambridge/2023-12-26/data/reviews.csv.gz"

def main():
    dataset.populate_index(INDEX_DIR, DATASET_CACHE_FILE, DATASET_URL)
    dataset.build_reviews_index(REVIEWS_URL)


if __name__ == "__main__":
    main()
