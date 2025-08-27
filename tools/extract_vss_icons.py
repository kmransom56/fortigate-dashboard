import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import glob

SVG_OUT = os.path.join(os.path.dirname(__file__), "..", "app", "static", "icons", "fortinet", "svg")


def which(cmd):
    return shutil.which(cmd) is not None


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def convert_with_soffice(vss_path, out_dir):
    cmd = ["soffice", "--headless", "--convert-to", "svg", vss_path, "--outdir", out_dir]
    subprocess.check_call(cmd)


def convert_with_unoconv(vss_path, out_dir):
    cmd = ["unoconv", "-f", "svg", "-o", out_dir, vss_path]
    subprocess.check_call(cmd)


def pick_and_rename_exports(tmp_dir, dest_dir):
    ensure_dir(dest_dir)
    exported = glob.glob(os.path.join(tmp_dir, "*.svg"))
    if not exported:
        return 0
    name_map = {
        "fortigate": ["fortigate", "fg", "firewall", "fortios"],
        "fortiswitch": ["fortiswitch", "switch"],
        "fortiap": ["fortiap", "ap", "wireless", "wifi"],
        "endpoint_desktop": ["desktop", "pc", "workstation"],
        "endpoint_laptop": ["laptop", "notebook"],
        "server_cloud": ["cloud", "server"],
    }
    copied = 0
    for src in exported:
        base = os.path.basename(src).lower()
        matched_key = None
        for key, clues in name_map.items():
            for clue in clues:
                if clue in base:
                    matched_key = key
                    break
            if matched_key:
                break
        if matched_key:
            dst = os.path.join(dest_dir, f"{matched_key}.svg")
            try:
                shutil.copyfile(src, dst)
                copied += 1
            except Exception:
                pass
    return copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+")
    parser.add_argument("--out", default=SVG_OUT)
    args = parser.parse_args()

    ensure_dir(args.out)

    any_success = False
    for in_path in args.input:
        if not os.path.exists(in_path):
            print(f"missing: {in_path}", file=sys.stderr)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                if which("soffice"):
                    convert_with_soffice(in_path, tmp)
                elif which("unoconv"):
                    convert_with_unoconv(in_path, tmp)
                else:
                    print("no converter available (install libreoffice or unoconv)", file=sys.stderr)
                    continue
                copied = pick_and_rename_exports(tmp, args.out)
                if copied > 0:
                    print(f"exported {copied} svg(s) from {in_path} into {args.out}")
                    any_success = True
                else:
                    print(f"no recognizable shapes exported from {in_path}", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(f"conversion failed for {in_path}: {e}", file=sys.stderr)

    if not any_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
