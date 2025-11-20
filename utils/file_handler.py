#utils/file_checker.py
import pandas as pd
import requests
import json
import os
from io import StringIO, BytesIO
from pandas import json_normalize
from utils.debug_utils import logger


SUPPORTED_EXT = ["csv", "json", "xlsx"]


def _detect_file_type(file_path: str) -> str:
    """
    Mendeteksi tipe file berdasarkan ekstensi atau isi file.
    Mengembalikan salah satu dari:
    'csv', 'xlsx', 'json', 'zip', atau None jika tidak dikenali.
    """
    import os

    ext = os.path.splitext(file_path)[1].lower().strip(".")
    if ext in ["csv", "xlsx", "xls", "json", "zip"]:
        return "zip" if ext == "zip" else ext

    # --- fallback: deteksi berdasarkan isi file
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
            if header.startswith(b"PK\x03\x04"):  # tanda khas file ZIP
                return "zip"
            elif header.startswith(b"\x50\x4B"):
                return "zip"
            elif b"{" in header or b"[" in header:
                return "json"
    except Exception:
        pass

    return None

def detect_file_type(file_path):
    # Ambil semua ekstensi berlapis
    exts = file_path.lower().split(".")[1:]
    
    # Prioritaskan format utama
    for e in reversed(exts):  # cek dari belakang
        if e in ["csv", "xlsx", "xls", "json", "zip"]:
            return e

    # --- fallback: deteksi berdasarkan isi file ---
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
            if header.startswith(b"PK\x03\x04"):  # ZIP
                return "zip"
            elif header[:2] == b"\x50\x4B":  # tanda khas XLSX (ZIP)
                return "zip"
            elif header.strip().startswith(b"{") or header.strip().startswith(b"["):
                return "json"
            elif b"," in header or b";" in header:  # CSV tanda koma/semicolon
                return "csv"
    except Exception:
        pass

    return None

def _read_json_to_df(content: bytes, limit: int = None):
    """Helper: membaca JSON dan melakukan normalisasi jika perlu."""
    try:
        df = pd.read_json(StringIO(content.decode("utf-8")))
        if df.shape[1] == 1 and isinstance(df.iloc[0, 0], (dict, list)):
            df = json_normalize(df.iloc[:, 0])
    except ValueError:
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = json_normalize(data)
        else:
            raise ValueError("Format JSON tidak dapat dikenali.")
    return df if limit is None else df.head(limit)


def read_file_preview(source, filename=None, limit=5):
    logger.info(f"Membaca preview file: {filename or source} (5 baris pertama)")
    """
    Membaca preview dataset (5 baris pertama).
    """
    ext = detect_file_type(filename or "")
    if not ext:
        return f"(Format file {filename} belum didukung untuk preview.)"

    try:
        if isinstance(source, str) and source.startswith("http"):
            response = requests.get(source)
            if response.status_code != 200:
                return f"(Gagal mengunduh file dari {source})"
            content = response.content
        elif isinstance(source, str):
            with open(source, "rb") as f:
                content = f.read()
        else:
            content = source.read()

        if ext == "csv":
            df = pd.read_csv(StringIO(content.decode("utf-8")), nrows=limit)
            dfull = pd.read_csv(StringIO(content.decode("utf-8")))
        elif ext == "json":
            df = _read_json_to_df(content, limit)
            dfull = _read_json_to_df(content, None)
        elif ext == "xlsx":
            df = pd.read_excel(BytesIO(content), nrows=limit)
            dfull = pd.read_excel(BytesIO(content))
        else:
            return f"(Preview untuk format {ext} belum tersedia.)"

        logger.info(f"Dari file {filename or source}, ditemukan {dfull.shape[0]} baris dan {dfull.shape[1]} kolom.")
        logger.info(f"Preview file {filename or source} berhasil dibaca.")
        #save_confirmation(local_path)
        return df.to_string(index=False)
    except Exception as e:
        logger.error(f"Gagal membaca file {filename or source}: {e}")
        return f"(Gagal membaca file {filename or source}: {e})"
    
def read_full_file(source, filename=None):
    """
    Membaca seluruh isi dataset (untuk analisis penuh).
    Bisa menerima path folder (akan mencari file CSV/XLSX/JSON pertama di dalamnya).
    """
    try:
        if os.path.isdir(source):
            # 🔍 Cari file pertama dengan ekstensi didukung
            for f in os.listdir(source):
                if detect_file_type(f):
                    source = os.path.join(source, f)
                    logger.info(f"File dataset terdeteksi di folder: {source}")
                    break
            else:
                raise ValueError("Tidak ditemukan file CSV/XLSX/JSON di folder dataset.")

        ext = detect_file_type(filename or source)
        if not ext:
            raise ValueError(f"Format file {filename or source} belum didukung untuk pembacaan penuh.")

        # --- Baca file ---
        if isinstance(source, str) and source.startswith("http"):
            response = requests.get(source)
            if response.status_code != 200:
                raise ValueError(f"Gagal mengunduh file dari {source}")
            content = response.content
        else:
            with open(source, "rb") as f:
                content = f.read()

        # --- Parse sesuai format ---
        if ext == "csv":
            df = pd.read_csv(StringIO(content.decode("utf-8")))
        elif ext == "json":
            import json
            try:
                df = pd.read_json(StringIO(content.decode("utf-8")))
            except ValueError:
                data = json.loads(content.decode("utf-8"))
                df = pd.json_normalize(data)
        elif ext == "xlsx":
            df = pd.read_excel(BytesIO(content))
        else:
            raise ValueError(f"Format {ext} belum didukung untuk pembacaan penuh.")

        logger.info(f"Dataset berhasil dibaca: {df.shape[0]} baris, {df.shape[1]} kolom.")
        return df

    except Exception as e:
        logger.error(f"Gagal membaca dataset penuh: {e}")
        raise
