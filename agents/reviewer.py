"""보고서 검토 노드 : 규칙 기반 검사 + LLM-as-a-Judge → 재작성(Loop) 여부 결정."""

import re

from agents.grounding import unsupported_numbers, cited_page_texts
from agents.schemas import ReviewResult
from config import MAX_REPORT_PAGES, MAX_REPORT_REVISION, TECHNOLOGIES
from llm import get_verifier
from prompts.templates import REVIEW_PROMPT
from report.pdf import count_pages

REQUIRED_SECTIONS = ["SUMMARY", "1. 분석 배경", "2. 기술 선정", "3. 기술 개요", "4. 관점별 평가",
                     "5. 시사점", "6. 한계점", "REFERENCE"]
SUMMARY_MAX_CHARS = 1200
BIAS_WORDS = ["추천한다", "더 우수", "우월", "승자", "유리하다"]


def rule_check(report_md: str) -> tuple[list[str], int]:
    issues = []
    headings = re.findall(r"^##\s+(.+)$", report_md, flags=re.M)
    for sec in REQUIRED_SECTIONS:
        if not any(h.strip().startswith(sec) for h in headings):
            issues.append(f"'{sec}' 섹션이 없음 - 목차를 지켜 추가할 것")
    if headings and not headings[0].startswith("SUMMARY"):
        issues.append("첫 섹션이 SUMMARY가 아님")
    if headings and not headings[-1].startswith("REFERENCE"):
        issues.append("마지막 섹션이 REFERENCE가 아님")
    summary = re.search(r"##\s+SUMMARY(.*?)\n##\s", report_md, flags=re.S)
    # 가이드 : SUMMARY 는 1/2 페이지 이내. 현재 PDF 서식에서 반 페이지는 약 1,200자(인용 포함)
    if summary and len(summary.group(1).strip()) > SUMMARY_MAX_CHARS:
        issues.append(f"SUMMARY가 {len(summary.group(1).strip())}자로 반 페이지를 넘는다 - {SUMMARY_MAX_CHARS}자 이내로 줄일 것")
    for w in BIAS_WORDS:
        if w in report_md:
            issues.append(f"우열 판정 표현 '{w}' 사용 - 중립적 표현으로 수정")
    pages = count_pages(report_md)
    if pages > MAX_REPORT_PAGES:
        issues.append(f"PDF 기준 {pages}페이지로 {MAX_REPORT_PAGES}페이지 제한 초과 - 표·서술을 줄여 분량을 약 "
                      f"{int(100 * MAX_REPORT_PAGES / pages) - 5}% 수준으로 축소할 것")
    return issues, pages


def to_source_tags(report_md: str) -> str:
    """REFERENCE 번호를 논문 source_id로 되돌려 ([1, p.17] → [P-SW p.17]) 수치 근거 검사에 사용."""
    ref_to_sid = {}
    for n, line in re.findall(r"^(\d+)\. (.+)$", report_md.split("## REFERENCE")[-1], flags=re.M):
        for t in TECHNOLOGIES.values():
            if t["arxiv_id"] in line:
                ref_to_sid[n] = t["source_id"]

    def convert(m: re.Match) -> str:
        parts = []
        for part in m.group(1).split(";"):
            mm = re.match(r"\s*(\d+),\s*(pp?\..+)", part)
            if mm and mm.group(1) in ref_to_sid:
                parts.append(f"[{ref_to_sid[mm.group(1)]} {mm.group(2).strip()}]")
            else:
                parts.append(f"[{part.strip()}]")
        return "".join(parts) or m.group(0)

    body = report_md.split("## REFERENCE")[0]
    return re.sub(r"\[([^\[\]]*\d+,\s*pp?\.[^\[\]]*)\]", convert, body)


def make_reviewer_node(retriever):
    judge = REVIEW_PROMPT | get_verifier().with_structured_output(ReviewResult)

    def reviewer(state):
        issues, pages = rule_check(state["report_md"])
        issues += [f"{f} - 원문 지표대로 고치거나 삭제할 것"
                   for f in unsupported_numbers(to_source_tags(state["report_md"]), retriever.page_text)]
        # 규칙 검사 결과는 모두 critical, LLM Judge 결과는 severity 에 따름
        critical = list(issues)
        minor = []
        tagged = to_source_tags(state["report_md"])
        evidence = cited_page_texts(tagged, retriever.page_text)
        web = "\n\n".join(
            f"### {s.get('id')} {s.get('url')}\n{s.get('content') or '[수집 본문 없음: 근거 미확인]'}"
            for s in state.get("sources", []) if s.get("kind") != "paper"
        )
        for i in judge.invoke({"report": state["report_md"],
                               "evidence": evidence + "\n\n[웹 검색 근거: 원문 전체가 아닌 검색 발췌일 수 있음]\n" + web}).issues:
            (critical if i.severity == "critical" else minor).append(f"'{i.quote[:80]}' → {i.fix}")
        passed = not critical
        print(f"[reviewer] {'통과' if passed else f'수정 필요 {len(critical)}건'} (minor {len(minor)}건, {pages}p)")
        return {"review": {"passed": passed, "issues": critical, "minor": minor, "pages": pages}}

    return reviewer


def route_after_review(state) -> str:
    if state["review"]["passed"]:
        return "approve"
    if state.get("revision_count", 0) < MAX_REPORT_REVISION:
        return "revise"
    # 재작성 한도 도달 : 저장은 하되 '검토 미통과'로 표시하고 잔여 의견을 별도 파일로 남겨 사람이 확인하게 한다
    return "unverified"
