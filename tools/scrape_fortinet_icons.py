import os
import sys
import subprocess
import shutil
import urllib.request

SVG_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "static", "icons", "fortinet", "svg")
PNG_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "static", "icons", "fortinet", "png")

ICON_SVGS = {
    "fortigate": "https://icons.fortinet.com/icons/Secure%20Networking/Products/FortiGate.svg",
    "fortiswitch": "https://icons.fortinet.com/icons/Secure%20Networking/Products/FortiSwitch.svg",
    "fortiap": "https://icons.fortinet.com/icons/Secure%20Networking/Products/FortiAP.svg",
    "endpoint_desktop": "https://icons.fortinet.com/icons/ZTNA/Technology/Desktop.svg",
    "endpoint_laptop": "https://icons.fortinet.com/icons/ZTNA/Technology/Laptop.svg",
    "server_cloud": "https://icons.fortinet.com/icons/Secure%20Networking/Technology/Cloud.svg",
}

def ensure_dirs():
    os.makedirs(SVG_DIR, exist_ok=True)
    os.makedirs(PNG_DIR, exist_ok=True)

def download_svgs():
    for name, url in ICON_SVGS.items():
        dst = os.path.join(SVG_DIR, f"{name}.svg")
        with urllib.request.urlopen(url) as resp, open(dst, "wb") as f:
            f.write(resp.read())
        print(f"saved {dst}")

def has_rsvg():
    return shutil.which("rsvg-convert") is not None

def convert_with_rsvg():
    for name in ICON_SVGS.keys():
        svg = os.path.join(SVG_DIR, f"{name}.svg")
        png = os.path.join(PNG_DIR, f"{name}.png")
        subprocess.check_call(["rsvg-convert", "-w", "256", "-h", "256", svg, "-o", png])
        print(f"converted {png}")

def convert_with_pillow():
    from PIL import Image  # noqa
    try:
        import cairosvg  # type: ignore
    except Exception:
        print("cairosvg not available; cannot convert SVGs without rsvg-convert", file=sys.stderr)
        sys.exit(2)
    for name in ICON_SVGS.keys():
        svg = os.path.join(SVG_DIR, f"{name}.svg")
        png = os.path.join(PNG_DIR, f"{name}.png")
        cairosvg.svg2png(url=svg, write_to=png, output_width=256, output_height=256)  # type: ignore
        print(f"converted {png}")

def main():
    ensure_dirs()
    download_svgs()
    if has_rsvg():
        convert_with_rsvg()
    else:
        try:
            convert_with_pillow()
        except Exception as e:
            print(f"conversion failed: {e}", file=sys.stderr)
            print("Install librsvg2-bin (rsvg-convert) or pip install cairosvg pillow", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
