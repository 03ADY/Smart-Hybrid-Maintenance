import json
import os
import sqlite3

import pandas as pd

DB_FILE = os.getenv("MAINTENANCE_DB", "maintenance_system.db")

_SCHEMA_V2_COLUMNS = [
    ("problem_description", "TEXT"),
    ("suggested_resolution", "TEXT"),
    ("action_label", "TEXT"),
    ("priority", "TEXT"),
    ("sensor_snapshot", "TEXT"),
    ("status", "TEXT"),
]


def init_db(force_reset: bool = False) -> None:
    if force_reset and os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine_id INTEGER NOT NULL,
                health_score REAL NOT NULL,
                failure_prob REAL NOT NULL,
                rul REAL NOT NULL,
                action INTEGER NOT NULL,
                explanation TEXT NOT NULL
            )
        """)
        for col, col_type in _SCHEMA_V2_COLUMNS:
            try:
                cursor.execute(f"ALTER TABLE reports ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        conn.commit()


def add_report(report: dict) -> None:
    init_db()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        conn.execute("""
            INSERT INTO reports (
                timestamp, machine_id, health_score, failure_prob, rul, action, explanation,
                problem_description, suggested_resolution, action_label, priority, sensor_snapshot, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["timestamp"],
            report["machine_id"],
            report.get("health_metrics", {}).get("health_score", 0.0),
            report.get("health_metrics", {}).get("failure_prob", 0.0),
            report.get("health_metrics", {}).get("rul", 0.0),
            report.get("maintenance_action", {}).get("action", 0),
            json.dumps(report.get("explanation", {})),
            report.get("problem_description", ""),
            report.get("suggested_resolution", ""),
            report.get("maintenance_action", {}).get("label", "No action"),
            report.get("priority", "—"),
            json.dumps(report.get("sensor_snapshot", {})),
            report.get("health_metrics", {}).get("status", "HEALTHY"),
        ))
        conn.commit()


def get_reports_by_machine(machine_id: int) -> pd.DataFrame:
    init_db()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        return pd.read_sql_query(
            "SELECT * FROM reports WHERE machine_id = ? ORDER BY timestamp ASC",
            conn,
            params=(machine_id,),
        )


def get_fleet_latest() -> pd.DataFrame:
    """Latest report per machine."""
    init_db()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        return pd.read_sql_query("""
            SELECT r.* FROM reports r
            INNER JOIN (
                SELECT machine_id, MAX(id) AS max_id FROM reports GROUP BY machine_id
            ) t ON r.id = t.max_id
            ORDER BY r.machine_id
        """, conn)


def get_all_machines() -> list[int]:
    init_db()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        rows = conn.execute("SELECT DISTINCT machine_id FROM reports ORDER BY machine_id").fetchall()
        return [r[0] for r in rows]


def get_fleet_history(limit: int = 5000) -> pd.DataFrame:
    init_db()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        return pd.read_sql_query(
            f"SELECT * FROM reports ORDER BY timestamp DESC LIMIT {int(limit)}",
            conn,
        )


def get_alerts(limit: int = 200) -> pd.DataFrame:
    """Rows with warnings, critical health, or active fault descriptions."""
    df = get_fleet_history(limit)
    if df.empty:
        return df
    if "problem_description" not in df.columns:
        df["problem_description"] = ""
    has_fault = df["problem_description"].fillna("").ne("No issue detected.") & df["problem_description"].fillna("").ne("")
    mask = (df["health_score"] < 0.75) | has_fault
    out = df[mask].copy()
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"])
    return out.sort_values("timestamp", ascending=False)


def fleet_kpis() -> dict:
    df = get_fleet_latest()
    with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
        total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    if df.empty:
        return {"avg_health": 0, "critical": 0, "warning": 0, "total_records": int(total)}
    critical = (df["health_score"] < 0.5).sum()
    warning = ((df["health_score"] >= 0.5) & (df["health_score"] < 0.75)).sum()
    return {
        "avg_health": float(df["health_score"].mean()),
        "critical": int(critical),
        "warning": int(warning),
        "total_records": int(total),
    }
