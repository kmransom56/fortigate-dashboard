import os
import sqlite3

DB_PATH = os.path.join(os.getcwd(), "app", "static", "icons.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS icons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT,
    device_type TEXT,
    slug TEXT,
    title TEXT,
    icon_path TEXT,
    source_url TEXT,
    tags TEXT
);
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()


def insert_icon(manufacturer, device_type, slug, title, icon_path, source_url, tags):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO icons (manufacturer, device_type, slug, title, icon_path, source_url, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (manufacturer, device_type, slug, title, icon_path, source_url, tags),
        )
        conn.commit()


def get_icon(manufacturer=None, device_type=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if manufacturer and device_type:
        cursor.execute(
            "SELECT icon_path, title, slug FROM icons WHERE manufacturer=? AND device_type=? ORDER BY id DESC LIMIT 1",
            (manufacturer, device_type),
        )
    elif manufacturer:
        cursor.execute(
            "SELECT icon_path, title, slug FROM icons WHERE manufacturer=? ORDER BY id DESC LIMIT 1",
            (manufacturer,),
        )
    elif device_type:
        cursor.execute(
            "SELECT icon_path, title, slug FROM icons WHERE device_type=? ORDER BY id DESC LIMIT 1",
            (device_type,),
        )
    else:
        conn.close()
        return None
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"icon_path": result[0], "title": result[1], "slug": result[2]}
    return None


def get_icons_by_tag(tag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT icon_path, title FROM icons WHERE tags LIKE ?", (f"%{tag}%",)
    )
    results = cursor.fetchall()
    conn.close()
    return [{"icon_path": r[0], "title": r[1]} for r in results]


def update_icon(icon_id, **kwargs):
    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values())
    values.append(icon_id)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE icons SET {fields} WHERE id = ?", values)
        conn.commit()
