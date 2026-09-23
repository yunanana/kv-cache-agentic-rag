"""Markdown → 스타일 HTML → PDF.

기본 : 노션 스타일 CSS를 입힌 HTML을 headless Chrome으로 인쇄 (가독성 중심)
대체 : Chrome이 없으면 fpdf2 + 한글 TTF 로 단순 렌더링
"""

import html as html_lib
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path

import markdown
from fpdf import FPDF, FontFace
from pypdf import PdfReader

from config import DOMAIN, REPORT_AUTHOR, TECHNOLOGIES

# ── 노션 스타일 HTML ──────────────────────────────────────

RATING_CLASS = {"높음": "high", "중간": "mid", "낮음": "low", "판단 유보": "hold"}
# 열 개수별 칸 너비(%) : 8열 = 관점별 평가표, 3열 = 기술 선정표
COLUMN_WIDTHS = {8: (6, 10, 11, 7, 24.5, 11, 7, 23.5), 3: (7, 13, 80), 4: (19, 27, 30, 24)}

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
:root {
  --text: #37352f; --muted: #787774; --line: #e9e9e7; --bg-soft: #f7f6f3;
  --blue-bg: #e7f3f8; --blue: #0b6e99;
  --green-bg: #dbeddb; --green: #1c7a45; --orange-bg: #fadec9; --orange: #b45a1e;
  --red-bg: #ffe2dd; --red: #c4382e; --gray-bg: #e3e2e0;
}
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", -apple-system, sans-serif;
  color: var(--text); font-size: 10pt; line-height: 1.65; margin: 0 auto; max-width: 860px;
  word-break: keep-all; overflow-wrap: anywhere;
}
h1 { font-size: 22pt; font-weight: 700; line-height: 1.3; margin: 0 0 6px; letter-spacing: -0.02em; }
h2 {
  font-size: 14pt; font-weight: 700; margin: 26px 0 10px; padding-bottom: 6px;
  border-bottom: 1px solid var(--line); break-after: avoid;
}
h3 { font-size: 11.5pt; font-weight: 600; margin: 18px 0 6px; break-after: avoid; }
h4 { font-size: 10.5pt; font-weight: 600; margin: 14px 0 4px; color: var(--muted); break-after: avoid; }
p { margin: 6px 0; }
ul, ol { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 3px 0; }
strong { font-weight: 600; }
code { background: var(--bg-soft); border-radius: 4px; padding: 1px 4px; font-size: 90%; color: #eb5757; }

.meta {
  display: flex; flex-wrap: wrap; gap: 4px 18px; color: var(--muted); font-size: 9pt;
  padding: 10px 0 14px; border-bottom: 1px solid var(--line); margin-bottom: 8px;
}
.meta b { color: var(--text); font-weight: 600; margin-right: 4px; }

.callout {
  display: flex; gap: 10px; background: var(--blue-bg); border-radius: 6px;
  padding: 12px 16px 10px 12px; margin: 8px 0 14px; break-inside: avoid;
}
.callout .icon { font-size: 14pt; line-height: 1.4; }
.callout ul { margin: 0; padding-left: 18px; }
.callout li { margin: 4px 0; }

table {
  width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 8.4pt; line-height: 1.5;
  break-inside: auto;
}
table.fixed { table-layout: fixed; }
.keep { break-inside: avoid; page-break-inside: avoid; }
tr { break-inside: avoid; }
th {
  background: var(--bg-soft); color: var(--muted); font-weight: 600; text-align: left;
  padding: 6px 6px; border: 1px solid var(--line); font-size: 7.8pt; overflow-wrap: normal;
}
td { padding: 6px 8px; border: 1px solid var(--line); vertical-align: top; overflow: hidden; }
td.muted { color: var(--muted); white-space: nowrap; }
td.center, th.center { text-align: center; }
td.nowrap { font-weight: 500; }

.pill {
  display: inline-block; border-radius: 4px; padding: 1px 6px; font-weight: 600;
  font-size: 8.2pt; max-width: 100%; white-space: normal; word-break: keep-all; text-align: center;
}
.pill.high { background: var(--green-bg); color: var(--green); }
.pill.mid { background: var(--orange-bg); color: var(--orange); }
.pill.low { background: var(--red-bg); color: var(--red); }
.pill.hold { background: var(--gray-bg); color: var(--muted); }

h2.new-page { break-before: page; page-break-before: always; margin-top: 0; }
.references ol { padding-left: 22px; }
.references li { font-size: 8.2pt; color: var(--muted); margin: 3px 0; }
.references a, a { color: var(--muted); text-decoration: underline; text-decoration-color: #c8c7c4; }
.references a { word-break: break-all; }
"""


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables", "sane_lists"])


def _pill(text: str) -> str:
    base = text.split("(")[0].strip()
    cls = RATING_CLASS.get(base)
    return f'<span class="pill {cls}">{text}</span>' if cls else text


def _style_tables(body: str) -> str:
    """등급 열은 색 배지, 신뢰도 열은 회색 글씨, ID 열은 가운데 정렬."""
    def style_table(m: re.Match) -> str:
        table = m.group(0)
        headers = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", table, flags=re.S)]

        def style_row(rm: re.Match) -> str:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", rm.group(0), flags=re.S)
            out = []
            for i, c in enumerate(cells):
                h = headers[i] if i < len(headers) else ""
                text = c.strip()
                if "등급" in h or (text.split("(")[0].strip() in RATING_CLASS and "신뢰도" not in h):
                    out.append(f"<td>{_pill(text)}</td>")
                elif "신뢰도" in h:
                    out.append(f'<td class="muted">{text}</td>')
                elif h.endswith("ID") or h == "진영":
                    out.append(f'<td class="center">{text}</td>')
                elif h in ("기술명", "기준"):
                    out.append(f'<td class="nowrap">{text}</td>')
                else:
                    out.append(f"<td>{text}</td>")
            return "<tr>" + "".join(out) + "</tr>"

        table = re.sub(r"<tr>\s*(?:<td[^>]*>.*?</td>\s*)+</tr>", style_row, table, flags=re.S)
        # 칸 너비 고정 : 근거 요약 칸에 폭을 몰아준다
        widths = COLUMN_WIDTHS.get(len(headers))
        # 8열 평가표, 기술 선정표(진영), 시사점표(주제)
        if widths and (len(headers) == 8 or headers[:1] in (["진영"], ["주제"])):
            cols = "".join(f'<col style="width:{w}%">' for w in widths)
            table = table.replace("<table>", f'<table class="fixed"><colgroup>{cols}</colgroup>', 1)
        if len(re.findall(r"<tr>", table)) <= 9:   # 머리글 + 데이터 8행 이하
            table = f'<div class="keep">{table}</div>'
        return table

    return re.sub(r"<table>.*?</table>", style_table, body, flags=re.S)


def _decorate(body: str) -> str:
    # SUMMARY → 노션 콜아웃 박스
    body = re.sub(
        r"(<h2>SUMMARY</h2>\s*)(<ul>.*?</ul>)",
        r'\1<div class="callout"><div class="icon">💡</div><div>\2</div></div>',
        body, count=1, flags=re.S,
    )
    # REFERENCE → 작은 회색 목록 + URL 링크
    parts = re.split(r"(<h2>REFERENCE</h2>)", body, maxsplit=1)
    if len(parts) == 3:
        refs = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', parts[2])
        # REFERENCE 는 항상 새 페이지에서 시작
        body = parts[0] + '<h2 class="new-page">REFERENCE</h2>' + f'<div class="references">{refs}</div>'
    return _style_tables(body)


def _meta_block() -> str:
    items = [
        ("작성", REPORT_AUTHOR),
        ("작성일", date.today().isoformat()),
        ("평가 대상", " vs ".join(t["name"].split(" (")[0] for t in TECHNOLOGIES.values())),
        ("평가 관점", "시장성 · 도메인 적용"),
        ("도메인", DOMAIN["name"]),
    ]
    return '<div class="meta">' + "".join(
        f"<span><b>{html_lib.escape(k)}</b>{html_lib.escape(v)}</span>" for k, v in items
    ) + "</div>"


def html_document(md_text: str, title: str = "KV cache 최적화 기술 다관점 평가 보고서") -> str:
    body = _decorate(md_to_html(md_text))
    # 제목(h1) 바로 아래에 메타 정보 카드 삽입
    body = re.sub(r"(</h1>)", r"\1" + _meta_block(), body, count=1)
    return (
        f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>{html_lib.escape(title)}</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


# ── Chrome 인쇄 ──────────────────────────────────────────

def _chrome_path() -> str | None:
    candidates = [
        os.getenv("CHROME_PATH", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def _finished_pages(path: Path) -> int | None:
    try:
        return len(PdfReader(str(path)).pages) if path.exists() and path.stat().st_size > 0 else None
    except Exception:  # 아직 쓰는 중인 파일
        return None


def _print_with_chrome(md_text: str, path: Path, timeout: float = 90) -> int:
    """headless Chrome으로 인쇄. 환경에 따라 PDF를 쓴 뒤에도 Chrome 보조 프로세스(업데이터 등)가
    종료되지 않는 경우가 있어, 완성된 PDF가 확인되면 프로세스 그룹을 직접 종료한다."""
    chrome = _chrome_path()
    path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "report.html"
        html_path.write_text(html_document(md_text), encoding="utf-8")
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
             "--no-default-browser-check", "--disable-background-networking", "--disable-component-update",
             f"--user-data-dir={tmp}/profile", f"--print-to-pdf={path}", html_path.as_uri()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
        deadline = time.monotonic() + timeout
        pages = None
        try:
            while time.monotonic() < deadline:
                pages = _finished_pages(path)
                if pages or proc.poll() is not None:
                    break
                time.sleep(0.5)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=10)
    pages = pages or _finished_pages(path)
    if not pages:
        raise subprocess.SubprocessError("Chrome이 PDF를 만들지 못함")
    return pages


# ── 대체 렌더러 (fpdf2) ──────────────────────────────────

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


def _pdf_safe_html(html: str) -> str:
    """fpdf2 는 표 셀 안의 중첩 태그를 지원하지 않으므로 <br>은 ' / '로, 나머지 태그는 제거."""
    def clean_cell(m: re.Match) -> str:
        inner = re.sub(r"<br\s*/?>", " / ", m.group(2))
        inner = re.sub(r"<[^>]+>", "", inner)
        return f"<{m.group(1)}>{inner}</{m.group(3)}>"
    html = re.sub(r"<(t[dh](?:\s[^>]*)?)>(.*?)</(t[dh])>", clean_cell, html, flags=re.S)

    def size_table(m: re.Match) -> str:
        table = m.group(0)
        # 8열 표는 근거 열에 폭을 더 준다
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


# ── 공개 함수 ────────────────────────────────────────────

def save_pdf(md_text: str, path: Path) -> int:
    if _chrome_path():
        try:
            return _print_with_chrome(md_text, Path(path))
        except (subprocess.SubprocessError, OSError) as e:
            print(f"[pdf] Chrome 렌더링 실패, 기본 렌더러로 대체: {e}")
    pdf = render_pdf(md_text)
    pdf.output(str(path))
    return pdf.page_no()


def count_pages(md_text: str) -> int:
    """제출 PDF와 같은 렌더러로 페이지 수를 센다 (10페이지 제한 검사용)."""
    with tempfile.TemporaryDirectory() as tmp:
        return save_pdf(md_text, Path(tmp) / "count.pdf")
