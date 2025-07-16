import os
import sqlite3

DB_PATH = os.path.join(os.getcwd(), "app", "static", "icons.db")


def get_icon(manufacturer=None, device_type=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if manufacturer:
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
