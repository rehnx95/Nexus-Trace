#!/usr/bin/env python3
"""
Fetch Indian Kanoon judgments and keep ONLY short, relevant excerpts
(paragraphs about phones, money, accused, FIR, etc.) so files stay small.

Setup:
    pip install requests
    export IK_TOKEN="your_token"          # Windows PowerShell: $env:IK_TOKEN="your_token"

Usage:
    python ik_fetch.py "cheating fraud mobile phone bank account" raw_files 10
                       ^ search query                ^ output dir   ^ number of docs

Then mask them:
    python mask_files.py raw_files masked_files

Cost (approx): ~Rs 0.50 per search page (10 results) + ~Rs 0.20 per document fetched.
The token is read from the IK_TOKEN environment variable. Never hardcode it or commit it.
"""
import html
import os
import re
import sys
import time
from pathlib import Path

import requests

BASE = "https://api.indiankanoon.org"
KEYWORDS = re.compile(
    r"\b(mobile|phone|call|sim|imei|account|bank|transaction|upi|cheque|transfer|"
    r"fir|accused|arrest|recovered|complainant|victim|witness|co-accused)\b",
    re.I,
)
MAX_PARAGRAPHS = 25      # per document
MAX_PARA_CHARS = 1200    # skip huge legal-citation paragraphs


def headers():
    token = os.environ.get("IK_TOKEN")
    if not token:
        sys.exit("Set the IK_TOKEN environment variable first.")
    return {"Authorization": f"Token {token}"}


def call(path, params):
    """Indian Kanoon docs show GET in places and POST in others, so try POST then GET."""
    url = f"{BASE}{path}"
    r = requests.post(url, headers=headers(), params=params, timeout=60)
    if r.status_code == 405:
        r = requests.get(url, headers=headers(), params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def html_to_paragraphs(raw_html: str):
    text = re.sub(r"(?i)<br\s*/?>|</p>|</blockquote>|</pre>", "\n", raw_html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    paras = [re.sub(r"\s+", " ", p).strip() for p in text.split("\n")]
    return [p for p in paras if len(p) > 40]


def relevant_excerpt(paras):
    keep = [p for p in paras if len(p) <= MAX_PARA_CHARS and KEYWORDS.search(p)]
    return keep[:MAX_PARAGRAPHS]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    query, out_dir = sys.argv[1], Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    out_dir.mkdir(parents=True, exist_ok=True)

    saved, page = 0, 0
    while saved < limit:
        result = call("/search/", {"formInput": query, "pagenum": page})
        docs = result.get("docs", [])
        if not docs:
            break
        for d in docs:
            if saved >= limit:
                break
            tid = d.get("tid")
            doc = call(f"/doc/{tid}/", {})
            paras = relevant_excerpt(html_to_paragraphs(doc.get("doc", "")))
            if len(paras) < 3:
                continue  # not enough useful text
            title = re.sub(r"<[^>]+>", "", d.get("title", "")).strip()
            header = f"SOURCE: Indian Kanoon doc {tid}\nTITLE: {title}\n\n"
            (out_dir / f"ik_{tid}.txt").write_text(header + "\n\n".join(paras), encoding="utf-8")
            saved += 1
            print(f"saved ik_{tid}.txt ({len(paras)} paragraphs)")
            time.sleep(1)  # be polite to the API
        page += 1

    print(f"\nDone: {saved} files in {out_dir}. Next: python mask_files.py {out_dir} masked_files")


if __name__ == "__main__":
    main()