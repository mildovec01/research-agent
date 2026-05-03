import asyncio
import time
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from memory.state import init_db
from tools.discord_bot import start_bot_thread, send_report
from agents.orchestrator import run as orchestrator_run
from config import SCHEDULE_HOUR, SCHEDULE_MINUTE


def scheduled_run():
    print(f"\n[Main] Scheduled run spuštěn – {datetime.now().isoformat()}")
    try:
        result = orchestrator_run()
        embeds = result.get("discord", [])
        send_report(embeds)
    except Exception as e:
        print(f"[Main] Chyba v scheduled runu: {e}")


def manual_run(topics: list[str] | None = None):
    print(f"\n[Main] Manuální run – {datetime.now().isoformat()}")
    result = orchestrator_run(topics=topics)
    embeds = result.get("discord", [])
    send_report(embeds)
    return result


def main():
    print("=" * 50)
    print("  ResearchBot – Multi-Agent Research System")
    print("=" * 50)

    init_db()
    print("[Main] Databáze inicializována")

    bot_thread = start_bot_thread()
    time.sleep(3)

    if "--now" in sys.argv:
        print("[Main] Spouštím okamžitý run (--now flag)")
        manual_run()
        time.sleep(5)
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scheduled_run,
        "cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
        id="daily_research",
    )
    scheduler.start()
    print(f"[Main] Scheduler spuštěn – daily run v {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
    print("[Main] Bot běží. Ctrl+C pro ukončení.\n")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[Main] Ukončuji...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
