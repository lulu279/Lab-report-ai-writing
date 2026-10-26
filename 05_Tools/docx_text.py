#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract paragraphs/tables from a DOCX using only the Python standard library.

Usage:
    python3 docx_text.py report.docx
    python3 docx_text.py report.docx --markdown out.md
    python3 docx_text.py report.docx --stats

This is a reading aid, not a DOCX renderer. Images are reported as [图片],
not extracted; open the DOCX for layout and figures.
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def p_text(p):
    return "".join(t.text or "" for t in p.iter(W + "t")).strip()


def p_style(p):
    el = p.find(W + "pPr/" + W + "pStyle")
    return el.get(W + "val", "") if el is not None else ""


def p_size(p):
    sizes = []
    for el in p.iter(W + "sz"):
        try:
            sizes.append(int(el.get(W + "val", "0")))
        except ValueError:
            pass
    return max(sizes) if sizes else 0


def cell_text(tc):
    parts = []
    for p in tc.iter(W + "p"):
        t = p_text(p)
        if t:
            parts.append(t)
    return " ".join(parts).replace("|", "\\|")


def table_rows(tbl):
    rows = []
    for tr in tbl.findall(W + "tr"):
        rows.append([cell_text(tc) for tc in tr.findall(W + "tc")])
    return rows


def heading_level(text):
    m = re.match(r"^(\d+(?:\.\d+)*)\s+\S", text)
    if not m:
        return 0
    depth = m.group(1).count(".") + 1
    return min(depth + 1, 4)


def convert(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    lines = []
    stats = {"paragraphs": 0, "tables": 0, "images": 0, "headings": 0}
    first_text = True

    for child in list(body):
        if child.tag == W + "p":
            stats["paragraphs"] += 1
            stats["images"] += len(list(child.iter(W + "drawing")))
            text = p_text(child)
            if not text:
                continue
            size = p_size(child)
            if first_text:
                lines.append("# " + text)
                stats["headings"] += 1
                first_text = False
                continue
            level = heading_level(text)
            if level:
                lines.append("")
                lines.append("#" * level + " " + text)
                stats["headings"] += 1
                continue
            if text in {"实验报告"}:
                lines.append("")
                lines.append("**" + text + "**")
                continue
            if (size and size <= 20) and re.match(r"^(图|表)\s*\d+", text) and len(text) < 120:
                lines.append("")
                lines.append("**" + text + "**")
                continue
            lines.append(text)
        elif child.tag == W + "tbl":
            stats["tables"] += 1
            rows = table_rows(child)
            if not rows:
                continue
            width = max(len(r) for r in rows)
            rows = [r + [""] * (width - len(r)) for r in rows]
            lines.append("")
            lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("|" + "|".join(["---"] * width) + "|")
            for row in rows[1:]:
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    header = [
        f"<!-- 机器转换自 {os.path.basename(path)}；版式、图片、公式以 DOCX 为准。 -->",
        "<!-- 本文件用于全文检索/仿写学习，不是提交模板。 -->",
        "",
    ]
    return "\n".join(header + lines).strip() + "\n", stats


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    md, stats = convert(path)
    if "--markdown" in sys.argv:
        i = sys.argv.index("--markdown")
        out = sys.argv[i + 1]
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)
        print("wrote", out)
    else:
        print(md)
    print(
        "stats: paragraphs={paragraphs} tables={tables} images={images} headings={headings}".format(**stats),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
