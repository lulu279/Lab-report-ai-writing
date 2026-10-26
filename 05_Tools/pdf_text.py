#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from a PDF with pypdf (host Python).

Usage:
    python3 pdf_text.py file.pdf
    python3 pdf_text.py file.pdf --pages 1-5
    python3 pdf_text.py file.pdf --out out.txt

Requires pypdf (available on the host Python 3.14 in this project).
"""
import argparse
import sys


def parse_pages(spec: str, n: int) -> list[int]:
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, min(int(b), n)))
        elif part:
            out.append(int(part) - 1)
    return [i for i in out if 0 <= i < n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="", help="e.g. 1-5 or 1,3,7")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    try:
        from pypdf import PdfReader
    except Exception as e:
        print("pypdf not available:", e, file=sys.stderr)
        return 2
    reader = PdfReader(args.pdf)
    pages = parse_pages(args.pages, len(reader.pages))
    chunks = []
    for i in pages:
        chunks.append(f"\n\n===== page {i + 1} =====\n")
        chunks.append(reader.pages[i].extract_text() or "")
    text = "".join(chunks).strip() + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
