"""Render the existing Markdown without calling APIs or changing historical run state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import OUTPUT_DIR
from report.pdf import html_document, save_pdf


def main():
    md = (OUTPUT_DIR / 'report.md').read_text(encoding='utf-8')
    # 수동 렌더링 대상은 자동 검토 통과본이 아니므로, 검토 상태(미통과 표시 또는 정정 주체 명시)가 본문에 있어야 한다
    if '검토 상태:' not in md and 'AI 도구로 논문·웹 출처를 대조' not in md:
        raise ValueError('수동 렌더링에는 검토 상태 또는 정정 주체를 먼저 명시해야 합니다')
    (OUTPUT_DIR / 'report.html').write_text(
        html_document(md, 'KV cache 최적화 기술 다관점 평가 보고서'), encoding='utf-8')
    path = OUTPUT_DIR / 'RAG-Output_판교_6반_권유나.pdf'
    print(path, save_pdf(md, path), 'pages')


if __name__ == '__main__':
    main()
