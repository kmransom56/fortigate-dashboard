#!/usr/bin/env python3
"""
Minimal test server to verify Flask is working
"""
from flask import Flask, jsonify
import sys
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "✅ TEST SERVER WORKING!",
        "message": "Network MCP Server environment is functional",
        "python_version": sys.version,
        "working_directory": os.getcwd()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "Test Server"})

if __name__ == '__main__':
    print("🧪 Starting minimal test server...")
    print("🌐 Access at: http://localhost:5000")
    print("🔧 Health check: http://localhost:5000/health")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")
