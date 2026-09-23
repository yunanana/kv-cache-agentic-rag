"""평가 관점별 평가 대상·기준 정의 (1인 과제 범위 : 2. 시장성, 4. 도메인 적용).

rating 의미 : 해당 관점에서 기술이 '유리하게 인식되는 정도' (기술 간 우열 판정이 아님)
- rag_questions : 논문(RAG)에서 확인할 질문 (영어 - 논문 원문 언어와 일치)
- web_queries   : 웹 검색 질의. 확증편향 방지를 위해 기준마다 비판/리스크 질의를 함께 둔다.
"""

TECH_RESEARCH_QUESTIONS = [
    "What problem does the method address regarding KV cache memory in LLM inference?",
    "What is the core mechanism or architecture of the method and how does it reduce KV cache memory pressure?",
    "What are the main reported results such as compression ratio, memory capacity, speedup, throughput or accuracy?",
    "What experimental setup (models, benchmarks, hardware, context lengths) was used to evaluate the proposed method?",
    "What are the limitations, assumptions, overheads or unsupported settings of the method?",
]

MARKET_CRITERIA = [
    {
        "id": "M1",
        "name": "시장 규모·성장성",
        "target": "기술이 속한 시장(LLM 추론 최적화 SW / CXL·메모리 확장 HW)의 규모와 성장 전망",
        "rubric": "높음: 시장 리포트·업계 발표로 뚜렷한 성장세 확인 / 중간: 성장 기대는 있으나 근거가 간접적(인접 시장 수치 등) "
                  "/ 낮음: 수요 불확실·축소 신호 / 판단 유보: 근거 부족",
        "rag_questions": [
            "What trends in context length, model size or memory demand motivate this work?",
        ],
        "web_queries": [
            "{category} market size growth forecast",
            "{category} demand risks challenges",
        ],
    },
    {
        "id": "M2",
        "name": "상용화·채택 현황",
        "target": "실제 제품 출시, 서비스 도입, 오픈소스 통합 사례",
        "rubric": "높음: 상용 제품 또는 주요 서빙 스택에 탑재되어 운영 중 / 중간: 시제품·PoC·실험적 통합 "
                  "/ 낮음: 논문·연구 단계 / 판단 유보: 근거 부족",
        "rag_questions": [
            "How is the method implemented and evaluated, and does it integrate with existing inference or serving systems?",
        ],
        "web_queries": [
            "{search_name} adoption production deployment",
            "{search_name} limitations criticism",
        ],
    },
    {
        "id": "M3",
        "name": "생태계 지지",
        "target": "지원 프레임워크(vLLM, SGLang, TensorRT-LLM 등), 표준화 동향, 파트너·벤더 참여",
        "rubric": "높음: 복수 주요 프레임워크 지원 또는 산업 표준 기반 / 중간: 일부 커뮤니티 구현·표준 논의 "
                  "/ 낮음: 독자 구현만 존재 / 판단 유보: 근거 부족",
        "rag_questions": [
            "Which frameworks, hardware platforms, interconnects or standards does the method build on or require?",
        ],
        "web_queries": [
            "{category} support vLLM SGLang TensorRT-LLM",
            "{category} industry standard ecosystem vendors",
        ],
    },
]

DOMAIN_CRITERIA = [
    {
        "id": "D1",
        "name": "비용 효율 (TCO)",
        "target": "같은 워크로드를 처리하는 데 필요한 GPU·메모리 비용의 절감 여지",
        "rubric": "높음: 추가 비용 없이 GPU당 수용량 확대가 수치로 확인 / 중간: 절감 효과는 있으나 추가 투자·조건 필요 "
                  "/ 낮음: 비용 증가 요인이 더 큼 / 판단 유보: 근거 부족",
        "rag_questions": [
            "How much KV cache memory reduction or memory capacity expansion does the method achieve, and at what hardware cost?",
        ],
        "web_queries": ["{search_name} cost savings datacenter TCO"],
    },
    {
        "id": "D2",
        "name": "처리량·지연",
        "target": "대규모 동시 요청 환경에서의 throughput, latency, SLO 영향",
        "rubric": "높음: 서빙 조건(배치·긴 문맥)에서 처리량 향상과 지연 유지가 확인 / 중간: 특정 조건에서만 개선 "
                  "/ 낮음: 지연·오버헤드 증가 / 판단 유보: 근거 부족",
        "rag_questions": [
            "What throughput or latency improvements are reported, and under what setup (models, batch size, context length, hardware)?",
        ],
        "web_queries": ["{search_name} throughput latency benchmark LLM serving"],
    },
    {
        "id": "D3",
        "name": "품질 유지",
        "target": "모델 정확도·출력 품질 손실 위험 (서비스 품질 SLA 관점)",
        "rubric": "높음: 품질 손실이 없거나 무시 가능함이 여러 벤치마크로 확인 / 중간: 조건부 손실 존재 "
                  "/ 낮음: 유의미한 손실 / 판단 유보: 근거 부족",
        "rag_questions": [
            "Does the method affect model accuracy or output quality? Which benchmarks and accuracy results are reported?",
        ],
        "web_queries": ["{search_name} accuracy quality degradation"],
    },
    {
        "id": "D4",
        "name": "도입 용이성",
        "target": "기존 GPU 클러스터·서빙 스택과의 호환성, 추가 하드웨어, 운영 복잡도",
        "rubric": "높음: 기존 인프라에 SW 변경만으로 도입 / 중간: 일부 커널·시스템 수정 또는 제한적 HW 추가 "
                  "/ 낮음: 신규 인프라·장비 필요 / 판단 유보: 근거 부족",
        "rag_questions": [
            "What hardware, software changes or system integration are required to deploy the method, and what overheads does it add?",
        ],
        "web_queries": ["{search_name} deployment infrastructure requirements"],
    },
]
