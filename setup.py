from placerank import (
    preprocessing,
    dataset,
    query_expansion
)
from placerank.config import *


def main():
    preprocessing.setup()
    dataset.populate_index(INDEX_DIR, DATASET_CACHE_FILE, DATASET_URL)
    dataset.build_reviews_index()
    query_expansion.setup([HF_MODEL_MASKING, HF_MODEL_ENCODING], HF_CACHE)

if __name__ == "__main__":
    main()