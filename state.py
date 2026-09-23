"""Graph State 정의.

시장성 평가·도메인 평가 에이전트는 병렬(fan-out)로 실행되므로
- 각 관점 결과는 서로 다른 키(market_eval / domain_eval)에만 쓰고
- 여러 노드가 함께 추가하는 값(sources, trace)은 reducer(operator.add)로 누적한다.
"""

import operator
from typing import Annotated, TypedDict


class ReportState(TypedDict, total=False):
    # 입력
    technologies: dict                  # {"sw": TechSpec, "hw": TechSpec} - config.TECHNOLOGIES
    domain: dict                        # 평가 도메인 - config.DOMAIN

    # 에이전트별 결과 (키 분리)
    tech_profiles: dict                 # 기술 조사 에이전트 : {"sw": TechProfile, "hw": TechProfile}
    market_eval: dict                   # 시장성 평가 에이전트 : {"sw": PerspectiveEvaluation, "hw": ...}
    domain_eval: dict                   # 도메인 평가 에이전트 : {"sw": PerspectiveEvaluation, "hw": ...}
    synthesis: dict                     # 평가 종합 에이전트 : Synthesis
    report_md: str                      # 보고서 생성 에이전트 : 마크다운 보고서
    review: dict                        # 보고서 검토 : {"passed", "issues", "pages"}
    revision_count: int                 # 보고서 재작성 횟수
    outputs: dict                       # 산출물 경로 {"md", "html", "pdf"}

    # 병렬 노드가 함께 쓰는 누적 키
    sources: Annotated[list[dict], operator.add]     # 인용 가능한 출처 레지스트리 (논문 + 웹)
    trace: Annotated[list[dict], operator.add]       # RAG 검색/판정 로그
