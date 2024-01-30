from placerank import (
    preprocessing,
    dataset,
    query_expansion
)

DATASET_URL = 'http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz'
INDEX_DIR = 'index/'
DATASET_CACHE_FILE = "datasets/listings.csv"
HF_MODEL_MASKING = 'bert-large-uncased-whole-word-masking'
HF_MODEL_ENCODING = 'bert-base-uncased'
HF_CACHE = 'hf_cache'

def main():
    preprocessing.setup()
    dataset.populate_index(INDEX_DIR, DATASET_CACHE_FILE, DATASET_URL)
    query_expansion.setup([HF_MODEL_MASKING, HF_MODEL_ENCODING], HF_CACHE)

if __name__ == "__main__":
    main()