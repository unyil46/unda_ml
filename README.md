# unda_ml

Aplikasi analisis data dan machine learning berbasis Python CLI. Mendukung pengambilan data dari Kaggle, Google Drive, atau URL serta metode analisis K-Means dan Apriori.

## Fitur Utama

- **Import data dari Kaggle, Google Drive, dan URL**
- **Analisis K-Means Clustering**
- **Analisis Apriori Association**
- Otomatisasi pengelolaan file data
- Semua dependensi terdaftar di `requirements.txt`

## Analisa Keamanan

- **API Key Kaggle** tidak disimpan di repository. Anda harus membuat file `.env` (atau environment variable) sendiri, yang isinya tidak di-publish.
- **config.py** hanya membaca variabel dari environment, bukan menyimpan data rahasia.
- Jangan upload file .env ke GitHub!

## Cara Menggunakan di Google Colab

### Copy-Paste Code Lengkap (Single Cell)

Buka [Google Colab](https://colab.research.google.com/) dan copy-paste code berikut di satu cell:

```python
# ===== UNDA ML - Setup & Run =====

# Step 1: Clone repository dari GitHub
!git clone https://github.com/unyil46/unda_ml.git
%cd unda_ml

# Step 2: Install semua dependencies yang dibutuhkan
!pip install -q -r requirements.txt

# Step 3: Setup Kaggle API credentials
# GANTI 'your_username_here' dan 'your_api_key_here' dengan credentials Kaggle Anda
import os
os.environ['KAGGLE_USERNAME'] = 'your_username_here'
os.environ['KAGGLE_KEY'] = 'your_api_key_here'

# Step 4: Jalankan aplikasi utama
!python main.py
```

**Cara mendapatkan API Key Kaggle:**
1. Login ke [Kaggle.com](https://www.kaggle.com/)
2. Klik foto profil → **Settings**
3. Scroll ke bagian **API** → klik **Create New Token**
4. File `kaggle.json` akan otomatis terdownload
5. Buka file tersebut, copy `username` dan `key`
6. Paste ke code di atas (ganti `your_username_here` dan `your_api_key_here`)

## Contoh Colab Notebook

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/unyil46/unda_ml/blob/main/run_in_colab.ipynb)

## Struktur Folder

```
unda_ml/
│
├── main.py
├── config.py
├── requirements.txt
├── .gitignore
│
├── data_sources/
├── utils/
│
└── data/
```

## Kontribusi

- Fork repo, buat branch dan PR untuk penambahan fitur atau perbaikan
- Issue untuk bug/pengembangan diterima

## Lisensi

MIT
