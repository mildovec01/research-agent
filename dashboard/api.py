import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "memory" / "state.db"
REPORTS_DIR = BASE_DIR / "reports"

app = Flask(__name__, static_folder="static")

RESEARCH_TOPICS = {
    "autonomous agricultural robots",
    "ROS2 robotics latest developments",
    "LiDAR sensor technology 2025",
    "autonomous vehicle market trends",
}

COMPETITOR_NAMES = ["Boston Dynamics", "ABB Robotics", "KUKA", "Fanuc", "Universal Robots"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/stats")
def stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM run_log WHERE status='completed'")
    total_runs = c.fetchone()["total"]
    c.execute("SELECT COUNT(DISTINCT topic) as topics FROM research_cache WHERE topic IN ({})".format(
        ",".join("?" * len(RESEARCH_TOPICS))
    ), list(RESEARCH_TOPICS))
    total_topics = c.fetchone()["topics"]
    report_files = list(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []
    c.execute("SELECT created_at FROM run_log WHERE status='completed' ORDER BY created_at DESC LIMIT 1")
    last_run = c.fetchone()
    last_run_time = last_run["created_at"][11:16] if last_run else "—"
    last_run_date = last_run["created_at"][:10] if last_run else "—"
    conn.close()
    return jsonify({
        "total_runs": total_runs,
        "total_topics": total_topics,
        "total_reports": len(report_files),
        "last_run": last_run_time,
        "last_run_date": last_run_date,
    })


@app.route("/api/runs")
def runs():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT run_id, status, summary, created_at FROM run_log ORDER BY created_at DESC LIMIT 20")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/timeline")
def timeline():
    reports = []
    if not REPORTS_DIR.exists():
        return jsonify([])
    for f in sorted(REPORTS_DIR.glob("*.md"), reverse=True)[:10]:
        content = f.read_text(encoding="utf-8")
        lines = content.split("\n")
        title = lines[0].replace("# ", "").replace("Daily Research Report – ", "").strip() if lines else f.stem
        summary = ""
        for i, line in enumerate(lines):
            if "## Executive Summary" in line and i + 1 < len(lines):
                summary = lines[i + 1].strip()
                break
        # truncate summary
        if len(summary) > 160:
            summary = summary[:160] + "…"
        trends = []
        in_trends = False
        for line in lines:
            if "## Key Trends" in line:
                in_trends = True
                continue
            if in_trends and line.startswith("##"):
                break
            if in_trends and line.startswith("- "):
                t = line[2:].strip()
                if len(t) > 35:
                    t = t[:35] + "…"
                trends.append(t)
        reports.append({
            "date": f.stem,
            "title": title,
            "summary": summary,
            "trends": trends[:3],
        })
    return jsonify(reports)


@app.route("/api/competitors")
def competitors():
    conn = get_db()
    c = conn.cursor()
    result = []
    for name in COMPETITOR_NAMES:
        keyword = name.split()[0]
        c.execute("""
            SELECT created_at FROM research_cache
            WHERE topic LIKE ?
            ORDER BY created_at DESC LIMIT 1
        """, (f"%{keyword}%",))
        row = c.fetchone()
        result.append({
            "name": name,
            "last_updated": row["created_at"][:10] if row else None,
        })
    conn.close()
    return jsonify(result)


@app.route("/api/projects")
def projects():
    conn = get_db()
    c = conn.cursor()
    competitor_keywords = ["Dynamics", "ABB", "KUKA", "Fanuc", "Universal"]
    exclusions = list(RESEARCH_TOPICS) + competitor_keywords
    query = """
        SELECT topic, results, created_at FROM research_cache
        WHERE topic NOT IN ({rt})
        {ck}
        ORDER BY created_at DESC LIMIT 50
    """.format(
        rt=",".join("?" * len(RESEARCH_TOPICS)),
        ck=" ".join(f"AND topic NOT LIKE ?" for _ in competitor_keywords)
    )
    params = list(RESEARCH_TOPICS) + [f"%{k}%" for k in competitor_keywords]
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    projects_list = []
    seen = set()
    for row in rows:
        topic = row["topic"]
        if topic in seen:
            continue
        seen.add(topic)
        try:
            data = json.loads(row["results"])
            mc = "?"
            price = "?"
            if isinstance(data, dict):
                mc_obj = data.get("microcontroller", {})
                if isinstance(mc_obj, dict):
                    mc = mc_obj.get("name", "?")
                price = data.get("total_price_czk", "?")
            projects_list.append({
                "name": topic,
                "date": row["created_at"][:10],
                "microcontroller": mc,
                "total_price": price,
            })
        except Exception:
            projects_list.append({"name": topic, "date": row["created_at"][:10], "microcontroller": "?", "total_price": "?"})
    return jsonify(projects_list)


@app.route("/api/score_history")
def score_history():
    scores = []
    if not REPORTS_DIR.exists():
        return jsonify([])
    for f in sorted(REPORTS_DIR.glob("*.md"))[-14:]:
        content = f.read_text(encoding="utf-8")
        score = None
        # look for score in run_log summary
        for line in content.split("\n"):
            m = re.search(r'(\d+)/10', line)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 10:
                    score = val
                    break
        if score is None:
            score = 5
        scores.append({"date": f.stem, "score": score})
    return jsonify(scores)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
