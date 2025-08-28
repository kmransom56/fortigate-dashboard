import os
import sys
import subprocess
import shutil
import urllib.request
import time

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
        try:
            with urllib.request.urlopen(url) as resp, open(dst, "wb") as f:
                f.write(resp.read())
            print(f"saved {dst}")
        except Exception as e:
            print(f"download failed {url}: {e}", file=sys.stderr)

def has_rsvg():
    return shutil.which("rsvg-convert") is not None

def convert_file_rsvg(svg_path, png_path, size=256):
    subprocess.check_call(["rsvg-convert", "-w", str(size), "-h", str(size), svg_path, "-o", png_path])

def convert_file_pillow(svg_path, png_path, size=256):
    from PIL import Image  # noqa
    try:
        import cairosvg  # type: ignore
    except Exception:
        print("cairosvg not available; cannot convert SVGs without rsvg-convert", file=sys.stderr)
        raise
    cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=size, output_height=size)  # type: ignore

def needs_convert(svg_path, png_path):
    if not os.path.exists(png_path):
        return True
    try:
        return os.path.getmtime(svg_path) > os.path.getmtime(png_path)
    except Exception:
        return True

def convert_directory():
    svgs = [f for f in os.listdir(SVG_DIR) if f.lower().endswith(".svg")]
    if not svgs:
        print("no svg files found to convert")
        return
    use_rsvg = has_rsvg()
    for name in svgs:
        svg = os.path.join(SVG_DIR, name)
        base = os.path.splitext(os.path.basename(name))[0]
        png = os.path.join(PNG_DIR, f"{base}.png")
        if not needs_convert(svg, png):
            continue
        try:
            if use_rsvg:
                convert_file_rsvg(svg, png, 256)
            else:
                convert_file_pillow(svg, png, 256)
            print(f"converted {png}")
            time.sleep(0.02)
        except Exception as e:
            print(f"convert failed {svg}: {e}", file=sys.stderr)

def main():
    ensure_dirs()
    download_svgs()
    convert_directory()

if __name__ == "__main__":
    main()
