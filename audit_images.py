"""Audit FoodConnect's local photo references without modifying the database."""
import json
from pathlib import Path
from collections import Counter
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
IMG = STATIC / "images"

def audit():
    files = [p for p in IMG.rglob("*") if p.is_file()]
    raster = [p for p in files if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    valid, invalid = [], []
    hashes = {}
    import hashlib
    for path in raster:
        try:
            with Image.open(path) as im:
                im.verify()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes.setdefault(digest, []).append(str(path.relative_to(ROOT)))
            valid.append(path)
        except (UnidentifiedImageError, OSError, ValueError):
            invalid.append(str(path.relative_to(ROOT)))
    duplicates = [v for v in hashes.values() if len(v) > 1]
    credits_path = IMG / "photo_credits.json"
    credits = json.loads(credits_path.read_text(encoding="utf-8")) if credits_path.exists() else []
    missing_credit_files = [x.get("file") for x in credits if not (STATIC / x.get("file", "")).is_file()]
    print(json.dumps({
        "raster_files": len(raster), "valid_raster_files": len(valid),
        "invalid_raster_files": invalid, "duplicate_groups": duplicates,
        "photo_credit_entries": len(credits), "missing_credit_files": missing_credit_files,
        "svg_files_remaining": len(list(IMG.rglob("*.svg"))),
    }, indent=2))
if __name__ == "__main__":
    audit()
