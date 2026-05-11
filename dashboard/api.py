import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "memory" / "state.db"
REPORTS_DIR = BASE_DIR / "reports"

app = Flask(__name__, static_folder="static")


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

    c.execute("SELECT COUNT(DISTINCT topic) as topics FROM research_cache")
    total_topics = c.fetchone()["topics"]

    report_files = list(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []

    c.execute("""
        SELECT created_at FROM run_log
        WHERE status='completed'
        ORDER BY created_at DESC LIMIT 1
    """)
    last_run = c.fetchone()
    last_run_time = last_run["created_at"][:16].replace("T", " ") if last_run else "Nikdy"

    conn.close()
    return jsonify({
        "total_runs": total_runs,
        "total_topics": total_topics,
        "total_reports": len(report_files),
        "last_run": last_run_time,
    })


@app.route("/api/runs")
def runs():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT run_id, status, summary, created_at
        FROM run_log
        ORDER BY created_at DESC
        LIMIT 30
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/timeline")
def timeline():
    reports = []
    if not REPORTS_DIR.exists():
        return jsonify([])

    for f in sorted(REPORTS_DIR.glob("*.md"), reverse=True)[:14]:
        content = f.read_text(encoding="utf-8")
        lines = content.split("\n")
        title = lines[0].replace("# ", "") if lines else f.stem
        summary = ""
        for i, line in enumerate(lines):
            if "## Executive Summary" in line and i + 1 < len(lines):
                summary = lines[i + 1].strip()
                break

        trends = []
        in_trends = False
        for line in lines:
            if "## Key Trends" in line:
                in_trends = True
                continue
            if in_trends and line.startswith("##"):
                break
            if in_trends and line.startswith("- "):
                trends.append(line[2:].strip())

        reports.append({
            "date": f.stem,
            "title": title,
            "summary": summary,
            "trends": trends[:4],
        })

    return jsonify(reports)


@app.route("/api/competitors")
def competitors():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT topic, results, created_at
        FROM research_cache
        WHERE topic LIKE '%Dynamics%'
           OR topic LIKE '%ABB%'
           OR topic LIKE '%KUKA%'
           OR topic LIKE '%Fanuc%'
           OR topic LIKE '%Universal%'
           OR topic LIKE '%Robots%'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = c.fetchall()
    conn.close()

    companies = {}
    for row in rows:
        topic = row["topic"]
        if topic not in companies:
            companies[topic] = {
                "name": topic,
                "last_updated": row["created_at"][:10],
            }

    return jsonify(list(companies.values()))


@app.route("/api/projects")
def projects():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT topic, results, created_at
        FROM research_cache
        WHERE topic NOT IN (
            'autonomous agricultural robots',
            'ROS2 robotics latest developments',
            'LiDAR sensor technology 2025',
            'autonomous vehicle market trends'
        )
        AND topic NOT LIKE '%Dynamics%'
        AND topic NOT LIKE '%ABB%'
        AND topic NOT LIKE '%KUKA%'
        AND topic NOT LIKE '%Fanuc%'
        AND topic NOT LIKE '%Universal%'
        ORDER BY created_at DESC
        LIMIT 50
    """)
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
            projects_list.append({
                "name": topic,
                "date": row["created_at"][:10],
                "microcontroller": data.get("microcontroller", {}).get("name", "?") if isinstance(data, dict) else "?",
                "total_price": data.get("total_price_czk", "?") if isinstance(data, dict) else "?",
            })
        except Exception:
            projects_list.append({
                "name": topic,
                "date": row["created_at"][:10],
                "microcontroller": "?",
                "total_price": "?",
            })

    return jsonify(projects_list)


@app.route("/api/score_history")
def score_history():
    scores = []
    if not REPORTS_DIR.exists():
        return jsonify([])

    for f in sorted(REPORTS_DIR.glob("*.md"))[-14:]:
        content = f.read_text(encoding="utf-8")
        score = 5
        for line in content.split("\n"):
            if "/10" in line and any(e in line for e in ["🟢", "🟡", "🔴"]):
                try:
                    score = int(line.split("/10")[0].strip()[-1])
                except Exception:
                    pass
        scores.append({"date": f.stem, "score": score})

    return jsonify(scores)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
