"""실행 스크립트 : 논문 준비 → 인덱스 구축 → 멀티 에이전트 그래프 실행 → 보고서 저장.

    uv run python app.py                  # 기본 실행
    uv run python app.py --rebuild-index  # 청크·벡터 인덱스 재생성
"""

import argparse
import os
import sys
import time

from config import EMBEDDING_MODEL, DOMAIN, OUTPUT_DIR, TECHNOLOGIES
from graph import build_graph
from rag.ingest import build_or_load_index, prepare_corpus
from rag.retriever import HybridRetriever
from scripts.download_papers import download_papers


def main():
    parser = argparse.ArgumentParser(description="KV cache 최적화 기술 다관점 평가 보고서 생성")
    parser.add_argument("--rebuild-index", action="store_true", help="청크·벡터 인덱스 재생성")
    parser.add_argument("--pdf-name", default=os.getenv("REPORT_PDF_NAME", "report.pdf"), help="출력 PDF 파일명")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY 가 없습니다. .env.example 을 복사해 .env 를 만들고 키를 넣어주세요.")
    if not os.getenv("TAVILY_API_KEY"):
        print("[warn] TAVILY_API_KEY 없음 - 웹 검색 없이 논문(RAG) 근거만으로 평가합니다.")

    start = time.time()
    download_papers()
    chunks = prepare_corpus(TECHNOLOGIES, rebuild=args.rebuild_index)
    vectorstore = build_or_load_index(EMBEDDING_MODEL, chunks, rebuild=args.rebuild_index)
    retriever = HybridRetriever(vectorstore, chunks)
    print(f"[rag] {len(chunks)} chunks / embedding = {EMBEDDING_MODEL}")

    app = build_graph(retriever, pdf_name=args.pdf_name)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "graph.mmd").write_text(app.get_graph().draw_mermaid(), encoding="utf-8")

    final = app.invoke({"technologies": TECHNOLOGIES, "domain": DOMAIN}, config={"recursion_limit": 30})

    out = final["outputs"]
    print(f"\n완료 ({time.time() - start:.0f}s) - {out['pages']} pages")
    print(f"  PDF  : {out['pdf']}\n  MD   : {out['md']}\n  HTML : {out['html']}")
    if not out["review_passed"]:
        print(f"\n[주의] 자동 검토를 통과하지 못한 채 저장됨 - {out['review']} 의 잔여 의견을 확인하세요:")
        print(*final["review"]["issues"], sep="\n   - ")


if __name__ == "__main__":
    main()
