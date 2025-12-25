#!/usr/bin/env python3
import os
import requests

print("Simple icon downloader test")

# Create downloads directory
download_dir = "downloaded_files"
os.makedirs(download_dir, exist_ok=True)
print(f"Using directory: {download_dir}")

# Test downloading a known icon
test_urls = [
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/fortinet.svg",
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/cisco.svg"
]

for url in test_urls:
    try:
        print(f"Downloading: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = os.path.basename(url)
            filepath = os.path.join(download_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ Saved: {filepath}")
        else:
            print(f"❌ Failed to download {url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

print("✅ Test complete")
