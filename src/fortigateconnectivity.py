# src/fortigateconnectivity.py

import os
import sys
import json
import redis
import paramiko
import tempfile
import shutil
import unittest
import requests
import logging
import threading
from flask import Flask, jsonify, render_template, request, Response
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Create a Flask app instance
app = Flask(__name__)

# Configuration
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

SESSION_PREFIX = 'ftg_session:'


# Helper functions for session storage
def save_session(session_id, troubleshooter):
    try:
        data = {
            "status_messages": troubleshooter.status_messages,
            "results": troubleshooter.results,
            "progress": troubleshooter.progress,
            "is_connected": troubleshooter.is_connected,
            "is_running": troubleshooter.is_running,
            "error": troubleshooter.error,
            "fortigate_version": getattr(troubleshooter, "fortigate_version", None),
            "completed_at": getattr(troubleshooter, "completed_at", None),
        }
        json_data = json.dumps(data, default=str)
        redis_client.set(SESSION_PREFIX + session_id, json_data)
    except Exception as e:
        app.logger.error(f"Error saving session to Redis: {str(e)}")


def load_session(session_id):
    try:
        data = redis_client.get(SESSION_PREFIX + session_id)
        if not data:
            app.logger.warning(f"No data found in Redis for session {session_id}")
            return None
        data = json.loads(data)
        t = type('DummyTroubleshooter', (), {})()
        t.status_messages = data.get('status_messages', [])
        t.results = data.get('results', {})
        t.progress = data.get('progress', 0)
        t.is_connected = data.get('is_connected', False)
        t.is_running = data.get('is_running', False)
        t.error = data.get('error', None)
        t.fortigate_version = data.get('fortigate_version', None)
        t.completed_at = data.get('completed_at', None)
        t.add_status = lambda self, message, level="info": self.status_messages.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": message,
                "level": level,
            }
        )
        return t
    except Exception as e:
        app.logger.error(f"Error loading session from Redis: {str(e)}")
        return None

# Define your routes
@app.route('/')
def index():
    return "Hello, World!"


@app.route("/switches")
def switches_page():
    return render_template("switches.html")


@app.route("/api/switches")
def proxy_api_switches():
    try:
        resp = requests.get("http://dashboard:10000/api/switches")
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get("Content-Type"),
        )
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.errorhandler(OSError)
def handle_socket_error(error):
    if "An operation was attempted on something that is not a socket" in str(error):
        app.logger.warning("Socket error during reload - this is normal during development")
        return "Server is reloading, please refresh the page", 503
    return str(error), 500

# Initialize logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "fortigate_troubleshooter.log")

handler = RotatingFileHandler(LOG_FILE, maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)


# Automated Testing Utilities
def create_app():
    # Return the Flask app instance for testing
    return app


class FlaskAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app().test_client()
        cls.ctx = app.app_context()
        cls.ctx.push()
        cls._log_dir = tempfile.mkdtemp()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()
        shutil.rmtree(cls._log_dir)

    def test_index_page(self):
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Hello, World!", resp.data)

    def test_switches_page(self):
        resp = self.app.get("/switches")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Switch", resp.data)

    def test_proxy_api_switches(self):
        resp = self.app.get("/api/switches")
        self.assertIn(resp.status_code, [200, 500])

    def test_proxy_api_refresh_vendor_cache(self):
        resp = self.app.get("/api/refresh-vendor-cache")
        self.assertIn(resp.status_code, [200, 500])

    def test_start_test_missing_store(self):
        resp = self.app.post("/start_test", data={})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"success", resp.data)


if __name__ == "__main__":
    unittest.main()
