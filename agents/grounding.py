"""결정론적 수치 근거 검사 : 논문 페이지를 인용한 문장의 수치가 실제 그 페이지 원문에 있는지 확인."""

import re

CITE_GROUP = re.compile(r"(?:\[[^\[\]]+\]\s*)+")
# 모델명·버전(Llama-3.1, Gen5 등)의 숫자는 제외
NUMBER = re.compile(r"(?<![\w.\-])(?:\d+\.\d+|\d+(?=\s*(?:[~–-]\s*\d|%|배|x|×|GB|TB|비트|bit|초|ms)))")
PAPER_CITE = re.compile(r"\[(P-SW|P-HW) pp?\.\s*([\d\-–,\sp.]+)\]")


def _pages(spec: str) -> set[int]:
    pages = set()
    for a, b in re.findall(r"(\d+)(?:\s*[-–]\s*(\d+))?", spec):
        lo, hi = int(a), int(b or a)
        pages.update(range(lo, hi + 1))
    return pages


def unsupported_numbers(text: str, page_text) -> list[str]:
    """인용 페이지의 숫자 토큰 검사. 지표·조건의 의미 검증은 원문을 받는 LLM이 담당.

    인용 묶음([..][..])은 '직전 인용 이후부터 자신까지의 텍스트 구간'을 뒷받침한다고 보고 그 구간 전체의 수치를 검사한다.
    그래서 '문장 A. 문장 B. [출처]'처럼 문단 끝에 인용이 한 번만 달린 경우도 A, B의 수치를 모두 검사한다.
    줄바꿈과 표 셀('|')은 구간 경계로 사용해 SW/HW 셀이 섞이지 않게 한다.
    """
    flagged = []
    text = re.sub(r"\b(pp?)\.\s+", r"\1.", text)   # 'p. 10' → 'p.10'
    for unit in re.split(r"\n|\|", text):
        pos = 0
        for group in CITE_GROUP.finditer(unit):
            segment, pos = unit[pos:group.start()], group.end()
            cites = PAPER_CITE.findall(group.group(0))
            if not cites:
                continue
            mixed = bool(re.search(r"\[(?:\d+|W[MD]\d+)\s*[\];,]", group.group(0)))
            for num in sorted(set(NUMBER.findall(segment))):
                token = re.compile(r"(?<![\d.])" + re.escape(num) + r"(?![\d.])")
                if any(token.search(page_text(sid, p)) for sid, spec in cites for p in _pages(spec)):
                    continue
                cited = ", ".join(f"{sid} p.{spec.strip()}" for sid, spec in cites)
                note = " 웹 근거 수치라면 논문 주장과 문장을 분리하고 해당 웹 출처만 인용할 것." if mixed else ""
                flagged.append(f"수치 '{num}'를 인용한 원문({cited})에서 찾지 못함 : {segment.strip()[:120]}{note}")
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
