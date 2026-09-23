"""오픈소스 임베딩 (fastembed, ONNX 기반 로컬 추론 - API 비용 없음)."""

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings

from config import MODEL_CACHE_DIR


class LocalEmbeddings(Embeddings):
    """fastembed 모델을 LangChain Embeddings 인터페이스로 감싼 클래스.

    문서는 passage_embed, 질의는 query_embed 를 사용해 모델별 prefix 규칙을 따른다.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name, cache_dir=str(MODEL_CACHE_DIR))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed(text))).tolist()


def slugify(model_name: str) -> str:
    return model_name.replace("/", "__")
