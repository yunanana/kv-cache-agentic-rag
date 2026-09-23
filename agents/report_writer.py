"""📝 보고서 생성 에이전트 : 단계별 결과를 연결해 보고서 작성 + 인용 기반 REFERENCE 자동 생성."""

import re

from langchain_core.output_parsers import StrOutputParser

from agents.common import to_json
from llm import get_llm
from agents.perspective import PERSPECTIVES, _criteria_text
from prompts.templates import REPORT_PROMPT

SOURCE_ID = r"P-SW|P-HW|WM\d+|WD\d+"
CITE_ID = re.compile(rf"^({SOURCE_ID})(?:\s*,?\s*(p{{1,2}}\.\s*[\d\-–]+(?:\s*,\s*(?:p{{1,2}}\.\s*)?[\d\-–]+)*))?$")
LOOKS_LIKE_CITE = re.compile(rf"^\s*({SOURCE_ID}|[MD]\d+)\b")
BRACKET = re.compile(r"\[([^\[\]]+)\]")


def _selection_text(technologies: dict) -> str:
    return "\n".join(
        f"- {t['camp']} : {t['name']} / 논문: {t['paper_title']} (arXiv {t['arxiv_id']})\n  선정 사유: {t['selection_reason']}"
        for t in technologies.values()
    )


def _sources_text(sources: list[dict]) -> str:
    return "\n".join(
        f"[{s['id']}] ({s['tech'].upper()}, {'논문' if s['kind'] == 'paper' else s['site']}) {s['title']}" for s in sources
    )


def _format_reference(src: dict) -> str:
    if src["kind"] == "paper":
        return f"{src['citation']} {src['url']}"
    return f"{src['site']}({src['date'] or 'n.d.'}). *{src['title']}*. {src['site']}, {src['url']}"


def finalize_references(report_md: str, sources: list[dict]) -> str:
    """본문 인용 태그([M3], [P-SW p.4])를 번호([2], [1, p.4])로 바꾸고, 실제 인용된 출처만 REFERENCE로 붙인다."""
    by_id = {s["id"]: s for s in sources}
    number: dict[str, int] = {}      # 동일 URL은 같은 번호
    ref_list: list[dict] = []

    def num_for(sid: str) -> int:
        key = by_id[sid]["url"]
        if key not in number:
            number[key] = len(ref_list) + 1
            ref_list.append(by_id[sid])
        return number[key]

    def replace(m: re.Match) -> str:
        parts = [p.strip() for p in re.split(rf"[;,](?=\s*(?:{SOURCE_ID}))", m.group(1))]
        matches = [CITE_ID.match(p) for p in parts]
        if not all(matches) or not all(mm.group(1) in by_id for mm in matches):
            # 변환할 수 없는 인용 형태(범위 표기, 존재하지 않는 ID 등)는 본문에서 제거
            return "" if LOOKS_LIKE_CITE.match(m.group(1)) else m.group(0)
        out = []
        for mm in matches:
            n = num_for(mm.group(1))
            cite = f"{n}, {mm.group(2).strip()}" if mm.group(2) else str(n)
            if cite not in out:
                out.append(cite)
        return "[" + "; ".join(out) + "]"

    body = re.split(r"\n#+\s*REFERENCE", report_md, flags=re.IGNORECASE)[0].rstrip()
    body = re.sub(r"(\n-{3,}\s*)?(\n\(.*\)\s*)?(\n#*\s*(끝|END|이상)\.?\s*)?$", "", body).rstrip()   # 종료 표시·꼬리말 제거
    body = BRACKET.sub(replace, body)
    body = re.sub(r"\]\s*,\s*(?=[|\n.]|$)", "]", body)   # 제거된 인용 뒤에 남은 쉼표 정리
    body = re.sub(r"(?<=\S) {2,}(?=\S)", " ", body)
    refs = "\n".join(f"{i}. {_format_reference(s)}" for i, s in enumerate(ref_list, 1))
    return f"{body}\n\n## REFERENCE\n\n{refs}\n"


def make_report_writer_node():
    chain = REPORT_PROMPT | get_llm() | StrOutputParser()

    def report_writer(state):
        review = state.get("review") or {}
        feedback = ""
        if review.get("issues"):
            feedback = "[이전 초안 검토 의견 - 반드시 반영하여 전체 보고서를 다시 작성]\n" + "\n".join(
                f"- {i}" for i in review["issues"]
            )
        draft = chain.invoke({
            "domain": state["domain"]["name"],
            "selection": _selection_text(state["technologies"]),
            "criteria": "\n".join(f"[{p['label']}]\n{_criteria_text(p['criteria'])}" for p in PERSPECTIVES.values()),
            "profiles": to_json(state["tech_profiles"]),
            "market": to_json(state["market_eval"]),
            "domain_eval": to_json(state["domain_eval"]),
            "synthesis": to_json(state["synthesis"]),
            "sources": _sources_text(state["sources"]),
            "feedback": feedback,
        })
        draft = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", draft.strip())
        revision = state.get("revision_count", -1) + 1
        print(f"[report_writer] 초안 v{revision + 1} 작성")
        return {"report_md": finalize_references(draft, state["sources"]), "revision_count": revision}

    return report_writer
