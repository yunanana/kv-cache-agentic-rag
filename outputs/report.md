# KV cache 최적화 기술 다관점 평가 보고서

## SUMMARY
- **품질** : TurboQuant은 저자 보고 기준 Llama-3.1-8B-Instruct의 Needle-In-A-Haystack 실험에서 KV cache를 25%만 사용하는 4배 압축 조건에서도 원본과 같은 리콜 0.997을 기록했다[1, p.17, p.19]. 다만 이는 해당 실험의 점수 유지이며 무손실 압축의 입증은 아니다. ITME는 원본 KV를 그대로 보관하는 구조이나 정확도 측정 수치는 보고하지 않았다[2, p.2].
- **성능·비용** : ITME는 저자 보고 기준 CPU 오프로딩 대비 최대 35.7% 처리량 향상을 보였으나[2, p.1, p.11], CXL-하이브리드 메모리·RDMA·FPGA 등 신규 하드웨어가 필요하고 비용 수치는 제시하지 않았다[2, p.2, p.8]. TurboQuant의 메모리 절감은 비용 절감의 간접 근거이며, 웹 자료가 인용한 vLLM 연구는 FP8·BF16 대비 처리량 20~34% 저하와 최악 구성의 지연 60~68% 증가도 함께 보고한다[5][8].
- **시장·채택** : 두 기술 모두 공식 상용 제품이나 서빙 스택 기본 탑재 근거는 없다. TurboQuant은 vLLM·SGLang 기반 구현 보고가 있으나 Google 실서비스 적용은 공개 근거가 없고[5], ITME는 FPGA·CMM 기반 프로토타입 단계다[2, p.1]. 시장성 등급은 TurboQuant 중간(인접 시장 근거), ITME 높음(CXL 시장 추정치)이다[3][4].
- **관점 간 상충** : 시장 자료는 TurboQuant의 메모리 절감과 ITME가 속한 CXL 시장의 성장을 부각하지만, 도메인 관점에서는 TurboQuant의 정상 부하 처리량·지연 저하와 ITME의 신규 인프라 투자 부담이 제약으로 남는다.
- **한계** : 핵심 수치 대부분이 저자 자체 실험이고 웹 출처는 2차 자료라, 대규모 상용 환경에서의 검증과 실제 TCO는 확인되지 않았다.

## 1. 분석 배경
LLM(대형 언어 모델) 추론에서 KV cache는 모델의 문맥 정보를 저장하는 핵심 메모리 구조로, 모델 크기와 문맥 길이가 증가함에 따라 KV cache 크기도 급격히 커져 메모리 사용량과 계산 속도의 병목이 된다[1, p.2]. 이 병목은 LLM 서빙 환경에서 처리량 저하, 지연 증가, 비용 상승으로 이어져 최적화가 필수적이다.

KV cache 최적화는 크게 소프트웨어(SW)와 하드웨어(HW) 두 진영으로 나뉜다. SW 진영은 기존 GPU/HBM 인프라 위에서 데이터 압축·양자화 등으로 메모리 사용량을 줄이는 접근법이며, HW 진영은 CXL(Compute Express Link) 기반 분리형 메모리 확장 등으로 물리적 메모리 용량을 늘려 병목을 완화한다.

이 두 접근법은 기술적 특성, 도입 방식, 비용 구조, 성능 영향 등에서 차이가 크므로, 시장성 및 도메인 적용 관점에서 다각도로 평가하여 상호 보완 가능성 및 한계점을 명확히 이해할 필요가 있다.

## 2. 기술 선정

| 진영 | 기술명 | 선정 사유 |
|---|---|---|
| SW | TurboQuant | KV cache를 사후 3비트 수준으로 온라인 벡터 양자화하여 기존 GPU/HBM 인프라에서 SW만으로 적용 가능. Google Research 발표 후 산업계 반응 자료가 많아 시장성 평가 근거 확보에 유리함. |
| HW | ITME | CXL 기반 분리형 하이브리드 메모리로 KV cache 원본 유지하며 용량 확장. SK hynix 제안, CXL 표준·제품화 흐름과 연계되어 시장성 근거 풍부하며, SW 압축과 정반대 방향으로 관점별 평가 대비가 명확함. |

## 3. 기술 개요

### 3.1 SW: TurboQuant
- **핵심 접근**: LLM 추론 시 KV cache 데이터를 온라인 벡터 양자화 기법으로 압축하여 메모리 사용량을 줄임[1, p.4]. 데이터 의존적 튜닝이나 사전 학습 없이 즉시 적용 가능하며, 내적 왜곡 최소화 설계로 정확도 저하를 방지함[1, p.2, p.4].
- **저자 보고 성과**: Llama-3.1-8B-Instruct 모델에서 4배 압축(메모리 25% 사용) 시에도 원본과 동일한 리콜 점수(0.997)를 달성함[1, p.17, p.19]. NVIDIA A100 GPU 환경에서 1536·3072차원 임베딩 데이터셋으로 실험 수행[1, p.15, p.19].
- **한계**: 하드웨어 최적화 및 대규모 분산 환경 적용에 대한 구체적 언급이 없으며, 실험 범위가 제한적임.

### 3.2 HW: ITME
- **핵심 접근**: CXL-하이브리드 메모리를 활용한 TB급 계층형 메모리 확장 아키텍처로, GPU 서버가 RDMA를 통해 대용량 KV cache와 모델 가중치에 접근 가능하도록 함[2, p.1, p.2]. NVMe SSD와 DRAM 캐시 간 하드웨어 선행 로딩, 다단계 DMA 파이프라인으로 저장소·네트워크 지연을 완화함[2, p.8, p.11].
- **저자 보고 성과**: SK hynix CMM과 PCIe Gen5 NVMe SSD 기반 프로토타입에서 CPU 오프로딩 대비 최대 35.7% 처리량 향상 보고[2, p.1, p.11]. Llama-3.1 8B/70B 모델과 ShareGPT 데이터셋으로 대규모 KV cache 상황에서 효율적 메모리 관리 및 지연 완화 확인[2, p.9].
- **한계**: 활성화된 KV cache 등 지연 민감 데이터는 GPU/호스트 메모리에 유지해야 하며, FPGA 프로토타입의 하드웨어 오버헤드 존재[2, p.2, p.11]. 실험은 특정 모델·데이터셋에 한정되어 일반화 판단 유보.

## 4. 관점별 평가

### 4.1 시장성 관점

| 기준 ID | 기준 | TurboQuant 등급 | 신뢰도 | 근거 요약 | ITME 등급 | 신뢰도 | 근거 요약 |
|---|---|---|---|---|---|---|---|
| M1 | 시장 규모·성장성 | 중간 | 중간 | 인접 시장인 KV cache 오프로딩 인프라 시장이 2024년 18.7억 달러에서 2033년 149.9억 달러(CAGR 23.6%)로 전망됨(시장조사기관 추정)[3]. 양자화 SW 고유 시장 수치는 미확인 | 높음 | 중간 | CXL 메모리 확장 시장 2025년 13억 달러에서 2034년 118억 달러(CAGR 28.7%), 그중 AI/ML 추론 부문은 매출 비중 38.5%·CAGR 약 32.6% 전망(시장조사기관 추정)[4]. ITME 고유 시장 수치는 없음 |
| M2 | 상용화·채택 현황 | 중간 | 중간 | 논문은 단일 A100 실험[1, p.15]. vLLM·SGLang 기반 구현·벤치마크 보고는 있으나 Google 실서비스 적용은 공개 근거 없음[5] | 낮음 | 높음 | FPGA·CMM 기반 프로토타입 단계[2, p.1]. 인접 제품인 CXL 기반 KV cache 서버(Penguin MemoryAI)는 출시됐으나 ITME 자체 제품 출시 근거는 없음[6] |
| M3 | 생태계 지지 | 중간 | 중간 | vLLM·SGLang 기반 구현·벤치마크 보고 존재[5]. 공식 기본 기능 탑재·표준화 근거는 미확인 | 중간 | 중간 | 논문은 vLLM 기반으로 구현·평가[2, p.9]. 인접 CXL 메모리 제품(Astera Leo)은 vLLM·TensorRT-LLM·SGLang 연동을 내세우나 ITME 자체 공식 통합 근거는 미확인[7] |

#### 해석
- **시장 규모·성장성**: TurboQuant은 KV cache 오프로딩 인프라처럼 인접 시장의 성장 전망만 확인되며 양자화 SW 고유 시장 수치는 없다. ITME는 자신이 속한 CXL 메모리 확장 시장, 특히 AI/ML 추론 부문의 성장 전망이 제시되지만 이 역시 시장조사기관의 추정치이며 ITME 고유 수치는 아니다.
- **상용화·채택 현황**: TurboQuant은 오픈소스 추론 엔진 위 구현·벤치마크가 보고된 실험적 통합 단계이며, Google 실서비스 적용은 공개 근거가 없다. ITME는 논문 기반 프로토타입 단계이며, 시장에 나온 CXL KV cache 서버는 ITME가 아닌 인접 제품이다.
- **생태계 지지**: TurboQuant은 vLLM·SGLang 기반 구현이 보고됐으나 공식 기본 기능 탑재는 확인되지 않았다. ITME는 vLLM 기반 구현 외에 공식 다중 프레임워크 지원·표준화 참여 근거가 없다.

### 4.2 도메인 적용 관점: 데이터센터·클라우드 LLM 서빙

| 기준 ID | 기준 | TurboQuant 등급 | 신뢰도 | 근거 요약 | ITME 등급 | 신뢰도 | 근거 요약 |
|---|---|---|---|---|---|---|---|
| D1 | 비용 효율 (TCO) | 중간 | 낮음 | 메모리 축소는 비용 절감 가능성의 간접 근거이며 실제 운영 TCO 측정과 구분 필요[8][1, p.19] | 중간 | 중간 | 최대 35.7% 처리량 향상 보고, 신규 하드웨어 투자 필요[2, p.1]. 인접 기술 자료는 간접 근거[9] |
| D2 | 처리량·지연 | 중간 | 중간 | 웹 자료가 인용한 vLLM 연구에서 FP8·BF16 대비 처리량 20~34% 저하, 최악 구성 지연 60~68% 증가, 대신 KV 용량 2.4~3.7배. 버스트 부하에서는 TTFT 급증을 막았다고 보고(2차 자료)[5] | 중간 | 중간 | 최대 35.7% 처리량 향상 및 지연 완화 보고, FPGA 오버헤드 및 인프라 조건 영향[2, p.11] |
| D3 | 품질 유지 | 높음 | 중간 | 저자 보고 기준 Llama-3.1-8B-Instruct의 Needle-In-A-Haystack 실험에서 원본과 같은 리콜 0.997. 해당 실험의 점수 유지이며 무손실 압축의 입증은 아님[1, p.19] | 판단 유보 | 중간 | KV cache 원본 유지 설계이나 정확도 측정 수치는 미보고[2, p.2] |
| D4 | 도입 용이성 | 중간 | 중간 | 사전 학습·데이터 의존 튜닝 없는 온라인 방식[1, p.4]. 대규모 분산 환경 검증은 없음 | 낮음 | 중간 | CXL-하이브리드 메모리, RDMA 네트워크, FPGA 프리페처 등 신규 하드웨어와 시스템 통합 필요[2, p.2, p.8]. 인접 CXL KV cache 구성도 전용 CXL 메모리 컨트롤러를 요구[10] |

#### 해석
- **비용 효율**: TurboQuant의 메모리 축소는 비용 절감 가능성의 간접 근거이며 실제 운영 TCO 절감액이 검증됐다는 뜻은 아니다. ITME도 처리량 향상과 비용 절감 가능성을 구분해야 하며 신규 인프라 투자 비용을 고려해야 한다.
- **처리량·지연**: TurboQuant은 일부 환경에서 처리량 저하와 지연 증가가 보고되나, 버스트 부하 시 SLO 유지에 기여한다. ITME는 하드웨어 기반 처리량 향상과 지연 완화가 보고되나, FPGA 오버헤드와 인프라 조건에 따른 성능 변동성이 존재한다.
- **품질 유지**: TurboQuant은 저자 보고 기준 해당 리콜 실험에서 점수 저하가 관측되지 않았다[1, p.19]. ITME는 원본 KV 유지 설계와 실제 정확도 측정을 구분해야 하며 정확도 측정 수치는 미보고다[2, p.2].
- **도입 용이성**: TurboQuant은 소프트웨어 변경만으로 도입 가능하나 대규모 분산 환경 검증이 부족하다. ITME는 신규 하드웨어 및 복잡한 시스템 통합이 요구된다.

## 5. 시사점

| 주제 | 시장성 관점 근거 | 도메인 관점 근거 | 엇갈리는 이유 |
|---|---|---|---|
| 비용 효율 - TurboQuant | 웹 자료는 메모리 축소에 따른 동시 사용자 증가를 비용 절감 시나리오로 제시(계산값)[8] | 논문은 비용·TCO를 측정하지 않음 | 시장 자료의 비용 수치는 추정이고, 도메인 평가는 측정된 운영 비용을 요구함 |
| 비용 효율 - ITME | 속한 CXL 메모리 확장 시장의 AI/ML 추론 부문 성장 전망(추정)[4] | CXL-하이브리드 메모리·RDMA·FPGA 등 신규 하드웨어가 필요하고 논문에 비용 수치 없음[2, p.2, p.8] | 시장 성장 전망이 개별 도입의 비용 효율을 뜻하지 않음 |
| 처리량·지연 - TurboQuant | 웹 자료는 버스트 부하에서 TTFT 급증을 막은 사례를 소개[5] | 같은 자료가 인용한 vLLM 연구는 FP8·BF16 대비 처리량 20~34% 저하, 최악 구성 지연 60~68% 증가를 보고[5] | 부하 조건(버스트 vs 정상)에 따라 평가가 달라짐 |
| 처리량·지연 - ITME | 저자 보고 기준 CPU 오프로딩 대비 최대 35.7% 처리량 향상[2, p.1, p.11] | FPGA 프로토타입의 하드웨어 오버헤드 등 실험 환경에 의존[2, p.11] | 저자 실험 조건과 실제 서빙 환경이 다를 수 있음 |
| 도입 용이성 - TurboQuant | 사전 학습·튜닝 없는 온라인 방식[1, p.4], vLLM·SGLang 기반 구현 보고[5] | 대규모 분산 환경 검증은 확인되지 않음 | 구현 용이성과 대규모 운영 검증은 별개 |
| 도입 용이성 - ITME | 인접 CXL KV cache 구성도 전용 CXL 메모리 컨트롤러를 요구[10] | 신규 하드웨어와 시스템 통합 필요[2, p.2, p.8] | 두 관점 모두 도입 장벽이 높다고 봄 |

### 두 기술의 인식 차이
TurboQuant은 웹 자료에서 메모리 절감과 버스트 부하 이점이 소개되지만[5][8], 도메인 관점에서는 정상 부하의 처리량·지연 저하와 대규모 환경 검증 부재가 제약으로 남는다[5]. ITME는 속한 CXL 메모리 시장의 성장 전망이 제시되지만(추정치)[4], 도메인 관점에서는 신규 인프라 투자와 시스템 통합 부담이 크다[2, p.2, p.8].

### 보완·병행 가능성
TurboQuant의 소프트웨어적 데이터 압축과 ITME의 하드웨어 기반 메모리 확장 기술은 기술적으로 상호 보완 가능하다. TurboQuant은 KV cache 데이터를 압축해 ITME가 요구하는 대용량 메모리 부담을 경감할 수 있고, ITME는 압축된 데이터를 대규모 메모리 공간에서 효율적으로 저장·관리하여 처리량과 지연 문제를 완화할 수 있다. 다만, 본 보고서는 특정 기술 채택이나 추천을 하지 않으며, 실제 통합의 필요성 및 효과는 별도 검토가 필요하다.

## 6. 한계점
본 보고서는 공개된 논문 및 웹 자료를 기반으로 평가하였으며, 각 기술의 저자 자체 실험 결과에 의존하는 부분이 많다. 공개 정보의 한계로 인해 상용화 현황, 대규모 분산 환경 적용, 다양한 하드웨어 플랫폼에서의 성능 검증 등에서 정보가 부족하다. 확증편향 방지를 위해 다수 출처를 교차 검증하고, 기술별 주장과 반대 근거를 균형 있게 반영하였다.

본 보고서는 멀티 에이전트 시스템이 생성한 초안의 자동 검토 미통과 항목에 대해 AI 도구로 논문·웹 출처를 대조하고 정정한 정정본이다. 이는 독립적인 사람 검수나 자동 검토 통과를 의미하지 않는다. 웹 출처는 대부분 블로그·시장조사 요약 등 2차 자료이며, 시장 규모 수치는 조사기관의 추정치다.

## REFERENCE

1. Zandieh, A., Daliri, M., Hadian, M., & Mirrokni, V.(2025). TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate. *arXiv*, 2504.19874. https://arxiv.org/abs/2504.19874
2. Jang, H., Min, Y., Kim, S., Ahn, T., Kim, H., Joo, Y., Kim, H., & Kim, J.(2026). ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories. *arXiv*, 2606.12556. https://arxiv.org/abs/2606.12556
3. growthmarketreports.com(n.d.). *KV-Cache Offloading Infrastructure Market Research Report 2033*. growthmarketreports.com, https://growthmarketreports.com/report/kv-cache-offloading-infrastructure-market
4. marketintelo.com(n.d.). *CXL Memory Expansion Market Research Report 2034*. marketintelo.com, https://marketintelo.com/report/cxl-memory-expansion-market
5. o-mega.ai(n.d.). *Google TurboQuant in August 2026: Where It Actually Runs*. o-mega.ai, https://o-mega.ai/articles/google-turboquant-the-2026-llm-compression-guide
6. stocktitan.net(n.d.). *Penguin Solutions Introduces Industry's First Production-Ready CXL-Based KV Cache Server*. stocktitan.net, https://www.stocktitan.net/news/PENG/penguin-solutions-introduces-industry-s-first-production-ready-cxl-pxfpc1e4d2nz.html
7. asteralabs.com(n.d.). *How CXL Memory Expansion Improves AI Economics*. asteralabs.com, https://www.asteralabs.com/resources/blog/inference-tokenomics-how-cxl-memory-expansion-improves-ai-economics
8. spheron.network(n.d.). *Google TurboQuant: 6x KV Cache Compression for LLM ...*. spheron.network, https://www.spheron.network/blog/google-turboquant-llm-compression-gpu-cloud
9. ownyourai.com(n.d.). *CXL-SpecKV: A Disaggregated FPGA Speculative KV-Cache for Datacenter LLM Serving – Own Your AI*. ownyourai.com, https://ownyourai.com/cxl-speckv-a-disaggregated-fpga-speculative-kv-cache-for-datacenter-llm-serving
10. asteralabs.com(n.d.). *How CXL Transforms RAG and KV Cache Performance*. asteralabs.com, https://www.asteralabs.com/resources/blog/breaking-through-the-memory-wall-how-cxl-transforms-rag-and-kv-cache-performance
