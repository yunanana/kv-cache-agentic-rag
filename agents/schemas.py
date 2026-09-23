"""에이전트 구조화 출력 스키마."""

from typing import Literal

from pydantic import BaseModel, Field


class TechProfile(BaseModel):
    one_liner: str = Field(description="기술을 한 문장으로 설명")
    problem_addressed: str = Field(description="해결하려는 KV cache 문제")
    core_mechanism: list[str] = Field(description="핵심 동작 방식 (인용 포함)")
    reported_results: list[str] = Field(description="저자 보고 주요 성과 수치 (인용 포함)")
    limitations: list[str] = Field(description="한계·가정·오버헤드 (인용 포함)")
    deployment_requirements: list[str] = Field(description="적용에 필요한 HW/SW 조건 (인용 포함)")


class CriterionAssessment(BaseModel):
    criterion_id: str
    criterion: str
    rating: Literal["높음", "중간", "낮음", "판단 유보"]
    rationale: str = Field(description="등급 판단 근거 요약 (인용 포함, 2~3문장)")
    supporting_evidence: list[str] = Field(description="등급을 지지하는 근거 (인용 포함)")
    counter_evidence: list[str] = Field(description="반대·한계·리스크 근거 (인용 포함). 없으면 '확인된 반대 근거 없음'")
    confidence: Literal["높음", "중간", "낮음"] = Field(description="근거의 양·독립성 기반 판단 신뢰도")


class PerspectiveEvaluation(BaseModel):
    assessments: list[CriterionAssessment]
    overall_view: str = Field(description="이 관점에서 기술이 어떻게 인식되는지 종합 (3~4문장, 인용 포함)")
    information_gaps: list[str] = Field(description="공개 정보로 확인하지 못한 부분")


class ConflictPoint(BaseModel):
    topic: str
    tech: str = Field(description="관련 기술 (SW / HW / 공통)")
    market_view: str
    domain_view: str
    why_diverge: str = Field(description="평가가 엇갈리는 이유")


class Synthesis(BaseModel):
    agreements: list[str] = Field(description="관점 간 평가가 일치하는 지점 (인용 포함)")
    conflicts: list[ConflictPoint] = Field(description="관점 간 평가가 상충하는 지점")
    tech_contrast: list[str] = Field(description="두 기술이 같은 관점에서 서로 다르게 인식되는 지점")
    complementarity: str = Field(description="SW·HW 접근의 보완·병행 가능성 (근거가 있을 때만)")
    caveats: list[str] = Field(description="종합 시 유의할 점 (정보 비대칭, 저자 자체 실험 의존 등)")


class ReviewResult(BaseModel):
    passed: bool
    issues: list[str] = Field(description="구체적인 수정 지시 목록")
