"""📊 시장성 평가 에이전트 / 🏭 도메인 평가 에이전트.

두 에이전트는 같은 흐름(기준별 RAG 검색 + 웹 검색 → 구조화 평가)을 공유하고,
평가 기준·출처 prefix·State 키만 다르다. Graph에서는 병렬(fan-out)로 실행된다.
"""

from agents.common import WebSourceRegistry, format_web, run_per_tech, to_json
from agents.schemas import PerspectiveEvaluation
from llm import get_llm
from prompts.criteria import DOMAIN_CRITERIA, MARKET_CRITERIA
from prompts.templates import PERSPECTIVE_PROMPT
from rag.agentic import agentic_search
from rag.retriever import HybridRetriever, format_docs

PERSPECTIVES = {
    "market": {
        "label": "시장성",
        "state_key": "market_eval",
        "prefix": "WM",
        "criteria": MARKET_CRITERIA,
        "description": "시장 규모·성장성, 상용화·채택 현황, 생태계 지지를 기준으로 시장이 이 기술을 어떻게 보는지 평가한다. "
                       "시장 근거는 주로 웹 자료, 논문은 구현·통합 수준 확인에 활용한다.",
    },
    "domain": {
        "label": "도메인 적용",
        "state_key": "domain_eval",
        "prefix": "WD",
        "criteria": DOMAIN_CRITERIA,
        "description": "",   # 실행 시 도메인 설명으로 채움
    },
}


def _criteria_text(criteria: list[dict]) -> str:
    return "\n".join(f"- {c['id']} {c['name']} : {c['target']}\n  등급 기준 - {c['rubric']}" for c in criteria)


def make_perspective_node(retriever: HybridRetriever, perspective: str):
    cfg = PERSPECTIVES[perspective]
    chain = PERSPECTIVE_PROMPT | get_llm().with_structured_output(PerspectiveEvaluation)

    def node(state):
        domain = state["domain"]
        description = cfg["description"] or (
            f"평가 도메인은 '{domain['name']}'이다. {domain['description']} "
            "이 도메인의 요구(비용, 처리량·지연, 품질, 도입 난이도)에 기술이 얼마나 부합하는지 평가한다. "
            "도메인 근거는 주로 논문 실험 결과, 웹 자료는 실제 서빙 환경 반응 보강에 활용한다."
        )
        registry = WebSourceRegistry(cfg["prefix"])
        trace = []

        def evaluate(tech: dict) -> dict:
            blocks = []
            for c in cfg["criteria"]:
                rag_parts = []
                for q in c["rag_questions"]:
                    found = agentic_search(retriever, q, tech)
                    trace.append({"agent": perspective, "tech": tech["key"], "criterion": c["id"],
                                  "question": q, "attempts": found["attempts"]})
                    rag_parts.append(format_docs(found["docs"]))
                web = []
                for tmpl in c["web_queries"]:
                    web += registry.search(tmpl.format(**tech), tech["key"])
                blocks.append(
                    f"## {c['id']} {c['name']}\n"
                    f"[논문 근거]\n{chr(10).join(p for p in rag_parts if p) or '(관련 근거를 찾지 못함)'}\n"
                    f"[웹 근거]\n{format_web(web) or '(검색 결과 없음)'}"
                )
            result = chain.invoke({
                "perspective": cfg["label"],
                "perspective_description": description,
                "criteria": _criteria_text(cfg["criteria"]),
                "name": tech["name"],
                "camp": tech["camp"],
                "profile": to_json(state["tech_profiles"][tech["key"]]),
                "evidence": "\n\n".join(blocks),
            })
            return result.model_dump()

        evaluations = run_per_tech(evaluate, state["technologies"])
        print(f"[{perspective}] 완료 - 웹 출처 {len(registry.sources)}건")
        return {cfg["state_key"]: evaluations, "sources": registry.sources, "trace": trace}

    node.__name__ = f"{perspective}_evaluation"
    return node
