#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the system's 00_交付文档.docx from 00_交付文档.md (standard library only).

IMPORTANT: this is NOT a lab-report generator. Its styles (16/14 pt headings,
docGrid) are for the delivery document, not for the course report profile.
For lab reports use 05_Tools/build_report_docx.py.

No python-docx / lxml required. Produces OOXML directly.
"""
import os, re, zipfile, datetime
from xml.sax.saxutils import escape

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
MD = os.path.join(ROOT, "00_交付文档.md")
OUT = os.path.join(ROOT, "00_交付文档.docx")

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'

def esc(s):
    return escape(s, {'"': '&quot;'})

def run_xml(text, bold=False, italic=False, size=None, font=None, color=None, shade=None):
    if text == "":
        return ""
    props = []
    if font:
        props.append(f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>')
    if bold:
        props.append('<w:b/><w:bCs/>')
    if italic:
        props.append('<w:i/><w:iCs/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if shade:
        props.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    rpr = f'<w:rPr>{"".join(props)}</w:rPr>' if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

INLINE_RE = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))')

def inline_runs(text, base_size=None, base_font=None, bold_all=False, italic_all=False, color=None):
    out = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            out.append(run_xml(text[pos:m.start()], bold=bold_all, italic=italic_all,
                               size=base_size, font=base_font, color=color))
        tok = m.group(0)
        if tok.startswith('**') and tok.endswith('**'):
            out.append(run_xml(tok[2:-2], bold=True, italic=italic_all, size=base_size,
                               font=base_font, color=color))
        elif tok.startswith('`') and tok.endswith('`'):
            out.append(run_xml(tok[1:-1], bold=bold_all, italic=False, size=(base_size or 19),
                               font="Consolas", color="333333", shade="F2F2F2"))
        elif tok.startswith('['):
            mm = re.match(r'\[([^\]]+)\]\(([^)]+)\)', tok)
            label, url = mm.group(1), mm.group(2)
            out.append(run_xml(label, bold=bold_all, italic=italic_all, size=base_size,
                               font=base_font, color=color))
            if not url.startswith('#'):
                out.append(run_xml(f"（{url}）", bold=False, italic=False, size=(base_size or 18),
                                   font=base_font, color="595959"))
        pos = m.end()
    if pos < len(text):
        out.append(run_xml(text[pos:], bold=bold_all, italic=italic_all, size=base_size,
                           font=base_font, color=color))
    return "".join(out) if out else run_xml("", size=base_size, font=base_font)

def para(text="", style=None, align=None, first=None, left=None, hanging=None,
         before=None, after=None, line=None, keep_next=False, page_break_before=False,
         border_bottom=None, shade=None, base_size=None, base_font=None,
         bold_all=False, italic_all=False, color=None, runs=None):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next: ppr.append('<w:keepNext/><w:keepLines/>')
    if page_break_before: ppr.append('<w:pageBreakBefore/>')
    if border_bottom:
        ppr.append(f'<w:pBdr><w:bottom w:val="single" w:sz="{border_bottom}" w:space="6" w:color="999999"/></w:pBdr>')
    if shade:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    sp = []
    if before is not None: sp.append(f'w:before="{before}"')
    if after is not None: sp.append(f'w:after="{after}"')
    if line is not None: sp.append(f'w:line="{line}" w:lineRule="auto"')
    if sp: ppr.append(f'<w:spacing {" ".join(sp)}/>')
    ind = []
    if first is not None: ind.append(f'w:firstLine="{first}"')
    if left is not None: ind.append(f'w:left="{left}"')
    if hanging is not None: ind.append(f'w:hanging="{hanging}"')
    if ind: ppr.append(f'<w:ind {" ".join(ind)}/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr_xml = f'<w:pPr>{"".join(ppr)}</w:pPr>' if ppr else ""
    body = runs if runs is not None else inline_runs(text, base_size=base_size, base_font=base_font,
                                                     bold_all=bold_all, italic_all=italic_all, color=color)
    return f'<w:p>{ppr_xml}{body}</w:p>'

def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

def table_xml(rows, ncols):
    size = 18 if ncols <= 5 else (17 if ncols <= 7 else 16)  # half-points
    total = 9300
    # estimate content width and distribute proportionally (min 650 twips)
    def vlen(s):
        s = re.sub(r'\*\*|`', '', s)
        return sum(2 if ord(ch) > 127 else 1 for ch in s)
    maxlens = []
    for c in range(ncols):
        m = 0
        for r in rows:
            if c < len(r):
                m = max(m, vlen(r[c]))
        maxlens.append(max(1, min(60, m)))
    weights = [x ** 0.65 for x in maxlens]
    minw = 650
    remain = total - minw * ncols
    if remain < 0:
        minw = total // ncols
        remain = 0
    widths = [minw + int(remain * w / sum(weights)) for w in weights]
    widths[-1] += total - sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
               '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
               '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '</w:tblBorders>')
    tblpr = (f'<w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/>'
             f'{borders}<w:tblLayout w:type="fixed"/>'
             f'<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="60" w:type="dxa"/>'
             f'<w:bottom w:w="40" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar>'
             f'</w:tblPr>')
    out = [f'<w:tbl>{tblpr}<w:tblGrid>{grid}</w:tblGrid>']
    for ri, row in enumerate(rows):
        is_header = (ri == 0)
        trpr = '<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if is_header else '<w:trPr><w:cantSplit/></w:trPr>'
        out.append(f'<w:tr>{trpr}')
        cells = row + [''] * (ncols - len(row))
        for ci, cell in enumerate(cells[:ncols]):
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="DCE6F1"/>' if is_header else ''
            tcpr = (f'<w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shd}'
                    '<w:vAlign w:val="center"/></w:tcPr>')
            # header bottom border
            if is_header:
                ppr_extra = ('<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="000000"/></w:pBdr>')
            else:
                ppr_extra = ''
            cell_para = (f'<w:p><w:pPr><w:pStyle w:val="TableText"/>{ppr_extra}'
                         '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
                         '<w:jc w:val="left"/></w:pPr>'
                         f'{inline_runs(cell, base_size=size, base_font=None, bold_all=is_header)}</w:p>')
            out.append(f'<w:tc>{tcpr}{cell_para}</w:tc>')
        out.append('</w:tr>')
    out.append('</w:tbl>')
    return "".join(out)

def parse_table(lines, i):
    # lines[i] is header row; returns rows, next index
    rows = []
    def cells(line):
        s = line.strip()
        if s.startswith('|'): s = s[1:]
        if s.endswith('|'): s = s[:-1]
        return [c.strip() for c in s.split('|')]
    header = cells(lines[i])
    rows.append(header)
    i += 1
    if i < len(lines) and re.match(r'^\s*\|?\s*:?-{2,}', lines[i]):
        i += 1
    while i < len(lines) and lines[i].strip().startswith('|'):
        rows.append(cells(lines[i]))
        i += 1
    return rows, i

def build_body(md_lines):
    out = []
    i = 0
    in_code = False
    code_lines = []
    started = False
    while i < len(md_lines):
        line = md_lines[i]
        stripped = line.strip()

        if stripped.startswith('```'):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                # flush code block
                out.append(para(runs='', after=0, before=60))
                for cl in code_lines:
                    out.append(para(runs=run_xml(cl if cl else " ", size=18, font="Consolas", color="333333"),
                                    style="Code", after=0, before=0, line=240, shade="F5F5F5"))
                out.append(para(runs='', after=80, before=0))
                in_code = False
            i += 1
            continue
        if in_code:
            code_lines.append(line.rstrip('\n'))
            i += 1
            continue

        if not started:
            if stripped.startswith('## '):
                started = True
            else:
                i += 1
                continue

        if stripped == '':
            i += 1
            continue

        # headings
        m = re.match(r'^(#{1,4})\s+(.*)$', stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            style = f'Heading{min(level,4)}'
            out.append(para(text, style=style, keep_next=True))
            i += 1
            continue

        # horizontal rule
        if re.match(r'^-{3,}$', stripped):
            out.append(para(runs='', border_bottom=6, before=60, after=60))
            i += 1
            continue

        # table
        if stripped.startswith('|') and i + 1 < len(md_lines):
            rows, ni = parse_table(md_lines, i)
            if len(rows) >= 2:
                ncols = max(len(r) for r in rows)
                out.append(para(runs='', after=0, before=40))
                out.append(table_xml(rows, ncols))
                out.append(para(runs='', after=80, before=0))
                i = ni
                continue

        # blockquote
        if stripped.startswith('> '):
            out.append(para(stripped[2:], style="Quote"))
            i += 1
            continue

        # numbered list
        m = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m:
            out.append(para(f"{m.group(1)}. {m.group(2)}", style="ListParagraph",
                            left=420, hanging=300, after=40))
            i += 1
            continue

        # checkbox list
        m = re.match(r'^[-*]\s+\[([ xX])\]\s+(.*)$', stripped)
        if m:
            mark = "☑" if m.group(1).lower() == 'x' else "□"
            out.append(para(f"{mark} {m.group(2)}", style="ListParagraph",
                            left=420, hanging=300, after=40))
            i += 1
            continue

        # bullet / nested bullet
        m = re.match(r'^(\s*)[-*]\s+(.*)$', line)
        if m:
            indent = len(m.group(1))
            left = 420 + (210 if indent >= 2 else 0)
            mark = "–" if indent >= 2 else "•"
            out.append(para(f"{mark} {m.group(2)}", style="ListParagraph",
                            left=left, hanging=210, after=30))
            i += 1
            continue

        # body paragraph
        out.append(para(stripped, style="BodyText", first=420, after=60))
        i += 1
    return "".join(out)

def cover_xml():
    parts = []
    parts.append(para(runs='', after=2200))
    parts.append(para("个人科研 AI 工作系统", align="center", base_size=24, color="595959", after=240))
    parts.append(para("交付文档", style="CoverTitle", align="center", after=180))
    parts.append(para("高分子物理实验版", align="center", base_size=32, base_font="宋体", after=120))
    parts.append(para("写作风格与初稿 → 终稿改稿规律", align="center", base_size=24, color="595959", after=300))
    parts.append(para(runs='', border_bottom=6, before=120, after=240))
    parts.append(para("版本 1.3　|　2026-10-26", align="center", base_size=21, after=120))
    parts.append(para("适用：华南理工大学前沿软物质学院《高分子物理实验》2026（第 1 组）", align="center", base_size=20, after=80))
    parts.append(para("依据：历史项目 8 份报告、课程讲义、空白模板、个人提示词与交付说明（原始材料不在包内）", align="center", base_size=20, color="595959", after=80))
    parts.append(para("1.3 新增：标准三线表硬性规则 + 生成器审计；1.2 新增：冷启动/起草/全文范例/生成器/人工闸门/污染检查", align="center", base_size=19, color="595959", after=600))
    parts.append(para("本文件整理自工作区历史材料，未修改任何现有实验报告。", align="center", base_size=20, color="7F7F7F", after=120))
    parts.append(page_break())
    return "".join(parts)

def toc_xml(headings):
    out = [para("目录", style="Heading1", align="left", before=0, after=120)]
    out.append(para("（按章节顺序排列；页码见页脚）", base_size=18, color="7F7F7F", after=140))
    for h in headings:
        out.append(para(h, style="TOCEntry", left=0, after=40))
    out.append(page_break())
    return "".join(out)

def main():
    with open(MD, 'r', encoding='utf-8') as f:
        md = f.read().replace('\r\n', '\n')
    lines = md.split('\n')

    # collect level-2 headings for TOC, skipping the title metadata
    headings = []
    for line in lines:
        m = re.match(r'^##\s+(.*)$', line.strip())
        if m:
            headings.append(m.group(1).strip())

    body = build_body(lines)

    doc = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document {W} {R}><w:body>
{cover_xml()}
{toc_xml(headings)}
{body}
<w:sectPr>
<w:headerReference w:type="default" r:id="rId3"/>
<w:footerReference w:type="default" r:id="rId4"/>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1247" w:right="1219" w:bottom="1134" w:left="1332" w:header="708" w:footer="708" w:gutter="0"/>
<w:cols w:space="708"/>
<w:titlePg/>
<w:docGrid w:linePitch="360"/>
</w:sectPr>
</w:body></w:document>'''

    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {W}>
<w:docDefaults>
<w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/>
<w:sz w:val="21"/><w:szCs w:val="21"/>
<w:lang w:val="en-US" w:eastAsia="zh-CN" w:bidi="ar-SA"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="0"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="0"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="60"/><w:jc w:val="both"/></w:pPr>
<w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="CoverTitle"><w:name w:val="Cover Title"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="0" w:after="180"/><w:jc w:val="center"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:b/><w:sz w:val="56"/><w:szCs w:val="56"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="360" w:after="180"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="300" w:after="140"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="100"/><w:outlineLvl w:val="3"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:b/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="BodyText"/><w:qFormat/>
<w:pPr><w:spacing w:line="340" w:lineRule="auto" w:after="40"/><w:ind w:left="420" w:hanging="210"/></w:pPr>
<w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="TOCEntry"><w:name w:val="TOC Entry"/><w:basedOn w:val="BodyText"/><w:qFormat/>
<w:pPr><w:spacing w:line="320" w:lineRule="auto" w:after="20"/><w:ind w:left="0" w:firstLine="0"/></w:pPr>
<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0" w:before="0"/><w:ind w:left="200" w:firstLine="0"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="宋体" w:cs="Consolas"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0" w:before="0"/><w:ind w:firstLine="0"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="BodyText"/><w:qFormat/>
<w:pPr><w:spacing w:line="320" w:lineRule="auto" w:after="60"/><w:ind w:left="420" w:firstLine="0"/></w:pPr>
<w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
</w:styles>'''

    settings = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings {W}><w:zoom w:percent="100"/><w:defaultTabStop w:val="420"/>
<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
<w:updateFields w:val="true"/></w:settings>'''

    header = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr {W}><w:p><w:pPr><w:pStyle w:val="Normal"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="4" w:color="BFBFBF"/></w:pBdr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:sz w:val="18"/><w:szCs w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve">个人科研 AI 工作系统 · 交付文档</w:t></w:r></w:p></w:hdr>'''

    footer = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr {W}><w:p><w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:sz w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve">第 </w:t></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:sz w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve"> 页 / 共 </w:t></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> NUMPAGES </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:sz w:val="18"/><w:color w:val="595959"/></w:rPr><w:t xml:space="preserve"> 页</w:t></w:r></w:p></w:ftr>'''

    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>个人科研 AI 工作系统交付文档（高分子物理实验版）</dc:title><dc:creator>Qoder</dc:creator><cp:lastModifiedBy>Qoder</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
<dc:subject>科研 AI 工作系统 / 高分子物理实验报告</dc:subject><dc:description>基于工作区 8 份报告、课程讲义与交付说明整理</dc:description>
</cp:coreProperties>'''

    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<Application>Qoder</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop><Company></Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion></Properties>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''

    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', doc)
        z.writestr('word/_rels/document.xml.rels', doc_rels)
        z.writestr('word/styles.xml', styles)
        z.writestr('word/settings.xml', settings)
        z.writestr('word/header1.xml', header)
        z.writestr('word/footer1.xml', footer)
        z.writestr('docProps/core.xml', core)
        z.writestr('docProps/app.xml', app)

    # validate zip and XML
    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        assert bad is None, f"zip bad: {bad}"
        for n in z.namelist():
            if n.endswith('.xml') or n.endswith('.rels'):
                import xml.etree.ElementTree as ET
                ET.fromstring(z.read(n))
    print("OK", OUT, os.path.getsize(OUT), "bytes")
    print("headings", len(headings), "tables", doc.count('<w:tbl>'), "paras", doc.count('<w:p>'))

if __name__ == '__main__':
    main()
