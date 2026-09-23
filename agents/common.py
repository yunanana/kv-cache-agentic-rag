"""에이전트 공통 유틸 : 병렬 실행, 웹 출처 등록, 근거 포맷."""

import itertools
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from tools.web_search import site_name, web_search


def run_per_tech(fn, technologies: dict) -> dict:
    """SW/HW 두 기술을 스레드로 동시에 처리하고 {tech_key: 결과} 반환."""
    with ThreadPoolExecutor(max_workers=len(technologies)) as ex:
        futures = {key: ex.submit(fn, tech) for key, tech in technologies.items()}
        return {key: f.result() for key, f in futures.items()}


class WebSourceRegistry:
    """노드 단위 웹 출처 레지스트리. prefix(WM/WD)로 병렬 노드 간 ID 충돌을 방지한다."""

    def __init__(self, prefix: str):
        self.prefix = prefix
        self._counter = itertools.count(1)
        self._lock = threading.Lock()
        self._by_url: dict[str, dict] = {}

    def search(self, query: str, tech_key: str, max_results: int = 3) -> list[dict]:
        registered = []
        for r in web_search(query, max_results=max_results):
            with self._lock:
                src = self._by_url.get(r["url"])
                if src is None:
                    src = {
                        "id": f"{self.prefix}{next(self._counter)}",
                        "kind": "web",
                        "tech": tech_key,
                        "title": r["title"],
                        "url": r["url"],
                        "site": site_name(r["url"]),
                        "date": r["published_date"],
                        "content": r["content"],
                    }
                    self._by_url[r["url"]] = src
            registered.append(src)
        return registered

    @property
    def sources(self) -> list[dict]:
        return list(self._by_url.values())


def format_web(results: list[dict]) -> str:
    return "\n".join(f"[{r['id']}] {r['title']} ({r['site']}, {r['date'] or 'n.d.'}): {r['content'][:600]}"
                     for r in results)


def paper_source(tech: dict) -> dict:
    return {
        "id": tech["source_id"],
        "kind": "paper",
        "tech": tech["key"],
        "title": tech["paper_title"],
        "url": f"https://arxiv.org/abs/{tech['arxiv_id']}",
        "citation": tech["citation"],
    }


def to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1)
