#!/usr/bin/env python3
"""
Simple FastAPI server for the web dashboard
Serves static files and provides API endpoints for the dashboard
"""
import json
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI(title="Network Device Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Sample data for dashboard (this would normally come from your FortiManager integration)
SAMPLE_DATA = {
    "brands": [
        {"name": "BWW", "device_count": 678, "healthy_count": 678, "status": "healthy"},
        {"name": "ARBYS", "device_count": 1057, "healthy_count": 1057, "status": "healthy"},
        {"name": "SONIC", "device_count": 3454, "healthy_count": 3454, "status": "healthy"}
    ],
    "fortimanager": [
        {"name": "BWW-FM", "device_count": 678, "status": "online"},
        {"name": "ARBYS-FM", "device_count": 1057, "status": "online"},
        {"name": "SONIC-FM", "device_count": 3454, "status": "online"}
    ]
}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard page"""
    dashboard_file = Path("web/dashboard.html")
    if dashboard_file.exists():
        return FileResponse("web/dashboard.html")
    else:
        # Fallback HTML if dashboard.html doesn't exist
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Device Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-number { font-size: 2em; font-weight: bold; color: #2c5aa0; }
                .stat-label { color: #666; margin-top: 5px; }
                .brand-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .brand-name { font-weight: bold; color: #2c5aa0; font-size: 1.2em; }
                .device-count { color: #666; margin-top: 5px; }
                .status-healthy { color: #28a745; }
                .loading { text-align: center; padding: 40px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌐 Network Device Dashboard</h1>
                    <p>Monitor and manage your network infrastructure across all brands</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-devices">Loading...</div>
                        <div class="stat-label">Total Devices</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number status-healthy" id="healthy-devices">Loading...</div>
                        <div class="stat-label">Healthy Devices</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-brands">3</div>
                        <div class="stat-label">Brands</div>
                    </div>
                </div>
                
                <div class="stats-grid" id="brand-cards">
                    <div class="loading">Loading brand information...</div>
                </div>
            </div>
            
            <script>
                async function loadDashboard() {
                    try {
                        const response = await fetch('/api/overview');
                        const data = await response.json();
                        
                        document.getElementById('total-devices').textContent = data.total_devices;
                        document.getElementById('healthy-devices').textContent = data.healthy_devices;
                        
                        const brandCardsContainer = document.getElementById('brand-cards');
                        brandCardsContainer.innerHTML = '';
                        
                        data.brands.forEach(brand => {
                            const card = document.createElement('div');
                            card.className = 'brand-card';
                            card.innerHTML = `
                                <div class="brand-name">${brand.name}</div>
                                <div class="device-count">${brand.device_count} devices</div>
                                <div class="status-healthy">✓ ${brand.healthy_count} healthy</div>
                            `;
                            brandCardsContainer.appendChild(card);
                        });
                    } catch (error) {
                        console.error('Error loading dashboard:', error);
                        document.getElementById('brand-cards').innerHTML = '<div class="loading">Error loading data</div>';
                    }
                }
                
                loadDashboard();
                setInterval(loadDashboard, 30000); // Refresh every 30 seconds
            </script>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "web-dashboard"}

@app.get("/api/brands")
async def get_brands():
    """Get brand information"""
    return SAMPLE_DATA["brands"]

@app.get("/api/fortimanager")
async def get_fortimanager():
    """Get FortiManager information"""
    return SAMPLE_DATA["fortimanager"]

@app.get("/api/overview")
async def get_overview():
    """Get dashboard overview data"""
    total_devices = sum(brand["device_count"] for brand in SAMPLE_DATA["brands"])
    healthy_devices = sum(brand["healthy_count"] for brand in SAMPLE_DATA["brands"])
    
    return {
        "total_devices": total_devices,
        "healthy_devices": healthy_devices,
        "brands": SAMPLE_DATA["brands"],
        "fortimanager_instances": SAMPLE_DATA["fortimanager"]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Network Device Dashboard on http://localhost:12000")
    uvicorn.run(app, host="0.0.0.0", port=12000)