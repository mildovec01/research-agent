import anthropic
import json
from datetime import datetime
from pathlib import Path
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi synthesis agent. Dostaneš výsledky od research agenta a competitor agenta.
Tvým úkolem je:
1. Sloučit a deduplikovat informace
2. Sestavit přehledný report
3. Zvýraznit nejdůležitější věci
4. Vrátit strukturovaný JSON pro Discord embed + markdown report

Vždy odpovídej POUZE validním JSON bez markdown bloků."""


def run(research_data: dict, competitor_data: dict) -> dict:
    print("[Synthesis] Generuji souhrnný report...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Syntetizuj tato data do reportu. Vrať JSON ve formátu:
{{
  "title": "Daily Research Report – {datetime.now().strftime('%d.%m.%Y')}",
  "executive_summary": "2-3 věty o nejdůležitějším",
  "top_stories": [
    {{"title": "...", "summary": "...", "url": "...", "category": "robotics|market|competitor"}}
  ],
  "key_trends": ["..."],
  "competitor_highlights": ["..."],
  "score": 7
}}

Research data: {json.dumps(research_data, ensure_ascii=False)}
Competitor data: {json.dumps(competitor_data, ensure_ascii=False)}"""
        }]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    result = json.loads(raw)

    save_markdown_report(result)
    return result


def save_markdown_report(data: dict):
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = reports_dir / f"{date_str}.md"

    lines = [
        f"# {data.get('title', 'Research Report')}",
        f"\n## Executive Summary\n{data.get('executive_summary', '')}",
        "\n## Top Stories",
    ]

    for story in data.get("top_stories", []):
        lines.append(f"\n### {story.get('title', '')}")
        lines.append(story.get("summary", ""))
        if story.get("url"):
            lines.append(f"[Zdroj]({story['url']})")

    lines.append("\n## Key Trends")
    for trend in data.get("key_trends", []):
        lines.append(f"- {trend}")

    lines.append("\n## Competitor Highlights")
    for item in data.get("competitor_highlights", []):
        lines.append(f"- {item}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Synthesis] Report uložen: {filepath}")
