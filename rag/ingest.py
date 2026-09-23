"""PREPROCESSING : Document Loader → Text Splitter → Embedding → Vector Store."""

import json
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, INDEX_DIR, MAX_DOC_PAGES, PAPER_DIR
from rag.embeddings import LocalEmbeddings, slugify

CHUNKS_PATH = INDEX_DIR / "chunks.json"


def _clean(text: str) -> str:
    text = re.sub(r"-\n(?=[a-z])", "", text)   # 줄바꿈 하이픈 결합
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_papers(technologies: dict) -> list[Document]:
    """기술별 논문 PDF를 페이지 단위로 로드하고 메타데이터(tech, source_id, page)를 부여."""
    pages: list[Document] = []
    for key, tech in technologies.items():
        path = PAPER_DIR / tech["file"]
        if not path.exists():
            raise FileNotFoundError(f"{path} 없음 - `uv run python scripts/download_papers.py` 실행")
        for d in PyPDFLoader(str(path)).load():
            pages.append(
                Document(
                    page_content=_clean(d.page_content),
                    metadata={
                        "tech": key,
                        "source_id": tech["source_id"],
                        "title": tech["paper_title"],
                        "page": d.metadata.get("page", 0) + 1,
                    },
                )
            )
    if len(pages) > MAX_DOC_PAGES:
        raise ValueError(f"RAG 문서가 {len(pages)} 페이지로 제한({MAX_DOC_PAGES})을 초과")
    return pages


def split_documents(pages: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = [c for c in splitter.split_documents(pages) if len(c.page_content) > 80]
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i          # 검색 평가(Hit Rate, MRR)용 청크 ID
    return chunks


def save_chunks(chunks: list[Document]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_PATH.write_text(
        json.dumps([{"text": c.page_content, "metadata": c.metadata} for c in chunks], ensure_ascii=False),
        encoding="utf-8",
    )


def load_chunks() -> list[Document]:
    raw = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return [Document(page_content=r["text"], metadata=r["metadata"]) for r in raw]


def build_or_load_index(model_name: str, chunks: list[Document], rebuild: bool = False) -> FAISS:
    embeddings = LocalEmbeddings(model_name)
    path = INDEX_DIR / slugify(model_name)
    if path.exists() and not rebuild:
        return FAISS.load_local(str(path), embeddings, allow_dangerous_deserialization=True)
    vs = FAISS.from_documents(chunks, embeddings, normalize_L2=True)   # 정규화 → 코사인 유사도 순위
    vs.save_local(str(path))
    return vs


def prepare_corpus(technologies: dict, rebuild: bool = False) -> list[Document]:
    """청크를 캐시에서 읽거나 새로 생성."""
    if CHUNKS_PATH.exists() and not rebuild:
        return load_chunks()
    pages = load_papers(technologies)
    chunks = split_documents(pages)
    save_chunks(chunks)
    print(f"[ingest] {len(pages)} pages → {len(chunks)} chunks")
    return chunks
