
import json
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import get_connection


app = Flask(__name__)
app.secret_key = "ransomwatch-demo-key"



def get_common_counts(conn):
    event_count = conn.execute("""
        SELECT COUNT(*) AS count FROM events
    """).fetchone()["count"]

    alert_count = conn.execute("""
        SELECT COUNT(*) AS count FROM alerts
    """).fetchone()["count"]

    unique_files = conn.execute("""
        SELECT COUNT(DISTINCT file_path) AS count FROM events
        WHERE file_path IS NOT NULL AND file_path != ''
    """).fetchone()["count"]

    return event_count, alert_count, unique_files



@app.route("/")
def dashboard():

    conn = get_connection()

    events = conn.execute("""
        SELECT * FROM events
        ORDER BY timestamp DESC
        LIMIT 8
    """).fetchall()

    alerts = conn.execute("""
        SELECT * FROM alerts
        ORDER BY timestamp DESC
        LIMIT 5
    """).fetchall()

    event_count, alert_count, unique_files = get_common_counts(conn)

    activity_data = conn.execute("""
        SELECT substr(timestamp, 1, 16) AS minute,
               COUNT(*) AS count
        FROM events
        GROUP BY substr(timestamp, 1, 16)
        ORDER BY minute DESC
        LIMIT 12
    """).fetchall()

    conn.close()

    activity_data = list(reversed(activity_data))

    chart_labels = []
    chart_values = []

    for row in activity_data:
        chart_labels.append(str(row["minute"]))
        chart_values.append(int(row["count"]))

    return render_template(
        "dashboard.html",
        events=events,
        alerts=alerts,
        event_count=event_count,
        alert_count=alert_count,
        unique_files=unique_files,
        chart_labels=chart_labels,
        chart_values=chart_values
    )



@app.route("/events")


def events_page():
    search = request.args.get("search", "").strip()
    event_type = request.args.get("event_type", "ALL").upper()

    event_type_map = {
        "CREATE": "created",
        "MODIFY": "modified",
        "RENAME": "renamed",
        "DELETE": "deleted",
    }

    if event_type != "ALL" and event_type not in event_type_map:
        event_type = "ALL"

    conn = get_connection()

    try:
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if search:
            query += """
                AND (
                    file_path LIKE ?
                    OR old_path LIKE ?
                    OR new_path LIKE ?
                )
            """
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        if event_type != "ALL":
            query += " AND LOWER(event_type) = ?"
            params.append(event_type_map[event_type])

        query += " ORDER BY timestamp DESC"
        events = conn.execute(query, params).fetchall()

        # Summary counts use the complete event history,
        # independent of the current search and filter.
        total_events = conn.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]

        create_count = conn.execute(
            "SELECT COUNT(*) FROM events WHERE LOWER(event_type) = 'created'"
        ).fetchone()[0]

        modify_count = conn.execute(
            "SELECT COUNT(*) FROM events WHERE LOWER(event_type) = 'modified'"
        ).fetchone()[0]

        rename_count = conn.execute(
            "SELECT COUNT(*) FROM events WHERE LOWER(event_type) = 'renamed'"
        ).fetchone()[0]

        alert_count = conn.execute(
    "SELECT COUNT(*) FROM alerts"
).fetchone()[0]

        events = [
            {
                **dict(row),
                "filename": (
                    row["file_path"]
                    or row["new_path"]
                    or row["old_path"]
                    or ""
                ),
            }
            for row in events
        ]

    finally:
        conn.close()

    return render_template(
        "events.html",
        events=events,
        alert_count=alert_count,
        search=search,
        event_type=event_type,
        total_events=total_events,
        create_count=create_count,
        modify_count=modify_count,
        rename_count=rename_count,
    )

   



@app.route("/alerts")
def alerts_page():

    conn = get_connection()

    alerts = conn.execute("""
        SELECT * FROM alerts
        ORDER BY timestamp DESC
    """).fetchall()

    alert_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM alerts
    """).fetchone()["count"]

    conn.close()

    return render_template(
        "alerts.html",
        alerts=alerts,
        alert_count=alert_count
    )



@app.route("/activity-trends")
def activity_trends():
    conn = get_connection()

    try:
        event_count = conn.execute("""
            SELECT COUNT(*) AS count FROM events
        """).fetchone()["count"]

        alert_count = conn.execute("""
            SELECT COUNT(*) AS count FROM alerts
        """).fetchone()["count"]

        unique_files = conn.execute("""
            SELECT COUNT(DISTINCT file_path) AS count
            FROM events
            WHERE file_path IS NOT NULL AND file_path != ''
        """).fetchone()["count"]

        
        event_counts = {}
        for event_type in ("created", "modified", "renamed", "deleted"):
            event_counts[event_type] = conn.execute("""
                SELECT COUNT(*) AS count
                FROM events
                WHERE LOWER(event_type) = ?
            """, (event_type,)).fetchone()["count"]

        
        activity_data = conn.execute("""
            SELECT substr(timestamp, 1, 16) AS minute,
                   COUNT(*) AS count
            FROM events
            GROUP BY substr(timestamp, 1, 16)
            ORDER BY minute DESC
            LIMIT 12
        """).fetchall()

    finally:
        conn.close()

    activity_data = list(reversed(activity_data))

    max_activity = max(
        (int(row["count"]) for row in activity_data),
        default=0
    )

    
    trend_data = []
    for row in activity_data:
        count = int(row["count"])
        minute = str(row["minute"])

        trend_data.append({
            "value": count,
            "height": round(count / max_activity * 100)
                      if max_activity else 0,
            "short_label": minute[11:16]
                           if len(minute) >= 16 else minute
        })

    
    event_definitions = [
        ("created", "CREATE", "green"),
        ("modified", "MODIFY", "blue"),
        ("renamed", "RENAME", "purple"),
        ("deleted", "DELETE", "red"),
    ]

    event_types = []
    for key, label, css_class in event_definitions:
        count = event_counts[key]
        percentage = round(count / event_count * 100, 1) \
                     if event_count else 0

        event_types.append({
            "name": label,
            "class": css_class,
            "count": count,
            "percentage": percentage
        })

    return render_template(
        "activity_trends.html",
        event_count=event_count,
        alert_count=alert_count,
        unique_files=unique_files,
        max_activity=max_activity,
        trend_data=trend_data,
        event_types=event_types
    )


if __name__ == "__main__":
    app.run(debug=True)