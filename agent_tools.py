#!/usr/bin/env python3
"""
AutoGen Agent Tools for FortiGate API Documentation and Code Maintenance

This module provides tools that the teachable agent can use to:
1. Generate API documentation from fortigate_self_api_doc.py
2. Analyze code for errors
3. Fix code issues
4. Maintain documentation
"""

import os
import sys
import json
import subprocess
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def run_fortigate_doc_script(command: str, **kwargs) -> Dict[str, Any]:
    """
    Run fortigate_self_api_doc.py with specified command and arguments
    
    Args:
        command: Command to run (sync, query, export, etc.)
        **kwargs: Additional arguments for the command
    
    Returns:
        Dictionary with success status and output
    """
    try:
        script_path = Path(__file__).parent / "fortigate_self_api_doc.py"
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "output": ""
            }
        
        # Build command
        cmd = [sys.executable, str(script_path), command]
        
        # Add kwargs as command-line arguments
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif not isinstance(value, bool):
                    cmd.append(f"--{key.replace('_', '-')}")
                    cmd.append(str(value))
        
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=Path(__file__).parent
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 5 minutes",
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output": ""
        }


def generate_api_documentation(output_file: str = "docs/API_DOCUMENTATION.md") -> Dict[str, Any]:
    """
    Generate comprehensive API documentation using fortigate_self_api_doc.py
    
    Args:
        output_file: Path to output documentation file
    
    Returns:
        Dictionary with success status and documentation path
    """
    try:
        # First, sync the device inventory
        sync_result = run_fortigate_doc_script("sync")
        if not sync_result["success"]:
            logger.warning(f"Sync failed: {sync_result.get('stderr', 'Unknown error')}")
        
        # Export topology data
        export_result = run_fortigate_doc_script("export", output=output_file.replace(".md", ".json"))
        
        if not export_result["success"]:
            return {
                "success": False,
                "error": export_result.get("error", export_result.get("stderr", "Unknown error")),
                "output_file": None
            }
        
        # Read the exported JSON
        json_file = output_file.replace(".md", ".json")
        if not os.path.exists(json_file):
            return {
                "success": False,
                "error": f"Exported JSON file not found: {json_file}",
                "output_file": None
            }
        
        with open(json_file, 'r') as f:
            topology_data = json.load(f)
        
        # Generate Markdown documentation
        doc_path = Path(output_file)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(doc_path, 'w') as f:
            f.write("# FortiGate Device Inventory API Documentation\n\n")
            f.write(f"**Generated**: {topology_data.get('exported_at', 'Unknown')}\n")
            f.write(f"**FortiGate IP**: {topology_data.get('fortigate_ip', 'Unknown')}\n")
            f.write(f"**VDOM**: {topology_data.get('vdom', 'root')}\n\n")
            f.write(f"**Total Devices**: {topology_data.get('total_devices', 0)}\n")
            f.write(f"**Online Devices**: {topology_data.get('online_devices', 0)}\n\n")
            
            f.write("## Device Topology by Port\n\n")
            
            topology_by_port = topology_data.get('topology_by_port', {})
            for port, devices in sorted(topology_by_port.items()):
                f.write(f"### Port: {port}\n\n")
                f.write(f"**Devices**: {len(devices)}\n\n")
                
                for device in devices:
                    f.write(f"#### {device.get('hostname', 'Unknown')} ({device.get('mac', 'N/A')})\n\n")
                    f.write(f"- **IP Address**: {device.get('ipv4_address', 'N/A')}\n")
                    f.write(f"- **Hardware Vendor**: {device.get('hardware_vendor', 'Unknown')}\n")
                    f.write(f"- **Hardware Model**: {device.get('hardware_version', 'Unknown')}\n")
                    f.write(f"- **OS**: {device.get('os_name', 'Unknown')} {device.get('os_version', '')}\n")
                    f.write(f"- **Status**: {'Online' if device.get('is_online') else 'Offline'}\n")
                    f.write(f"- **Last Seen**: {device.get('last_seen', 'N/A')}\n")
                    f.write(f"- **Host Source**: {device.get('host_src', 'N/A')}\n")
                    
                    if device.get('fortiswitch_port_name'):
                        f.write(f"- **FortiSwitch Port**: {device.get('fortiswitch_port_name')}\n")
                    if device.get('fortiap_ssid'):
                        f.write(f"- **FortiAP SSID**: {device.get('fortiap_ssid')}\n")
                    
                    f.write("\n")
        
        return {
            "success": True,
            "output_file": str(doc_path),
            "json_file": json_file,
            "device_count": topology_data.get('total_devices', 0),
            "online_count": topology_data.get('online_devices', 0)
        }
    
    except Exception as e:
        logger.error(f"Error generating API documentation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "output_file": None
        }


def analyze_code_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for common errors and issues
    
    Args:
        file_path: Path to Python file to analyze
    
    Returns:
        Dictionary with analysis results
    """
    issues = []
    suggestions = []
    
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "issues": [],
                "suggestions": []
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "severity": "error",
                "message": f"Syntax error: {e.msg}",
                "line": e.lineno,
                "column": e.offset
            })
            return {
                "success": True,
                "file": file_path,
                "issues": issues,
                "suggestions": suggestions
            }
        
        # Check for common issues
        lines = content.split('\n')
        
        # Check for unused imports
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
        import_names = set()
        for imp in imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    import_names.add(alias.name.split('.')[0])
            elif isinstance(imp, ast.ImportFrom):
                if imp.module:
                    import_names.add(imp.module.split('.')[0])
        
        # Check for print statements (should use logger)
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and 'logger' not in line.lower():
                issues.append({
                    "type": "code_quality",
                    "severity": "warning",
                    "message": "Consider using logger instead of print()",
                    "line": i,
                    "suggestion": "Replace print() with logger.info() or logger.debug()"
                })
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE):
                issues.append({
                    "type": "todo",
                    "severity": "info",
                    "message": f"Found {re.search(r'\\b(TODO|FIXME|XXX|HACK)\\b', line, re.IGNORECASE).group()} comment",
                    "line": i,
                    "content": line.strip()
                })
        
        # Check for potential issues
        # Missing docstrings in functions/classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                if not node.name.startswith('_') or node.name.startswith('__'):
                    suggestions.append({
                        "type": "documentation",
                        "severity": "info",
                        "message": f"Function '{node.name}' lacks a docstring",
                        "line": node.lineno
                    })
        
        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({
                    "type": "error_handling",
                    "severity": "warning",
                    "message": "Bare except clause - should specify exception type",
                    "line": node.lineno
                })
        
        return {
            "success": True,
            "file": file_path,
            "issues": issues,
            "suggestions": suggestions,
            "total_issues": len(issues),
            "total_suggestions": len(suggestions)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing code file: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "file": file_path,
            "issues": [],
            "suggestions": []
        }


def fix_code_issues(file_path: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Attempt to automatically fix code issues
    
    Args:
        file_path: Path to Python file
        issues: List of issues to fix
    
    Returns:
        Dictionary with fix results
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "fixed": [],
                "failed": []
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed = []
        failed = []
        
        # Sort issues by line number (descending) to avoid offset issues
        sorted_issues = sorted(issues, key=lambda x: x.get('line', 0), reverse=True)
        
        for issue in sorted_issues:
            issue_type = issue.get('type')
            line_num = issue.get('line', 0) - 1  # Convert to 0-based index
            
            if line_num < 0 or line_num >= len(lines):
                failed.append({
                    "issue": issue,
                    "reason": "Line number out of range"
                })
                continue
            
            try:
                if issue_type == "code_quality" and "print" in issue.get('message', '').lower():
                    # Replace print with logger
                    original_line = lines[line_num]
                    # Simple replacement - could be improved
                    new_line = original_line.replace('print(', 'logger.info(')
                    if new_line != original_line:
                        lines[line_num] = new_line
                        fixed.append({
                            "issue": issue,
                            "fix": "Replaced print() with logger.info()"
                        })
                    else:
                        failed.append({
                            "issue": issue,
                            "reason": "Could not replace print statement"
                        })
                else:
                    failed.append({
                        "issue": issue,
                        "reason": f"Auto-fix not available for issue type: {issue_type}"
                    })
            except Exception as e:
                failed.append({
                    "issue": issue,
                    "reason": f"Error applying fix: {str(e)}"
                })
        
        # Write back if we fixed anything
        if fixed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        return {
            "success": True,
            "file": file_path,
            "fixed": fixed,
            "failed": failed,
            "total_fixed": len(fixed),
            "total_failed": len(failed)
        }
    
    except Exception as e:
        logger.error(f"Error fixing code issues: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "file": file_path,
            "fixed": [],
            "failed": []
        }


def analyze_project_code(directory: str = ".", pattern: str = "*.py") -> Dict[str, Any]:
    """
    Analyze all Python files in a directory
    
    Args:
        directory: Directory to analyze
        pattern: File pattern to match
    
    Returns:
        Dictionary with analysis results for all files
    """
    results = []
    total_issues = 0
    total_suggestions = 0
    
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
                "files": []
            }
        
        # Find all Python files
        python_files = list(dir_path.rglob(pattern))
        
        # Exclude common directories
        exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.venv'}
        python_files = [
            f for f in python_files
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]
        
        for file_path in python_files:
            result = analyze_code_file(str(file_path))
            if result.get("success"):
                results.append(result)
                total_issues += result.get("total_issues", 0)
                total_suggestions += result.get("total_suggestions", 0)
        
        return {
            "success": True,
            "directory": directory,
            "files_analyzed": len(results),
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "files": results
        }
    
    except Exception as e:
        logger.error(f"Error analyzing project code: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "files": []
        }


def get_api_endpoint_info(endpoint: str) -> Dict[str, Any]:
    """
    Get information about a specific API endpoint from the reference documentation
    
    Args:
        endpoint: API endpoint path (e.g., "monitor/user/device/query")
    
    Returns:
        Dictionary with endpoint information
    """
    try:
        ref_file = Path(__file__).parent / "API_ENDPOINTS_REFERENCE.md"
        if not ref_file.exists():
            return {
                "success": False,
                "error": "API_ENDPOINTS_REFERENCE.md not found"
            }
        
        with open(ref_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Search for endpoint in documentation
        endpoint_lower = endpoint.lower()
        lines = content.split('\n')
        
        info = {
            "endpoint": endpoint,
            "found": False,
            "description": "",
            "method": "",
            "parameters": [],
            "returns": []
        }
        
        in_section = False
        for i, line in enumerate(lines):
            if endpoint_lower in line.lower() or endpoint.replace('/', '-') in line.lower():
                in_section = True
                info["found"] = True
                # Look for description in following lines
                for j in range(i, min(i + 20, len(lines))):
                    next_line = lines[j]
                    if next_line.startswith('- **'):
                        if 'Method' in next_line:
                            info["method"] = next_line.split('**')[1].strip()
                        elif 'Purpose' in next_line:
                            info["description"] = next_line.split('**')[1].strip()
                        elif 'Returns' in next_line:
                            # Get return info
                            pass
                    elif next_line.startswith('####'):
                        break
        
        return {
            "success": True,
            **info
        }
    
    except Exception as e:
        logger.error(f"Error getting API endpoint info: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint
        }
