"""Download the raw Amazon Reviews'23 files for the category set in configs/config.yaml.

Run from the repository root:
    python src/download_data.py

What it does:
1. Reads the category name from configs/config.yaml.
2. Downloads the review file and the product metadata file (.jsonl.gz) into data/raw/.
   Files that already exist are skipped, so the script is safe to run again.
   Interrupted downloads resume where they stopped. A file downloaded by hand
   (e.g. with a download manager) can simply be placed in data/raw/; the script
   then only records it in the manifest.
3. Writes data/download_manifest.json with the URL, download date, size and SHA-256
   hash of each file. The manifest is small and IS committed to GitHub, so anyone
   can check they have exactly the same files we used.

The files stay compressed (.gz). Later scripts read them line by line, so the full
data never has to fit in memory.
"""

import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import yaml
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]

# Official hosts listed on the dataset pages; the first one that works is used.
# (datarepo.eng.ucsd.edu is listed on Hugging Face but returned 404 on 2026-10-14.)
BASE_URLS = [
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw",
    "https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw",
]
MAX_RETRIES = 30          # reconnect attempts per host after a dropped connection
RETRY_WAIT_SECONDS = 10


def load_config():
    with open(ROOT / "configs" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Use certifi's up-to-date certificate list; Windows Python often lacks one,
# which causes CERTIFICATE_VERIFY_FAILED. Certificate checking stays ON.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def download(url, dest):
    """Stream a file to disk with a progress bar, resuming if interrupted.

    Data goes to a .part file first, so a broken download never has the final
    name. If a .part file already exists, only the missing bytes are requested
    (HTTP Range). Stop with Ctrl+C at any time and run the script again later.
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    have = tmp.stat().st_size if tmp.exists() else 0

    req = urllib.request.Request(url)
    if have:
        req.add_header("Range", f"bytes={have}-")

    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
        if have and resp.status != 206:
            print("  server does not support resume; starting from zero")
            have = 0
        remaining = int(resp.headers.get("Content-Length", 0))
        total = have + remaining if remaining else None
        mode = "ab" if have else "wb"
        with open(tmp, mode) as out, tqdm(
            total=total, initial=have, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            while chunk := resp.read(1024 * 1024):
                out.write(chunk)
                bar.update(len(chunk))

    if total and tmp.stat().st_size != total:
        raise IOError(f"incomplete: {tmp.stat().st_size} of {total} bytes")
    tmp.rename(dest)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    cfg = load_config()
    category = cfg["data"]["category"]
    raw_dir = ROOT / cfg["data"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "reviews": f"review_categories/{category}.jsonl.gz",
        "meta": f"meta_categories/meta_{category}.jsonl.gz",
    }

    manifest_path = ROOT / "data" / "download_manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for kind, rel in files.items():
        dest = raw_dir / Path(rel).name
        if dest.exists():
            print(f"[skip] {dest.name} already exists")
            used_url = manifest.get(dest.name, {}).get("url", "unknown")
        else:
            used_url = None
            for base in BASE_URLS:
                url = f"{base}/{rel}"
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        print(f"[download] {url}  (attempt {attempt})")
                        download(url, dest)
                        used_url = url
                        break
                    except urllib.error.HTTPError as e:
                        # 404 and similar: this host does not have the file
                        print(f"  failed: {e}; trying the next host")
                        break
                    except (urllib.error.URLError, OSError) as e:
                        # dropped connection: wait, then resume from the .part file
                        print(f"  connection lost: {e}; retrying in {RETRY_WAIT_SECONDS}s")
                        time.sleep(RETRY_WAIT_SECONDS)
                if used_url:
                    break
            if used_url is None:
                raise SystemExit(f"Could not download {rel} from any host.")

        if dest.name not in manifest or "sha256" not in manifest[dest.name]:
            print(f"[hash] {dest.name}")
            manifest[dest.name] = {
                "kind": kind,
                "category": category,
                "url": used_url,
                "downloaded_utc": datetime.fromtimestamp(
                    dest.stat().st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
                "size_bytes": dest.stat().st_size,
                "sha256": sha256(dest),
            }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written to {manifest_path.relative_to(ROOT)}")
    for name, info in manifest.items():
        print(f"  {name}: {info['size_bytes'] / 1e9:.2f} GB, {info['downloaded_utc']}")


if __name__ == "__main__":
    main()
