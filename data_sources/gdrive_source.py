# data_sources/gdrive_source.py

import gdown
import os
import logging
import tempfile
import requests

from utils.file_handler import detect_file_type, read_file_preview
from utils.file_manager import extract_zip_and_list, save_confirmation, handle_zip_preview, handle_direct_preview
from utils.debug_utils import logger


logger = logging.getLogger(__name__)

def preview_from_gdrive(file_id:str):
    file_path = download_from_gdrive(file_id)
    
    """
    Menampilkan preview dataset dari file hasil unduhan Google Drive.
    - Jika file ZIP → ekstrak ke tmp dan tampilkan daftar file
    - Jika file data langsung (csv, xlsx, json) → tampilkan preview
    """

    logger.info(f"📦 Memproses file hasil unduhan dari Google Drive: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ File tidak ditemukan: {file_path}")
        return

    # Deteksi tipe file dari konten (bukan ekstensi URL)
    file_name = os.path.basename(file_path)
    file_type = detect_file_type(file_name)
    logger.info(f"Tipe file terdeteksi: {file_type}")

    if file_type is None:
        print(f"❌ Format file tidak dikenali untuk preview otomatis.")
        return

    # --- Jika file ZIP → ekstrak dan tampilkan pilihan file
    if file_type == "zip":
        return handle_zip_preview(file_path)
    # --- Jika file langsung (csv/xlsx/json)
    elif file_type in ["csv", "xlsx", "json"]:
       return handle_direct_preview(file_path, file_type)

    else:
        print(f"❌ Format file '{file_type}' tidak didukung untuk preview otomatis.")
        return


def download_from_gdrive(file_id: str) -> str:
    """
    Mengunduh file dari Google Drive menggunakan file_id.
    - Mendapatkan nama & ekstensi file dari header Content-Disposition (jika ada).
    - Menyimpan file di direktori sementara.
    - Mengembalikan path lengkap file hasil unduhan.
    """
    if not file_id:
        raise ValueError("❌ file_id tidak boleh kosong.")

    base_url = f"https://drive.google.com/uc?id={file_id}"
    tmp_dir = tempfile.mkdtemp(prefix="gdrive_")
    output_path = None

    logger.info(f"🌐 Mengunduh file dari Google Drive: {base_url}")

    try:
        with requests.get(base_url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()

            # Ambil nama file dari header
            cd = r.headers.get("Content-Disposition", "")
            filename = None
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('"\' ')
            else:
                # fallback jika tidak ada header
                filename = f"gdrive_file_{file_id[:6]}"

            output_path = os.path.join(tmp_dir, filename)

            # Simpan file
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"✅ File berhasil diunduh ke: {output_path}")
        return output_path

    except Exception as e:
        # Fallback ke gdown jika requests gagal (misalnya file sharing terbatas)
        logger.warning(f"⚠️ Gagal menggunakan requests: {e}, mencoba gdown...")
        try:
            fallback_path = os.path.join(tmp_dir, "downloaded_file")
            gdown.download(base_url, fallback_path, quiet=False)
            logger.info(f"✅ File berhasil diunduh (gdown) ke: {fallback_path}")
            return fallback_path
        except Exception as gerr:
            logger.error(f"Gagal mengunduh file dari Google Drive: {gerr}")
            raise RuntimeError(f"Gagal mengunduh file dari Google Drive: {gerr}")
