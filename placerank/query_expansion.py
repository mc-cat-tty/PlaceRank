from functools import cache
from huggingface_hub import snapshot_download
from typing import List
import nltk

def setup(repo_ids: List[str], cache_dir: str):
    for id in repo_ids:
        snapshot_download(repo_id = id, cache_dir = cache_dir)
    nltk.download("wordnet")
