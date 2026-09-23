"""Markdown → HTML → PDF (fpdf2, 한글 폰트)."""

import os
import re
from pathlib import Path

import markdown
from fpdf import FPDF, FontFace

FONT_CANDIDATES = [
    os.getenv("PDF_FONT_PATH", ""),
    "/Library/Fonts/Arial Unicode.ttf",                             # macOS
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",         # macOS
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",              # Linux (fonts-nanum)
    "C:/Windows/Fonts/malgun.ttf",                                  # Windows
]


def _font_path() -> str:
    for p in FONT_CANDIDATES:
        if p and Path(p).exists():
            return p
    raise FileNotFoundError("한글 TTF 폰트를 찾지 못함 - .env 에 PDF_FONT_PATH 지정")


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables", "sane_lists"])


def html_document(md_text: str, title: str) -> str:
    return (
        f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>{title}</title>"
        "<style>body{font-family:sans-serif;max-width:860px;margin:40px auto;line-height:1.6;padding:0 16px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:4px 8px;font-size:14px}"
        "th{background:#f0f0f0}</style></head><body>" + md_to_html(md_text) + "</body></html>"
    )


def _pdf_safe_html(html: str) -> str:
    """fpdf2 는 표 셀 안의 중첩 태그를 지원하지 않으므로 <br>은 ' / '로, 나머지 태그는 제거."""
    def clean_cell(m: re.Match) -> str:
        inner = re.sub(r"<br\s*/?>", " / ", m.group(2))
        inner = re.sub(r"<[^>]+>", "", inner)
        return f"<{m.group(1)}>{inner}</{m.group(3)}>"
    html = re.sub(r"<(t[dh](?:\s[^>]*)?)>(.*?)</(t[dh])>", clean_cell, html, flags=re.S)
    def size_table(m: re.Match) -> str:
        table = m.group(0)
        # Give evidence columns room; equal-width eight-column tables are unreadable.
        if len(re.findall(r"<th>", table)) == 8:
            widths = iter((5, 12, 10, 7, 24, 11, 7, 24))
            table = re.sub(r"<th>", lambda _: f'<th width="{next(widths)}%">', table)
        return table
    return re.sub(r"<table>.*?</table>", size_table, html, flags=re.S)


def render_pdf(md_text: str) -> FPDF:
    pdf = FPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(True, margin=16)
    font = _font_path()
    for style in ("", "B", "I", "BI"):
        pdf.add_font("KR", style, font)
    pdf.set_font("KR", size=10.5)
    pdf.add_page()
    pdf.write_html(
        _pdf_safe_html(md_to_html(md_text)),
        font_family="KR",
        tag_styles={
            "h1": FontFace(size_pt=16, color=(20, 40, 90)),
            "h2": FontFace(size_pt=13, color=(20, 40, 90)),
            "h3": FontFace(size_pt=11, color=(40, 60, 110)),
        },
        table_line_separators=True,
    )
    return pdf


def save_pdf(md_text: str, path: Path) -> int:
    pdf = render_pdf(md_text)
    pdf.output(str(path))
    return pdf.page_no()


def count_pages(md_text: str) -> int:
    return render_pdf(md_text).page_no()
