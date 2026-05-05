import uuid
from datetime import datetime
from agents import research, competitor, synthesis
from memory.state import log_run


CATEGORY_COLORS = {
    "robotics": 0x1D9E75,
    "market": 0x7F77DD,
    "competitor": 0xD85A30,
    "default": 0x888780,
}


def run(topics: list[str] | None = None, companies: list[str] | None = None, skip_competitor: bool = False) -> dict:
    run_id = str(uuid.uuid4())[:8]
    print(f"\n{'='*50}")
    print(f"[Orchestrator] Spouštím run {run_id} – {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    log_run(run_id, "started")

    try:
        print("\n[Orchestrator] Fáze 1: Research agent")
        research_data = research.run(topics)

        print("\n[Orchestrator] Fáze 2: Competitor agent")
        competitor_data = competitor.run(companies) if not skip_competitor else {"company_updates": [], "market_trends": [], "opportunities": []}

        print("\n[Orchestrator] Fáze 3: Synthesis agent")
        final_report = synthesis.run(research_data, competitor_data)

        discord_payload = build_discord_payload(final_report)
        log_run(run_id, "completed", final_report.get("executive_summary", ""))

        print(f"\n[Orchestrator] Run {run_id} dokončen ✓")
        return {"report": final_report, "discord": discord_payload}

    except Exception as e:
        log_run(run_id, "failed", str(e))
        print(f"[Orchestrator] Run {run_id} selhal: {e}")
        raise


def build_discord_payload(report: dict) -> list[dict]:
    embeds = []

    main_embed = {
        "title": report.get("title", "Research Report"),
        "description": report.get("executive_summary", ""),
        "color": 0x1D9E75,
        "fields": [],
        "footer": {"text": f"ResearchBot • {datetime.now().strftime('%d.%m.%Y %H:%M')}"},
        "thumbnail": {"url": "https://cdn.discordapp.com/embed/avatars/0.png"},
    }

    trends = report.get("key_trends", [])
    if trends:
        main_embed["fields"].append({
            "name": "📈 Key Trends",
            "value": "\n".join(f"• {t}" for t in trends[:4]),
            "inline": False,
        })

    competitors = report.get("competitor_highlights", [])
    if competitors:
        main_embed["fields"].append({
            "name": "🏭 Competitor Highlights",
            "value": "\n".join(f"• {c}" for c in competitors[:3]),
            "inline": False,
        })

    score = report.get("score", 5)
    main_embed["fields"].append({
        "name": "Relevance Score",
        "value": f"{'🟢' if score >= 7 else '🟡' if score >= 4 else '🔴'} {score}/10",
        "inline": True,
    })

    embeds.append(main_embed)

    for story in report.get("top_stories", [])[:3]:
        color = CATEGORY_COLORS.get(story.get("category", "default"), CATEGORY_COLORS["default"])
        story_embed = {
            "title": story.get("title", ""),
            "description": story.get("summary", ""),
            "color": color,
            "url": story.get("url", ""),
        }
        embeds.append(story_embed)

    return embeds
