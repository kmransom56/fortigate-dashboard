import os
import sqlite3
from functools import lru_cache

# Resolve DB path relative to this file, so it works regardless of CWD
_UTILS_DIR = os.path.dirname(__file__)
_APP_DIR = os.path.dirname(_UTILS_DIR)
DB_PATH = os.path.join(_APP_DIR, "static", "icons.db")

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

BINDINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS icon_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT NOT NULL,          -- 'serial' | 'manufacturer' | 'mac' | 'device_type'
    key_value TEXT NOT NULL,
    device_type TEXT,
    title TEXT,
    icon_path TEXT NOT NULL,
    priority INTEGER DEFAULT 100,
    UNIQUE(key_type, key_value)
);
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.execute(BINDINGS_TABLE_SQL)
        conn.commit()


def insert_icon(manufacturer, device_type, slug, title, icon_path, source_url, tags):
    filename = (
        os.path.basename(icon_path) if icon_path else slug or title or "unknown.svg"
    )
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO icons (filename, path, full_path, size, hash, width, height, modified, manufacturer, device_type, slug, title, icon_path, source_url, tags)
            VALUES (?, '', '', NULL, NULL, '', '', NULL, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filename,
                manufacturer,
                device_type,
                slug,
                title,
                icon_path,
                source_url,
                tags,
            ),
        )
        conn.commit()


@lru_cache(maxsize=500)
def get_icon(manufacturer=None, device_type=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if manufacturer and device_type:
        cursor.execute(
            """
            SELECT icon_path, title, slug FROM icons
            WHERE manufacturer=? AND device_type=?
            ORDER BY (CASE WHEN icon_path LIKE '%/affinity/%/square/red/%' THEN 0 ELSE 1 END), id DESC
            LIMIT 1
            """,
            (manufacturer, device_type),
        )
    elif manufacturer:
        cursor.execute(
            """
            SELECT icon_path, title, slug FROM icons
            WHERE manufacturer=?
            ORDER BY (CASE WHEN icon_path LIKE '%/affinity/%/square/red/%' THEN 0 ELSE 1 END), id DESC
            LIMIT 1
            """,
            (manufacturer,),
        )
    elif device_type:
        cursor.execute(
            """
            SELECT icon_path, title, slug FROM icons
            WHERE device_type=?
            ORDER BY (CASE WHEN icon_path LIKE '%/affinity/%/square/red/%' THEN 0 ELSE 1 END), id DESC
            LIMIT 1
            """,
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


from typing import Optional


def add_icon_binding(
    key_type: str,
    key_value: str,
    icon_path: str,
    title: Optional[str] = None,
    device_type: Optional[str] = None,
    priority: int = 100,
):
    """Create or update a binding of a serial/manufacturer/mac/device_type to an icon path."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(BINDINGS_TABLE_SQL)
        conn.execute(
            """
            INSERT INTO icon_bindings (key_type, key_value, device_type, title, icon_path, priority)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key_type, key_value) DO UPDATE SET
              device_type=excluded.device_type,
              title=excluded.title,
              icon_path=excluded.icon_path,
              priority=excluded.priority
            """,
            (key_type, key_value, device_type, title, icon_path, priority),
        )
        conn.commit()


@lru_cache(maxsize=500)
def get_icon_binding(
    manufacturer: Optional[str] = None,
    serial: Optional[str] = None,
    mac: Optional[str] = None,
    device_type: Optional[str] = None,
):
    """Return the highest-priority icon binding for given identifiers."""
    init_db()
    clauses = []
    params = []
    if serial:
        clauses.append(("serial", serial))
    if mac:
        clauses.append(("mac", mac))
    if manufacturer:
        clauses.append(("manufacturer", manufacturer))
    if device_type:
        clauses.append(("device_type", device_type))
    if not clauses:
        return None
    # Build UNION query to prioritize by provided order then by priority asc
    union_parts = []
    for key_type, key_value in clauses:
        union_parts.append(
            "SELECT icon_path, title, device_type, priority FROM icon_bindings WHERE key_type=? AND key_value=?"
        )
        params.extend([key_type, key_value])
    sql = " UNION ALL ".join(union_parts) + " ORDER BY priority ASC LIMIT 1"
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        if row:
            return {
                "icon_path": row[0],
                "title": row[1],
                "device_type": row[2],
                "priority": row[3],
            }
    return None


def _icon_exists(conn, manufacturer: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM icons WHERE manufacturer = ? LIMIT 1", (manufacturer,))
    return cur.fetchone() is not None


def seed_default_icons():
    """Seed common vendor icons into the icons.db if they are not present.

    This is idempotent and safe to call at startup.
    """
    init_db()
    vendors = [
        # Apple
        {
            "icon_path": "icons/apple.svg",
            "title": "Apple",
            "source_url": "https://apple.com/",
            "tags": "vendor,apple,endpoint,tablet,phone",
            "aliases": [
                "Apple",
                "Apple Inc.",
            ],
        },
        # Microsoft
        {
            "icon_path": "icons/microsoft.svg",
            "title": "Microsoft",
            "source_url": "https://microsoft.com/",
            "tags": "vendor,microsoft,pc,server,endpoint",
            "aliases": [
                "Microsoft",
                "Microsoft Corporation",
            ],
        },
        # Intel
        {
            "icon_path": "icons/intel.svg",
            "title": "Intel",
            "source_url": "https://intel.com/",
            "tags": "vendor,intel,pc",
            "aliases": [
                "Intel",
                "Intel Corporate",
            ],
        },
        # AMD
        {
            "icon_path": "icons/amd.svg",
            "title": "AMD",
            "source_url": "https://amd.com/",
            "tags": "vendor,amd,pc",
            "aliases": [
                "Advanced Micro Devices",
                "Advanced Micro Devices, Inc.",
                "AMD",
            ],
        },
        # NVIDIA
        {
            "icon_path": "icons/nvidia.svg",
            "title": "NVIDIA",
            "source_url": "https://nvidia.com/",
            "tags": "vendor,nvidia,gpu",
            "aliases": [
                "NVIDIA",
                "NVIDIA Corporation",
            ],
        },
        # HP / HPE
        {
            "icon_path": "icons/hp.svg",
            "title": "HP",
            "source_url": "https://hp.com/",
            "tags": "vendor,hp,hewlett packard,pc,printer",
            "aliases": [
                "HP",
                "HP Inc.",
                "Hewlett Packard",
                "Hewlett-Packard",
                "Hewlett-Packard Company",
                "Hewlett Packard Enterprise",
                "HPE",
            ],
        },
        # Ubiquiti
        {
            "icon_path": "icons/ubiquiti.svg",
            "title": "Ubiquiti",
            "source_url": "https://ui.com/",
            "tags": "vendor,ubiquiti,network,wireless",
            "aliases": [
                "Ubiquiti",
                "Ubiquiti Inc.",
                "Ubiquiti Networks",
                "Ubiquiti Networks Inc.",
            ],
        },
    ]

    # Network diagram device-type icon seeds (generic)
    device_types = [
        {
            "device_type": "fortigate",
            "title": "Firewall",
            "icon_path": "icons/nd/firewall.svg",
        },
        {
            "device_type": "firewall",
            "title": "Firewall",
            "icon_path": "icons/nd/firewall.svg",
        },
        {
            "device_type": "fortiswitch",
            "title": "Switch",
            "icon_path": "icons/nd/switch.svg",
        },
        {
            "device_type": "switch",
            "title": "Switch",
            "icon_path": "icons/nd/switch.svg",
        },
        {
            "device_type": "router",
            "title": "Router",
            "icon_path": "icons/nd/router.svg",
        },
        {
            "device_type": "endpoint",
            "title": "Endpoint",
            "icon_path": "icons/nd/laptop.svg",
        },
        {
            "device_type": "server",
            "title": "Server",
            "icon_path": "icons/nd/server.svg",
        },
        {
            "device_type": "access-point",
            "title": "Access Point",
            "icon_path": "icons/nd/access-point.svg",
        },
        {"device_type": "cloud", "title": "Cloud", "icon_path": "icons/nd/cloud.svg"},
        {
            "device_type": "internet",
            "title": "Internet",
            "icon_path": "icons/nd/internet.svg",
        },
        {
            "device_type": "printer",
            "title": "Printer",
            "icon_path": "icons/nd/printer.svg",
        },
        {
            "device_type": "camera",
            "title": "Camera",
            "icon_path": "icons/nd/camera.svg",
        },
        {"device_type": "nas", "title": "NAS", "icon_path": "icons/nd/nas.svg"},
        {"device_type": "phone", "title": "Phone", "icon_path": "icons/nd/phone.svg"},
        {
            "device_type": "tablet",
            "title": "Tablet",
            "icon_path": "icons/nd/tablet.svg",
        },
        {
            "device_type": "wifi-controller",
            "title": "WiFi Controller",
            "icon_path": "icons/nd/wifi-controller.svg",
        },
        {
            "device_type": "load-balancer",
            "title": "Load Balancer",
            "icon_path": "icons/nd/load-balancer.svg",
        },
        {"device_type": "vpn", "title": "VPN", "icon_path": "icons/nd/vpn.svg"},
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_TABLE_SQL)
        for v in vendors:
            for alias in v["aliases"]:
                if not _icon_exists(conn, alias):
                    filename = (
                        os.path.basename(v["icon_path"])
                        if v["icon_path"]
                        else alias.lower().replace(" ", "-") + ".svg"
                    )
                    conn.execute(
                        """
                        INSERT INTO icons (filename, path, full_path, size, hash, width, height, modified, manufacturer, device_type, slug, title, icon_path, source_url, tags)
                        VALUES (?, '', '', NULL, NULL, '', '', NULL, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            filename,
                            alias,
                            None,
                            alias.lower().replace(" ", "-"),
                            v["title"],
                            v["icon_path"],
                            v["source_url"],
                            v["tags"],
                        ),
                    )
        # Seed device-type icons if missing
        for dt in device_types:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM icons WHERE device_type = ? LIMIT 1",
                (dt["device_type"],),
            )
            if cur.fetchone() is None:
                filename = (
                    os.path.basename(dt["icon_path"])
                    if dt["icon_path"]
                    else dt["device_type"] + ".svg"
                )
                conn.execute(
                    """
                    INSERT INTO icons (filename, path, full_path, size, hash, width, height, modified, manufacturer, device_type, slug, title, icon_path, source_url, tags)
                    VALUES (?, '', '', NULL, NULL, '', '', NULL, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filename,
                        None,
                        dt["device_type"],
                        dt["device_type"],
                        dt["title"],
                        dt["icon_path"],
                        None,
                        "network-diagram,default",
                    ),
                )
        conn.commit()


def browse_icons(manufacturer=None, device_type=None, limit=50, offset=0):
    """Browse icons with optional filtering"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Build WHERE clause based on filters
    where_conditions = []
    params = []

    if manufacturer:
        where_conditions.append("manufacturer = ?")
        params.append(manufacturer)

    if device_type:
        where_conditions.append("device_type = ?")
        params.append(device_type)

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    # Get total count
    count_query = f"SELECT COUNT(*) FROM icons {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get icons with pagination
    query = f"""
        SELECT manufacturer, device_type, slug, title, icon_path, source_url, tags
        FROM icons
        {where_clause}
        ORDER BY manufacturer, device_type, title
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()

    icons = []
    for row in results:
        manufacturer, device_type, slug, title, icon_path, source_url, tags = row
        icons.append(
            {
                "manufacturer": manufacturer,
                "device_type": device_type,
                "slug": slug,
                "title": title,
                "icon_path": icon_path,
                "source_url": source_url,
                "tags": tags.split(",") if tags else [],
            }
        )

    conn.close()

    return {
        "icons": icons,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def search_icons(query, limit=20):
    """Search icons by title or tags"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    search_term = f"%{query}%"

    cursor.execute(
        """
        SELECT manufacturer, device_type, slug, title, icon_path, source_url, tags
        FROM icons
        WHERE title LIKE ? OR tags LIKE ? OR manufacturer LIKE ?
        ORDER BY 
            CASE 
                WHEN title LIKE ? THEN 1
                WHEN manufacturer LIKE ? THEN 2  
                WHEN tags LIKE ? THEN 3
                ELSE 4
            END,
            title
        LIMIT ?
    """,
        (
            search_term,
            search_term,
            search_term,
            search_term,
            search_term,
            search_term,
            limit,
        ),
    )

    results = cursor.fetchall()

    icons = []
    for row in results:
        manufacturer, device_type, slug, title, icon_path, source_url, tags = row
        icons.append(
            {
                "manufacturer": manufacturer,
                "device_type": device_type,
                "slug": slug,
                "title": title,
                "icon_path": icon_path,
                "source_url": source_url,
                "tags": tags.split(",") if tags else [],
            }
        )

    conn.close()

    return {"icons": icons, "query": query, "count": len(icons)}
