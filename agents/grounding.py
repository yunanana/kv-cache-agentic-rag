"""결정론적 수치 근거 검사 : 논문 페이지를 인용한 문장의 수치가 실제 그 페이지 원문에 있는지 확인."""

import re

NUMBER = re.compile(r"(?<![\w.])(?:\d+\.\d+|\d+(?=\s*(?:[~–-]\s*\d|%|배|x|×|GB|TB|비트|bit|초|ms)))")
PAPER_CITE = re.compile(r"\[(P-SW|P-HW) pp?\.\s*([\d\-–,\sp.]+)\]")


def _pages(spec: str) -> set[int]:
    pages = set()
    for a, b in re.findall(r"(\d+)(?:\s*[-–]\s*(\d+))?", spec):
        lo, hi = int(a), int(b or a)
        pages.update(range(lo, hi + 1))
    return pages


def unsupported_numbers(text: str, page_text) -> list[str]:
    """인용 페이지의 숫자 토큰 검사. 지표·조건의 의미 검증은 원문을 받는 LLM이 담당."""
    flagged = []
    # 문장 분리 : '마침표+공백'·줄바꿈 기준 (35.7, p.10 같은 소수점·페이지 표기는 분리하지 않음)
    # 표 셀('|')도 분리 단위로 사용해 SW/HW 셀이 섞이지 않게 한다
    # Protect page abbreviations before splitting sentences.
    text = re.sub(r"\b(pp?)\.\s+", r"\1.", text)
    for sent in re.split(r"(?<=\.)\s+|\n|\|", text):
        cites = PAPER_CITE.findall(sent)
        # 혼합 인용도 검사한다. 출처가 불명확하면 문장을 분리하도록 요청한다.
        if not cites:
            continue
        mixed = bool(re.search(r"\[(?:\d+|W[MD]\d+)\s*[\];,]", sent))
        claim = re.sub(r"\[[^\]]*\]", "", sent)
        for num in sorted(set(NUMBER.findall(claim))):
            found = False
            for sid, spec in cites:
                pages = _pages(spec)
                token = re.compile(r"(?<![\d.])" + re.escape(num) + r"(?![\d.])")
                if any(token.search(page_text(sid, p)) for p in pages):
                    found = True
                    break
            if not found:
                cited = ", ".join(f"{sid} p.{spec.strip()}" for sid, spec in cites)
                note = " 웹 근거 수치라면 논문 주장과 문장을 분리하고 해당 웹 출처만 인용할 것." if mixed else ""
                flagged.append(f"수치 '{num}'를 인용한 원문({cited})에서 찾지 못함 : {sent.strip()[:120]}{note}")
    return flagged


def cited_page_texts(text: str, page_text, max_pages: int | None = None) -> str:
    """평가 결과가 인용한 논문 페이지의 원문 전체를 모아 검증자에게 제공 (잘린 청크가 아닌 페이지 단위 대조)."""
    cited = []
    for sid, spec in PAPER_CITE.findall(text):
        for p in sorted(_pages(spec)):
            if (sid, p) not in cited:
                cited.append((sid, p))
    if max_pages is not None and len(cited) > max_pages:
        raise ValueError("인용 페이지 제한 초과: 근거를 조용히 생략할 수 없습니다")
    return "\n\n".join(f"### {sid} p.{p}\n{page_text(sid, p).strip() or '[원문 누락: 검증 불가]'}"
                        for sid, p in cited)
