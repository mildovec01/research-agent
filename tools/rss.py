import feedparser
from datetime import datetime, timezone
from config import RSS_FEEDS

def fetch_rss_feeds(max_per_feed: int = 5) -> list[dict]:
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_feed]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", ""),
                "source": feed.feed.get("title", url),
            })
    articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    return articles
