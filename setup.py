from placerank import (
    preprocessing,
    dataset,
    query_expansion
)
from placerank.config import *


def main():
    preprocessing.setup()
    dataset.populate_index(INDEX_DIR, DATASET_CACHE_FILE, DATASET_URL)

    # Retrieves reviews.csv from REVIEWS_URL and stores it into REVIEWS_DATASET_CACHE_FILE
    # Computes sentiment for each entry
    dataset.build_reviews_index(REVIEWS_URL)

    # Populate an in-memory database of reviews using REVIEWS_DATASET_CACHE_FILE, stored in REVIEWS_DB
    dataset.ReviewsDatabase(REVIEWS_DATASET_CACHE_FILE)
    
    query_expansion.setup([HF_MODEL_MASKING, HF_MODEL_ENCODING], HF_CACHE)

if __name__ == "__main__":
    main()