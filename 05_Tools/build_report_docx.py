#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a course lab-report DOCX from Markdown, using only the Python standard library.

Why this exists
---------------
The working system needs a report generator that can run on a plain Python 3
install (no python-docx, no lxml, no LibreOffice). This script writes OOXML
directly: cover page, headings, body text, figures with captions, three-line
tables, page numbers, A4 margins and explicit Chinese/Western fonts.

Usage
-----
    python3 build_report_docx.py report.md
    python3 build_report_docx.py report.md --out report.docx
    python3 build_report_docx.py report.md --draft
    python3 build_report_docx.py report.md --margins template   # 2.54 cm all sides
    python3 build_report_docx.py --audit report.docx

This script implements the default profile in FORMAT_PROFILE; it does NOT
inject COURSE_TEMPLATE.docx content (logo/cover placeholders). If the course
requires the exact official template, generate the DOCX then adjust it in
Word/WPS, or use the template manually.

Markdown front matter (required for a submission-ready build)
--------------------------------------------------------------
    ---
    title: 高分子物理实验报告
    experiment: 差示扫描量热法测定 PE 与 PET 的热转变
    class: 1班
    name: 张三
    student_id: 2020XXXX
    group: 第 1 组
    date: 2026.10.20
    ---

Required fields (course hard rule): experiment, class, name, student_id.
Optional: group, date (missing -> "未记录" with a warning).
Use --draft to build with 【待填】 placeholders; a draft must not be submitted.

Body syntax (subset)
--------------------
    ## 1 引言                  -> level-1 heading
    ### 2.1 实验目的           -> level-2 heading
    #### 2.1.1 ...             -> level-3 heading
    **bold**  *italic*  `code`  $inline math$
    ![图 1　样品 DSC 曲线](figures/fig1.png)   -> figure + caption
    表 1　样品与条件                              -> table caption (line before table)
    | 样品 | Tm / ℃ |
    |---|---|
    | PE | 109.0 |
    > 引用/限制句
    - 列表项
    1. 编号项
    ```text ... ```             -> code block
    $$ ... $$                   -> centered formula line (text, not OMML)
    <!-- pagebreak -->          -> page break

Images: PNG or JPEG. They are scaled to <= 15 cm wide and <= 20 cm tall.
Tables: all pipe tables are rendered as standard three-line tables (top/bottom
1.5 pt, header rule 0.75 pt, no vertical/inside borders). --audit checks this.
Formulas are rendered as centered italic text, not native Word equations.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
EMU_PER_CM = 360000
MAX_IMG_W_CM = 15.0
MAX_IMG_H_CM = 20.0
CONTENT_W_TWIPS = 9300
CN_FONT = "宋体"
EN_FONT = "Times New Roman"


# --------------------------------------------------------------------------
# low-level helpers
# --------------------------------------------------------------------------
def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def run_xml(text: str, size: int = 21, bold: bool = False, italic: bool = False,
            font_en: str = EN_FONT, font_cn: str = CN_FONT, color: str | None = None,
            underline: bool = False) -> str:
    if text == "":
        return ""
    props = [
        f'<w:rFonts w:ascii="{font_en}" w:hAnsi="{font_en}" w:eastAsia="{font_cn}" w:cs="{font_en}"/>',
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>',
    ]
    if bold:
        props.append("<w:b/><w:bCs/>")
    if italic:
        props.append("<w:i/><w:iCs/>")
    if underline:
        props.append('<w:u w:val="single"/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    return f'<w:r><w:rPr>{"".join(props)}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


INLINE_RE = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*|`[^`\n]+`|\$[^$\n]+\$)")


def inline_runs(text: str, size: int = 21, bold: bool = False, italic: bool = False,
                color: str | None = None) -> str:
    out: list[str] = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            out.append(run_xml(text[pos:m.start()], size=size, bold=bold, italic=italic, color=color))
        tok = m.group(0)
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            out.append(run_xml(tok[2:-2], size=size, bold=True, italic=italic, color=color))
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            out.append(run_xml(tok[1:-1], size=size, bold=bold, italic=True, color=color))
        elif tok.startswith("`") and tok.endswith("`"):
            out.append(run_xml(tok[1:-1], size=max(16, size - 2), bold=bold, italic=False,
                               font_en="Consolas", font_cn="宋体", color="333333"))
        elif tok.startswith("$") and tok.endswith("$"):
            out.append(run_xml(tok[1:-1], size=size, bold=bold, italic=True, color=color))
        pos = m.end()
    if pos < len(text):
        out.append(run_xml(text[pos:], size=size, bold=bold, italic=italic, color=color))
    return "".join(out)


def para(text: str = "", style: str = "BodyText", align: str | None = None,
         first: int | None = None, left: int | None = None, hanging: int | None = None,
         before: int | None = None, after: int | None = None, line: int | None = None,
         keep_next: bool = False, page_break_before: bool = False,
         border_bottom: int | None = None, shade: str | None = None,
         size: int = 21, bold: bool = False, italic: bool = False,
         color: str | None = None, runs: str | None = None) -> str:
    ppr: list[str] = [f'<w:pStyle w:val="{style}"/>']
    if keep_next:
        ppr.append("<w:keepNext/><w:keepLines/>")
    if page_break_before:
        ppr.append("<w:pageBreakBefore/>")
    if border_bottom:
        ppr.append(f'<w:pBdr><w:bottom w:val="single" w:sz="{border_bottom}" w:space="4" w:color="000000"/></w:pBdr>')
    if shade:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    sp: list[str] = []
    if before is not None:
        sp.append(f'w:before="{before}"')
    if after is not None:
        sp.append(f'w:after="{after}"')
    if line is not None:
        sp.append(f'w:line="{line}" w:lineRule="auto"')
    if sp:
        ppr.append(f'<w:spacing {" ".join(sp)}/>')
    ind: list[str] = []
    if first is not None:
        ind.append(f'w:firstLine="{first}"')
    if left is not None:
        ind.append(f'w:left="{left}"')
    if hanging is not None:
        ind.append(f'w:hanging="{hanging}"')
    if ind:
        ppr.append(f'<w:ind {" ".join(ind)}/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    body = runs if runs is not None else inline_runs(text, size=size, bold=bold, italic=italic, color=color)
    return f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>{body}</w:p>'


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


# --------------------------------------------------------------------------
# image size
# --------------------------------------------------------------------------
def image_size(path: str) -> tuple[int, int]:
    with open(path, "rb") as f:
        head = f.read(32)
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            if len(head) < 24:
                raise ValueError(f"truncated PNG: {path}")
            w, h = struct.unpack(">II", head[16:24])
            return int(w), int(h)
        if head.startswith(b"\xff\xd8"):
            f.seek(2)
            while True:
                b = f.read(1)
                if not b:
                    break
                if b != b"\xff":
                    continue
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if not marker:
                    break
                if marker[0] in (0xD8, 0xD9):
                    continue
                seg_len_b = f.read(2)
                if len(seg_len_b) < 2:
                    break
                seg_len = struct.unpack(">H", seg_len_b)[0]
                if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                                 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    data = f.read(5)
                    if len(data) < 5:
                        break
                    h, w = struct.unpack(">HH", data[1:5])
                    return int(w), int(h)
                f.seek(seg_len - 2, 1)
    raise ValueError(f"only PNG/JPEG images are supported: {path}")


def image_block(path: str, caption: str, media: list[dict], next_rid: list[int],
                image_counter: list[int]) -> str:
    w_px, h_px = image_size(path)
    if w_px <= 0 or h_px <= 0:
        raise ValueError(f"bad image size: {path}")
    w_cm = w_px / 96.0 * 2.54
    h_cm = h_px / 96.0 * 2.54
    scale = min(1.0, MAX_IMG_W_CM / w_cm, MAX_IMG_H_CM / h_cm)
    cx = int(w_cm * scale * EMU_PER_CM)
    cy = int(h_cm * scale * EMU_PER_CM)
    image_counter[0] += 1
    idx = image_counter[0]
    rid = f"rId{next_rid[0]}"
    next_rid[0] += 1
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "jpeg":
        ext = "jpg"
    media.append({"rid": rid, "path": path, "name": f"image{idx}.{ext}", "ext": ext})
    drawing = f'''<w:p><w:pPr><w:pStyle w:val="Figure"/><w:jc w:val="center"/><w:keepNext/><w:spacing w:before="120" w:after="40" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="{idx}" name="Picture {idx}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="{PIC_NS}"><pic:pic><pic:nvPicPr><pic:cNvPr id="{idx}" name="{esc(media[-1]['name'])}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
    if caption:
        return drawing + para(caption, style="Caption", align="center", size=18, line=240, after=120)
    return drawing


# --------------------------------------------------------------------------
# table
# --------------------------------------------------------------------------
def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|") for c in cells]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells)


def table_xml(rows: list[list[str]], caption: str | None = None) -> str:
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    def vlen(s: str) -> int:
        s = re.sub(r"\*\*|`|\$", "", s)
        return sum(2 if ord(ch) > 127 else 1 for ch in s)
    maxlens = [max(1, min(60, max(vlen(r[c]) for r in rows))) for c in range(ncols)]
    weights = [x ** 0.65 for x in maxlens]
    minw = 700
    remain = CONTENT_W_TWIPS - minw * ncols
    if remain < 0:
        minw = CONTENT_W_TWIPS // ncols
        remain = 0
    widths = [minw + int(remain * w / sum(weights)) for w in weights]
    widths[-1] += CONTENT_W_TWIPS - sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
               '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
               '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '</w:tblBorders>')
    tblpr = (f'<w:tblPr><w:tblW w:w="{CONTENT_W_TWIPS}" w:type="dxa"/><w:jc w:val="center"/>'
             f'{borders}<w:tblLayout w:type="fixed"/>'
             '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
             '<w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'
             '</w:tblPr>')
    out = [f'<w:tbl>{tblpr}<w:tblGrid>{grid}</w:tblGrid>']
    for ri, row in enumerate(rows):
        header = ri == 0
        trpr = '<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if header else '<w:trPr><w:cantSplit/></w:trPr>'
        out.append(f"<w:tr>{trpr}")
        for ci, cell in enumerate(row[:ncols]):
            tc_borders = ""
            if header:
                tc_borders = ('<w:tcBorders><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
                              '</w:tcBorders>')
            tcpr = (f'<w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{tc_borders}'
                    '<w:vAlign w:val="center"/></w:tcPr>')
            cell_para = (f'<w:p><w:pPr><w:pStyle w:val="TableText"/><w:spacing w:before="0" w:after="0" '
                         'w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
                         f'{inline_runs(cell, size=18, bold=header)}</w:p>')
            out.append(f"<w:tc>{tcpr}{cell_para}</w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    prefix = ""
    if caption:
        prefix = para(caption, style="TableCaption", align="center", size=18, line=240,
                      before=120, after=40, keep_next=True)
    return prefix + "".join(out) + para(runs="", style="BodyText", after=80, before=0, line=240, first=0)


# --------------------------------------------------------------------------
# front matter + body parser
# --------------------------------------------------------------------------
REQUIRED = ["experiment", "class", "name", "student_id"]
OPTIONAL = ["group", "date"]


def parse_front_matter(lines: list[str]) -> tuple[dict, list[str]]:
    meta: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = lines[i + 1:]
                for line in lines[1:i]:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
                return meta, body
    return meta, lines


def is_placeholder(value: str) -> bool:
    v = (value or "").strip()
    return v == "" or "待填" in v or "XXX" in v.upper() or v in {"待定", "TBD"}


def cover_xml(meta: dict, draft: bool) -> str:
    missing = [k for k in REQUIRED if is_placeholder(meta.get(k, ""))]
    if missing and not draft:
        raise SystemExit(
            "封面四项缺失： " + ", ".join(missing) +
            "\n请先填 00_START/COVER_FIELDS.md，或使用 --draft 仅生成草稿。"
        )
    optional_missing = [k for k in OPTIONAL if is_placeholder(meta.get(k, ""))]
    if optional_missing:
        print("WARN: 封面可选字段未填，写“未记录”： " + ", ".join(optional_missing))
    def val(k: str) -> str:
        v = meta.get(k, "").strip()
        if is_placeholder(v):
            return "【待填】" if k in REQUIRED else "未记录"
        return v
    title = meta.get("title", "高分子物理实验报告").strip() or "高分子物理实验报告"
    parts = [
        para(title, style="CoverTitle", align="center", size=32, bold=True, line=360, after=120),
        para(val("experiment"), style="CoverSubtitle", align="center", size=28, line=360, after=480),
        para(f'班级：{val("class")}', style="CoverInfo", align="center", size=24, line=360, after=80),
        para(f'姓名：{val("name")}', style="CoverInfo", align="center", size=24, line=360, after=80),
        para(f'学号：{val("student_id")}', style="CoverInfo", align="center", size=24, line=360, after=80),
        para(f'组别：{val("group")}', style="CoverInfo", align="center", size=24, line=360, after=80),
        para(f'实验日期：{val("date")}', style="CoverInfo", align="center", size=24, line=360, after=80),
        page_break(),
    ]
    if missing:
        parts.insert(0, para("【草稿：封面字段未填全，不得提交】", style="CoverInfo", align="center",
                             size=21, color="C00000", line=300, after=120))
    return "".join(parts)


def parse_body(lines: list[str], media: list[dict], next_rid: list[int],
               image_counter: list[int], docx_dir: str, warnings: list[str]) -> str:
    out: list[str] = []
    buf: list[str] = []
    i = 0
    pending_table_caption: str | None = None
    in_refs = False

    def flush() -> None:
        nonlocal buf
        if buf:
            text = "".join(buf).strip()
            if text:
                if in_refs:
                    out.append(para(text, style="Reference", size=18, line=240,
                                    left=420, hanging=420, after=40))
                else:
                    out.append(para(text, style="BodyText", size=21, line=360, first=420, after=60))
            buf = []

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if s == "":
            flush()
            i += 1
            continue

        if s.startswith("<!--"):
            flush()
            if "pagebreak" in s.lower():
                out.append(page_break())
            i += 1
            continue

        if s == "---":
            flush()
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush()
            level = len(m.group(1))
            text = m.group(2).strip()
            in_refs = text in {"参考文献", "References", "参考书目"}
            if level == 1:
                out.append(para(text, style="Heading1", size=24, bold=True, line=360,
                                before=240, after=120, keep_next=True))
            elif level == 2:
                out.append(para(text, style="Heading1", size=24, bold=True, line=360,
                                before=240, after=120, keep_next=True))
            elif level == 3:
                out.append(para(text, style="Heading2", size=24, bold=True, line=360,
                                before=180, after=90, keep_next=True))
            else:
                out.append(para(text, style="Heading3", size=21, bold=True, line=360,
                                before=120, after=60, keep_next=True))
            i += 1
            continue

        m = re.match(r"^!\[(.*?)\]\((.*?)\)\s*$", s)
        if m:
            flush()
            caption, rel = m.group(1).strip(), m.group(2).strip()
            path = rel if os.path.isabs(rel) else os.path.normpath(os.path.join(docx_dir, rel))
            if not os.path.exists(path):
                warnings.append(f"图片不存在：{rel}")
                out.append(para(f"【缺图：{rel}】", style="Caption", align="center", size=18, color="C00000"))
            else:
                out.append(image_block(path, caption, media, next_rid, image_counter))
            i += 1
            continue

        if s.startswith("```"):
            flush()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            for cl in code:
                out.append(para(runs=run_xml(cl if cl else " ", size=18, font_en="Consolas",
                                             font_cn="宋体", color="333333"),
                                style="Code", line=240, after=0, before=0, left=200, shade="F2F2F2"))
            out.append(para(runs="", style="BodyText", after=40, before=0, line=240, first=0))
            continue

        if s.startswith("$$"):
            flush()
            rest = s[2:]
            formula: list[str] = []
            if rest.strip().endswith("$$"):
                formula.append(rest.strip()[:-2].strip())
                i += 1
            else:
                if rest.strip():
                    formula.append(rest.strip())
                i += 1
                while i < len(lines):
                    cur = lines[i].strip()
                    if cur.endswith("$$"):
                        formula.append(cur[:-2].strip())
                        i += 1
                        break
                    formula.append(cur)
                    i += 1
            out.append(para(" ".join(x for x in formula if x), style="Formula", align="center", size=21,
                            italic=True, line=360, before=80, after=80))
            continue

        if s.startswith("> "):
            flush()
            out.append(para(s[2:].strip(), style="Quote", size=21, italic=True, line=340,
                            left=420, after=60))
            i += 1
            continue

        if s.startswith("|"):
            flush()
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not is_separator(lines[i]):
                    rows.append(split_row(lines[i]))
                i += 1
            if rows:
                out.append(table_xml(rows, pending_table_caption))
                if not pending_table_caption:
                    warnings.append("表格缺少表题（表 N　…）")
            pending_table_caption = None
            continue

        if re.match(r"^表\s*\d+", s):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip().startswith("|"):
                flush()
                pending_table_caption = s
                i += 1
                continue

        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            flush()
            out.append(para("• " + m.group(1), style="ListParagraph", size=21, line=340,
                            left=420, hanging=210, after=40))
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            flush()
            out.append(para(f"{m.group(1)}. {m.group(2)}", style="ListParagraph", size=21,
                            line=340, left=420, hanging=210, after=40))
            i += 1
            continue

        buf.append(line)
        i += 1

    flush()
    return "".join(out)


# --------------------------------------------------------------------------
# package parts
# --------------------------------------------------------------------------
def styles_xml() -> str:
    def style(sid: str, name: str, size: int, bold: bool = False, italic: bool = False,
              align: str | None = None, before: int = 0, after: int = 0, line: int = 360,
              first: int = 0, left: int = 0, hanging: int = 0, color: str | None = None,
              keep_next: bool = False, outline: int | None = None) -> str:
        ppr = [f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>']
        if first:
            ppr.append(f'<w:ind w:firstLine="{first}"/>')
        if left or hanging:
            ppr.append(f'<w:ind w:left="{left}" w:hanging="{hanging}"/>')
        if align:
            ppr.append(f'<w:jc w:val="{align}"/>')
        if keep_next:
            ppr.append("<w:keepNext/><w:keepLines/>")
        if outline is not None:
            ppr.append(f'<w:outlineLvl w:val="{outline}"/>')
        rpr = [f'<w:rFonts w:ascii="{EN_FONT}" w:hAnsi="{EN_FONT}" w:eastAsia="{CN_FONT}" w:cs="{EN_FONT}"/>',
               f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>']
        if bold:
            rpr.append("<w:b/><w:bCs/>")
        if italic:
            rpr.append("<w:i/><w:iCs/>")
        if color:
            rpr.append(f'<w:color w:val="{color}"/>')
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
                f'<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr>{"".join(ppr)}</w:pPr>'
                f'<w:rPr>{"".join(rpr)}</w:rPr></w:style>')
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="{EN_FONT}" w:hAnsi="{EN_FONT}" w:eastAsia="{CN_FONT}" w:cs="{EN_FONT}"/>
<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US" w:eastAsia="zh-CN" w:bidi="ar-SA"/>
</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:widowControl/><w:snapToGrid w:val="0"/><w:spacing w:line="360" w:lineRule="auto" w:after="0"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:widowControl/><w:snapToGrid w:val="0"/><w:spacing w:line="360" w:lineRule="auto" w:after="0"/></w:pPr><w:rPr><w:rFonts w:ascii="{EN_FONT}" w:hAnsi="{EN_FONT}" w:eastAsia="{CN_FONT}" w:cs="{EN_FONT}"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>
{style("BodyText","Body Text",21,align="both",after=60,line=360,first=420)}
{style("Heading1","heading 1",24,bold=True,before=240,after=120,line=360,keep_next=True,outline=0)}
{style("Heading2","heading 2",24,bold=True,before=180,after=90,line=360,keep_next=True,outline=1)}
{style("Heading3","heading 3",21,bold=True,before=120,after=60,line=360,keep_next=True,outline=2)}
{style("CoverTitle","Cover Title",32,bold=True,align="center",after=120,line=360)}
{style("CoverSubtitle","Cover Subtitle",28,align="center",after=480,line=360)}
{style("CoverInfo","Cover Info",24,align="center",after=80,line=360)}
{style("Caption","Caption",18,align="center",before=40,after=120,line=240)}
{style("TableCaption","Table Caption",18,align="center",before=120,after=40,line=240,keep_next=True)}
{style("TableText","Table Text",18,line=240)}
{style("Figure","Figure",21,align="center",before=120,after=40,line=240,keep_next=True)}
{style("ListParagraph","List Paragraph",21,after=40,line=340,left=420,hanging=210)}
{style("Code","Code",18,line=240,left=200)}
{style("Quote","Quote",21,italic=True,align="both",after=60,line=340,left=420,color="595959")}
{style("Reference","Reference",18,line=240,left=420,hanging=420,after=40)}
{style("Formula","Formula",21,italic=True,align="center",before=80,after=80,line=360)}
</w:styles>'''


def header_xml(text: str = "") -> str:
    if not text:
        return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr xmlns:w="{W_NS}"><w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr></w:p></w:hdr>'
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{W_NS}"><w:p><w:pPr><w:pStyle w:val="Normal"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="4" w:color="BFBFBF"/></w:pBdr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="{EN_FONT}" w:hAnsi="{EN_FONT}" w:eastAsia="{CN_FONT}"/><w:sz w:val="18"/><w:szCs w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p></w:hdr>'''


def footer_xml(page: bool = True) -> str:
    if not page:
        return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{W_NS}"><w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr></w:p></w:ftr>'
    def r(text: str) -> str:
        return (f'<w:r><w:rPr><w:rFonts w:ascii="{EN_FONT}" w:hAnsi="{EN_FONT}" w:eastAsia="{CN_FONT}"/>'
                f'<w:sz w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>')
    def field(instr: str) -> str:
        return (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{W_NS}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
            + r("第 ") + field("PAGE") + r(" 页 / 共 ") + field("NUMPAGES") + r(" 页") + "</w:p></w:ftr>")


def document_xml(body: str, margins: str = "default") -> str:
    if margins == "template":
        top = right = bottom = left = 1440  # official template: 2.54 cm all sides
    else:
        top, right, bottom, left = 1247, 1219, 1134, 1332  # DSC/IR default
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}"><w:body>
{body}
<w:sectPr>
<w:headerReference w:type="default" r:id="rId3"/><w:footerReference w:type="default" r:id="rId4"/>
<w:headerReference w:type="first" r:id="rId5"/><w:footerReference w:type="first" r:id="rId6"/>
<w:titlePg/>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}" w:left="{left}" w:header="708" w:footer="708" w:gutter="0"/>
<w:cols w:space="708"/>
</w:sectPr></w:body></w:document>'''


def settings_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}"><w:zoom w:percent="100"/><w:defaultTabStop w:val="420"/>
<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
<w:updateFields w:val="true"/></w:settings>'''


def content_types(media: list[dict]) -> str:
    defaults = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                '<Default Extension="xml" ContentType="application/xml"/>']
    exts = {m["ext"] for m in media}
    for ext in sorted(exts):
        if ext == "png":
            defaults.append('<Default Extension="png" ContentType="image/png"/>')
        elif ext in {"jpg", "jpeg"}:
            defaults.append('<Default Extension="jpg" ContentType="image/jpeg"/>')
    overrides = [
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>',
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>',
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>',
        '<Override PartName="/word/header2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>',
        '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{"".join(defaults + overrides)}</Types>')


def core_xml(meta: dict) -> str:
    now = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    title = esc(meta.get("experiment", "高分子物理实验报告"))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>{title}</dc:title><dc:creator>Qoder (AI-assisted)</dc:creator><cp:lastModifiedBy>student</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
<dc:subject>高分子物理实验报告</dc:subject><dc:description>由 build_report_docx.py 生成；学生需确认内容、数值与署名。</dc:description>
</cp:coreProperties>'''


def app_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Qoder</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion></Properties>'''


def package(meta: dict, body: str, media: list[dict], out: str, margins: str = "default") -> None:
    doc_rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>',
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>',
        '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
        '<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header2.xml"/>',
        '<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer2.xml"/>',
    ]
    for m in media:
        doc_rels.append(f'<Relationship Id="{m["rid"]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{m["name"]}"/>')
    doc_rels_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(doc_rels)}</Relationships>')
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    header_text = f"高分子物理实验报告　{meta.get('experiment', '')}".strip()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(media))
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document_xml(body, margins))
        z.writestr("word/_rels/document.xml.rels", doc_rels_xml)
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/settings.xml", settings_xml())
        z.writestr("word/header1.xml", header_xml(header_text))
        z.writestr("word/footer1.xml", footer_xml(True))
        z.writestr("word/header2.xml", header_xml(""))
        z.writestr("word/footer2.xml", footer_xml(False))
        z.writestr("docProps/core.xml", core_xml(meta))
        z.writestr("docProps/app.xml", app_xml())
        for m in media:
            with open(m["path"], "rb") as f:
                z.writestr(f'word/media/{m["name"]}', f.read())


# --------------------------------------------------------------------------
# validation / audit
# --------------------------------------------------------------------------
def audit(path: str, strict: bool = True) -> int:
    print(f"audit: {path}" + (" (strict)" if strict else " (draft-tolerant)"))
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print("  FAIL: not a zip/DOCX:", e)
        return 1
    bad = z.testzip()
    if bad:
        print("  FAIL: bad zip member:", bad)
        return 1
    xml_bad = 0
    for n in z.namelist():
        if n.endswith(".xml") or n.endswith(".rels"):
            try:
                ET.fromstring(z.read(n))
            except Exception as e:
                print("  FAIL XML:", n, e)
                xml_bad += 1
    doc = z.read("word/document.xml").decode("utf-8")
    media = [n for n in z.namelist() if n.startswith("word/media/")]
    tables = doc.count("<w:tbl>")
    drawings = doc.count("<w:drawing>")
    paras = doc.count("<w:p>")
    theme = doc.count("themeFont") + z.read("word/styles.xml").decode("utf-8").count("themeFont")
    print(f"  media={len(media)} tables={tables} drawings={drawings} paragraphs={paras} themeFont={theme}")
    table_blocks = re.findall(r"<w:tbl>.*?</w:tbl>", doc, re.S)
    bad_tables = 0
    for idx, tbl in enumerate(table_blocks, 1):
        borders = re.search(r"<w:tblBorders>.*?</w:tblBorders>", tbl, re.S)
        b = borders.group(0) if borders else ""
        standard = all(x in b for x in (
            'w:top w:val="single" w:sz="12"',
            'w:bottom w:val="single" w:sz="12"',
            'w:left w:val="none"',
            'w:right w:val="none"',
            'w:insideH w:val="none"',
            'w:insideV w:val="none"',
        )) and ('<w:tcBorders><w:bottom w:val="single" w:sz="6"' in tbl)
        if not standard:
            print(f"  FAIL: table {idx} is not a standard three-line table")
            bad_tables += 1
    if table_blocks:
        print(f"  three_line_tables={len(table_blocks) - bad_tables}/{len(table_blocks)}")
    if bad_tables:
        xml_bad += bad_tables
    m = re.search(r'<w:pgMar w:top="(\d+)" w:right="(\d+)" w:bottom="(\d+)" w:left="(\d+)"', doc)
    if m:
        print(f"  margins twips top/right/bottom/left={m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}")
    text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", doc, re.S))
    placeholder_hit = False
    for kw in ("【待填】", "【待核", "【缺图", "TODO", "待补"):
        if kw in text:
            print(f"  WARN: placeholder found: {kw}")
            placeholder_hit = True
    try:
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        rel_map = {r.get("Id"): r.get("Target") for r in rels}
        for rid in re.findall(r'r:embed="(rId\d+)"', doc):
            target = rel_map.get(rid)
            if not target:
                print(f"  FAIL: image relationship {rid} missing")
                xml_bad += 1
            elif f"word/{target}" not in z.namelist():
                print(f"  FAIL: image target missing: word/{target}")
                xml_bad += 1
        referenced = set(re.findall(r'Target="media/([^"]+)"', z.read("word/_rels/document.xml.rels").decode("utf-8")))
        for m in media:
            if m.split("word/media/")[-1] not in referenced:
                print(f"  WARN: media not referenced: {m}")
    except Exception as e:
        print("  FAIL: cannot check image relationships:", e)
        xml_bad += 1
    if theme:
        print("  WARN: theme font references found")
    if xml_bad:
        return 1
    if placeholder_hit and strict:
        print("  FAIL: placeholders remain; not submission-ready")
        return 1
    print("  OK" + (" (draft)" if placeholder_hit else ""))
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Build a lab-report DOCX from Markdown (stdlib only).")
    ap.add_argument("input", nargs="?", help="input Markdown file")
    ap.add_argument("--out", help="output DOCX path")
    ap.add_argument("--draft", action="store_true", help="allow missing cover fields; inserts 【待填】")
    ap.add_argument("--margins", choices=["default", "template"], default="default",
                    help="default = DSC/IR margins; template = official template 2.54 cm all sides")
    ap.add_argument("--audit", metavar="DOCX", help="audit an existing DOCX and exit")
    args = ap.parse_args()

    if args.audit:
        return audit(args.audit, strict=True)
    if not args.input:
        ap.print_help()
        return 2

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.read().replace("\r\n", "\n").split("\n")
    meta, body_lines = parse_front_matter(lines)
    media: list[dict] = []
    next_rid = [7]
    image_counter = [0]
    warnings: list[str] = []
    body = cover_xml(meta, args.draft) + parse_body(
        body_lines, media, next_rid, image_counter, os.path.dirname(os.path.abspath(args.input)), warnings
    )
    out = args.out or (os.path.splitext(args.input)[0] + ".docx")
    package(meta, body, media, out, args.margins)
    print("wrote", out)
    if warnings:
        print("warnings:")
        for w in warnings:
            print("  -", w)
    return audit(out, strict=not args.draft)


if __name__ == "__main__":
    raise SystemExit(main())
