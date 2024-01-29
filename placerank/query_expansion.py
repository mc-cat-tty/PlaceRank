from functools import cache
from huggingface_hub import snapshot_download

def setup(repo_id: str, cache_dir: str):
    snapshot_download(repo_id = repo_id, cache_dir = cache_dir)
