#!/usr/bin/env python3
"""
Project Integration Setup Script
Automatically sets up and validates integration with existing Fortinet projects
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

class ProjectIntegrator:
    """
    Manages integration setup for all existing Fortinet projects
    """
    
    def __init__(self):
        self.base_path = Path.home()
        self.mcp_path = Path(__file__).parent
        self.projects = {
            'fortigatevlans': {
                'path': self.base_path / 'fortigatevlans',
                'description': 'VLAN management and configuration',
                'key_files': ['vlancollector.py', 'database_helper.py'],
                'integration_status': 'not_checked'
            },
            'fortigate-troubleshooter': {
                'path': self.base_path / 'fortigate-troubleshooter',
                'description': 'Device diagnostics and troubleshooting',
                'key_files': ['src/fortigate-webapp.py', 'src/fortigateconnectivity.py'],
                'integration_status': 'not_checked'
            },
            'addfortiap': {
                'path': self.base_path / 'addfortiap',
                'description': 'FortiAP deployment and wireless management',
                'key_files': ['add_fortiaps.py', 'fortiap_mcp.py'],
                'integration_status': 'not_checked'
            },
            'fortimanagerdashboard': {
                'path': self.base_path / 'fortimanagerdashboard',
                'description': 'Advanced dashboard features and SSL management',
                'key_files': ['fortimanager_api_server.py', 'ssl_certificate_handler.py'],
                'integration_status': 'not_checked'
            },
            'Utilities': {
                'path': self.base_path / 'Utilities',
                'description': 'Network utilities and diagnostic tools',
                'key_files': ['device_discovery_tool_enhanced.py', 'snmp_checker.py'],
                'integration_status': 'not_checked'
            }
        }
        
    def run_complete_integration_setup(self):
        """
        Run complete integration setup for all projects
        """
        print("🚀 Network Device MCP Server - Project Integration Setup")
        print("=" * 70)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Analyze existing projects
        print("📊 Step 1: Analyzing existing projects...")
        project_analysis = self.analyze_all_projects()
        
        # Step 2: Validate integration modules
        print("\n🔧 Step 2: Validating integration modules...")
        integration_status = self.validate_integration_modules()
        
        # Step 3: Test API endpoints
        print("\n🌐 Step 3: Testing unified API endpoints...")
        api_status = self.test_api_endpoints()
        
        # Step 4: Generate integration report
        print("\n📋 Step 4: Generating integration report...")
        report = self.generate_integration_report(project_analysis, integration_status, api_status)
        
        # Step 5: Save configuration
        print("\n💾 Step 5: Saving integration configuration...")
        self.save_integration_config(report)
        
        print("\n" + "=" * 70)
        print("✅ Project Integration Setup Complete!")
        print("=" * 70)
        
        return report
    
    def analyze_all_projects(self):
        """
        Analyze all existing projects for integration readiness
        """
        analysis_results = {}
        
        for project_name, project_info in self.projects.items():
            print(f"   📂 Analyzing {project_name}...")
            analysis = self.analyze_project(project_name, project_info)
            analysis_results[project_name] = analysis
            
            status = "✅ Ready" if analysis['ready'] else "⚠️ Issues found"
            print(f"      {status} - {analysis['file_count']} files, {analysis['ready_files']} ready")
        
        return analysis_results
    
    def analyze_project(self, project_name, project_info):
        """
        Analyze a specific project for integration readiness
        """
        project_path = project_info['path']
        key_files = project_info['key_files']
        
        analysis = {
            'name': project_name,
            'path': str(project_path),
            'exists': project_path.exists(),
            'file_count': 0,
            'ready_files': 0,
            'key_files_status': {},
            'python_files': [],
            'ready': False
        }
        
        if not project_path.exists():
            analysis['error'] = f"Project directory not found: {project_path}"
            return analysis
        
        # Count all Python files
        try:
            python_files = list(project_path.rglob("*.py"))
            analysis['python_files'] = [str(f.relative_to(project_path)) for f in python_files]
            analysis['file_count'] = len(python_files)
        except Exception as e:
            analysis['error'] = f"Failed to scan directory: {e}"
            return analysis
        
        # Check key files
        for key_file in key_files:
            key_file_path = project_path / key_file
            file_exists = key_file_path.exists()
            analysis['key_files_status'][key_file] = {
                'exists': file_exists,
                'path': str(key_file_path),
                'size': key_file_path.stat().st_size if file_exists else 0
            }
            if file_exists:
                analysis['ready_files'] += 1
        
        # Project is ready if at least 50% of key files exist
        analysis['ready'] = (analysis['ready_files'] / len(key_files)) >= 0.5
        
        return analysis
    
    def validate_integration_modules(self):
        """
        Validate that integration modules are properly set up
        """
        integrations_path = self.mcp_path / "src" / "integrations"
        modules = ['vlan_manager', 'troubleshooter', 'ap_manager', 'utilities', 'dashboard_merger']
        
        validation_results = {
            'integrations_path_exists': integrations_path.exists(),
            'modules': {}
        }
        
        for module in modules:
            module_file = integrations_path / f"{module}.py"
            validation_results['modules'][module] = {
                'exists': module_file.exists(),
                'size': module_file.stat().st_size if module_file.exists() else 0,
                'importable': False
            }
            
            # Test import
            try:
                if module_file.exists():
                    # Add to path temporarily
                    sys.path.insert(0, str(integrations_path))
                    __import__(module)
                    validation_results['modules'][module]['importable'] = True
                    print(f"      ✅ {module} - importable")
                else:
                    print(f"      ❌ {module} - file missing")
            except ImportError as e:
                validation_results['modules'][module]['import_error'] = str(e)
                print(f"      ⚠️  {module} - import issues: {e}")
            except Exception as e:
                validation_results['modules'][module]['error'] = str(e)
                print(f"      ❌ {module} - error: {e}")
            finally:
                # Clean up path
                if str(integrations_path) in sys.path:
                    sys.path.remove(str(integrations_path))
        
        return validation_results
    
    def test_api_endpoints(self):
        """
        Test that the unified API endpoints are available
        """
        # Check if REST API server has the integration endpoints
        rest_api_file = self.mcp_path / "rest_api_server.py"
        
        api_status = {
            'rest_api_exists': rest_api_file.exists(),
            'integration_endpoints': 0,
            'endpoint_categories': {
                'vlans': 0,
                'troubleshoot': 0,
                'fortiaps': 0,
                'utilities': 0,
                'dashboard': 0
            }
        }
        
        if rest_api_file.exists():
            try:
                with open(rest_api_file, 'r') as f:
                    content = f.read()
                
                # Count integration endpoints
                for category in api_status['endpoint_categories']:
                    count = content.count(f'/api/{category}')
                    api_status['endpoint_categories'][category] = count
                    api_status['integration_endpoints'] += count
                
                # Check for integration availability check
                api_status['has_integration_check'] = 'INTEGRATIONS_AVAILABLE' in content
                
                print(f"      📊 Found {api_status['integration_endpoints']} integration endpoints")
                for category, count in api_status['endpoint_categories'].items():
                    if count > 0:
                        print(f"         • {category}: {count} endpoints")
                
            except Exception as e:
                api_status['error'] = str(e)
        
        return api_status
    
    def generate_integration_report(self, project_analysis, integration_status, api_status):
        """
        Generate comprehensive integration report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'integration_summary': {
                'total_projects': len(self.projects),
                'projects_ready': len([p for p in project_analysis.values() if p.get('ready', False)]),
                'integration_modules_ready': len([m for m in integration_status['modules'].values() if m.get('importable', False)]),
                'api_endpoints_available': api_status.get('integration_endpoints', 0)
            },
            'project_analysis': project_analysis,
            'integration_status': integration_status,
            'api_status': api_status,
            'recommendations': self.generate_recommendations(project_analysis, integration_status, api_status)
        }
        
        # Print summary
        summary = report['integration_summary']
        print(f"      📊 Integration Summary:")
        print(f"         • Projects: {summary['projects_ready']}/{summary['total_projects']} ready")
        print(f"         • Modules: {summary['integration_modules_ready']}/5 working")
        print(f"         • API Endpoints: {summary['api_endpoints_available']} available")
        
        return report
    
    def generate_recommendations(self, project_analysis, integration_status, api_status):
        """
        Generate recommendations based on analysis results
        """
        recommendations = []
        
        # Project recommendations
        for project_name, analysis in project_analysis.items():
            if not analysis.get('ready', False):
                if not analysis.get('exists', False):
                    recommendations.append(f"Create or locate {project_name} project directory")
                else:
                    missing_files = [f for f, status in analysis['key_files_status'].items() if not status['exists']]
                    if missing_files:
                        recommendations.append(f"Restore missing files in {project_name}: {', '.join(missing_files)}")
        
        # Integration module recommendations
        for module, status in integration_status.get('modules', {}).items():
            if not status.get('importable', False):
                if not status.get('exists', False):
                    recommendations.append(f"Create integration module: {module}.py")
                else:
                    recommendations.append(f"Fix import issues in integration module: {module}.py")
        
        # API recommendations
        if api_status.get('integration_endpoints', 0) == 0:
            recommendations.append("Add integration endpoints to REST API server")
        
        # Success recommendations
        if not recommendations:
            recommendations.extend([
                "All projects are ready for integration",
                "Start the unified web dashboard: python rest_api_server.py",
                "Access the integrated platform at: http://localhost:5000",
                "Share with team: http://[YOUR-IP]:5000 (after firewall setup)"
            ])
        
        return recommendations
    
    def save_integration_config(self, report):
        """
        Save integration configuration for future reference
        """
        config_file = self.mcp_path / "integration_config.json"
        
        config = {
            'last_setup': report['timestamp'],
            'projects': {name: str(info['path']) for name, info in self.projects.items()},
            'integration_status': report['integration_summary'],
            'recommendations': report['recommendations']
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"      💾 Configuration saved to: {config_file}")
        except Exception as e:
            print(f"      ❌ Failed to save configuration: {e}")
    
    def create_integration_shortcuts(self):
        """
        Create shortcuts for easy integration management
        """
        shortcuts = [
            ("test-integration.bat", self.create_windows_test_script()),
            ("test-integration.sh", self.create_linux_test_script()),
            ("integration-status.py", self.create_status_script())
        ]
        
        for filename, content in shortcuts:
            shortcut_path = self.mcp_path / filename
            try:
                with open(shortcut_path, 'w') as f:
                    f.write(content)
                print(f"      📋 Created shortcut: {filename}")
            except Exception as e:
                print(f"      ❌ Failed to create {filename}: {e}")
    
    def create_windows_test_script(self):
        """Create Windows batch script for testing integration"""
        return '''@echo off
echo 🧪 Testing Project Integration...
echo ================================
python setup-project-integration.py
echo.
echo 🌐 Starting web dashboard for testing...
python rest_api_server.py
pause
'''
    
    def create_linux_test_script(self):
        """Create Linux shell script for testing integration"""
        return '''#!/bin/bash
echo "🧪 Testing Project Integration..."
echo "================================"
python3 setup-project-integration.py
echo
echo "🌐 Starting web dashboard for testing..."
python3 rest_api_server.py
'''
    
    def create_status_script(self):
        """Create Python script for checking integration status"""
        return '''#!/usr/bin/env python3
"""Quick integration status check"""
from setup_project_integration import ProjectIntegrator

integrator = ProjectIntegrator()
report = integrator.run_complete_integration_setup()

print("\\n🎯 Quick Status:")
summary = report['integration_summary']
print(f"Projects Ready: {summary['projects_ready']}/{summary['total_projects']}")
print(f"Modules Working: {summary['integration_modules_ready']}/5")
print(f"API Endpoints: {summary['api_endpoints_available']}")

if report['recommendations']:
    print("\\n📋 Next Steps:")
    for i, rec in enumerate(report['recommendations'][:5], 1):
        print(f"{i}. {rec}")
'''

def main():
    """
    Main integration setup function
    """
    print("🔧 Network Device MCP Server - Project Integration Setup")
    print("=" * 60)
    
    integrator = ProjectIntegrator()
    
    try:
        # Run complete integration setup
        report = integrator.run_complete_integration_setup()
        
        # Create shortcuts
        print("\n📋 Creating integration shortcuts...")
        integrator.create_integration_shortcuts()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 Integration Setup Complete!")
        print("=" * 60)
        
        print("\n🚀 Next Steps:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\n📄 Full report saved to: integration_config.json")
        print("🌐 Start dashboard: python rest_api_server.py")
        print("📊 Check status anytime: python integration-status.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)