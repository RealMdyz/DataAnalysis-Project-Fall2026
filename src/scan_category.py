"""First scan of the raw files: how big is the remote-control (RC) part of the category?

Run from the repository root:
    python src/scan_category.py

This answers one question for task 3: should we keep the whole category or focus on
RC products? It reads both .jsonl.gz files line by line (low memory) and prints:
  - how many products and reviews the category has
  - the most common sub-categories (Amazon's own product tree)
  - how many products / reviews are RC under two definitions
  - for RC products: how many product-quarters have at least N reviews
    (our report needs enough reviews per product per 3-month window)

Output is also saved to reports/phase1/category_scan.json (small, committed).
Takes several minutes: the review file has about 16 million lines.
"""

import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]

# Definition A: Amazon's own category tree contains a remote/app-controlled node.
RC_CATEGORY = re.compile(r"remote\s*&\s*app\s*controlled|remote[- ]control", re.I)
# Definition B: the product title mentions RC or remote control.
RC_TITLE = re.compile(r"\bRC\b|remote[- ]control", re.I)

MIN_REVIEWS_PER_QUARTER = [5, 10, 20, 50]


def quarter_of(ts_ms):
    d = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def main():
    cfg = yaml.safe_load(open(ROOT / "configs" / "config.yaml", encoding="utf-8"))
    cat = cfg["data"]["category"]
    raw = ROOT / cfg["data"]["raw_dir"]

    # ---- pass 1: product metadata ----
    rc_by_cat, rc_by_title = set(), set()
    subcats = Counter()
    n_meta = 0
    with gzip.open(raw / f"meta_{cat}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="meta", unit=" products"):
            p = json.loads(line)
            n_meta += 1
            pid = p.get("parent_asin")
            cats = p.get("categories") or []
            if len(cats) >= 2:
                subcats[cats[1]] += 1
            if any(RC_CATEGORY.search(c) for c in cats):
                rc_by_cat.add(pid)
            if RC_TITLE.search(p.get("title") or ""):
                rc_by_title.add(pid)
    rc_any = rc_by_cat | rc_by_title

    # ---- pass 2: reviews (only product id and time are needed here) ----
    n_reviews = 0
    reviews_per_product = Counter()
    rc_quarter_counts = defaultdict(Counter)  # product -> quarter -> n reviews
    first_ts, last_ts = None, None
    with gzip.open(raw / f"{cat}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="reviews", unit=" reviews"):
            r = json.loads(line)
            n_reviews += 1
            pid, ts = r.get("parent_asin"), r.get("timestamp")
            reviews_per_product[pid] += 1
            if ts is not None:
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)
                if pid in rc_any:
                    rc_quarter_counts[pid][quarter_of(ts)] += 1

    def review_total(ids):
        return sum(reviews_per_product[i] for i in ids)

    def quarters_with_at_least(ids, k):
        return sum(
            1 for i in ids for n in rc_quarter_counts[i].values() if n >= k
        )

    def products_with_a_quarter_at_least(ids, k):
        return sum(
            1 for i in ids if any(n >= k for n in rc_quarter_counts[i].values())
        )

    summary = {
        "category": cat,
        "products_in_meta": n_meta,
        "products_with_reviews": len(reviews_per_product),
        "reviews": n_reviews,
        "first_review_utc": quarter_of(first_ts) if first_ts else None,
        "last_review_utc": quarter_of(last_ts) if last_ts else None,
        "top_subcategories": subcats.most_common(15),
        "rc": {},
    }
    for name, ids in [
        ("by_category_tree", rc_by_cat),
        ("by_title", rc_by_title),
        ("either", rc_any),
    ]:
        reviewed = {i for i in ids if reviews_per_product[i] > 0}
        summary["rc"][name] = {
            "products": len(ids),
            "products_with_reviews": len(reviewed),
            "reviews": review_total(ids),
            "share_of_all_reviews": round(review_total(ids) / max(n_reviews, 1), 4),
            "product_quarters_with_at_least": {
                k: quarters_with_at_least(reviewed, k) for k in MIN_REVIEWS_PER_QUARTER
            },
            "products_with_any_quarter_at_least": {
                k: products_with_a_quarter_at_least(reviewed, k)
                for k in MIN_REVIEWS_PER_QUARTER
            },
        }

    out = ROOT / "reports" / "phase1" / "category_scan.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
