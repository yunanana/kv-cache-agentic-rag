"""LLM 생성 헬퍼."""

from langchain_openai import ChatOpenAI

from config import JUDGE_MODEL, LLM_MODEL, VERIFY_MODEL


def _chat(model: str) -> ChatOpenAI:
    # gpt-5 계열 reasoning 모델은 temperature 조정을 지원하지 않음
    if model.startswith(("gpt-5", "o1", "o3", "o4")):
        return ChatOpenAI(model=model)
    return ChatOpenAI(model=model, temperature=0)


def get_llm() -> ChatOpenAI:
    return _chat(LLM_MODEL)


def get_judge() -> ChatOpenAI:
    return _chat(JUDGE_MODEL)


def get_verifier() -> ChatOpenAI:
    return _chat(VERIFY_MODEL)
