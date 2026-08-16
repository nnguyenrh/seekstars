import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from starseek.models.chart import BirthChart, SynastryReport
from starseek.services.geocoding import GeocodingResult


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS charts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT,
    birth_datetime TEXT NOT NULL,
    birth_location TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timezone TEXT NOT NULL,
    house_system TEXT NOT NULL DEFAULT 'Placidus',
    chart_data JSON NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS locations_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_query TEXT NOT NULL UNIQUE,
    city_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timezone_id TEXT NOT NULL,
    country_code TEXT,
    cached_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_locations_query ON locations_cache(city_query);
CREATE INDEX IF NOT EXISTS idx_charts_name ON charts(name);
CREATE INDEX IF NOT EXISTS idx_charts_user_id ON charts(user_id);

CREATE TABLE IF NOT EXISTS synastry_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chart_a_id INTEGER NOT NULL,
    chart_b_id INTEGER NOT NULL,
    name_a TEXT,
    name_b TEXT,
    report_data JSON NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chart_a_id) REFERENCES charts(id) ON DELETE CASCADE,
    FOREIGN KEY (chart_b_id) REFERENCES charts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_synastry_user_id ON synastry_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_synastry_chart_a ON synastry_reports(chart_a_id);
CREATE INDEX IF NOT EXISTS idx_synastry_chart_b ON synastry_reports(chart_b_id);
"""

DEFAULT_ADMIN_USER = "admin"


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str, admin_password: str = "admin", force: bool = False) -> None:
    if force and Path(db_path).exists():
        Path(db_path).unlink()

    conn = _get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)

        row = conn.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USER,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
                (DEFAULT_ADMIN_USER, admin_password, "Admin", "admin"),
            )
            conn.commit()
    finally:
        conn.close()


def _get_admin_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USER,)).fetchone()
    if row is None:
        raise RuntimeError("Admin user not found. Run init_db first.")
    return row["id"]


def save_chart(db_path: str, chart: BirthChart) -> int:
    conn = _get_connection(db_path)
    try:
        user_id = _get_admin_id(conn)
        chart_json = chart.model_dump_json()

        cursor = conn.execute(
            """INSERT INTO charts (user_id, name, birth_datetime, birth_location,
               latitude, longitude, timezone, house_system, chart_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                chart.name,
                chart.birth_datetime.isoformat(),
                chart.birth_location,
                chart.latitude,
                chart.longitude,
                chart.timezone,
                chart.house_system.value,
                chart_json,
            ),
        )
        conn.commit()
        chart_id = cursor.lastrowid
        return chart_id
    finally:
        conn.close()


def load_chart(db_path: str, chart_id: int) -> BirthChart | None:
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id, chart_data FROM charts WHERE id = ?",
            (chart_id,),
        ).fetchone()

        if row is None:
            return None

        chart = BirthChart.model_validate_json(row["chart_data"])
        chart.id = row["id"]
        return chart
    finally:
        conn.close()


@dataclass
class ChartListItem:
    id: int
    name: Optional[str]
    birth_datetime: str
    birth_location: str
    house_system: str
    created_at: str


def list_charts(
    db_path: str,
    limit: int = 20,
    offset: int = 0,
    name_filter: str | None = None,
) -> tuple[list[ChartListItem], int]:
    conn = _get_connection(db_path)
    try:
        where_clause = ""
        params: list = []

        if name_filter:
            where_clause = "WHERE name LIKE ?"
            params.append(f"%{name_filter}%")

        count_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM charts {where_clause}",
            params,
        ).fetchone()
        total = count_row["cnt"]

        rows = conn.execute(
            f"""SELECT id, name, birth_datetime, birth_location, house_system, created_at
                FROM charts {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()

        items = [
            ChartListItem(
                id=r["id"],
                name=r["name"],
                birth_datetime=r["birth_datetime"],
                birth_location=r["birth_location"],
                house_system=r["house_system"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

        return items, total
    finally:
        conn.close()


def delete_chart(db_path: str, chart_id: int) -> bool:
    conn = _get_connection(db_path)
    try:
        cursor = conn.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def save_synastry(db_path: str, report: SynastryReport) -> int:
    conn = _get_connection(db_path)
    try:
        user_id = _get_admin_id(conn)
        report_json = report.model_dump_json()

        cursor = conn.execute(
            """INSERT INTO synastry_reports
               (user_id, chart_a_id, chart_b_id, name_a, name_b, report_data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                report.chart_a.id,
                report.chart_b.id,
                report.chart_a.name,
                report.chart_b.name,
                report_json,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_synastry(db_path: str, report_id: int) -> SynastryReport | None:
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id, report_data FROM synastry_reports WHERE id = ?",
            (report_id,),
        ).fetchone()

        if row is None:
            return None

        return SynastryReport.model_validate_json(row["report_data"])
    finally:
        conn.close()


@dataclass
class SynastryListItem:
    id: int
    name_a: Optional[str]
    name_b: Optional[str]
    chart_a_id: int
    chart_b_id: int
    created_at: str


def list_synastries(
    db_path: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[SynastryListItem], int]:
    conn = _get_connection(db_path)
    try:
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM synastry_reports"
        ).fetchone()
        total = count_row["cnt"]

        rows = conn.execute(
            """SELECT id, name_a, name_b, chart_a_id, chart_b_id, created_at
               FROM synastry_reports
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            [limit, offset],
        ).fetchall()

        items = [
            SynastryListItem(
                id=r["id"],
                name_a=r["name_a"],
                name_b=r["name_b"],
                chart_a_id=r["chart_a_id"],
                chart_b_id=r["chart_b_id"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

        return items, total
    finally:
        conn.close()


def delete_synastry(db_path: str, report_id: int) -> bool:
    conn = _get_connection(db_path)
    try:
        cursor = conn.execute("DELETE FROM synastry_reports WHERE id = ?", (report_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def cache_location(db_path: str, query: str, result: GeocodingResult) -> None:
    conn = _get_connection(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO locations_cache
               (city_query, city_name, latitude, longitude, timezone_id, country_code)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                query.lower().strip(),
                result.city_name,
                result.latitude,
                result.longitude,
                result.timezone,
                result.country_code,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_location(db_path: str, query: str) -> GeocodingResult | None:
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT city_name, latitude, longitude, timezone_id, country_code FROM locations_cache WHERE city_query = ?",
            (query.lower().strip(),),
        ).fetchone()

        if row is None:
            return None

        return GeocodingResult(
            city_name=row["city_name"],
            country="",
            country_code=row["country_code"] or "",
            latitude=row["latitude"],
            longitude=row["longitude"],
            timezone=row["timezone_id"],
        )
    finally:
        conn.close()
