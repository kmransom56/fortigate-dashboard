#!/usr/bin/env python3
"""
Super simple Flask test - just to verify Flask works
"""
try:
    print("🔍 Testing Flask installation...")
    import flask
    print(f"✅ Flask imported successfully, version: {flask.__version__}")
    
    print("🔍 Creating Flask app...")
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "🎉 Flask is working! Your Network MCP Server environment is ready."
    
    @app.route('/test')
    def test():
        return jsonify({"status": "success", "message": "Flask server is functional"})
    
    print("✅ Flask app created successfully")
    print("🚀 Starting server on http://localhost:5000")
    print("   Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install flask flask-cors")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("Check your Python environment")
