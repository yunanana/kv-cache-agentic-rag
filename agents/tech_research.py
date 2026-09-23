"""🔍 기술 조사 에이전트 (RAG) : 논문 원문에서 기술 개요·성과·한계를 추출."""

from agents.common import paper_source, run_per_tech, to_json
from agents.schemas import TechProfile
from llm import get_judge, get_llm
from prompts.criteria import TECH_RESEARCH_QUESTIONS
from prompts.templates import PROFILE_CHECK_PROMPT, TECH_PROFILE_PROMPT
from rag.agentic import agentic_search
from rag.retriever import HybridRetriever, format_docs


def make_tech_research_node(retriever: HybridRetriever):
    chain = TECH_PROFILE_PROMPT | get_llm().with_structured_output(TechProfile)
    checker = PROFILE_CHECK_PROMPT | get_judge().with_structured_output(TechProfile)

    def research(tech: dict) -> dict:
        findings = [agentic_search(retriever, q, tech) for q in TECH_RESEARCH_QUESTIONS]
        evidence = "\n\n".join(
            f"### Q. {f['question']}\n{format_docs(f['docs']) or '(관련 근거를 찾지 못함)'}" for f in findings
        )
        profile = chain.invoke({
            "name": tech["name"], "camp": tech["camp"], "paper_title": tech["paper_title"], "evidence": evidence,
        })
        # Reflection : baseline·관련 연구 서술이 대상 기술 항목에 섞였는지 검증 후 수정
        checked = checker.invoke({"name": tech["name"], "profile": to_json(profile.model_dump()), "evidence": evidence})
        return {"profile": checked.model_dump(), "findings": findings}

    def tech_research(state):
        techs = state["technologies"]
        results = run_per_tech(research, techs)
        print("[tech_research] 완료")
        return {
            "tech_profiles": {k: r["profile"] for k, r in results.items()},
            "sources": [paper_source(t) for t in techs.values()],
            "trace": [
                {"agent": "tech_research", "tech": k, "question": f["question"], "attempts": f["attempts"]}
                for k, r in results.items() for f in r["findings"]
            ],
        }

    return tech_research
