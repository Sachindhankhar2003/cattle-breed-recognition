"""
Dataset Downloader for Cattle & Buffalo Breed Recognition
----------------------------------------------------------
Downloads images from Bing Image Search for each breed.
No API key needed — uses Bing's public image search.

Usage:
    pip install requests pillow icrawler
    python download_dataset.py

Output:
    ai-service/dataset/
        Murrah/        (buffalo)
        Surti/         (buffalo)
        Mehsana/       (buffalo)
        Jaffarabadi/   (buffalo)
        Bhadawari/     (buffalo)
        Gir/           (cattle)
        Sahiwal/       (cattle)
        Kankrej/       (cattle)
        Tharparkar/    (cattle)
        Ongole/        (cattle)
"""

import os
import sys

# Install icrawler if not present
try:
    from icrawler.builtin import BingImageCrawler
except ImportError:
    print("Installing icrawler...")
    os.system(f"{sys.executable} -m pip install icrawler")
    from icrawler.builtin import BingImageCrawler

from PIL import Image
import shutil

# ── Configuration ──────────────────────────────────────────────────────────────
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
IMAGES_PER_BREED = 80   # Download 80 images per breed (keeps dataset small but effective)

# Search queries for each breed — more specific = better quality images
BREEDS = {
    # Buffalo breeds
    "Murrah":      "Murrah buffalo India dairy breed",
    "Surti":       "Surti buffalo Gujarat India breed",
    "Mehsana":     "Mehsana buffalo Gujarat India breed",
    "Jaffarabadi": "Jaffarabadi buffalo Gujarat India largest breed",
    "Bhadawari":   "Bhadawari buffalo Uttar Pradesh India breed",
    # Cattle breeds
    "Gir":         "Gir cow cattle India Saurashtra breed",
    "Sahiwal":     "Sahiwal cow cattle India Punjab breed",
    "Kankrej":     "Kankrej cow cattle Gujarat India breed",
    "Tharparkar":  "Tharparkar cow cattle Rajasthan India breed",
    "Ongole":      "Ongole cow cattle Andhra Pradesh India breed",
}

# ── Download ───────────────────────────────────────────────────────────────────
def clean_image(path):
    """Verify image is valid RGB and resize to 224x224."""
    try:
        img = Image.open(path).convert("RGB")
        img = img.resize((224, 224))
        img.save(path, "JPEG", quality=90)
        return True
    except Exception:
        return False

def download_breed(breed_name, search_query, count):
    save_dir = os.path.join(DATASET_DIR, breed_name)
    os.makedirs(save_dir, exist_ok=True)

    existing = len([f for f in os.listdir(save_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if existing >= count:
        print(f"  ✅ {breed_name}: already has {existing} images, skipping.")
        return existing

    print(f"  📥 {breed_name}: downloading {count} images...")
    crawler = BingImageCrawler(
        storage={"root_dir": save_dir},
        feeder_threads=1,
        parser_threads=1,
        downloader_threads=4,
    )
    crawler.crawl(
        keyword=search_query,
        max_num=count,
        min_size=(100, 100),
        file_idx_offset="auto",
    )

    # Clean and validate downloaded images
    files = [f for f in os.listdir(save_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
    valid = 0
    for fname in files:
        fpath = os.path.join(save_dir, fname)
        if clean_image(fpath):
            valid += 1
        else:
            os.remove(fpath)
            print(f"    ⚠️  Removed corrupt image: {fname}")

    print(f"  ✅ {breed_name}: {valid} valid images saved.")
    return valid

def main():
    print("=" * 60)
    print("  Cattle & Buffalo Breed Dataset Downloader")
    print("=" * 60)
    print(f"  Dataset directory: {DATASET_DIR}")
    print(f"  Images per breed:  {IMAGES_PER_BREED}")
    print(f"  Total breeds:      {len(BREEDS)}")
    print("=" * 60)

    os.makedirs(DATASET_DIR, exist_ok=True)
    total = 0

    for breed, query in BREEDS.items():
        count = download_breed(breed, query, IMAGES_PER_BREED)
        total += count

    print("\n" + "=" * 60)
    print(f"  ✅ Dataset ready! Total images: {total}")
    print(f"  📁 Location: {DATASET_DIR}")
    print("\n  Next step — train the model:")
    print("    python train.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
