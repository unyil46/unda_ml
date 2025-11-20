#
import os
import time
import json

CACHE_DIR = "cache"

def load_cache(dataset_name: str):
    """Cek apakah dataset preview sudah ada di cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{dataset_name.replace('/', '_')}.json")

    if not os.path.exists(cache_file):
        return None

    # Hapus cache lebih lama dari 1 hari
    if time.time() - os.path.getmtime(cache_file) > 86400:
        os.remove(cache_file)
        return None

    with open(cache_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(dataset_name: str, data):
    """Simpan hasil preview dataset ke cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{dataset_name.replace('/', '_')}.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
