"""Agentic RAG : 검색 → 관련성 판정 → (관련 문서 없으면) 질의 재작성 → 재검색.

각 평가 에이전트가 논문 근거가 필요할 때 이 루프를 도구처럼 호출한다.
"""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config import MAX_QUERY_REWRITE
from llm import get_judge, get_llm
from rag.retriever import HybridRetriever


class GradeResult(BaseModel):
    relevant_ids: list[int] = Field(description="질문에 답하는 데 실제로 도움이 되는 문서 번호 목록 (없으면 빈 리스트)")


class RewrittenQuery(BaseModel):
    query: str = Field(description="검색에 적합하게 재작성한 영어 질의 (핵심 키워드 중심)")


GRADE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You grade retrieved passages from a research paper for relevance. "
     "A passage is relevant only if it contains information that helps answer the question "
     "(facts, numbers, mechanisms, conditions, limitations). Reference lists and unrelated sections are NOT relevant."),
    ("human", "Question: {question}\n\nPassages:\n{passages}\n\nReturn the numbers of relevant passages."),
])

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "The search query below did not retrieve relevant passages from the paper about {tech_name}. "
     "Rewrite it as a short English keyword query that is more likely to match the paper's wording."),
    ("human", "Original question: {question}\nPrevious query: {query}"),
])


def agentic_search(retriever: HybridRetriever, question: str, tech: dict) -> dict:
    grader = GRADE_PROMPT | get_judge().with_structured_output(GradeResult)
    rewriter = REWRITE_PROMPT | get_llm().with_structured_output(RewrittenQuery)

    query = question
    attempts = []
    relevant: list[Document] = []
    for attempt in range(MAX_QUERY_REWRITE + 1):
        docs = retriever.invoke(query, tech=tech["key"])
        passages = "\n\n".join(f"({i}) {d.page_content[:1200]}" for i, d in enumerate(docs))
        ids = grader.invoke({"question": question, "passages": passages}).relevant_ids
        relevant = [docs[i] for i in ids if 0 <= i < len(docs)]
        attempts.append({
            "query": query,
            "retrieved": [d.metadata["chunk_id"] for d in docs],
            "relevant": [d.metadata["chunk_id"] for d in relevant],
        })
        if relevant or attempt == MAX_QUERY_REWRITE:
            break
        query = rewriter.invoke({"tech_name": tech["name"], "question": question, "query": query}).query

    relevant = [retriever.with_context(d) for d in relevant]
    return {"tech": tech["key"], "question": question, "docs": relevant, "attempts": attempts}
