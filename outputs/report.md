# KV cache 최적화 기술 다관점 평가 보고서

## SUMMARY
- TurboQuant과 ITME는 모두 LLM 추론에서 KV cache 메모리 문제 해결을 목표로 하며, 품질 유지 측면에서 TurboQuant은 저자 보고 기준 무손실 압축을 입증했고, ITME는 설계상 정확도 손실이 없다고 주장하나 수치 보고는 없다.
- 두 기술 모두 현재 연구·프로토타입 단계로, 공식 상용 제품 출시나 주요 LLM 서빙 스택 내 공식 통합 근거는 부족하다.
- TurboQuant은 소프트웨어 기반 압축으로 추가 하드웨어 투자 없이 GPU 메모리 수용량 확대와 비용 절감 효과가 수치로 확인되나, 처리량·지연에서 일부 오버헤드가 존재하며 대규모 분산 환경 적용 검증은 부족하다.
- ITME는 CXL-하이브리드 메모리 기반 대규모 메모리 확장과 I/O 병목 완화로 최대 35.7% 처리량 향상 실험 결과가 있으나, 신규 하드웨어 및 복잡한 시스템 통합이 요구되고 직접적인 비용 절감 수치는 논문에 제시되지 않았다.
- 시장성 관점에서는 TurboQuant이 LLM 추론 최적화 SW 시장 내 간접적 성장 근거를, ITME는 CXL 메모리 확장 시장 내 AI/ML 추론 부문 성장 근거를 바탕으로 각각 중간·높음 등급을 받았다.
- 두 기술은 기술적 조합 가능성이 있으나, 실제 통합의 필요성 및 효과는 별도 검토가 필요하며, 다양한 LLM 모델과 상용 환경에서의 장기 운영 검증 및 ROI 분석이 부족하다.

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
| M1 | 시장 규모·성장성 | 중간 | 중간 | LLM 추론 최적화 시장 성장 간접 근거, TurboQuant 고유 수치는 부재[3][1, p.2] | 높음 | 높음 | CXL 메모리 확장 시장 내 AI/ML 추론 부문 고성장 보고[4][2, p.1] |
| M2 | 상용화·채택 현황 | 중간 | 중간 | 논문 실험 검증 및 일부 간접적 생산 환경 적용 사례 있으나 공식 상용화 근거 부족[1, p.15][5] | 낮음 | 높음 | 논문 기반 프로토타입 단계, 상용 제품 출시 근거 없음[2, p.1][6] |
| M3 | 생태계 지지 | 낮음 | 중간 | TurboQuant 고유 프레임워크 통합·표준화 근거 미확인[7][8] | 중간 | 중간 | vLLM 내 구현 평가, 공식 다중 프레임워크 통합 근거는 미확인[2, p.9][9] |

#### 해석
- **시장 규모·성장성**: TurboQuant은 LLM 추론 최적화 SW 시장의 성장 전망에 기반하나, 기술 고유 시장 점유율 근거는 부족하다. ITME는 CXL 메모리 확장 시장 내 AI/ML 추론 부문 성장세가 뚜렷해 간접적 시장성 근거가 강하다.
- **상용화·채택 현황**: TurboQuant은 논문 실험과 일부 간접적 생산 환경 적용 사례가 있으나 공식 상용화 근거는 부족하다. ITME는 논문 기반 프로토타입 단계로 상용 제품 출시 근거가 없다.
- **생태계 지지**: TurboQuant은 주요 LLM 엔진 내 공식 통합 근거가 미흡하며, ITME는 일부 프레임워크 내 구현은 있으나 공식 다중 프레임워크 지원 및 표준화 참여 근거는 제한적이다.

### 4.2 도메인 적용 관점: 데이터센터·클라우드 LLM 서빙

| 기준 ID | 기준 | TurboQuant 등급 | 신뢰도 | 근거 요약 | ITME 등급 | 신뢰도 | 근거 요약 |
|---|---|---|---|---|---|---|---|
| D1 | 비용 효율 (TCO) | 높음 | 높음 | 4배 압축 시 품질 유지, GPU당 수용량 확대 및 비용 절감 사례 보고[10][1, p.17] | 중간 | 중간 | 최대 35.7% 처리량 향상 보고, 신규 하드웨어 투자 필요[2, p.1][11] |
| D2 | 처리량·지연 | 중간 | 높음 | 일부 환경에서 처리량 20~34% 저하, 지연 60~68% 증가 보고, 버스트 부하 시 SLO 유지 기여[5] | 중간 | 중간 | 최대 35.7% 처리량 향상 및 지연 완화 보고, FPGA 오버헤드 및 인프라 조건 영향[2, p.11] |
| D3 | 품질 유지 | 높음 | 높음 | 4배 압축 시 리콜 점수 0.997로 무손실 확인, 다양한 모델에서 무손실 보고[1, p.17][12] | 높음(설계상) | 중간 | KV cache 데이터 변경 없이 무손실 구조 주장, 정확도 수치 미보고[2, p.2] |
| D4 | 도입 용이성 | 중간 | 중간 | 소프트웨어 변경만으로 도입 가능, 대규모 분산 환경 검증 부족, 일부 처리량·지연 저하 보고[1, p.4][5] | 낮음 | 중간 | CXL-HW, 고속 네트워크, FPGA 등 신규 하드웨어 및 복잡한 시스템 통합 요구[2, p.8][13] |

#### 해석
- **비용 효율**: TurboQuant은 추가 하드웨어 없이 GPU당 수용량 확대와 비용 절감이 수치로 확인된다. ITME는 처리량 향상과 간접적 비용 절감 가능성을 보이나, 신규 인프라 투자 필요성이 비용 효율성에 영향을 준다.
- **처리량·지연**: TurboQuant은 일부 환경에서 처리량 저하와 지연 증가가 보고되나, 버스트 부하 시 SLO 유지에 기여한다. ITME는 하드웨어 기반 처리량 향상과 지연 완화가 보고되나, FPGA 오버헤드와 인프라 조건에 따른 성능 변동성이 존재한다.
- **품질 유지**: TurboQuant은 저자 보고 기준 무손실 압축을 입증했다. ITME는 설계상 정확도 손실이 없다고 주장하나, 수치 보고는 없다.
- **도입 용이성**: TurboQuant은 소프트웨어 변경만으로 도입 가능하나 대규모 분산 환경 검증이 부족하다. ITME는 신규 하드웨어 및 복잡한 시스템 통합이 요구된다.

## 5. 시사점

| 주제 | 시장성 관점 | 도메인 관점 | 엇갈리는 이유 |
|---|---|---|---|
| 비용 효율 (TCO) - TurboQuant | 추가 하드웨어 투자 없이 비용 절감 효과가 수치로 확인됨 | 처리량·지연 오버헤드와 대규모 환경 적용 한계가 비용 효율성에 영향 | 시장은 SW 기반 비용 절감에 주목하나, 도메인은 성능 영향과 환경별 검증 부족을 고려 |
| 비용 효율 (TCO) - ITME | 대규모 메모리 확장과 처리량 향상으로 비용 절감 가능성 인정 | 신규 하드웨어 투자와 시스템 복잡성으로 실제 비용 절감 확보 어려움 | 시장은 성장 잠재력에 주목하나, 도메인은 초기 투자 부담과 통합 난이도에 주목 |
| 처리량·지연 - TurboQuant | 일부 오버헤드 존재하나 SLO 유지 기여로 긍정적 평가 | 명확한 처리량 저하 및 지연 증가로 비용·품질 부담으로 인식 | 시장은 오버헤드를 허용 가능한 수준으로 보나, 도메인은 성능 저하를 부담으로 평가 |
| 처리량·지연 - ITME | 하드웨어 기반 처리량 향상과 지연 완화 가능성 강조 | 하드웨어 오버헤드와 인프라 조건에 따른 성능 변동성 문제로 인식 | 시장은 하드웨어 성능 향상에 주목하나, 도메인은 환경 의존성 문제를 지적 |
| 도입 용이성 - TurboQuant | 소프트웨어 변경만으로 도입 가능해 용이성 높음 | 처리량·지연 저하 및 대규모 환경 검증 부족으로 제한적 가능성 | 시장은 SW 접근의 도입 편의성에 주목하나, 도메인은 운영상 고려사항을 강조 |
| 도입 용이성 - ITME | 신규 하드웨어 및 복잡한 시스템 통합 요구로 용이성 낮음 | 도메인도 동일하게 신규 인프라 구축 필요성 인정 | 시장과 도메인 모두 도입 복잡성에 대해 일치된 평가 |

### 두 기술의 인식 차이
TurboQuant은 소프트웨어 기반 압축으로 비용 절감과 도입 편의성에 대한 시장의 기대가 크나, 도메인에서는 처리량·지연 오버헤드와 대규모 환경 적용 검증 부족을 우려한다. ITME는 하드웨어 기반 메모리 확장으로 시장에서 성장 잠재력과 처리량 향상을 주목받으나, 도메인에서는 신규 인프라 투자와 시스템 통합 복잡성으로 인한 도입 장벽을 강조한다.

### 보완·병행 가능성
TurboQuant의 소프트웨어적 데이터 압축과 ITME의 하드웨어 기반 메모리 확장 기술은 기술적으로 상호 보완 가능하다. TurboQuant은 KV cache 데이터를 압축해 ITME가 요구하는 대용량 메모리 부담을 경감할 수 있고, ITME는 압축된 데이터를 대규모 메모리 공간에서 효율적으로 저장·관리하여 처리량과 지연 문제를 완화할 수 있다. 다만, 본 보고서는 특정 기술 채택이나 추천을 하지 않으며, 실제 통합의 필요성 및 효과는 별도 검토가 필요하다.

## 6. 한계점
본 보고서는 공개된 논문 및 웹 자료를 기반으로 평가하였으며, 각 기술의 저자 자체 실험 결과에 의존하는 부분이 많다. 공개 정보의 한계로 인해 상용화 현황, 대규모 분산 환경 적용, 다양한 하드웨어 플랫폼에서의 성능 검증 등에서 정보가 부족하다. 확증편향 방지를 위해 다수 출처를 교차 검증하고, 기술별 주장과 반대 근거를 균형 있게 반영하였다.

## REFERENCE

1. Zandieh, A., Daliri, M., Hadian, M., & Mirrokni, V.(2025). TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate. *arXiv*, 2504.19874. https://arxiv.org/abs/2504.19874
2. Jang, H., Min, Y., Kim, S., Ahn, T., Kim, H., Joo, Y., Kim, H., & Kim, J.(2026). ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories. *arXiv*, 2606.12556. https://arxiv.org/abs/2606.12556
3. growthmarketreports.com(n.d.). *KV-Cache Offloading Infrastructure Market Research Report 2033*. growthmarketreports.com, https://growthmarketreports.com/report/kv-cache-offloading-infrastructure-market
4. marketintelo.com(n.d.). *CXL Memory Expansion Market Research Report 2034*. marketintelo.com, https://marketintelo.com/report/cxl-memory-expansion-market
5. o-mega.ai(n.d.). *Google TurboQuant in August 2026: Where It Actually Runs*. o-mega.ai, https://o-mega.ai/articles/google-turboquant-the-2026-llm-compression-guide
6. stocktitan.net(n.d.). *Penguin Solutions Introduces Industry's First Production-Ready CXL-Based KV Cache Server*. stocktitan.net, https://www.stocktitan.net/news/PENG/penguin-solutions-introduces-industry-s-first-production-ready-cxl-pxfpc1e4d2nz.html
7. inferenceengineering.tech(n.d.). *vLLM vs SGLang vs TensorRT-LLM - Inference Engineering*. inferenceengineering.tech, https://inferenceengineering.tech/learn/vllm-vs-sglang-vs-tensorrt-llm
8. jarvislabs.ai(n.d.). *SGLang vs vLLM: H100 Benchmarks, with TensorRT-LLM*. jarvislabs.ai, https://jarvislabs.ai/blog/vllm-sglang-trtllm-comparison
9. asteralabs.com(n.d.). *How CXL Memory Expansion Improves AI Economics*. asteralabs.com, https://www.asteralabs.com/resources/blog/inference-tokenomics-how-cxl-memory-expansion-improves-ai-economics
10. spheron.network(n.d.). *Google TurboQuant: 6x KV Cache Compression for LLM ...*. spheron.network, https://www.spheron.network/blog/google-turboquant-llm-compression-gpu-cloud
11. ownyourai.com(n.d.). *CXL-SpecKV: A Disaggregated FPGA Speculative KV-Cache for Datacenter LLM Serving – Own Your AI*. ownyourai.com, https://ownyourai.com/cxl-speckv-a-disaggregated-fpga-speculative-kv-cache-for-datacenter-llm-serving
12. blog.everpuredata.com(n.d.). *TurboQuant Compresses KV Cache by 5X. Does That ...*. blog.everpuredata.com, https://blog.everpuredata.com/purely-technical/turboquant-compresses-kv-cache-by-5x-does-that-mean-you-need-less-memory
13. asteralabs.com(n.d.). *How CXL Transforms RAG and KV Cache Performance*. asteralabs.com, https://www.asteralabs.com/resources/blog/breaking-through-the-memory-wall-how-cxl-transforms-rag-and-kv-cache-performance
