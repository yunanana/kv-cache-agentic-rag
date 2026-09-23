"""보고서 검토 노드 : 규칙 기반 검사 + LLM-as-a-Judge → 재작성(Loop) 여부 결정."""

import re

from agents.schemas import ReviewResult
from config import MAX_REPORT_PAGES, MAX_REPORT_REVISION
from llm import get_judge
from prompts.templates import REVIEW_PROMPT
from report.pdf import count_pages

REQUIRED_SECTIONS = ["SUMMARY", "1. 분석 배경", "2. 기술 선정", "3. 기술 개요", "4. 관점별 평가",
                     "5. 시사점", "6. 한계점", "REFERENCE"]
BIAS_WORDS = ["추천한다", "우수", "우월", "승자", "유리하다"]


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
    if summary and len(summary.group(1).strip()) > 900:
        issues.append(f"SUMMARY가 {len(summary.group(1).strip())}자로 길다 - 700자 이내로 줄일 것")
    for w in BIAS_WORDS:
        if w in report_md:
            issues.append(f"우열 판정 표현 '{w}' 사용 - 중립적 표현으로 수정")
    pages = count_pages(report_md)
    if pages > MAX_REPORT_PAGES:
        issues.append(f"PDF 기준 {pages}페이지로 {MAX_REPORT_PAGES}페이지 제한 초과 - 표·서술을 줄여 분량을 약 "
                      f"{int(100 * MAX_REPORT_PAGES / pages) - 5}% 수준으로 축소할 것")
    return issues, pages


def make_reviewer_node():
    judge = REVIEW_PROMPT | get_judge().with_structured_output(ReviewResult)

    def reviewer(state):
        issues, pages = rule_check(state["report_md"])
        verdict = judge.invoke({"report": state["report_md"]})
        issues += verdict.issues if not verdict.passed else []
        passed = not issues
        print(f"[reviewer] {'통과' if passed else f'수정 필요 {len(issues)}건'} ({pages}p)")
        return {"review": {"passed": passed, "issues": issues, "pages": pages}}

    return reviewer


def route_after_review(state) -> str:
    if state["review"]["passed"] or state.get("revision_count", 0) >= MAX_REPORT_REVISION:
        return "approve"
    return "revise"
