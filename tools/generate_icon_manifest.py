#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path


def _normalize_key(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return value.upper()


def _keys_for_filename(stem: str) -> set[str]:
    """Generate one or more lookup keys from an icon filename stem.

    Heuristic:
    - Always include the full stem as a key (uppercased)
    - If the stem looks like multiple models joined by '_' (e.g. FG-100F_101F),
      also include each component expanded using the first prefix.
    """

    stem = stem.strip()
    keys: set[str] = set()

    full_key = _normalize_key(stem)
    if full_key:
        keys.add(full_key)

    # Split joined models like FG-100F_101F or FAP-231F_233F_431F_433F
    if "_" in stem:
        parts = [p for p in stem.split("_") if p]
        if parts:
            first = parts[0]
            keys.add(_normalize_key(first))

            # Determine a prefix from the first part, e.g. "FG-" or "FAP-"
            prefix_match = re.match(r"^([A-Za-z]+-)\d", first)
            prefix = prefix_match.group(1) if prefix_match else ""

            for part in parts[1:]:
                part_norm = part
                if prefix and not part_norm.upper().startswith(prefix.upper()):
                    part_norm = prefix + part_norm
                keys.add(_normalize_key(part_norm))

    return {k for k in keys if k}


def build_manifest(icons_dir: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}

    for path in icons_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".svg":
            continue

        rel_path = path.relative_to(icons_dir)
        filename = rel_path.as_posix()
        stem = path.stem

        for key in _keys_for_filename(stem):
            # Prefer a top-level file over nested duplicates if possible.
            if key in manifest:
                existing = manifest[key]
                if "/" in existing and "/" not in filename:
                    manifest[key] = filename
                continue
            manifest[key] = filename

    return dict(sorted(manifest.items(), key=lambda kv: kv[0]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--icons-dir",
        default="app/static/icons",
        help="Directory containing icon SVGs (default: app/static/icons)",
    )
    parser.add_argument(
        "--output",
        default="app/static/icons/manifest.json",
        help="Output manifest path (default: app/static/icons/manifest.json)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = (repo_root / args.icons_dir).resolve()
    output_path = (repo_root / args.output).resolve()

    if not icons_dir.exists() or not icons_dir.is_dir():
        raise SystemExit(f"Icons directory not found: {icons_dir}")

    manifest = build_manifest(icons_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    os.replace(tmp_path, output_path)

    print(f"Wrote {len(manifest)} entries to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
