# utils/chart_utils.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils.debug_utils import logger


# ==========================================================
# 🔹 Utility: pastikan folder output grafik tersedia
# ==========================================================
def ensure_plot_dir():
    plot_dir = os.path.join("data", "plots")
    os.makedirs(plot_dir, exist_ok=True)
    return plot_dir


# ==========================================================
# 🔹 1. Visualisasi hasil K-Means Clustering
# ==========================================================
def plot_kmeans_clusters(df, x_col=None, y_col=None, cluster_col="Cluster", title="Visualisasi K-Means"):
    """
    Membuat scatter plot hasil clustering 2D berdasarkan 2 kolom numerik.
    """
    try:
        if cluster_col not in df.columns:
            print("❌ Kolom 'Cluster' tidak ditemukan pada dataset.")
            return

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if len(numeric_cols) < 2:
            print("❌ Dataset tidak memiliki cukup kolom numerik untuk plot 2D.")
            return

        # Jika user tidak menentukan, pakai dua kolom pertama numerik
        x_col = x_col or numeric_cols[0]
        y_col = y_col or numeric_cols[1]

        plt.figure(figsize=(8, 6))
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=cluster_col, palette="tab10", s=60)
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.legend(title="Cluster")
        plt.tight_layout()

        plot_dir = ensure_plot_dir()
        plot_path = os.path.join(plot_dir, f"{title.replace(' ', '_')}.png")
        plt.savefig(plot_path)
        plt.show()

        logger.info(f"Plot K-Means disimpan di {plot_path}")
        print(f"📊 Grafik disimpan ke: {plot_path}")

    except Exception as e:
        logger.error(f"Gagal membuat grafik K-Means: {e}")
        print(f"❌ Gagal membuat grafik: {e}")


# ==========================================================
# 🔹 2. Visualisasi hasil Regresi Linier
# ==========================================================
def plot_linear_regression(y_test, y_pred, title="Hasil Regresi Linier"):
    """
    Membuat scatter plot antara nilai aktual dan prediksi.
    """
    try:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=y_test, y=y_pred)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
        plt.title(title)
        plt.xlabel("Nilai Aktual (Y Test)")
        plt.ylabel("Nilai Prediksi (Y Pred)")
        plt.tight_layout()

        plot_dir = ensure_plot_dir()
        plot_path = os.path.join(plot_dir, f"{title.replace(' ', '_')}.png")
        plt.savefig(plot_path)
        plt.show()

        logger.info(f"Plot regresi linier disimpan di {plot_path}")
        print(f"📈 Grafik disimpan ke: {plot_path}")

    except Exception as e:
        logger.error(f"Gagal membuat grafik regresi linier: {e}")
        print(f"❌ Gagal membuat grafik: {e}")


# ==========================================================
# 🔹 3. Visualisasi hasil Apriori (frekuensi itemset)
# ==========================================================
def plot_apriori_support(df, support_col="support", item_col="itemsets", top_n=10, title="Top Itemset Berdasarkan Support"):
    """
    Membuat bar chart itemset dengan support tertinggi.
    """
    try:
        if support_col not in df.columns or item_col not in df.columns:
            print("❌ Data hasil apriori tidak memiliki kolom 'support' atau 'itemsets'.")
            return

        df_sorted = df.sort_values(by=support_col, ascending=False).head(top_n)
        df_sorted["itemsets"] = df_sorted["itemsets"].astype(str)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=support_col, y=item_col, data=df_sorted, palette="viridis")
        plt.title(title)
        plt.xlabel("Support")
        plt.ylabel("Itemset")
        plt.tight_layout()

        plot_dir = ensure_plot_dir()
        plot_path = os.path.join(plot_dir, f"{title.replace(' ', '_')}.png")
        plt.savefig(plot_path)
        plt.show()

        logger.info(f"Plot Apriori disimpan di {plot_path}")
        print(f"📈 Grafik disimpan ke: {plot_path}")

    except Exception as e:
        logger.error(f"Gagal membuat grafik Apriori: {e}")
        print(f"❌ Gagal membuat grafik Apriori: {e}")


# ==========================================================
# 🔹 4. Visualisasi Distribusi Kolom (Histogram)
# ==========================================================
def plot_distribution(df, column, bins=20):
    """
    Membuat histogram distribusi data untuk kolom tertentu.
    """
    try:
        if column not in df.columns:
            print(f"❌ Kolom '{column}' tidak ditemukan di dataset.")
            return

        plt.figure(figsize=(8, 6))
        sns.histplot(df[column], bins=bins, kde=True)
        plt.title(f"Distribusi Kolom: {column}")
        plt.xlabel(column)
        plt.ylabel("Frekuensi")
        plt.tight_layout()

        plot_dir = ensure_plot_dir()
        plot_path = os.path.join(plot_dir, f"Distribusi_{column}.png")
        plt.savefig(plot_path)
        plt.show()

        logger.info(f"Plot distribusi '{column}' disimpan di {plot_path}")
        print(f"📊 Grafik disimpan ke: {plot_path}")

    except Exception as e:
        logger.error(f"Gagal membuat grafik distribusi: {e}")
        print(f"❌ Gagal membuat grafik distribusi: {e}")
