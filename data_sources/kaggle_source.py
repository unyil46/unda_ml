# utils/kaggle_source.py

import os
import subprocess
import requests
import json
import pandas as pd
from utils.debug_utils import logger
from utils.file_handler import read_file_preview
from utils.file_manager import download_and_extract_zip, list_local_datasets,download_and_preview_zip
from utils.debug_utils import logger
from utils.cache_manager import load_cache, save_cache

""" CACHE_DIR = os.path.join(".cache", "preview")
os.makedirs(CACHE_DIR, exist_ok=True) 

CACHE_DIR = os.path.join(".cache", "preview")
os.makedirs(CACHE_DIR, exist_ok=True) """

def setup_kaggle_api(username, key):
    if not username or not key:
        logger.error("Kredensial Kaggle tidak ditemukan. Pastikan file .env berisi KAGGLE_USERNAME dan KAGGLE_KEY.")
        return False
    os.environ['KAGGLE_USERNAME'] = username
    os.environ['KAGGLE_KEY'] = key
    logger.info("Kaggle API disiapkan.")
    return True


def download_kaggle_dataset(dataset, output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["kaggle", "datasets", "download", "-d", dataset, "-p", output_dir, "--unzip"]
    subprocess.run(cmd)
    logger.info(f"Dataset '{dataset}' diunduh ke {output_dir}")


def _search_kaggle_dataset(query,limit=5):
    logger.info(f"Mencari dataset dengan kata kunci: {query}")
    url = f"https://www.kaggle.com/api/v1/datasets/list?search={query}"
    response = requests.get(url)
    if response.status_code == 200:
        datasets = response.json()
        for i, ds in enumerate(datasets[:limit], 1):
            print(f"{i}. {ds['title']} ({ds['ref']})")
    else:
        logger.error("Gagal mengambil hasil pencarian dari Kaggle.")

def __search_kaggle_dataset(query, limit=5):
    """Cari dataset Kaggle dan tawarkan preview hasil pilihan user."""
    logger.info(f"Mencari dataset dengan kata kunci: {query}")

    url = f"https://www.kaggle.com/api/v1/datasets/list?search={query}"
    response = requests.get(url)

    if response.status_code != 200:
        logger.error("Gagal mengambil hasil pencarian dari Kaggle.")
        print("❌ Gagal mengambil hasil pencarian dari Kaggle.")
        return

    datasets = response.json()
    if not datasets:
        print("⚠️ Tidak ditemukan dataset dengan kata kunci tersebut.")
        return

    print(f"\n=== Hasil Pencarian Dataset (limit={limit}) ===")
    for i, ds in enumerate(datasets[:limit], 1):
        print(f"{i}. {ds.get('title', '(tanpa judul)')}")
        print(f"   📂 Ref : {ds.get('ref')}")
        print(f"   🧑 Owner : {ds.get('ownerName', '-')}")
        #print(f"   🏷️ Tags  : {', '.join(ds.get('tags', [])) if ds.get('tags') else '-'}")
        print("-" * 60)

    try:
        choice = input("Masukkan nomor dataset untuk preview (atau tekan Enter untuk batal): ").strip()
        if not choice:
            print("❎ Preview dibatalkan.")
            return

        choice = int(choice)
        if choice < 1 or choice > min(limit, len(datasets)):
            print("⚠️ Nomor tidak valid.")
            return

        selected = datasets[choice - 1]
        dataset_ref = selected.get("ref")

        if not dataset_ref:
            print("❌ Dataset tidak memiliki referensi yang valid.")
            return

        print(f"\n🔍 Menampilkan preview dataset: {dataset_ref}")
        preview_kaggle_dataset(dataset_ref)

    except ValueError:
        print("⚠️ Input tidak valid, masukkan angka saja.")
        return
    
def search_kaggle_dataset(query, limit=25):
    """Cari dataset Kaggle dan tawarkan preview hasil pilihan user (dengan pagination)."""
    logger.info(f"Mencari dataset dengan kata kunci: {query}")
    base_url = "https://www.kaggle.com/api/v1/datasets/list"
    
    datasets = []
    page = 1
    per_page = 20  # batas maksimum per halaman oleh API Kaggle
    
    while len(datasets) < limit:
        url = f"{base_url}?search={query}&page={page}&pageSize={per_page}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error("Gagal mengambil hasil pencarian dari Kaggle.")
            print("❌ Gagal mengambil hasil pencarian dari Kaggle.")
            return
        
        page_data = response.json()
        if not page_data:
            break
        
        datasets.extend(page_data)
        if len(page_data) < per_page:
            break  # tidak ada halaman berikutnya
        
        page += 1
    
    datasets = datasets[:limit]

    if not datasets:
        print("⚠️ Tidak ditemukan dataset dengan kata kunci tersebut.")
        return

    print(f"\n=== Hasil Pencarian Dataset (total ditampilkan={len(datasets)}) ===")
    for i, ds in enumerate(datasets, 1):
        print(f"{i}. {ds.get('title', '(tanpa judul)')}")
        print(f"   📂 Ref : {ds.get('ref')}")
        print(f"   🧑 Owner : {ds.get('ownerName', '-')}")
        print("-" * 60)

    try:
        choice = input("Masukkan nomor dataset untuk preview (atau tekan Enter untuk batal): ").strip()
        if not choice:
            print("❎ Preview dibatalkan.")
            return

        choice = int(choice)
        if choice < 1 or choice > len(datasets):
            print("⚠️ Nomor tidak valid.")
            return

        selected = datasets[choice - 1]
        dataset_ref = selected.get("ref")

        if not dataset_ref:
            print("❌ Dataset tidak memiliki referensi yang valid.")
            return

        print(f"\n🔍 Menampilkan preview dataset: {dataset_ref}")
        preview_kaggle_dataset(dataset_ref)

    except ValueError:
        print("⚠️ Input tidak valid, masukkan angka saja.")
        return

def preview_kaggle_dataset(dataset):
    """Preview dataset Kaggle.
       - Jika file punya URL langsung → preview online.
       - Jika tidak → tawarkan unduhan zip & preview file di dalamnya.
    """
    cached = load_cache(dataset)
    if cached:
        print("\n=== PREVIEW DATASET (Cached) ===")
        print(cached["metadata"])
        print("\n--- Cuplikan 5 baris pertama (Cached) ---")
        print(cached.get("preview", "(tidak ada preview)"))
        return

    logger.info(f"Mengambil metadata dataset: {dataset}")
    url = f"https://www.kaggle.com/api/v1/datasets/view/{dataset}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error("Gagal mengambil metadata dataset.")
        return

    data = response.json()
    metadata_text = (
        f"Judul     : {data.get('title')}\n"
        f"Subtitle  : {data.get('subtitle')}\n"
        f"Owner     : {data.get('ownerUser', {}).get('username')}\n"
        f"Tags      : {', '.join([t['name'] for t in data.get('tags', [])])}\n"
        f"URL       : https://www.kaggle.com/datasets/{dataset}"
    )

    print("\n=== PREVIEW DATASET ===")
    print(metadata_text) 

    files = data.get("files", [])
    if not files:
        print("\n⚠️ Tidak ada daftar file dari API Kaggle.")
        print("Dataset mungkin hanya tersedia dalam bentuk ZIP.")
        #confirm = input("Unduh ZIP dan preview isinya? (y/n): ").lower().strip() 
        #if confirm != "y":
        #    print("Preview dibatalkan.")
        #    return
        download_and_preview_zip(dataset, metadata_text)
        return

    print("\nDaftar file:")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f['name']} ({f.get('totalBytesReadable', 'ukuran tak diketahui')})")

    try:
        choice = int(input("\nPilih nomor file untuk preview [1-n]: "))
        if choice < 1 or choice > len(files):
            print("Nomor tidak valid.")
            return
    except ValueError:
        print("Input tidak valid.")
        return

    file_info = files[choice - 1]
    file_url = file_info.get("directUrl") or file_info.get("url")

    if file_url:
        print(f"\n🔗 File memiliki URL langsung. Melakukan preview online...")
        preview_text = read_file_preview(file_url, file_info["name"])
        print("\n--- Cuplikan 5 baris pertama ---")
        print(preview_text)
    else:
        print(f"\n⚠️ File tidak memiliki URL langsung.")
        confirm = input("File akan diunduh (ZIP) dan diekstrak untuk preview. Lanjutkan? (y/n): ").lower().strip()
        if confirm != "y":
            print("Preview dibatalkan.")
            return
        preview_text = download_and_preview_zip(dataset, metadata_text)
    print("\n--- Cuplikan 5 baris pertama ---")
    print(preview_text)
    save_cache(dataset, {"metadata": metadata_text, "preview": preview_text})
