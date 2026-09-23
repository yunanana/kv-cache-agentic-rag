# KV cache 최적화 기술 다관점 평가 보고서

## SUMMARY

- TurboQuant과 ITME는 모두 LLM 추론에서 KV cache 메모리 병목 문제를 해결하기 위한 혁신적 기술로, 시장성 및 도메인 적용 관점에서 각각 다른 특성과 평가 결과를 보인다.
- 시장성 관점에서 두 기술 모두 높은 시장 성장 가능성을 보이나, 상용화 및 생태계 지지 단계는 초기로 Google 중심의 TurboQuant과 PoC 단계의 ITME가 일부 적용 사례를 보이고 있다.
- 도메인 적용 관점에서는 두 기술 모두 처리량과 품질 유지 측면에서 긍정적 평가를 받으며, TurboQuant은 소프트웨어적 압축으로 비용 효율과 도입 용이성에서 상대적으로 유연한 반면, ITME는 하드웨어 확장으로 처리량 향상과 품질 유지에 기여하나 도입 난이도가 높다.
- 비용 효율과 도입 용이성에서 시장성과 도메인 관점 간 평가가 엇갈리며, TurboQuant은 소프트웨어 중심 비용 절감과 도입 용이성을 강조하는 반면, ITME는 초기 하드웨어 투자 부담과 인프라 요구로 비용 효율과 도입 난이도에 대한 신중한 평가가 나타난다.
- 두 기술은 상호 보완 가능성이 있으며, TurboQuant의 데이터 축소와 ITME의 공간 확장 기술을 병행 적용할 경우 KV cache 메모리 병목 문제를 다각도로 완화할 수 있으나, 각 기술의 요구사항과 도입 난이도를 고려한 신중한 설계가 필요하다.
- 본 평가 결과는 저자 보고 수치와 제한된 하드웨어 환경에 기반하며, 대규모 클라우드 및 데이터센터 환경에서의 일반화와 장기 운영 검증이 추가로 요구된다.

## 1. 분석 배경

LLM(대형 언어 모델) 추론 과정에서 KV cache는 모델의 문맥 정보를 저장하는 핵심 메모리 영역으로, 모델 크기와 문맥 길이가 증가함에 따라 KV cache 크기가 급격히 커져 메모리 사용량과 계산 속도에 병목 현상을 초래한다[1, p.2][2, p.1]. 이로 인해 GPU 메모리 한계에 도달하거나 데이터 전송 지연이 발생하여 추론 처리량과 지연 시간에 부정적 영향을 미친다.

KV cache 최적화는 크게 두 가지 접근으로 나뉜다. 소프트웨어(SW) 진영은 KV cache 데이터를 압축하거나 양자화하여 메모리 사용량을 줄이는 방식이며, 하드웨어(HW) 진영은 메모리 계층을 확장하거나 외부 메모리를 활용해 저장 공간을 넓히는 방식이다. 각각은 기술적 특성과 도입 조건, 비용 구조가 상이하여 단일 관점으로 평가하기 어렵다.

따라서 KV cache 최적화 기술의 시장성(시장 규모, 상용화, 생태계 지지)과 도메인 적용(비용 효율, 처리량·지연, 품질 유지, 도입 용이성) 관점에서 다각도로 평가함으로써, 기술별 특성과 적용 가능성을 균형 있게 이해할 필요가 있다.

## 2. 기술 선정

| 진영 | 기술명 | 선정 사유 |
|---|---|---|
| SW | TurboQuant | KV cache를 사후 3비트 수준으로 온라인 벡터 양자화하는 전형적 SW 접근. 기존 GPU/HBM 인프라 위에서 SW만으로 적용 가능하며, Google Research 발표 후 산업계 반응과 시장성 평가 근거가 풍부함. |
| HW | ITME | CXL 기반 분리형 하이브리드 메모리로 KV cache 용량을 확장하는 HW 접근 대표. SK hynix가 제안한 구조로 CXL 표준 및 제품화 흐름과 연계되어 시장성 근거가 풍부하며, SW 압축과 정반대 방향으로 관점별 평가 대비가 명확함. |

## 3. 기술 개요

### 3.1 SW: TurboQuant

- **핵심 접근**  
  TurboQuant은 LLM 추론 시 KV cache 메모리 압박을 완화하기 위해 내적 왜곡을 최소화하는 온라인 벡터 양자화 기법을 적용한다. 데이터 의존적 튜닝 없이 즉시 적용 가능한 데이터-불가지론적 1비트 양자화(QJL)를 활용하며, 사전 학습이나 복잡한 전처리 없이 실시간으로 양자화한다[1, p.3-4].

- **저자 보고 성과**  
  Llama-3.1-8B-Instruct 모델에서 4배 압축(메모리 25% 사용) 시에도 원본과 동일한 리콜 점수를 달성했으며, NVIDIA A100 GPU 환경에서 4k~104k 토큰 길이의 긴 문맥 처리 실험을 수행하였다[1, p.16-17][3][4].

- **한계**  
  실험은 단일 NVIDIA A100 GPU 환경에 국한되어 하드웨어 및 평가 모델 규모, 벤치마크 범위에 제약이 존재한다. 또한, 내적 왜곡 최소화를 위한 양자화 알고리즘 구현과 고성능 GPU 환경이 요구된다[1, p.17].

### 3.2 HW: ITME

- **핵심 접근**  
  ITME는 CXL-하이브리드 메모리를 기반으로 TB급 계층형 메모리 확장 아키텍처를 제안한다. GPU 서버가 RDMA 프로토콜로 원격 메모리 영역에 접근 가능하며, 하드웨어 및 사용자 수준 프리페처를 통해 저장소 지연을 숨기고 PCIe 대역폭을 최대한 활용한다. 멀티티어 DMA 파이프라인으로 네트워크 및 저장소 접근 지연을 겹치게 하여 총 지연을 효과적으로 마스킹한다[2, p.2-9].

- **저자 보고 성과**  
  SK hynix CMM과 PCIe Gen5 NVMe SSD를 사용한 저자 자체 실험에서 최대 35.7% 추론 처리량 향상을 달성했으며, Llama-3.1 8B 및 70B 모델과 ShareGPT 데이터셋을 활용한 다중 대화 평가에서 CPU 오프로딩 대비 유사하거나 우수한 품질을 보였다[2, p.10-11][5][6].

- **한계**  
  활성화 및 작업 중인 KV cache처럼 지연에 민감한 데이터는 GPU 또는 호스트 메모리에 유지해야 하며, ITME는 예측 가능하고 대용량인 데이터에 적합하다. FPGA 프로토타입의 하드웨어 오버헤드로 성능 저하 가능성이 있고, 특정 하드웨어 및 모델 환경에 한정된 평가로 일반화에 한계가 있다.

## 4. 관점별 평가

### 4.1 시장성 관점

| 평가 기준 | ID | TurboQuant (SW) | ITME (HW) |
|---|---|---|---|
| 시장 규모·성장성 | M1 | 높음<br>중간 신뢰도<br>LLM 추론 최적화 SW 시장 성장 뚜렷, Google 등 주요 기업 도입 사례 존재[1, p.2][7][8][9] | 높음<br>높은 신뢰도<br>CXL 메모리 확장 시장 연평균 30% 이상 성장 전망, KV cache 수요 증가와 연계[2, p.1-2][10][11] |
| 상용화·채택 현황 | M2 | 중간<br>중간 신뢰도<br>Google 중심 일부 상용화 및 PoC, 오픈소스 통합 제한적[1, p.15][9][12] | 중간<br>중간 신뢰도<br>FPGA 프로토타입 및 PoC 단계, 일부 상용 제품 사례 있으나 완전 상용화 미흡[2, p.1][6][13] |
| 생태계 지지 | M3 | 중간<br>중간 신뢰도<br>주요 LLM 프레임워크 일부 지원, 표준화 초기 단계[1, p.4][14][15] | 중간<br>중간 신뢰도<br>주요 프레임워크 통합 시도, CXL 표준 및 벤더 참여 있으나 완전한 표준화 미흡[2, p.9][16][17] |

- **해석**  
  두 기술 모두 LLM 추론 및 메모리 확장 시장에서 높은 성장 가능성을 보인다. TurboQuant은 Google 중심의 상용화와 산업계 관심이 뚜렷하며, ITME는 CXL 메모리 확장 시장 성장과 연계되어 긍정적 평가를 받는다. 다만, 상용화 및 생태계 지지 단계는 초기로, 복수 주요 프레임워크 통합 및 산업 표준화는 미흡하다. TurboQuant은 SW 중심으로 빠른 적용 가능성을 강조하는 반면, ITME는 HW 중심으로 표준 및 벤더 참여가 활발하나 완전한 상용화는 진행 중이다.

- **반대 근거**  
  TurboQuant은 실험 환경 제한과 과도한 압축 시 신뢰성 저하 위험이 존재하며, ITME는 특정 하드웨어 환경에 한정된 평가와 FPGA 프로토타입의 성능 저하 가능성이 있다.

### 4.2 도메인 적용 관점: 데이터센터·클라우드 LLM 서빙

| 평가 기준 | ID | TurboQuant (SW) | ITME (HW) |
|---|---|---|---|
| 비용 효율 (TCO) | D1 | 높음<br>중간 신뢰도<br>4~6배 압축으로 GPU 메모리 사용량 감소, 추가 HW 없이 TCO 절감 가능[1, p.17][3][4] | 중간<br>중간 신뢰도<br>CXL 메모리 확장으로 처리량 향상 보고, 추가 HW 및 인프라 투자 필요[2, p.1][5][6] |
| 처리량·지연 | D2 | 높음<br>중간 신뢰도<br>압축으로 데이터 전송량 감소, 최대 8배 빠른 어텐션 및 13배 처리량 증가 보고[1, p.17][18][19] | 높음<br>중간 신뢰도<br>최대 35.7% 처리량 향상, 저장소 지연 마스킹으로 지연 유지[2, p.10-11][20][21] |
| 품질 유지 | D3 | 높음<br>중간 신뢰도<br>3~4비트 압축 시 원본과 동일하거나 무시 가능한 품질 손실 보고[1, p.16-17][22][23] | 높음<br>중간 신뢰도<br>8B 및 70B 모델에서 CPU 오프로딩 대비 유사 품질, 손실 1~5% 이내[2, p.10][24][25] |
| 도입 용이성 | D4 | 중간<br>중간 신뢰도<br>기존 GPU 클러스터에서 SW 변경만으로 도입 가능하나, 고성능 GPU 및 알고리즘 구현 필요[1, p.4][26][9] | 낮음<br>중간 신뢰도<br>CXL 메모리, FPGA 프로토타입, 고속 네트워크 등 신규 HW 및 인프라 필요[2, p.2][27][28] |

- **해석**  
  TurboQuant은 소프트웨어적 압축으로 GPU 메모리 사용량을 크게 줄여 비용 효율과 도입 용이성에서 유연성을 보인다. 처리량과 지연 개선도 압축에 따른 데이터 전송량 감소로 긍정적이다. ITME는 하드웨어 확장으로 처리량 향상과 품질 유지에 기여하나, 신규 하드웨어 및 인프라 투자와 프레임워크 변경이 필요해 도입 난이도가 높다.

- **반대 근거**  
  TurboQuant은 단일 GPU 환경에 국한된 실험으로 대규모 클러스터 환경 검증이 부족하며, ITME는 초기 투자 비용과 운영 복잡성, 특정 하드웨어 의존성으로 비용 효율과 도입 용이성에 제약이 있다.

## 5. 시사점

| 주제 | 시장성 관점 | 도메인 관점 | 엇갈리는 이유 |
|---|---|---|---|
| 비용 효율 (TCO) - TurboQuant | SW 중심 비용 절감 효과 강조, 추가 HW 투자 불필요 | 단일 GPU 환경 실험 제한, 대규모 환경 검증 부족 | 시장은 SW 중심 비용 절감에 주목, 도메인은 실험 환경 제한과 검증 부족에 신중 |
| 비용 효율 (TCO) - ITME | CXL 시장 성장과 잠재적 비용 절감 기대, 초기 투자 부담 인정 | 추가 HW 및 인프라 요구로 초기 비용 부담 크고 검증 부족 | 시장은 성장 잠재력에 주목, 도메인은 도입 복잡성과 초기 비용에 주목 |
| 도입 용이성 - TurboQuant | SW 변경만으로 도입 가능, 데이터 의존 튜닝 불필요 | 고성능 GPU 요구 및 알고리즘 구현 난이도 존재 | 시장은 SW 중심 도입 용이성 강조, 도메인은 구현 난이도와 HW 요구 고려 |
| 도입 용이성 - ITME | 신규 HW 및 인프라 필요, 도입 난이도 높음 | 동일하게 신규 HW 및 인프라 요구로 도입 난이도 높음 | 양측 모두 도입 난이도 높음에 일치 |

- **두 기술의 인식 차이**  
  TurboQuant은 소프트웨어 중심으로 빠른 적용과 비용 절감을 강조하는 반면, ITME는 하드웨어 중심으로 처리량 향상과 확장성에 중점을 두고 초기 투자와 도입 난이도를 신중히 평가한다. 시장성 관점은 성장 가능성과 기술 혁신에 주목하는 반면, 도메인 관점은 실제 운영 환경에서의 비용, 성능, 도입 복잡성에 더 엄격한 기준을 적용한다.

- **보완·병행 가능성**  
  TurboQuant의 데이터 축소 기술과 ITME의 공간 확장 기술은 상호 보완적이다. TurboQuant으로 KV cache 메모리 압박을 줄이면서 ITME를 통해 대규모 KV cache를 외부 메모리로 확장하면, 메모리 병목 문제를 다각도로 완화할 수 있다. 다만, 두 기술의 하드웨어 및 소프트웨어 요구사항과 도입 난이도를 고려해 병행 적용 시 신중한 설계와 검증이 필요하다.

## 6. 한계점

본 보고서는 공개된 논문과 산업계 자료, 저자 자체 실험 결과에 기반하여 평가를 수행하였다. 각 기술의 성능 수치와 효과는 저자 보고 기준임을 명확히 하며, 특정 하드웨어 환경(NVIDIA A100 GPU, SK hynix CMM, PCIe Gen5 등)과 제한된 모델 규모(Llama-3.1 8B 등)에 국한되어 있어 대규모 클라우드 및 데이터센터 환경에서의 일반화와 장기 운영 검증이 필요하다.

또한, 상용화 및 생태계 지지 현황은 Google 중심 또는 PoC 단계에 머무르고 있어 타 벤더 및 오픈소스 커뮤니티 통합, 산업 표준화 진행 상황에 대한 추가 정보가 요구된다. 평가 과정에서 확증편향을 방지하기 위해 다양한 출처를 교차 검증하고, 기술별 장단점과 관점별 평가 차이를 균형 있게 서술하였다.

## REFERENCE

1. Zandieh, A., Daliri, M., Hadian, M., & Mirrokni, V.(2025). TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate. *arXiv*, 2504.19874. https://arxiv.org/abs/2504.19874
2. Jang, H., Min, Y., Kim, S., Ahn, T., Kim, H., Joo, Y., Kim, H., & Kim, J.(2026). ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories. *arXiv*, 2606.12556. https://arxiv.org/abs/2606.12556
3. medium.com(n.d.). *TurboQuant Changes the Economics of Local AI Inference*. medium.com, https://medium.com/@michael.hannecke/googles-turboquant-changes-the-economics-of-local-ai-inference-acce5839014d
4. mindstudio.ai(n.d.). *What Is Google TurboQuant? The KV Cache Compression ...*. mindstudio.ai, https://www.mindstudio.ai/blog/what-is-google-turboquant-kv-cache-compression
5. acecloud.ai(n.d.). *CXL Memory For LLM Inference: Breaking The AI ...*. acecloud.ai, https://acecloud.ai/blog/cxl-memory-llm-inference
6. arxiv.org(n.d.). *CXL-Enabled KV-Cache Management Beyond GPU Limits*. arxiv.org, https://arxiv.org/html/2511.00321v1
7. trendforce.com(n.d.). *Overcoming the Memory Bottleneck: CXL Expansion and KV Cache Compression Innovations | TrendForce*. trendforce.com, https://www.trendforce.com/research/download/RP260715HU
8. developer.nvidia.com(n.d.). *Optimizing Inference for Long Context and Large Batch ...*. developer.nvidia.com, https://developer.nvidia.com/blog/optimizing-inference-for-long-context-and-large-batch-sizes-with-nvfp4-kv-cache
9. o-mega.ai(n.d.). *Google TurboQuant in August 2026: Where It Actually Runs*. o-mega.ai, https://o-mega.ai/articles/google-turboquant-the-2026-llm-compression-guide
10. fortunebusinessinsights.com(n.d.). *CXL Memory Expansion Market Size, Share and Forecast ...*. fortunebusinessinsights.com, https://www.fortunebusinessinsights.com/cxl-memory-expansion-market-119032
11. sphericalinsights.com(n.d.). *CXL Memory Expansion Market Growth, Forecast Report ...*. sphericalinsights.com, https://www.sphericalinsights.com/reports/cxl-memory-expansion-market
12. tradingkey.com(n.d.). *อัลกอริทึมการบีบอัด TurboQuant ของ Google คืออะไร? และจะส่งผลกระทบต่ออุตสาหกรรมชิปจัดเก็บข้อมูลสำหรับ AI อย่างไร?*. tradingkey.com, https://www.tradingkey.com/th/analysis/stocks/us-stocks/261728273-what-is-google-turboquant-compression-algorithm-how-impact-ai-memory-chip-industry-tradingkey
13. stocktitan.net(n.d.). *Penguin Solutions Introduces Industry's First Production-Ready CXL-Based KV Cache Server*. stocktitan.net, https://www.stocktitan.net/news/PENG/penguin-solutions-introduces-industry-s-first-production-ready-cxl-pxfpc1e4d2nz.html
14. inferenceengineering.tech(n.d.). *vLLM vs SGLang vs TensorRT-LLM - Inference Engineering*. inferenceengineering.tech, https://inferenceengineering.tech/learn/vllm-vs-sglang-vs-tensorrt-llm
15. youtube.com(n.d.). *KV Cache as the New AI Memory Abstraction*. youtube.com, https://www.youtube.com/watch?v=HxhuAl1wQpE&vl=en
16. asteralabs.com(n.d.). *How CXL Memory Expansion Improves AI Economics*. asteralabs.com, https://www.asteralabs.com/resources/blog/inference-tokenomics-how-cxl-memory-expansion-improves-ai-economics
17. arxiv.org(n.d.). *ITME: Inference Tiered Memory Expansion with ...*. arxiv.org, https://arxiv.org/html/2606.12556v2
18. nandigamharikrishna.substack.com(n.d.). *TurboQuant Explained: How KV Cache Compression Cuts LLM Memory by 6x*. nandigamharikrishna.substack.com, https://nandigamharikrishna.substack.com/p/turboquant-explained-how-kv-cache
19. spheron.network(n.d.). *Google TurboQuant: 6x KV Cache Compression for LLM ...*. spheron.network, https://www.spheron.network/blog/google-turboquant-llm-compression-gpu-cloud
20. neurips.cc(n.d.). *Exploring CXL-based KV Cache Storage for LLM Serving*. neurips.cc, https://neurips.cc/virtual/2024/103619
21. mlforsystems.org(n.d.). *Exploring CXL-based KV Cache Storage for LLM Serving*. mlforsystems.org, https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf
22. infoq.com(n.d.). *Google's TurboQuant Compression May Support Faster ...*. infoq.com, https://www.infoq.com/news/2026/04/turboquant-compression-kv-cache
23. tradingkey.com(n.d.). *หุ้น Micron ปรับตัวร่วงลง การโจมตีอย่างแม่นยำโดย Google TurboQuant? อาณาจักรหน่วยความจำ AI ของ Micron กำลังเผชิญกับบททดสอบ*. tradingkey.com, https://tradingkey.com/th/analysis/stocks/us-stocks/261723403-micron-stock-price-declining-google-turboquant-striking-tradingkey
24. computer.org(n.d.). *OASIS: Outlier-Aware KV Cache Clustering for Scaling ...*. computer.org, https://www.computer.org/csdl/journal/ca/2025/01/10990150/26wpHF5GHOo
25. medium.com(n.d.). *The KV Cache Is Killing Your LLM at Scale*. medium.com, https://medium.com/@adityaj5400/the-kv-cache-is-killing-your-llm-at-scale-heres-the-low-level-physics-nobody-talks-about-b577c4c7549e
26. jtanruan.medium.com(n.d.). *TurboQuant: How Google Solved the KV Cache Memory Wall at 3 Bits Per Element | by Jin Tan Ruan, CSE Computer Science - ML Engineer | Medium*. jtanruan.medium.com, https://jtanruan.medium.com/turboquant-how-google-solved-the-kv-cache-memory-wall-at-3-bits-per-element-03742b35135a
27. asteralabs.com(n.d.). *How CXL Transforms RAG and KV Cache Performance*. asteralabs.com, https://www.asteralabs.com/resources/blog/breaking-through-the-memory-wall-how-cxl-transforms-rag-and-kv-cache-performance
28. hotinfra.org(n.d.). *Reimagining LLM Inference Infrastructure with Memory- ...*. hotinfra.org, https://hotinfra.org/2026/papers/hotinfra26-final59.pdf
