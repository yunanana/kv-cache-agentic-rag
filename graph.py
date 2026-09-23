"""LangGraph 워크플로 : 기술 조사 → (시장성 ∥ 도메인) → 종합 → 보고서 ⇄ 검토 → 저장."""

from langgraph.graph import END, START, StateGraph

from agents.exporter import make_exporter_node
from agents.perspective import make_perspective_node
from agents.report_writer import make_report_writer_node
from agents.reviewer import make_reviewer_node, route_after_review
from agents.synthesis import make_synthesis_node
from agents.tech_research import make_tech_research_node
from rag.retriever import HybridRetriever
from state import ReportState


def build_graph(retriever: HybridRetriever, pdf_name: str = "report.pdf"):
    g = StateGraph(ReportState)

    g.add_node("tech_research", make_tech_research_node(retriever))
    g.add_node("market_evaluation", make_perspective_node(retriever, "market"))
    g.add_node("domain_evaluation", make_perspective_node(retriever, "domain"))
    g.add_node("synthesis", make_synthesis_node())
    g.add_node("report_writer", make_report_writer_node())
    g.add_node("reviewer", make_reviewer_node(retriever))
    g.add_node("exporter", make_exporter_node(pdf_name))

    g.add_edge(START, "tech_research")
    # Fan-out : 두 관점 평가를 병렬 실행 (결과는 market_eval / domain_eval 로 키 분리)
    g.add_edge("tech_research", "market_evaluation")
    g.add_edge("tech_research", "domain_evaluation")
    # Fan-in : 두 평가가 모두 끝나면 종합
    g.add_edge(["market_evaluation", "domain_evaluation"], "synthesis")
    g.add_edge("synthesis", "report_writer")
    g.add_edge("report_writer", "reviewer")
    # Loop : 검토 미통과 시 재작성 (최대 MAX_REPORT_REVISION 회). 한도 도달 시 '검토 미통과'로 표시해 저장
    g.add_conditional_edges(
        "reviewer", route_after_review,
        {"revise": "report_writer", "approve": "exporter", "unverified": "exporter"},
    )
    g.add_edge("exporter", END)

    return g.compile()
