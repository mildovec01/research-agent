import anthropic
import json
from config import ANTHROPIC_API_KEY, RESEARCH_TOPICS
from tools.search import web_search
from tools.rss import fetch_rss_feeds
from memory.state import save_research, get_recent_research

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi research agent specializovaný na robotiku a autonomní vozidla.
Dostaneš surová data z webového vyhledávání a RSS feedů.
Tvým úkolem je:
1. Identifikovat nejdůležitější novinky a trendy
2. Ohodnotit relevanci každého článku (1-10)
3. Extrahovat klíčová fakta a technické detaily
4. Vrátit strukturovaný JSON výstup

Vždy odpovídej POUZE validním JSON bez markdown bloků."""


def run(topics: list[str] | None = None) -> dict:
    if topics is None:
        topics = RESEARCH_TOPICS

    all_web_results = []
    all_rss_articles = []

    for topic in topics:
        cached = get_recent_research(topic)
        if cached:
            print(f"[Research] Cache hit pro: {topic}")
            all_web_results.extend(cached.get("web", []))
            continue

        print(f"[Research] Hledám: {topic}")
        results = web_search(topic, max_results=4)
        all_web_results.extend(results)
        save_research(topic, {"web": results})

    print("[Research] Načítám RSS feedy...")
    all_rss_articles = fetch_rss_feeds(max_per_feed=4)

    data_for_claude = {
        "web_results": all_web_results[:20],
        "rss_articles": all_rss_articles[:15],
    }

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Analyzuj tato data a vrať JSON ve formátu:
{{
  "top_findings": [
    {{"title": "...", "summary": "...", "relevance": 8, "url": "...", "category": "robotics|av|market"}}
  ],
  "key_trends": ["trend1", "trend2"],
  "urgent_news": ["urgent item if any"]
}}

Data: {json.dumps(data_for_claude, ensure_ascii=False)}"""
        }]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
