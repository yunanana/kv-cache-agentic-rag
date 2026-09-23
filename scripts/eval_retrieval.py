"""검색 성능 평가 : 오픈소스 임베딩 후보 비교 + Dense / Sparse / Hybrid 비교.

평가 데이터셋 : 정답 청크를 LLM에 주고 그 청크로만 답할 수 있는 질문을 생성 → (질문, gold chunk_id)
지표 : Hit Rate@K (정답 청크가 상위 K 안에 있는가), MRR@5 (정답이 몇 번째에 나오는가)

    uv run python scripts/eval_retrieval.py
"""

import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from config import EMBEDDING_CANDIDATES, EVAL_DIR, OUTPUT_DIR, TECHNOLOGIES  # noqa: E402
from llm import get_llm  # noqa: E402
from rag.ingest import build_or_load_index, prepare_corpus  # noqa: E402
from rag.retriever import HybridRetriever  # noqa: E402
from scripts.download_papers import download_papers  # noqa: E402

N_PER_TECH = 15
KS = (1, 3, 5)
QA_PATH = EVAL_DIR / "qa.json"


class GeneratedQuestion(BaseModel):
    question: str


QG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Write ONE specific English question that can be answered using the passage below, as an engineer "
     "researching this method would ask it. Paraphrase: do not copy long phrases verbatim from the passage."),
    ("human", "{passage}"),
])


def _is_body_text(text: str) -> bool:
    # 참고문헌·수식 위주 청크 제외
    return len(text) > 400 and len(re.findall(r"\[\d+\]|et al\.", text)) < 4 and "References" not in text[:40]


def build_qa_set(chunks) -> list[dict]:
    if QA_PATH.exists():
        return json.loads(QA_PATH.read_text(encoding="utf-8"))
    rng = random.Random(42)
    chain = QG_PROMPT | get_llm().with_structured_output(GeneratedQuestion)
    qa = []
    for tech in TECHNOLOGIES:
        pool = [c for c in chunks if c.metadata["tech"] == tech and _is_body_text(c.page_content)]
        for c in rng.sample(pool, min(N_PER_TECH, len(pool))):
            q = chain.invoke({"passage": c.page_content}).question
            qa.append({"question": q, "gold_id": c.metadata["chunk_id"], "tech": tech})
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    QA_PATH.write_text(json.dumps(qa, ensure_ascii=False, indent=1), encoding="utf-8")
    return qa


def evaluate(search, qa) -> dict:
    hits = {k: 0 for k in KS}
    rr = 0.0
    for e in qa:
        ids = [d.metadata["chunk_id"] for d in search(e["question"], e["tech"])][: max(KS)]
        if e["gold_id"] in ids:
            rank = ids.index(e["gold_id"]) + 1
            rr += 1 / rank
            for k in KS:
                hits[k] += rank <= k
    n = len(qa)
    return {**{f"Hit@{k}": round(hits[k] / n, 3) for k in KS}, "MRR@5": round(rr / n, 3)}


def main():
    download_papers()
    chunks = prepare_corpus(TECHNOLOGIES)
    qa = build_qa_set(chunks)
    print(f"평가 질문 {len(qa)}개")

    results = {}
    for model in EMBEDDING_CANDIDATES:
        retriever = HybridRetriever(build_or_load_index(model, chunks), chunks, k=max(KS))
        results[f"Dense · {model}"] = evaluate(lambda q, t: retriever.dense(q, t), qa)
        print(model, results[f"Dense · {model}"])

    best = max(EMBEDDING_CANDIDATES, key=lambda m: (results[f"Dense · {m}"]["MRR@5"], results[f"Dense · {m}"]["Hit@5"]))
    retriever = HybridRetriever(build_or_load_index(best, chunks), chunks, k=max(KS))
    results["Sparse · BM25"] = evaluate(lambda q, t: retriever.sparse(q, t), qa)
    results[f"Hybrid · BM25 + {best}"] = evaluate(lambda q, t: retriever.invoke(q, t), qa)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "retrieval_eval.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    header = "| Retriever | " + " | ".join(next(iter(results.values())).keys()) + " |"
    lines = [header, "|" + "---|" * (len(header.split("|")) - 2)]
    lines += [f"| {name} | " + " | ".join(str(v) for v in m.values()) + " |" for name, m in results.items()]
    table = "\n".join(lines)
    (OUTPUT_DIR / "retrieval_eval.md").write_text(
        f"# Retrieval Evaluation\n\n- 질문 수 : {len(qa)} (기술별 {N_PER_TECH})\n- 최고 Dense 임베딩 : {best}\n\n{table}\n",
        encoding="utf-8",
    )
    print("\n" + table + f"\n\n최고 Dense 임베딩 : {best}")


if __name__ == "__main__":
    main()
