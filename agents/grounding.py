"""결정론적 수치 근거 검사 : 논문 페이지를 인용한 문장의 수치가 실제 그 페이지 원문에 있는지 확인."""

import re

NUMBER = re.compile(r"\d+(?:\.\d+)?(?=\s*(?:%|배|x|×|GB|TB|비트|bit|초|ms))")
PAPER_CITE = re.compile(r"\[(P-SW|P-HW) p\.\s*([\d\-–,\sp.]+)\]")


def _pages(spec: str) -> set[int]:
    pages = set()
    for a, b in re.findall(r"(\d+)(?:\s*[-–]\s*(\d+))?", spec):
        lo, hi = int(a), int(b or a)
        pages.update(range(lo, hi + 1))
    return pages


def _significant(num: str) -> bool:
    # 한 자리 정수(4배, 8배 등)는 원문 어디에나 있어 검사 의미가 없으므로 제외
    return "." in num or len(num) >= 2


def unsupported_numbers(text: str, page_text) -> list[str]:
    """page_text(source_id, page) -> str. 인용 페이지(±1)에서 찾지 못한 수치 목록을 반환."""
    flagged = []
    # 문장 분리 : '마침표+공백'·줄바꿈 기준 (35.7, p.10 같은 소수점·페이지 표기는 분리하지 않음)
    # 표 셀('|')도 분리 단위로 사용해 SW/HW 셀이 섞이지 않게 한다
    for sent in re.split(r"(?<=\.)\s+|\n|\|", text):
        cites = PAPER_CITE.findall(sent)
        # 웹 출처([3], [WM2])를 함께 인용한 문장은 수치가 웹 자료에서 왔을 수 있어 검사 대상에서 제외
        if not cites or re.search(r"\[(?:\d+|W[MD]\d+)\s*[\];,]", sent):
            continue
        for num in {n for n in NUMBER.findall(sent) if _significant(n)}:
            found = False
            for sid, spec in cites:
                pages = {p + d for p in _pages(spec) for d in (-1, 0, 1)}
                if any(num in page_text(sid, p) for p in pages):
                    found = True
                    break
            if not found:
                cited = ", ".join(f"{sid} p.{spec.strip()}" for sid, spec in cites)
                flagged.append(f"수치 '{num}'를 인용한 원문({cited})에서 찾지 못함 : {sent.strip()[:120]}")
    return flagged


def cited_page_texts(text: str, page_text, max_pages: int = 8) -> str:
    """평가 결과가 인용한 논문 페이지의 원문 전체를 모아 검증자에게 제공 (잘린 청크가 아닌 페이지 단위 대조)."""
    cited = []
    for sid, spec in PAPER_CITE.findall(text):
        for p in sorted(_pages(spec)):
            if (sid, p) not in cited:
                cited.append((sid, p))
    return "\n\n".join(f"### {sid} p.{p}\n{page_text(sid, p).strip()}" for sid, p in cited[:max_pages]
                        if page_text(sid, p))
