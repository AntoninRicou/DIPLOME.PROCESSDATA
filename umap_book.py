import json
import os
import math
import numpy as np
import umap
from sentence_transformers import SentenceTransformer
from collections import defaultdict

print("START BOOK UMAP")

# Text embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Paths
BASE_DIR = os.path.dirname(__file__)
MAPPING_PATH = os.path.abspath(os.path.join(BASE_DIR, "../cache/mapping.json"))
OUTPUT_PATH = os.path.join(BASE_DIR, "../cache/umap_book2_pca.json")

# Target on-screen aspect ratio (width / height). 16:9 ≈ 1.778.
TARGET_ASPECT = 16.0 / 9.0

# Load metadata
with open(MAPPING_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"items: {len(data)}")

# Group images by exact book edition (title + author + year)
books_dict = defaultdict(list)
book_texts = []
unique_books = []
seen_books = set()

for i, item in enumerate(data):
    title = str(item.get("title", "") or "").strip()
    author = str(item.get("author", "") or "").strip()
    year = str(item.get("year", "") or "").strip()

    if not title:
        title = "Unknown Title"
    if not author:
        author = "Unknown Author"
    if not year:
        year = "Unknown Year"

    book_key = f"{title} | {author} | {year}"
    books_dict[book_key].append(item.get("id", i))

    if book_key not in seen_books:
        seen_books.add(book_key)
        unique_books.append((title, author, year))
        book_texts.append(f"{title} {author} {year}")

print(f"unique books: {len(unique_books)}")

# Encode book texts into embeddings
print("encoding books...")
book_embeddings = model.encode(book_texts, show_progress_bar=True)
book_embeddings = np.array(book_embeddings)

# 2D UMAP projection for book centers
print("UMAP projection for book centers...")
reducer = umap.UMAP(
    n_neighbors=max(2, min(15, len(unique_books) - 1)),
    min_dist=0.32,
    metric="cosine",
    random_state=42,
)
book_positions = reducer.fit_transform(book_embeddings)

# Rotate so the cloud's natural longest axis lies along X, then stretch X
# to match TARGET_ASPECT. Distances along the rotated principal axis are
# preserved; the perpendicular axis is implicitly compressed relative to
# the principal one to reach the target bbox aspect.
mean = book_positions.mean(axis=0)
centered = book_positions - mean
cov = np.cov(centered, rowvar=False)
eigvals, eigvecs = np.linalg.eigh(cov)
order = np.argsort(eigvals)[::-1]
R = eigvecs[:, order]
rotated = centered @ R
rx = rotated[:, 0].max() - rotated[:, 0].min()
ry = rotated[:, 1].max() - rotated[:, 1].min()
cur_aspect = rx / ry if ry > 0 else 1.0
rotated[:, 0] *= TARGET_ASPECT / cur_aspect
book_positions = rotated
print(f"PCA: bbox aspect after rotate={cur_aspect:.3f} → stretched to {TARGET_ASPECT:.3f}")

# Spread cluster centers farther apart in the final 2D space.
CENTER_SPREAD = 1.35

# Create output: one circle per unique edition
output = []

# Keep a consistent arc-length spacing between adjacent images on each circle.
# Books with more images therefore get larger circles automatically.
IMAGE_ARC_SPACING = 0.075
MIN_CIRCLE_RADIUS = 0.18

for book_idx, (title, author, year) in enumerate(unique_books):
    book_key = f"{title} | {author} | {year}"
    image_indices = books_dict[book_key]

    center_x, center_y = book_positions[book_idx]
    center_x *= CENTER_SPREAD
    center_y *= CENTER_SPREAD

    num_images = len(image_indices)
    # Radius derived from fixed arc spacing: circumference = n * spacing.
    radius = max(MIN_CIRCLE_RADIUS, (num_images * IMAGE_ARC_SPACING) / (2 * math.pi))

    for circle_idx, image_id in enumerate(image_indices):
        angle = (2 * math.pi * circle_idx) / max(1, num_images)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        output.append(
            {
                "id": image_id,
                "x": float(x),
                "y": float(y),
                "book": book_key,
                "text": f"{title} | {author} | {year}",
                "title": title,
                "author": author,
                "year": year,
            }
        )

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f)

print(f"DONE → {OUTPUT_PATH} ({len(output)} points in {len(unique_books)} books)")
