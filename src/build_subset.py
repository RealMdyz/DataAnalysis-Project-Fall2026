"""Build the remote-controlled (RC) subset from the raw files and audit their raw schema.

Run from the repository root:
    python src/build_subset.py

Steps
1. Read the product metadata line by line. Keep products whose Amazon category
   tree matches `subset.category_regex` in configs/config.yaml.
2. Read the reviews line by line. Keep reviews whose `parent_asin` is a kept product.
3. Save both as Parquet files in data/processed/ (columnar, compressed, fast to load):
       meta_rc.parquet      one row per product
       reviews_rc.parquet   one row per review
4. While reading, count for EVERY field of EVERY line which Python types appear
   (str, float, list, missing, ...). Saved to reports/phase1/raw_schema_audit.json.
   This is part of the structure audit: it shows type inconsistencies in the raw
   data (e.g. a price stored sometimes as a number and sometimes as text).

Design choices
- Nested fields (lists / dicts such as images, categories, details) are stored as
  JSON text so every batch has the same column types. Notebooks decode them when needed.
- `price` is kept twice: `price_raw` (exactly as in the file, as text) and `price`
  (a number, or empty if the raw value is not a plain number). Nothing is thrown away.
- Rows are written in batches, so memory use stays small even on a laptop.
"""

import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 50_000

REVIEW_SCHEMA = pa.schema([
    ("rating", pa.float64()),
    ("title", pa.string()),
    ("text", pa.string()),
    ("images", pa.string()),            # JSON list
    ("n_images", pa.int32()),
    ("asin", pa.string()),
    ("parent_asin", pa.string()),
    ("user_id", pa.string()),
    ("timestamp", pa.int64()),          # Unix time in milliseconds
    ("helpful_vote", pa.int64()),
    ("verified_purchase", pa.bool_()),
])

META_SCHEMA = pa.schema([
    ("parent_asin", pa.string()),
    ("main_category", pa.string()),
    ("title", pa.string()),
    ("store", pa.string()),
    ("average_rating", pa.float64()),   # LEAKAGE RISK: computed at crawl time
    ("rating_number", pa.int64()),      # LEAKAGE RISK: computed at crawl time
    ("price", pa.float64()),
    ("price_raw", pa.string()),
    ("categories", pa.string()),        # JSON list (Amazon category path)
    ("features", pa.string()),          # JSON list
    ("description", pa.string()),       # JSON list
    ("details", pa.string()),           # JSON dict
    ("images", pa.string()),            # JSON list
    ("n_images", pa.int32()),
    ("videos", pa.string()),            # JSON list
    ("n_videos", pa.int32()),
    ("bought_together", pa.string()),   # JSON
])


def type_name(v):
    return "missing" if v is None else type(v).__name__


def to_json(v):
    return None if v is None else json.dumps(v, ensure_ascii=False)


def to_float(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace("$", "").replace(",", "").strip())
        except ValueError:
            return None
    return None


def to_int(v):
    f = to_float(v)
    return None if f is None else int(f)


def review_row(r):
    imgs = r.get("images")
    vp = r.get("verified_purchase")
    return {
        "rating": to_float(r.get("rating")),
        "title": r.get("title"),
        "text": r.get("text"),
        "images": to_json(imgs),
        "n_images": len(imgs) if isinstance(imgs, list) else None,
        "asin": r.get("asin"),
        "parent_asin": r.get("parent_asin"),
        "user_id": r.get("user_id"),
        "timestamp": to_int(r.get("timestamp")),
        # the docs name this field both helpful_vote and helpful_votes
        "helpful_vote": to_int(r.get("helpful_vote", r.get("helpful_votes"))),
        "verified_purchase": vp if isinstance(vp, bool) else None,
    }


def meta_row(p):
    imgs, vids = p.get("images"), p.get("videos")
    price = p.get("price")
    return {
        "parent_asin": p.get("parent_asin"),
        "main_category": p.get("main_category"),
        "title": p.get("title"),
        "store": p.get("store"),
        "average_rating": to_float(p.get("average_rating")),
        "rating_number": to_int(p.get("rating_number")),
        "price": to_float(price),
        "price_raw": None if price is None else str(price),
        "categories": to_json(p.get("categories")),
        "features": to_json(p.get("features")),
        "description": to_json(p.get("description")),
        "details": to_json(p.get("details")),
        "images": to_json(imgs),
        "n_images": len(imgs) if isinstance(imgs, list) else None,
        "videos": to_json(vids),
        "n_videos": len(vids) if isinstance(vids, list) else None,
        "bought_together": to_json(p.get("bought_together")),
    }


class BatchWriter:
    """Collect rows and write them to a Parquet file in batches."""

    def __init__(self, path, schema):
        self.path, self.schema, self.rows, self.n = path, schema, [], 0
        self.writer = pq.ParquetWriter(path, schema, compression="zstd")

    def add(self, row):
        self.rows.append(row)
        if len(self.rows) >= BATCH_SIZE:
            self.flush()

    def flush(self):
        if self.rows:
            self.writer.write_table(pa.Table.from_pylist(self.rows, schema=self.schema))
            self.n += len(self.rows)
            self.rows = []

    def close(self):
        self.flush()
        self.writer.close()


def main():
    cfg = yaml.safe_load(open(ROOT / "configs" / "config.yaml", encoding="utf-8"))
    cat = cfg["data"]["category"]
    raw = ROOT / cfg["data"]["raw_dir"]
    out_dir = ROOT / cfg["data"]["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rc_regex = re.compile(cfg["subset"]["category_regex"], re.I)

    audit = {"meta": defaultdict(Counter), "reviews": defaultdict(Counter)}
    n_lines = {"meta": 0, "reviews": 0}
    bad_json = {"meta": 0, "reviews": 0}

    # ---- product metadata ----
    keep = set()
    duplicate_meta_ids = 0
    w = BatchWriter(out_dir / "meta_rc.parquet", META_SCHEMA)
    with gzip.open(raw / f"meta_{cat}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="meta", unit=" products"):
            n_lines["meta"] += 1
            try:
                p = json.loads(line)
            except json.JSONDecodeError:
                bad_json["meta"] += 1
                continue
            for k, v in p.items():
                audit["meta"][k][type_name(v)] += 1
            cats = p.get("categories") or []
            if any(isinstance(c, str) and rc_regex.search(c) for c in cats):
                pid = p.get("parent_asin")
                if pid in keep:
                    duplicate_meta_ids += 1
                keep.add(pid)
                w.add(meta_row(p))
    w.close()
    n_meta_kept = w.n

    # ---- reviews ----
    w = BatchWriter(out_dir / "reviews_rc.parquet", REVIEW_SCHEMA)
    with gzip.open(raw / f"{cat}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="reviews", unit=" reviews"):
            n_lines["reviews"] += 1
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad_json["reviews"] += 1
                continue
            for k, v in r.items():
                audit["reviews"][k][type_name(v)] += 1
            if r.get("parent_asin") in keep:
                w.add(review_row(r))
    w.close()
    n_reviews_kept = w.n

    # fields that are absent from a line count as "absent" (not the same as null)
    for part in ("meta", "reviews"):
        for k, c in audit[part].items():
            present = sum(c.values())
            if present < n_lines[part] - bad_json[part]:
                c["absent"] = n_lines[part] - bad_json[part] - present

    summary = {
        "lines_read": n_lines,
        "unparseable_lines": bad_json,
        "kept": {"products": n_meta_kept, "reviews": n_reviews_kept},
        "duplicate_parent_asin_in_kept_meta": duplicate_meta_ids,
        "field_types": {part: {k: dict(c) for k, c in sorted(audit[part].items())}
                        for part in audit},
    }
    out = ROOT / "reports" / "phase1" / "raw_schema_audit.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nKept {n_meta_kept:,} products and {n_reviews_kept:,} reviews")
    print(f"Unparseable lines: {bad_json}")
    print(f"Duplicate parent_asin among kept products: {duplicate_meta_ids}")
    print(f"Parquet files in {out_dir.relative_to(ROOT)}; audit in {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
