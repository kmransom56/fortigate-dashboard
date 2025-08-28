This folder contains vendor icons for the 3D topology.

- Place original SVGs under app/static/icons/fortinet/svg
- Generated PNGs (256x256) go under app/static/icons/fortinet/png

Use tools/scrape_fortinet_icons.py to fetch from https://icons.fortinet.com/ and convert to PNGs.
Requires either:
- rsvg-convert (librsvg2-bin), or
- Python packages: pillow and cairosvg
