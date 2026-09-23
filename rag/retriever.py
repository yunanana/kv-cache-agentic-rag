"""RUNTIME : Hybrid Retriever (Sparse BM25 + Dense FAISS, Reciprocal Rank Fusion)."""

import re

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from config import TOP_K, PAPER_DIR, TECHNOLOGIES


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class HybridRetriever:
    """기술(tech) 메타데이터로 필터링한 뒤 BM25와 벡터 검색 결과를 RRF로 결합한다.

    - Dense : 의미 유사도 (용어가 달라도 같은 개념 검색)
    - Sparse : 키워드 정확 매칭 (CXL, 3-bit, throughput 같은 고유 용어)
    """

    def __init__(self, vectorstore: FAISS, chunks: list[Document], k: int = TOP_K, rrf_k: int = 60):
        self.vs = vectorstore
        self.k = k
        self.rrf_k = rrf_k
        self._by_id = {c.metadata["chunk_id"]: c for c in chunks}
        self._pages: dict[tuple[str, int], str] = {}
        # Grounding must use original PDF pages, not filtered/overlapping chunks.
        from pypdf import PdfReader
        for tech in TECHNOLOGIES.values():
            for number, page in enumerate(PdfReader(PAPER_DIR / tech["file"]).pages, 1):
                self._pages[(tech["source_id"], number)] = page.extract_text() or ""
        self._bm25: dict[str | None, tuple[BM25Okapi, list[Document]]] = {}
        groups: dict[str | None, list[Document]] = {None: chunks}
        for c in chunks:
            groups.setdefault(c.metadata["tech"], []).append(c)
        for tech, docs in groups.items():
            self._bm25[tech] = (BM25Okapi([_tokenize(d.page_content) for d in docs]), docs)

    def dense(self, query: str, tech: str | None = None, k: int | None = None) -> list[Document]:
        k = k or self.k
        flt = {"tech": tech} if tech else None
        return self.vs.similarity_search(query, k=k, filter=flt, fetch_k=max(60, k * 10))

    def sparse(self, query: str, tech: str | None = None, k: int | None = None) -> list[Document]:
        k = k or self.k
        bm25, docs = self._bm25[tech]
        scores = bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)[:k]
        return [docs[i] for i in ranked]

    def invoke(self, query: str, tech: str | None = None, k: int | None = None) -> list[Document]:
        k = k or self.k
        fused: dict[int, float] = {}
        by_id: dict[int, Document] = {}
        for ranked in (self.dense(query, tech, k * 2), self.sparse(query, tech, k * 2)):
            for rank, doc in enumerate(ranked):
                cid = doc.metadata["chunk_id"]
                by_id[cid] = doc
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (self.rrf_k + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [by_id[cid] for cid in top]

    def page_text(self, source_id: str, page: int) -> str:
        return self._pages.get((source_id, page), "")

    def with_context(self, doc: Document, chars: int = 500) -> Document:
        """앞 청크의 끝부분을 붙여 반환 (Parent Document 방식의 문맥 보강).

        청크 경계에서 주어가 잘려 다른 기법의 설명을 대상 기술로 오인하는 문제를 줄인다.
        """
        prev = self._by_id.get(doc.metadata["chunk_id"] - 1)
        if prev is None or prev.metadata["source_id"] != doc.metadata["source_id"]:
            return doc
        return Document(page_content=f"(...{prev.page_content[-chars:]}) {doc.page_content}", metadata=doc.metadata)


def format_docs(docs: list[Document]) -> str:
    """출처 태그 [P-SW p.N] 를 붙여 LLM이 근거 페이지를 인용할 수 있게 한다."""
    return "\n\n".join(
        f"[{d.metadata['source_id']} p.{d.metadata['page']}] {d.page_content}" for d in docs
    )
