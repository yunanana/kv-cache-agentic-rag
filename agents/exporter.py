"""산출물 저장 : report.md / report.html / report.pdf + 중간 결과(run_state.json)."""

import json

from config import OUTPUT_DIR
from report.pdf import html_document, save_pdf


def make_exporter_node(pdf_name: str):
    def exporter(state):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        review = state["review"]
        notice = "검토 상태: 미통과 - 자동 검토의 필수 수정 의견이 남아 있습니다. 제출 전 사람이 근거를 확인해야 합니다."
        md = state["report_md"]
        if not review["passed"]:
            md = notice + "\n\n" + md
        md_path = OUTPUT_DIR / "report.md"
        html_path = OUTPUT_DIR / "report.html"
        pdf_path = OUTPUT_DIR / pdf_name
        md_path.write_text(md, encoding="utf-8")
        html_path.write_text(html_document(md, "KV cache 최적화 기술 다관점 평가 보고서"), encoding="utf-8")
        pages = save_pdf(md, pdf_path)

        snapshot = {k: state.get(k) for k in
                    ("tech_profiles", "market_eval", "domain_eval", "synthesis", "review", "revision_count", "trace")}
        snapshot["sources"] = [{k: v for k, v in s.items() if k != "content"} for s in state["sources"]]
        (OUTPUT_DIR / "run_state.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")

        review = state["review"]
        review_path = OUTPUT_DIR / "review.md"
        status = "통과" if review["passed"] else "미통과 - 아래 잔여 의견을 사람이 확인해야 함"
        review_path.write_text(
            f"# 자동 검토 결과 : {status}\n\n- 재작성 횟수 : {state.get('revision_count', 0)}\n- PDF 페이지 : {pages}\n\n"
            + "## 필수 수정(critical)\n" + ("".join(f"- {i}\n" for i in review["issues"]) or "- 없음\n")
            + "\n## 개선 제안(minor)\n" + ("".join(f"- {i}\n" for i in review.get("minor", [])) or "- 없음\n"),
            encoding="utf-8",
        )
        print(f"[exporter] {pdf_path.name} ({pages}p) 저장 - 자동 검토 {status}")
        return {"outputs": {"md": str(md_path), "html": str(html_path), "pdf": str(pdf_path), "pages": pages,
                            "review": str(review_path), "review_passed": review["passed"]}}

    return exporter
