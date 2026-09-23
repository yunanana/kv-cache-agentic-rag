"""⚖️ 평가 종합 에이전트 : 관점 간 일치/상충 지점 도출."""

from agents.common import to_json
from agents.schemas import Synthesis
from llm import get_llm
from prompts.templates import SYNTHESIS_PROMPT


def make_synthesis_node():
    chain = SYNTHESIS_PROMPT | get_llm().with_structured_output(Synthesis)

    def synthesis(state):
        result = chain.invoke({
            "domain": state["domain"]["name"],
            "profiles": to_json(state["tech_profiles"]),
            "market": to_json(state["market_eval"]),
            "domain_eval": to_json(state["domain_eval"]),
        })
        print("[synthesis] 완료")
        return {"synthesis": result.model_dump()}

    return synthesis
