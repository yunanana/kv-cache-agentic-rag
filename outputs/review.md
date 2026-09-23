# 검토 결과 : 자동 검토 미통과 → AI 도구 보조 정정본

> 아래 대조·정정은 AI 도구가 수행했다. 독립적인 사람 검수나 자동 검토 통과를 의미하지 않으며, 전체 정확성을 보증하지 않는다.

## 경위
1. 멀티 에이전트 실행 결과가 자동 검토(규칙 검사 + LLM Judge)를 재작성 2회 후에도 통과하지 못함
2. 코드 개선 후 전체 재실행도 미통과 (critical 13건). 재실행본은 TurboQuant을 '무손실 구조'로 서술하는 등 사실 오류가 있어 채택하지 않음 (커밋 `adc9629` 이후 기록)
3. 이전 실행본(18:23)을 바탕으로, AI 도구로 인용 논문 페이지와 웹 출처를 대조해 정정 → 현재 `report.md` / PDF

## 자동 검사 (정정본 기준)
- 규칙 검사 : 목차·SUMMARY 길이·10페이지 제한·우열 표현 통과 (5페이지)
- 수치-원문 대조 : 논문 인용 구간의 수치 전부가 인용 페이지 원문에 존재 (위반 0건)
- 한계 : 숫자 존재 검사는 지표·조건의 의미 일치를 보장하지 않음 → 아래 AI 도구 대조로 보완 (의미 검증의 완전성은 보장하지 않음)

## AI 도구 대조 : 논문 인용
| 주장 | 인용 | 확인 |
|---|---|---|
| TurboQuant 4배 압축(KV 25% 사용), 4k~104k 문맥 | TurboQuant p.17 | 일치 (compression ratio 0.25, 4× compression) |
| NIAH 리콜 0.997 (Full-Precision·TurboQuant 동일) | TurboQuant p.19 | 일치 (그림 4 : 둘 다 0.997) |
| 단일 A100, 1536/3072차원 데이터셋 | TurboQuant p.15, p.19 | 일치 |
| 온라인·데이터 비의존, 사전처리 불필요 | TurboQuant p.4 | 일치 |
| ITME 최대 35.7% 처리량 향상 (CPU-offload 대비) | ITME p.1, p.11 | 일치 (p.10에도 있음) |
| ITME Llama-3.1 8B/70B, ShareGPT, vLLM 기반 | ITME p.9 | 일치 |
| ITME 정확도·품질 측정 | ITME 전체 | 논문에 정확도 측정 없음 → '미보고'로 서술 (p.10 의 1–5%는 실행 성능 차이) |
| ITME 신규 HW (CXL-하이브리드 메모리, RDMA, FPGA) | ITME p.2, p.8 | 일치 |

## AI 도구 대조 : 웹 출처 (페이지를 불러와 확인 후 정정한 부분)
| 출처 | 원문 확인 내용 | 조치 |
|---|---|---|
| o-mega.ai | vLLM 연구 인용 : FP8·BF16 대비 처리량 20~34% 저하, 최악 구성 지연 60~68% 증가, KV 용량 2.4~3.7배 / 버스트 부하 TTFT 급증 방지 / Google 실서비스 적용은 "공개 근거 없음" / vLLM·SGLang 구현 소개 | 조건 명시. '간접적 생산 환경 적용 사례' 삭제. 생태계 지지(M3) 낮음 → 중간 정정 |
| growthmarketreports.com | KV cache 오프로딩 인프라 시장 18.7억(2024)→149.9억 달러(2033), CAGR 23.6%. 양자화 언급 없음 | 인접 시장 수치로 명시 |
| marketintelo.com | CXL 메모리 확장 시장 13억(2025)→118억 달러(2034), CAGR 28.7%. AI/ML 추론 비중 38.5%, CAGR 약 32.6% | 수치·추정치임을 명시, 신뢰도 높음 → 중간 (단일 조사기관) |
| spheron.network | 비용 절감 수치는 VRAM 여유 기반 계산 시나리오 (측정값 아님) | TCO 절감을 '간접 근거'로 유지 |
| stocktitan.net (Penguin) | CXL KV cache 서버 출시, ITME 언급 없음 | 인접 제품으로 명시 |
| asteralabs.com (2건) | Astera Leo CXL 컨트롤러 자료, ITME 언급 없음 | 인접 제품 자료로 명시 |
| ownyourai.com | CXL-SpecKV (다른 시스템) | 간접 근거 표시 유지 |
| inferenceengineering.tech, jarvislabs.ai, everpuredata | 주장을 직접 뒷받침하지 않음 | 인용 제거, REFERENCE 에서 삭제 |

## 남은 한계
- 웹 출처는 블로그·시장조사 요약 등 2차 자료이며 게시일(n.d.)을 확인하지 못함
- TurboQuant 처리량·지연 수치는 원 연구가 아닌 이를 인용한 웹 글로 확인함
