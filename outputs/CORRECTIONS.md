# 산출물 구분 및 수정 내역

## 산출물
| 구분 | 파일 | 설명 |
|---|---|---|
| **자동 생성 원본** | `outputs/auto_generated/RAG-Output_판교_6반_권유나_자동생성원본.pdf`<br>`outputs/auto_generated/report.md` | `app.py` 실행(2026-09-23 18:23)이 그대로 만든 결과. 수정하지 않음 |
| 원본의 자동 검토 기록 | `outputs/auto_generated/review.md` | 재작성 2회 후 **미통과** (critical 3건) |
| 원본 실행 기록 | `outputs/run_state.json`, `outputs/run.log` | 원본을 만든 실행의 에이전트별 중간 결과·검색 로그 |
| **정정본 (제출 PDF)** | `outputs/RAG-Output_판교_6반_권유나.pdf`<br>`outputs/report.md` | 원본의 오류를 AI 도구로 논문·웹 출처와 대조해 수정한 보고서 |
| 대조·정정 근거 | `outputs/review.md` | 어떤 주장을 어떤 원문과 대조했고 무엇을 고쳤는지 |

## 재현성에 대한 설명
- `uv run python app.py`를 실행하면 보고서가 **자동으로 새로 생성**됩니다 (원본과 같은 과정).
- LLM 생성은 실행마다 문장과 세부 판단이 달라지므로, 재실행 결과는 원본과도 정확히 같지 않습니다.
- **정정본은 자동 실행만으로 재현되지 않습니다.** 원본 생성 뒤 별도로 AI 도구로 출처를 대조해 수정했기 때문입니다. 이는 독립적인 사람 검수나 자동 검토 통과를 의미하지 않습니다.
- 정정본은 정정된 Markdown을 코드로 다시 렌더링한 것입니다 (`scripts/render_existing_report.py`). 원본 PDF는 당시 렌더러(fpdf2)로, 정정본은 개선된 렌더러(노션 스타일 HTML → Chrome)로 만들어져 모양이 다릅니다.

## 원본의 주요 오류와 정정 이유
| 원본 서술 | 문제 | 정정 |
|---|---|---|
| TurboQuant이 "무손실 압축을 입증" | 특정 벤치마크(Needle-In-A-Haystack) 점수 유지를 무손실 압축으로 과장 | "해당 실험에서 리콜 0.997 유지, 무손실 압축 입증은 아님" |
| TurboQuant "비용 절감 효과가 수치로 확인" | 근거가 VRAM 계산 시나리오(웹)이며 측정된 TCO 아님 | "비용 절감 가능성의 간접 근거"로 한정, 등급 높음→중간 |
| ITME 품질 "설계상 무손실, 높음" | 논문에 정확도 측정이 없음 | "판단 유보, 정확도 측정 수치 미보고" |
| 리콜 0.997 인용 p.17 | 수치는 논문 p.19 그림 4에 있음 | 인용 페이지 p.19로 정정 |
| TurboQuant "일부 간접적 생산 환경 적용 사례" | 출처 원문은 "Google 실서비스 적용은 공개 근거 없음" | 문장 삭제, 원문대로 서술 |
| TurboQuant 생태계 지지 "통합 근거 미확인, 낮음" | 같은 출처에 vLLM·SGLang 기반 구현이 소개됨 | "구현·벤치마크 보고 존재, 공식 탑재는 미확인, 중간" |
| 인접 시장·제품(KV cache 오프로딩 시장, Penguin, Astera, CXL-SpecKV)을 직접 근거처럼 인용 | 대상 기술 자체에 대한 자료가 아님 | "인접 시장·제품, 간접 근거"로 명시 |
| 주장을 뒷받침하지 않는 출처 3건 | 인용 부적절 | 인용과 REFERENCE에서 제거 |

## 원본 → 정정본 전체 변경 (unified diff)
```diff
--- auto_generated/report.md (자동 생성 원본)
+++ report.md (정정본)
@@ -4,4 +4,4 @@
-- TurboQuant과 ITME는 모두 LLM 추론에서 KV cache 메모리 문제 해결을 목표로 하며, 품질 유지 측면에서 TurboQuant은 저자 보고 기준 무손실 압축을 입증했고, ITME는 설계상 정확도 손실이 없다고 주장하나 수치 보고는 없다.
-- 두 기술 모두 현재 연구·프로토타입 단계로, 공식 상용 제품 출시나 주요 LLM 서빙 스택 내 공식 통합 근거는 부족하다.
-- TurboQuant은 소프트웨어 기반 압축으로 추가 하드웨어 투자 없이 GPU 메모리 수용량 확대와 비용 절감 효과가 수치로 확인되나, 처리량·지연에서 일부 오버헤드가 존재하며 대규모 분산 환경 적용 검증은 부족하다.
-- ITME는 CXL-하이브리드 메모리 기반 대규모 메모리 확장과 I/O 병목 완화로 최대 35.7% 처리량 향상 실험 결과가 있으나, 신규 하드웨어 및 복잡한 시스템 통합이 요구되고 직접적인 비용 절감 수치는 논문에 제시되지 않았다.
+- TurboQuant은 저자 보고 기준 Llama-3.1-8B-Instruct의 Needle-In-A-Haystack 실험에서 원본과 같은 리콜 0.997을 기록했다. 이는 해당 실험의 점수 유지이며 원본 데이터의 무손실 압축을 뜻하지 않는다[1, p.19]. ITME는 원본 KV를 유지하는 설계이나 정확도 측정 수치는 미보고다[2, p.2].
+- 두 기술 모두 공식 상용 제품이나 주요 LLM 서빙 스택의 기본 기능 탑재 근거는 확인되지 않았다. TurboQuant은 vLLM·SGLang 기반 구현·벤치마크 보고가 있으나 Google 실서비스 적용은 공개 근거가 없고[5], ITME는 프로토타입 단계다[2, p.1].
+- TurboQuant의 메모리 축소는 비용 절감 가능성을 시사하지만 실제 운영 TCO 절감의 측정·검증과는 구분해야 한다[1, p.19]. 처리량·지연 오버헤드에 관한 웹 평가는 별도 환경의 간접 근거다[5].
+- ITME는 저자 보고 기준 최대 35.7% 처리량 향상 결과가 있으나[2, p.1, p.11], 신규 하드웨어 및 시스템 통합이 필요하며 직접적인 비용 절감 수치는 논문에 제시되지 않았다.
@@ -43,3 +43,3 @@
-| M1 | 시장 규모·성장성 | 중간 | 중간 | LLM 추론 최적화 시장 성장 간접 근거, TurboQuant 고유 수치는 부재[3][1, p.2] | 높음 | 높음 | CXL 메모리 확장 시장 내 AI/ML 추론 부문 고성장 보고[4][2, p.1] |
-| M2 | 상용화·채택 현황 | 중간 | 중간 | 논문 실험 검증 및 일부 간접적 생산 환경 적용 사례 있으나 공식 상용화 근거 부족[1, p.15][5] | 낮음 | 높음 | 논문 기반 프로토타입 단계, 상용 제품 출시 근거 없음[2, p.1][6] |
-| M3 | 생태계 지지 | 낮음 | 중간 | TurboQuant 고유 프레임워크 통합·표준화 근거 미확인[7][8] | 중간 | 중간 | vLLM 내 구현 평가, 공식 다중 프레임워크 통합 근거는 미확인[2, p.9][9] |
+| M1 | 시장 규모·성장성 | 중간 | 중간 | 인접 시장인 KV cache 오프로딩 인프라 시장이 2024년 18.7억 달러에서 2033년 149.9억 달러(CAGR 23.6%)로 전망됨(시장조사기관 추정)[3]. 양자화 SW 고유 시장 수치는 미확인 | 높음 | 중간 | CXL 메모리 확장 시장 2025년 13억 달러에서 2034년 118억 달러(CAGR 28.7%), 그중 AI/ML 추론 부문은 매출 비중 38.5%·CAGR 약 32.6% 전망(시장조사기관 추정)[4]. ITME 고유 시장 수치는 없음 |
+| M2 | 상용화·채택 현황 | 중간 | 중간 | 논문은 단일 A100 실험[1, p.15]. vLLM·SGLang 기반 구현·벤치마크 보고는 있으나 Google 실서비스 적용은 공개 근거 없음[5] | 낮음 | 높음 | FPGA·CMM 기반 프로토타입 단계[2, p.1]. 인접 제품인 CXL 기반 KV cache 서버(Penguin MemoryAI)는 출시됐으나 ITME 자체 제품 출시 근거는 없음[6] |
+| M3 | 생태계 지지 | 중간 | 중간 | vLLM·SGLang 기반 구현·벤치마크 보고 존재[5]. 공식 기본 기능 탑재·표준화 근거는 미확인 | 중간 | 중간 | 논문은 vLLM 기반으로 구현·평가[2, p.9]. 인접 CXL 메모리 제품(Astera Leo)은 vLLM·TensorRT-LLM·SGLang 연동을 내세우나 ITME 자체 공식 통합 근거는 미확인[7] |
@@ -48,3 +48,3 @@
-- **시장 규모·성장성**: TurboQuant은 LLM 추론 최적화 SW 시장의 성장 전망에 기반하나, 기술 고유 시장 점유율 근거는 부족하다. ITME는 CXL 메모리 확장 시장 내 AI/ML 추론 부문 성장세가 뚜렷해 간접적 시장성 근거가 강하다.
-- **상용화·채택 현황**: TurboQuant은 논문 실험과 일부 간접적 생산 환경 적용 사례가 있으나 공식 상용화 근거는 부족하다. ITME는 논문 기반 프로토타입 단계로 상용 제품 출시 근거가 없다.
-- **생태계 지지**: TurboQuant은 주요 LLM 엔진 내 공식 통합 근거가 미흡하며, ITME는 일부 프레임워크 내 구현은 있으나 공식 다중 프레임워크 지원 및 표준화 참여 근거는 제한적이다.
+- **시장 규모·성장성**: TurboQuant은 KV cache 오프로딩 인프라처럼 인접 시장의 성장 전망만 확인되며 양자화 SW 고유 시장 수치는 없다. ITME는 자신이 속한 CXL 메모리 확장 시장, 특히 AI/ML 추론 부문의 성장 전망이 제시되지만 이 역시 시장조사기관의 추정치이며 ITME 고유 수치는 아니다.
+- **상용화·채택 현황**: TurboQuant은 오픈소스 추론 엔진 위 구현·벤치마크가 보고된 실험적 통합 단계이며, Google 실서비스 적용은 공개 근거가 없다. ITME는 논문 기반 프로토타입 단계이며, 시장에 나온 CXL KV cache 서버는 ITME가 아닌 인접 제품이다.
+- **생태계 지지**: TurboQuant은 vLLM·SGLang 기반 구현이 보고됐으나 공식 기본 기능 탑재는 확인되지 않았다. ITME는 vLLM 기반 구현 외에 공식 다중 프레임워크 지원·표준화 참여 근거가 없다.
@@ -56,4 +56,4 @@
-| D1 | 비용 효율 (TCO) | 높음 | 높음 | 4배 압축 시 품질 유지, GPU당 수용량 확대 및 비용 절감 사례 보고[10][1, p.17] | 중간 | 중간 | 최대 35.7% 처리량 향상 보고, 신규 하드웨어 투자 필요[2, p.1][11] |
-| D2 | 처리량·지연 | 중간 | 높음 | 일부 환경에서 처리량 20~34% 저하, 지연 60~68% 증가 보고, 버스트 부하 시 SLO 유지 기여[5] | 중간 | 중간 | 최대 35.7% 처리량 향상 및 지연 완화 보고, FPGA 오버헤드 및 인프라 조건 영향[2, p.11] |
-| D3 | 품질 유지 | 높음 | 높음 | 4배 압축 시 리콜 점수 0.997로 무손실 확인, 다양한 모델에서 무손실 보고[1, p.17][12] | 높음(설계상) | 중간 | KV cache 데이터 변경 없이 무손실 구조 주장, 정확도 수치 미보고[2, p.2] |
-| D4 | 도입 용이성 | 중간 | 중간 | 소프트웨어 변경만으로 도입 가능, 대규모 분산 환경 검증 부족, 일부 처리량·지연 저하 보고[1, p.4][5] | 낮음 | 중간 | CXL-HW, 고속 네트워크, FPGA 등 신규 하드웨어 및 복잡한 시스템 통합 요구[2, p.8][13] |
+| D1 | 비용 효율 (TCO) | 중간 | 낮음 | 메모리 축소는 비용 절감 가능성의 간접 근거이며 실제 운영 TCO 측정과 구분 필요[8][1, p.19] | 중간 | 중간 | 최대 35.7% 처리량 향상 보고, 신규 하드웨어 투자 필요[2, p.1]. 인접 기술 자료는 간접 근거[9] |
+| D2 | 처리량·지연 | 중간 | 중간 | 웹 자료가 인용한 vLLM 연구에서 FP8·BF16 대비 처리량 20~34% 저하, 최악 구성 지연 60~68% 증가, 대신 KV 용량 2.4~3.7배. 버스트 부하에서는 TTFT 급증을 막았다고 보고(2차 자료)[5] | 중간 | 중간 | 최대 35.7% 처리량 향상 및 지연 완화 보고, FPGA 오버헤드 및 인프라 조건 영향[2, p.11] |
+| D3 | 품질 유지 | 높음 | 중간 | 저자 보고 기준 Llama-3.1-8B-Instruct의 Needle-In-A-Haystack 실험에서 원본과 같은 리콜 0.997. 해당 실험의 점수 유지이며 무손실 압축의 입증은 아님[1, p.19] | 판단 유보 | 중간 | KV cache 원본 유지 설계이나 정확도 측정 수치는 미보고[2, p.2] |
+| D4 | 도입 용이성 | 중간 | 중간 | 사전 학습·데이터 의존 튜닝 없는 온라인 방식[1, p.4]. 대규모 분산 환경 검증은 없음 | 낮음 | 중간 | CXL-하이브리드 메모리, RDMA 네트워크, FPGA 프리페처 등 신규 하드웨어와 시스템 통합 필요[2, p.2, p.8]. 인접 CXL KV cache 구성도 전용 CXL 메모리 컨트롤러를 요구[10] |
@@ -62 +62 @@
-- **비용 효율**: TurboQuant은 추가 하드웨어 없이 GPU당 수용량 확대와 비용 절감이 수치로 확인된다. ITME는 처리량 향상과 간접적 비용 절감 가능성을 보이나, 신규 인프라 투자 필요성이 비용 효율성에 영향을 준다.
+- **비용 효율**: TurboQuant의 메모리 축소는 비용 절감 가능성의 간접 근거이며 실제 운영 TCO 절감액이 검증됐다는 뜻은 아니다. ITME도 처리량 향상과 비용 절감 가능성을 구분해야 하며 신규 인프라 투자 비용을 고려해야 한다.
@@ -64 +64 @@
-- **품질 유지**: TurboQuant은 저자 보고 기준 무손실 압축을 입증했다. ITME는 설계상 정확도 손실이 없다고 주장하나, 수치 보고는 없다.
+- **품질 유지**: TurboQuant은 저자 보고 기준 해당 리콜 실험에서 점수 저하가 관측되지 않았다[1, p.19]. ITME는 원본 KV 유지 설계와 실제 정확도 측정을 구분해야 하며 정확도 측정 수치는 미보고다[2, p.2].
@@ -71 +71 @@
-| 비용 효율 (TCO) - TurboQuant | 추가 하드웨어 투자 없이 비용 절감 효과가 수치로 확인됨 | 처리량·지연 오버헤드와 대규모 환경 적용 한계가 비용 효율성에 영향 | 시장은 SW 기반 비용 절감에 주목하나, 도메인은 성능 영향과 환경별 검증 부족을 고려 |
+| 비용 효율 (TCO) - TurboQuant | 메모리 축소를 통한 비용 절감 가능성은 간접 근거 | 처리량·지연 오버헤드와 대규모 환경 적용 한계가 비용 효율성에 영향 | 메모리 절감과 실제 운영 TCO의 측정·검증은 구분해야 함 |
@@ -86,0 +87,2 @@
+본 보고서는 멀티 에이전트 시스템이 생성한 초안의 자동 검토 미통과 항목에 대해 AI 도구로 논문·웹 출처를 대조하고 정정한 정정본이다. 이는 독립적인 사람 검수나 자동 검토 통과를 의미하지 않는다. 웹 출처는 대부분 블로그·시장조사 요약 등 2차 자료이며, 시장 규모 수치는 조사기관의 추정치다.
+
@@ -95,7 +97,4 @@
-7. inferenceengineering.tech(n.d.). *vLLM vs SGLang vs TensorRT-LLM - Inference Engineering*. inferenceengineering.tech, https://inferenceengineering.tech/learn/vllm-vs-sglang-vs-tensorrt-llm
-8. jarvislabs.ai(n.d.). *SGLang vs vLLM: H100 Benchmarks, with TensorRT-LLM*. jarvislabs.ai, https://jarvislabs.ai/blog/vllm-sglang-trtllm-comparison
-9. asteralabs.com(n.d.). *How CXL Memory Expansion Improves AI Economics*. asteralabs.com, https://www.asteralabs.com/resources/blog/inference-tokenomics-how-cxl-memory-expansion-improves-ai-economics
-10. spheron.network(n.d.). *Google TurboQuant: 6x KV Cache Compression for LLM ...*. spheron.network, https://www.spheron.network/blog/google-turboquant-llm-compression-gpu-cloud
-11. ownyourai.com(n.d.). *CXL-SpecKV: A Disaggregated FPGA Speculative KV-Cache for Datacenter LLM Serving – Own Your AI*. ownyourai.com, https://ownyourai.com/cxl-speckv-a-disaggregated-fpga-speculative-kv-cache-for-datacenter-llm-serving
-12. blog.everpuredata.com(n.d.). *TurboQuant Compresses KV Cache by 5X. Does That ...*. blog.everpuredata.com, https://blog.everpuredata.com/purely-technical/turboquant-compresses-kv-cache-by-5x-does-that-mean-you-need-less-memory
-13. asteralabs.com(n.d.). *How CXL Transforms RAG and KV Cache Performance*. asteralabs.com, https://www.asteralabs.com/resources/blog/breaking-through-the-memory-wall-how-cxl-transforms-rag-and-kv-cache-performance
+7. asteralabs.com(n.d.). *How CXL Memory Expansion Improves AI Economics*. asteralabs.com, https://www.asteralabs.com/resources/blog/inference-tokenomics-how-cxl-memory-expansion-improves-ai-economics
+8. spheron.network(n.d.). *Google TurboQuant: 6x KV Cache Compression for LLM ...*. spheron.network, https://www.spheron.network/blog/google-turboquant-llm-compression-gpu-cloud
+9. ownyourai.com(n.d.). *CXL-SpecKV: A Disaggregated FPGA Speculative KV-Cache for Datacenter LLM Serving – Own Your AI*. ownyourai.com, https://ownyourai.com/cxl-speckv-a-disaggregated-fpga-speculative-kv-cache-for-datacenter-llm-serving
+10. asteralabs.com(n.d.). *How CXL Transforms RAG and KV Cache Performance*. asteralabs.com, https://www.asteralabs.com/resources/blog/breaking-through-the-memory-wall-how-cxl-transforms-rag-and-kv-cache-performance
```
