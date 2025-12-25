import requests
import json
import textwrap
import sys
url="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/_data/simple-icons.json"
r=requests.get(url, timeout=10)
print(r.status_code)
print(r.text[:300])