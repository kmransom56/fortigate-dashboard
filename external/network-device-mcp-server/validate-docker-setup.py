#!/usr/bin/env python3
"""
Docker Setup Validation Script
Checks if all Docker files are properly configured
"""
import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

def check_docker_setup():
    """Validate the Docker setup"""
    print("🔍 Validating Docker Setup...")
    print("=" * 50)
    
    all_good = True
    
    # Check Docker Compose files
    all_good &= check_file_exists("docker-compose.production.yml", "Production Docker Compose")
    
    # Check Dockerfiles
    all_good &= check_file_exists("Dockerfile.fastapi", "FastAPI Dockerfile")
    all_good &= check_file_exists("Dockerfile.web", "Web Dashboard Dockerfile")
    all_good &= check_file_exists("Dockerfile.mcp", "MCP Server Dockerfile")
    
    # Check startup scripts
    all_good &= check_file_exists("ONE-CLICK-START.bat", "Windows Startup Script")
    all_good &= check_file_exists("one-click-start.sh", "Unix Startup Script")
    all_good &= check_file_exists("STOP-DOCKER.bat", "Windows Stop Script")
    
    # Check supporting files
    all_good &= check_file_exists("docker/web_server.py", "Web Server Python File")
    all_good &= check_file_exists("DOCKER-README.md", "Docker Documentation")
    
    # Check application directories
    all_good &= check_file_exists("fastapi_app/", "FastAPI Application")
    all_good &= check_file_exists("web/", "Web Dashboard")
    all_good &= check_file_exists("config/", "Configuration Directory")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 SUCCESS: All Docker files are present!")
        print("\nYour coworkers can now:")
        print("1. Clone the repository")
        print("2. Install Docker Desktop")
        print("3. Run ONE-CLICK-START.bat (Windows) or one-click-start.sh (Mac/Linux)")
        print("4. Access the dashboard at http://localhost:12000")
        return True
    else:
        print("❌ ISSUES FOUND: Some Docker files are missing")
        print("Please create the missing files before distributing")
        return False

if __name__ == "__main__":
    success = check_docker_setup()
    sys.exit(0 if success else 1)