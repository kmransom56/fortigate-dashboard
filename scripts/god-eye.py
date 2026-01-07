import os
import requests
import sqlite3
import subprocess
from termcolor import colored

def check_service(name, url):
    try:
        response = requests.get(url, timeout=2)
        status = colored("ONLINE", "green") if response.status_code == 200 else colored(f"ERROR {response.status_code}", "yellow")
        print(f"[*] Service {name:20}: {status}")
        return response.status_code == 200
    except Exception:
        print(f"[*] Service {name:20}: " + colored("OFFLINE", "red"))
        return False

def check_icons_db():
    db_path = "app/utils/icons.db"
    if not os.path.exists(db_path):
        print(f"[*] Icons DB {db_path:17}: " + colored("MISSING", "red"))
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM icons")
        count = cursor.fetchone()[0]
        print(f"[*] Icons Library {db_path:12}: " + colored(f"HEALTHY ({count} icons)", "green"))
        return True
    except Exception as e:
        print(f"[*] Icons Library {db_path:12}: " + colored(f"CORRUPT ({str(e)})", "red"))
        return False

def verify_site_zero():
    try:
        response = requests.get("http://localhost:8001/api/v1/local/topology_data", timeout=2)
        data = response.json()
        devices = {d['name']: d['icon'] for d in data.get('devices', [])}
        
        critical_devices = ["LGwebOSTV", "KEITH-s-Tab-S10-FE", "CASERVER"]
        results = []
        for cd in critical_devices:
            if cd in devices:
                results.append(colored(f"{cd} (OK)", "green"))
            else:
                results.append(colored(f"{cd} (MISSING)", "red"))
        
        print(f"[*] Site 0 Readiness      : " + ", ".join(results))
    except Exception:
        print(f"[*] Site 0 Readiness      : " + colored("API UNREACHABLE", "red"))

if __name__ == "__main__":
    print(colored("\n=== FORTIGATE DASHBOARD COMMAND CENTER ===", "blue", attrs=["bold"]))
    check_service("Dashboard (Direct)", "http://localhost:8001")
    check_service("Icon Library", "http://localhost:8001/icons")
    check_icons_db()
    verify_site_zero()

    print("\n" + colored("--- RUNNING E2E SMOKE TESTS ---", "cyan"))
    subprocess.run(["npx", "playwright", "test", "--reporter=line"])
    print(colored("\n=== SYSTEM FOCUS COMPLETE ===", "blue", attrs=["bold"]))
