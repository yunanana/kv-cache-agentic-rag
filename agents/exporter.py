"""산출물 저장 : report.md / report.html / report.pdf + 중간 결과(run_state.json)."""

import json

from config import OUTPUT_DIR
from report.pdf import html_document, save_pdf


def make_exporter_node(pdf_name: str):
    def exporter(state):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        md = state["report_md"]
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

        print(f"[exporter] {pdf_path.name} ({pages}p) 저장")
        return {"outputs": {"md": str(md_path), "html": str(html_path), "pdf": str(pdf_path), "pages": pages}}

    return exporter
