# url_source.py
import re
import os
import requests
import tempfile
import zipfile
import mimetypes
from urllib.parse import unquote
from urllib.parse import urlparse
from utils.debug_utils import logger
from utils.file_manager import download_and_preview_zip, DATA_DIR
from utils.file_handler import detect_file_type, read_file_preview
from utils.file_manager import extract_zip_and_list, save_confirmation,handle_direct_preview, handle_zip_preview
from utils.debug_utils import logger
from data_sources.gdrive_source import download_from_gdrive
SUPPORTED_EXT = ["csv", "xlsx", "json", "txt"]


def ensure_data_dir():
    """Pastikan folder data lokal tersedia."""
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def download_from_url(url: str):
    """
    Unduh file dataset dari URL (ZIP atau langsung file data),
    simpan di folder /data/local_datasets/<nama_dataset>.
    """
    ensure_data_dir()

    # Tentukan nama file & folder dataset
    filename = os.path.basename(urlparse(url).path)
    if not filename:
        raise ValueError("URL tidak valid: tidak ada nama file.")

    dataset_name = os.path.splitext(filename)[0]
    dataset_dir = os.path.join(DATA_DIR, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)

    logger.info(f"Mengunduh dataset dari URL: {url}")
    file_path = os.path.join(dataset_dir, filename)

    # Unduh file
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    logger.info(f"✅ Dataset disimpan di: {file_path}")
    return file_path

def resolve_gdrive_url(url: str) -> str:
    """
    Deteksi apakah URL adalah Google Drive, dan ubah menjadi direct download link.
    """
    # Pola umum ID file GDrive
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)

    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def download_from_url_tmp(url: str, tmpdir: str) -> str | None:
    """
    Unduh file dari URL ke direktori sementara.
    - Jika URL Google Drive, ubah ke direct download link.
    - Deteksi nama file dari header atau URL.
    - Tambahkan ekstensi dari Content-Type jika perlu.
    - Kembalikan path lokal file yang diunduh.
    """
    # 🔍 Ubah dulu jika link GDrive
    url = resolve_gdrive_url(url)
    logger.info(f"Mengunduh file dari URL (resolved): {url}")

    try:
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()

            # Log header untuk debugging
            logger.info(f"Content-Disposition header: {r.headers.get('Content-Disposition', '')}")

            # 🧩 Deteksi nama file dari header Content-Disposition
            cd = r.headers.get("Content-Disposition", "")
            filename = None
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip().strip('"').strip("'")
                filename = unquote(filename)

            # Jika tidak ada nama file di header, ambil dari URL
            if not filename:
                filename = os.path.basename(url.split("?")[0])

            # Jika masih tanpa ekstensi, coba dari Content-Type
            if not os.path.splitext(filename)[1]:
                mime_type = r.headers.get("Content-Type", "")
                ext = mimetypes.guess_extension(mime_type.split(";")[0].strip())
                if ext:
                    filename += ext

            local_path = os.path.join(tmpdir, filename or "downloaded_file")

            # Simpan isi file ke local_path
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"File sementara disimpan di: {local_path}")
        return local_path

    except Exception as e:
        logger.error(f"Gagal mengunduh file dari URL: {e}")
        print(f"❌ Gagal mengunduh file: {e}")
        return None

def __preview_from_url(url: str):
    """
    Unduh dan tampilkan preview dataset dari URL.
    - Jika file ZIP → ekstrak, tampilkan daftar file, lalu preview salah satu.
    - Jika file CSV/XLSX/JSON → langsung preview.
    - File disimpan sementara di folder tmp (belum ke data/local_datasets).
    """
    logger.info(f"Memproses URL dataset: {url}")
    print(f"🌐 Mengunduh dataset dari URL: {url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, "downloaded_file")

        # --- Unduh file ---
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            logger.error(f"Gagal mengunduh file dari URL: {e}")
            print(f"❌ Gagal mengunduh file: {e}")
            return None

        logger.info(f"File sementara disimpan di: {local_path}")

        # --- Deteksi tipe file ---
        file_type = detect_file_type(local_path)
        logger.info(f"Tipe file terdeteksi: {file_type}")

        # === Jika file ZIP ===
        if file_type == "zip":
            print("📦 File ZIP terdeteksi — mengekstrak sementara...")
            try:
                with zipfile.ZipFile(local_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)
            except zipfile.BadZipFile:
                print("❌ File ZIP rusak atau tidak valid.")
                return None

            extracted_files = [
                f for f in os.listdir(tmpdir)
                if not os.path.isdir(os.path.join(tmpdir, f)) and f != "downloaded_file"
            ]

            if not extracted_files:
                print("(ZIP kosong, tidak ada file data.)")
                return None

            print("\n=== File yang tersedia di ZIP ===")
            for i, name in enumerate(extracted_files, 1):
                print(f"{i}. {name}")

            try:
                choice = int(input("\nPilih file untuk preview [1-n]: "))
                if choice < 1 or choice > len(extracted_files):
                    print("Nomor tidak valid.")
                    return None
            except ValueError:
                print("Input tidak valid.")
                return None

            chosen_file = os.path.join(tmpdir, extracted_files[choice - 1])
            logger.info(f"Preview file dari ZIP: {chosen_file}")
            preview_text = read_file_preview(chosen_file, extracted_files[choice - 1])

            print("\n--- Cuplikan 5 baris pertama ---")
            print(preview_text)
            return preview_text

        # === Jika file langsung (csv/json/xlsx/dll) ===
        elif file_type in ("csv", "xlsx", "json"):
            preview_text = read_file_preview(local_path, f"downloaded_file.{file_type}")
            print("\n=== PREVIEW DATASET ===")
            print(f"Tipe file: {file_type}")
            print("\n--- Cuplikan Data ---")
            print(preview_text)
            return preview_text

        else:
            print(f"❌ Format file '{file_type}' tidak didukung untuk preview otomatis.")
            return None

def preview_from_url(url: str):
    """
    Unduh dan tampilkan preview dataset dari URL.
    - Jika file ZIP → ekstrak, tampilkan daftar file, lalu preview salah satu.
    - Jika file CSV/XLSX/JSON → langsung preview.
    - Jika URL tidak langsung mengandung nama file, coba ambil dari header Content-Disposition.
    - File disimpan sementara di folder tmp (belum ke data/local_datasets).
    """
    logger.info(f"Memproses URL dataset: {url}")
    #print(f"🌐 Mengunduh dataset dari URL: {url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # --- Deteksi Google Drive ---
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            logger.info(f"Deteksi: URL berasal dari Google Drive (id={file_id})")
            local_path = download_from_gdrive(file_id)
        else:
            local_path = download_from_url_tmp(url, tmpdir)

        if not local_path or not os.path.exists(local_path):
            print("❌ Gagal mengunduh file.")
            return None
        
        # --- Deteksi tipe file ---
        file_type = detect_file_type(local_path)
        logger.info(f"Tipe file terdeteksi: {file_type}")

        # --- Jika file ZIP → ekstrak dan tampilkan pilihan file
        if file_type == "zip":
            handle_zip_preview(local_path)
            return None
    
        # === Jika file langsung (csv/json/xlsx/dll) ===
        elif file_type in ("csv", "xlsx", "json"):
            handle_direct_preview(local_path, file_type)
            return None

        else:
            print(f"❌ Format file '{file_type}' tidak didukung untuk preview otomatis.")
            return None

def load_and_preview_from_url(url: str):
    """
    Fungsi utama yang dipanggil dari menu:
    - Mendeteksi jenis file
    - Mengunduh & menampilkan preview otomatis
    """
    logger.info(f"Memulai proses load & preview dataset dari URL: {url}")
    return preview_from_url(url)
