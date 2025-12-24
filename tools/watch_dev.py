#!/usr/bin/env python3
"""
Development file watcher for FortiGate Dashboard
Monitors Python, HTML, CSS, JS files and automatically restarts the FastAPI server
"""

import time
import subprocess
import sys
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FortiGateDashboardHandler(FileSystemEventHandler):
    def __init__(self, command, restart_delay=2):
        self.command = command
        self.process = None
        self.restart_delay = restart_delay
        self.last_restart = 0
        self.start_server()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Monitor specific file types
        file_extensions = {".py", ".html", ".css", ".js", ".json", ".env"}
        file_path = Path(event.src_path)

        if file_path.suffix.lower() in file_extensions:
            # Avoid rapid restarts
            current_time = time.time()
            if current_time - self.last_restart > self.restart_delay:
                print(f"📝 File changed: {file_path.name}")
                self.restart_server()
                self.last_restart = current_time

    def start_server(self):
        print("🚀 Starting FortiGate Dashboard server...")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())

        self.process = subprocess.Popen(
            self.command, shell=True, env=env, cwd=str(Path.cwd())
        )
        print(f"✅ Server started with PID: {self.process.pid}")

    def restart_server(self):
        if self.process:
            print("🔄 Restarting server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("⚠️  Force killed server process")

        self.start_server()

    def stop_server(self):
        if self.process:
            print("🛑 Stopping server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def main():
    # Command to start your FastAPI server
    command = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

    print("🔍 FortiGate Dashboard Development Watcher")
    print("=" * 50)
    print(f"📂 Watching: {Path.cwd()}")
    print(f"🖥️  Command: {command}")
    print("📝 Monitoring: .py, .html, .css, .js, .json, .env files")
    print("⌨️  Press Ctrl+C to stop")
    print("=" * 50)

    handler = FortiGateDashboardHandler(command)
    observer = Observer()

    # Watch the entire project directory recursively
    observer.schedule(handler, path=".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down watcher...")
        observer.stop()
        handler.stop_server()
        print("✅ Cleanup complete")

    observer.join()


if __name__ == "__main__":
    # Install watchdog if not present
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Installing watchdog dependency...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

    main()
