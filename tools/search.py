from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def web_search(query: str, max_results: int = 5) -> list[dict]:
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=True,
    )
    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:500],
            "score": r.get("score", 0),
        })
    return results


def search_company(company: str) -> list[dict]:
    queries = [
        f"{company} latest news 2025",
        f"{company} new products robotics",
        f"{company} funding valuation",
    ]
    all_results = []
    for q in queries:
        all_results.extend(web_search(q, max_results=3))
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    return unique[:8]
