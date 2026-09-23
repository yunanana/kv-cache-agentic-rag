"""프로젝트 전역 설정 : 경로, 모델, 대상 기술, 평가 도메인."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# ── 경로 ──────────────────────────────────────────────
DATA_DIR = ROOT / "data"
PAPER_DIR = DATA_DIR / "papers"
INDEX_DIR = DATA_DIR / "index"
EVAL_DIR = DATA_DIR / "eval"
MODEL_CACHE_DIR = DATA_DIR / "models"
OUTPUT_DIR = ROOT / "outputs"

# ── LLM ───────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")      # 조사·평가·보고서 생성
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4.1-mini")  # 관련성 판정·보고서 검토

# ── RAG ───────────────────────────────────────────────
# 오픈소스 임베딩 : scripts/eval_retrieval.py 실험 결과(Hit Rate@K, MRR)로 선정
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "snowflake/snowflake-arctic-embed-s")
EMBEDDING_CANDIDATES = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "snowflake/snowflake-arctic-embed-s",
]
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 5
MAX_DOC_PAGES = 200          # 가이드 제약 : RAG 문서 총 200 페이지 이내
MAX_QUERY_REWRITE = 1        # Agentic RAG : 관련 문서가 없을 때 질의 재작성 횟수
MAX_REPORT_REVISION = 2      # 보고서 검토 후 재작성 횟수
MAX_REPORT_PAGES = 10        # 가이드 제약 : 보고서 10 페이지 이내

# ── 평가 대상 (2안 : Human 기반 선정, Doc Pool 진영별 1개) ──────
TECHNOLOGIES = {
    "sw": {
        "key": "sw",
        "source_id": "P-SW",
        "camp": "SW 진영 - 데이터를 작게 만들자 (압축/양자화)",
        "name": "TurboQuant",
        "category": "KV cache quantization",
        "search_name": "Google TurboQuant KV cache",
        "paper_title": "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate",
        "arxiv_id": "2504.19874",
        "file": "turboquant_2504.19874.pdf",
        "citation": (
            "Zandieh, A., Daliri, M., Hadian, M., & Mirrokni, V.(2025). "
            "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate. "
            "*arXiv*, 2504.19874."
        ),
        "selection_reason": (
            "이미 생성된 KV cache를 사후에 3비트 수준으로 양자화하는 방식으로, 기존 GPU/HBM 인프라 위에서 "
            "SW만으로 적용 가능한 'SW 진영'의 전형. 데이터 비의존(online) 방식이라 서빙 시스템 통합이 쉽고, "
            "Google Research 발표 이후 산업계 반응 자료가 많아 시장성 관점 평가 근거 확보에 유리함."
        ),
    },
    "hw": {
        "key": "hw",
        "source_id": "P-HW",
        "camp": "HW 진영 - 담을 공간을 넓히자 (메모리/스토리지 계층 확장)",
        "name": "ITME (SK hynix, CXL-Hybrid 계층 메모리)",
        "category": "CXL memory expansion for LLM KV cache",
        "search_name": "CXL memory KV cache LLM inference",
        "paper_title": "ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories",
        "arxiv_id": "2606.12556",
        "file": "itme_2606.12556.pdf",
        "citation": (
            "Jang, H., Min, Y., Kim, S., Ahn, T., Kim, H., Joo, Y., Kim, H., & Kim, J.(2026). "
            "ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories. "
            "*arXiv*, 2606.12556."
        ),
        "selection_reason": (
            "KV cache 원본은 유지한 채 CXL 기반 분리형(disaggregated) 메모리로 용량을 넓히는 'HW 진영'의 대표 접근. "
            "메모리 제조사(SK hynix)가 직접 제안한 구조로 CXL 표준·제품화 흐름과 맞닿아 있어 시장성 근거가 풍부하고, "
            "SW 압축(TurboQuant)과 정반대 방향이라 관점별 평가 대비가 선명함."
        ),
    },
}

# ── 도메인 적용 관점 : 평가 도메인 ─────────────────────────
DOMAIN = {
    "name": "데이터센터·클라우드 LLM 서빙",
    "description": (
        "다수 사용자의 요청을 GPU 클러스터에서 처리하는 대규모 추론 서비스. "
        "처리량(throughput)·지연(SLO)·총소유비용(TCO)에 민감하고, 긴 문맥과 동시 사용자 증가로 "
        "KV cache가 GPU 메모리 병목이 되는 대표 환경."
    ),
}
