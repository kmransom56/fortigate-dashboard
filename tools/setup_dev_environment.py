#!/usr/bin/env python3
"""
FortiGate Dashboard Development Environment Setup
Automated setup and configuration for development workflow
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import requests
import time

def run_command(command, check=True, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Check if virtual environment exists
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        success, stdout, stderr = run_command(f"{sys.executable} -m venv .venv")
        if not success:
            print(f"❌ Failed to create virtual environment: {stderr}")
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_path = ".venv\\Scripts\\pip.exe"
        python_path = ".venv\\Scripts\\python.exe"
    else:  # Unix/Linux
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    # Upgrade pip first
    print("⬆️  Upgrading pip...")
    run_command(f"{pip_path} install --upgrade pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        print("📋 Installing from requirements.txt...")
        success, stdout, stderr = run_command(f"{pip_path} install -r requirements.txt")
        if not success:
            print(f"❌ Failed to install requirements: {stderr}")
            return False
    
    # Install development dependencies
    dev_deps = [
        "watchdog",      # For file watching
        "pytest",        # For testing
        "pytest-json-report",  # For test reporting
        "black",         # Code formatting
        "flake8",        # Linting
        "requests",      # HTTP requests
        "python-dotenv", # Environment variables
    ]
    
    print("🔧 Installing development dependencies...")
    for dep in dev_deps:
        print(f"   Installing {dep}...")
        success, stdout, stderr = run_command(f"{pip_path} install {dep}")
        if not success:
            print(f"⚠️  Warning: Failed to install {dep}: {stderr}")
    
    print("✅ Dependencies installed successfully!")
    return True

def setup_git_hooks():
    """Setup Git hooks for automated workflows"""
    print("🪝 Setting up Git hooks...")
    
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("❌ Git repository not found")
        return False
    
    # Make pre-commit hook executable
    pre_commit_hook = hooks_dir / "pre-commit"
    if pre_commit_hook.exists():
        if os.name != 'nt':  # Unix/Linux
            os.chmod(pre_commit_hook, 0o755)
        print("✅ Pre-commit hook configured")
    
    return True

def create_directories():
    """Create necessary directories for the development environment"""
    print("📁 Creating directory structure...")
    
    directories = [
        "automation/logs",
        "automation/logs/api_requests",
        "automation/api_exports",
        "C:/users/south/backups/fortigate-dashboard",
        "tests",
        "docs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    print("✅ Directory structure created!")
    return True

def setup_environment_file():
    """Setup .env file with default values"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("🔧 Creating .env file template...")
    
    env_template = """# FortiGate API Configuration
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_API_TOKEN=your-api-token-here

# Path to FortiGate SSL Certificate
FORTIGATE_CERT_PATH=/app/certs/fortigate.pem

# Logging Configuration
LOG_LEVEL=DEBUG

# Development Configuration
DEVELOPMENT_MODE=true
DEBUG_API_CALLS=true

# FortiSwitch Configuration (optional)
FORTISWITCH_HOST=10.255.1.2
FORTISWITCH_USERNAME=admin
FORTISWITCH_PASSWORD=your-password-here

# Power Automate Integration
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/your-webhook-url
NOTIFICATION_EMAIL=your-email@domain.com

# Backup Configuration
BACKUP_RETENTION_DAYS=30
MAX_BACKUPS=10
"""
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print("✅ .env file created with template values")
    print("⚠️  Please update the values in .env with your actual configuration")
    return True

def test_fortigate_connection():
    """Test connection to FortiGate API"""
    print("🔗 Testing FortiGate API connection...")
    
    try:
        from fortigate_dev_helper import FortiGateDevAPI
        
        api = FortiGateDevAPI()
        result = api.test_connection()
        
        if result['success']:
            print("✅ FortiGate API connection successful!")
            print(f"   Host: {result['host']}")
            print(f"   Response time: {result['response_time']}ms")
            if result['system_info']:
                print(f"   Hostname: {result['system_info'].get('hostname', 'Unknown')}")
                print(f"   Version: {result['system_info'].get('version', 'Unknown')}")
        else:
            print(f"❌ FortiGate API connection failed: {result['error']}")
            print("💡 Check your FORTIGATE_HOST and FORTIGATE_API_TOKEN in .env file")
            return False
    except ImportError:
        print("⚠️  FortiGate dev helper not available, skipping connection test")
    except Exception as e:
        print(f"❌ Error testing connection: {str(e)}")
        return False
    
    return True

def create_test_files():
    """Create basic test files"""
    print("🧪 Creating test files...")
    
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    
    # Create __init__.py
    (tests_dir / "__init__.py").touch()
    
    # Create basic test file
    test_content = '''"""
Basic tests for FortiGate Dashboard
"""

import pytest
import os
from pathlib import Path

def test_environment_variables():
    """Test that required environment variables are set"""
    assert os.getenv('FORTIGATE_HOST'), "FORTIGATE_HOST not set"
    assert os.getenv('FORTIGATE_API_TOKEN'), "FORTIGATE_API_TOKEN not set"

def test_project_structure():
    """Test that required files and directories exist"""
    assert Path("app/main.py").exists(), "Main application file not found"
    assert Path("requirements.txt").exists(), "Requirements file not found"
    assert Path(".env").exists(), "Environment file not found"

def test_fortigate_connection():
    """Test FortiGate API connection"""
    try:
        from fortigate_dev_helper import FortiGateDevAPI
        api = FortiGateDevAPI()
        result = api.test_connection()
        assert result['success'], f"Connection failed: {result['error']}"
    except ImportError:
        pytest.skip("FortiGate dev helper not available")

@pytest.mark.parametrize("endpoint", [
    "system_status",
    "system_interface", 
    "dhcp_leases"
])
def test_api_endpoints(endpoint):
    """Test common API endpoints"""
    try:
        from fortigate_dev_helper import FortiGateDevAPI
        api = FortiGateDevAPI()
        result = api.make_request(api.endpoints[endpoint])
        assert result['status_code'] == 200, f"Endpoint {endpoint} failed"
    except ImportError:
        pytest.skip("FortiGate dev helper not available")
'''
    
    with open(tests_dir / "test_basic.py", 'w') as f:
        f.write(test_content)
    
    print("✅ Test files created!")
    return True

def create_development_scripts():
    """Create additional development convenience scripts"""
    print("🔧 Creating development scripts...")
    
    # Create run_tests.bat
    test_script = '''@echo off
echo Running FortiGate Dashboard Tests
echo ================================

if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
)

python -m pytest tests/ -v --tb=short --json-report --json-report-file=test_results.json

echo.
echo Test results saved to test_results.json
pause
'''
    
    with open("run_tests.bat", 'w') as f:
        f.write(test_script)
    
    # Create format_code.bat
    format_script = '''@echo off
echo Formatting Python Code
echo ======================

if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
)

echo Running Black formatter...
python -m black app/ tests/ *.py

echo Running Flake8 linter...
python -m flake8 app/ tests/ *.py --max-line-length=88 --ignore=E203,W503

echo.
echo Code formatting complete!
pause
'''
    
    with open("format_code.bat", 'w') as f:
        f.write(format_script)
    
    # Create quick_deploy.bat
    deploy_script = '''@echo off
echo Quick Deploy to Production
echo ==========================

echo Creating backup...
powershell.exe -ExecutionPolicy Bypass -File "C:\\users\\south\\Scripts\\backup_fortigate_dashboard.ps1"

echo Running tests...
if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
)
python -m pytest tests/ --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo Tests failed! Deployment aborted.
    pause
    exit /b 1
)

echo Deploying to production...
robocopy "." "G:\\My Drive\\home\\keith\\fortigate-dashboard" /E /XO /XD __pycache__ .git .venv venv node_modules

echo Deployment complete!
pause
'''
    
    with open("quick_deploy.bat", 'w') as f:
        f.write(deploy_script)
    
    print("✅ Development scripts created!")
    return True

def main():
    """Main setup function"""
    print("🚀 FortiGate Dashboard Development Environment Setup")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ This doesn't appear to be the FortiGate Dashboard project directory")
        print("   Please run this script from the project root directory")
        return 1
    
    setup_steps = [
        ("Creating directories", create_directories),
        ("Setting up environment file", setup_environment_file),
        ("Installing dependencies", install_dependencies),
        ("Setting up Git hooks", setup_git_hooks),
        ("Creating test files", create_test_files),
        ("Creating development scripts", create_development_scripts),
        ("Testing FortiGate connection", test_fortigate_connection),
    ]
    
    success_count = 0
    for step_name, step_function in setup_steps:
        print(f"🔄 {step_name}...")
        try:
            if step_function():
                success_count += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {str(e)}")
        print()
    
    print("=" * 60)
    print(f"🎉 Setup completed! {success_count}/{len(setup_steps)} steps successful")
    print()
    
    if success_count == len(setup_steps):
        print("🎯 Your development environment is ready!")
        print()
        print("Next steps:")
        print("1. Update the .env file with your FortiGate credentials")
        print("2. Run 'start_dev_watch.bat' to start the development server")
        print("3. Run 'run_tests.bat' to execute the test suite")
        print("4. Use the automation scripts in the automation/ directory")
        print()
        print("Available commands:")
        print("  start_dev_watch.bat     - Start development server with file watching")
        print("  run_tests.bat          - Run the test suite")
        print("  format_code.bat        - Format and lint code")
        print("  quick_deploy.bat       - Quick deployment to production")
        print()
        print("Automation scripts:")
        print("  C:\\users\\south\\Scripts\\backup_fortigate_dashboard.ps1")
        print("  automation\\power_automate_integration.ps1")
        print("  automation\\webhook_listener.ps1")
        
        return 0
    else:
        print("⚠️  Some setup steps failed. Please check the error messages above.")
        print("   You may need to manually complete the failed steps.")
        return 1

if __name__ == '__main__':
    exit(main())
