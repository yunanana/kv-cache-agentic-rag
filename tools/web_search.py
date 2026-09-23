"""웹 검색 도구 (Tavily). 논문에 없는 시장·채택 동향 보강용."""

import os
from urllib.parse import urlparse

from tavily import TavilyClient


def web_search(query: str, max_results: int = 4) -> list[dict]:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    try:
        res = TavilyClient(api_key=key).search(query=query, max_results=max_results, search_depth="basic")
    except Exception as e:  # 검색 실패 시 해당 질의만 건너뜀
        print(f"[web_search] '{query}' 실패: {e}")
        return []
    return [
        {
            "title": r.get("title", "").strip(),
            "url": r.get("url", ""),
            "content": r.get("content", "").strip(),
            "published_date": (r.get("published_date") or "")[:10],
        }
        for r in res.get("results", [])
    ]


def site_name(url: str) -> str:
    host = urlparse(url).netloc
    return host[4:] if host.startswith("www.") else host
