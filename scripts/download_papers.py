"""Doc Pool 논문 PDF를 arXiv에서 내려받는다 (저작권상 저장소에는 PDF를 포함하지 않음)."""

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import PAPER_DIR, TECHNOLOGIES  # noqa: E402


def download_papers() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    for tech in TECHNOLOGIES.values():
        path = PAPER_DIR / tech["file"]
        if path.exists():
            continue
        url = f"https://arxiv.org/pdf/{tech['arxiv_id']}"
        print(f"[download] {url} → {path.name}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kv-cache-report)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())


if __name__ == "__main__":
    download_papers()
