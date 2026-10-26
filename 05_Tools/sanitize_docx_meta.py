#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anonymize DOCX core properties (creator / lastModifiedBy / description).

Usage:
    python3 sanitize_docx_meta.py report.docx
    python3 sanitize_docx_meta.py report.docx --creator "anonymized" --last "anonymized"

Rewrites only docProps/core.xml; all other parts are copied unchanged.
"""
import argparse
import re
import shutil
import zipfile
import os


def sanitize(path: str, creator: str, last: str, desc: str | None = None) -> None:
    tmp = path + ".tmp"
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                text = data.decode("utf-8")
                text = re.sub(r"<dc:creator>.*?</dc:creator>", f"<dc:creator>{creator}</dc:creator>", text, flags=re.S)
                text = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", f"<cp:lastModifiedBy>{last}</cp:lastModifiedBy>", text, flags=re.S)
                if desc is not None:
                    text = re.sub(r"<dc:description>.*?</dc:description>", f"<dc:description>{desc}</dc:description>", text, flags=re.S)
                    if "<dc:description>" not in text:
                        text = text.replace("</cp:coreProperties>", f"<dc:description>{desc}</dc:description></cp:coreProperties>")
                data = text.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--creator", default="anonymized")
    ap.add_argument("--last", default="anonymized")
    ap.add_argument("--desc", default="historical exemplar; anonymized")
    args = ap.parse_args()
    if not os.path.exists(args.docx):
        print("not found:", args.docx)
        return 2
    sanitize(args.docx, args.creator, args.last, args.desc)
    print("sanitized", args.docx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
