#!/usr/bin/env python3
import argparse
import os
import re
from typing import Optional

# Allow running from repo root
import sys
sys.path.append(os.path.abspath('.'))

from app.utils.icon_db import init_db, insert_icon

DEVICE_TYPE_MAP = [
    (re.compile(r"firewall", re.I), "firewall"),
    (re.compile(r"switch|lan-?switch|stack", re.I), "switch"),
    (re.compile(r"router|gateway|edge|nat", re.I), "router"),
    (re.compile(r"server|rack|blade|db|database|vm|compute", re.I), "server"),
    (re.compile(r"ap|access[-_ ]?point|wifi|wireless", re.I), "access-point"),
    (re.compile(r"cloud", re.I), "cloud"),
    (re.compile(r"internet|globe|wan", re.I), "internet"),
    (re.compile(r"printer|print", re.I), "printer"),
    (re.compile(r"camera|cctv|ipcam|webcam", re.I), "camera"),
    (re.compile(r"nas|storage|san", re.I), "nas"),
    (re.compile(r"phone|voip|sip", re.I), "phone"),
    (re.compile(r"tablet|ipad", re.I), "tablet"),
    (re.compile(r"controller|wlc|wifi[-_ ]?controller", re.I), "wifi-controller"),
    (re.compile(r"load[-_ ]?balancer|adc|f5|netscaler", re.I), "load-balancer"),
    (re.compile(r"vpn|ipsec|ssl-vpn", re.I), "vpn"),
    (re.compile(r"pc|desktop|laptop|endpoint|workstation", re.I), "endpoint"),
]

# Affinity style prioritization: allow selecting color/shape
AFFINITY_STYLE_HINTS = {
    # e.g., 'square/red', 'circle/blue', etc.
    'square/red': ('square', 'red'),
    'square/blue': ('square', 'blue'),
    'circle/red': ('circle', 'red'),
    'circle/blue': ('circle', 'blue'),
}

STATIC_PREFIX = os.path.join("app", "static")


def guess_device_type(filename: str) -> Optional[str]:
    base = os.path.splitext(os.path.basename(filename))[0]
    for pattern, dtype in DEVICE_TYPE_MAP:
        if pattern.search(base):
            return dtype
    return None


def to_slug(name: str) -> str:
    base = os.path.splitext(os.path.basename(name))[0]
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def main():
    parser = argparse.ArgumentParser(description="Import icon pack into icons.db")
    parser.add_argument("directory", help="Path under app/static to the icon pack directory (e.g., app/static/icons/packs/ntwrk-clean-and-flat)")
    parser.add_argument("--pack", default=None, help="Pack name tag (default: directory name)")
    parser.add_argument("--manufacturer", default=None, help="Manufacturer to assign (optional)")
    parser.add_argument("--affinity-style", default=None, help="Affinity style hint like 'square/red' to prioritize those files")
    args = parser.parse_args()

    directory = args.directory
    if not os.path.isdir(directory):
        print(f"Directory not found: {directory}")
        sys.exit(1)

    # Ensure directory is under app/static so we can compute relative icon_path
    static_abs = os.path.abspath(STATIC_PREFIX)
    dir_abs = os.path.abspath(directory)
    if not dir_abs.startswith(static_abs + os.sep):
        print("Directory must be under app/static")
        sys.exit(1)

    rel_dir = os.path.relpath(dir_abs, static_abs)
    pack = args.pack or os.path.basename(dir_abs)

    init_db()

    inserted = 0
    # If affinity style hint provided, walk that subdir first
    walk_dirs = []
    if args.affinity_style and 'affinity' in os.path.basename(dir_abs).lower():
        style = AFFINITY_STYLE_HINTS.get(args.affinity_style)
        if style:
            shape, color = style
            pref = os.path.join(dir_abs, 'svg', shape, color)
            if os.path.isdir(pref):
                walk_dirs.append(pref)
    walk_dirs.append(dir_abs)

    seen = set()
    for base_dir in walk_dirs:
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if not fn.lower().endswith((".svg", ".png")):
                    continue
                abs_path = os.path.join(root, fn)
                rel_path = os.path.relpath(abs_path, static_abs).replace(os.sep, "/")
                dtype = guess_device_type(fn)
                if not dtype:
                    # Skip unknown types to keep DB clean
                    continue
                key = (dtype, rel_path)
                if key in seen:
                    continue
                title = dtype.replace("-", " ").title()
                slug = to_slug(fn)
                insert_icon(
                    manufacturer=args.manufacturer,
                    device_type=dtype,
                    slug=slug,
                    title=title,
                    icon_path=rel_path,
                    source_url=f"pack:{pack}",
                    tags=f"network-diagram,pack:{pack},{dtype}",
                )
                inserted += 1
                seen.add(key)

    print(f"Imported {inserted} icons into DB from {pack}")


if __name__ == "__main__":
    main()
