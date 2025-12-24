"""
AutoGen Skills Module - Platform-aware agent skills for network management.

This module provides skills that can be imported into AutoGen Studio or 
used directly with AutoGen agents for network diagnostics, healing, and teaching.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime


class NetworkDiagnostics:
    """Skills for diagnosing network platform health and issues."""
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        
    def check_platform_health(self) -> Dict[str, Any]:
        """
        Check the overall health of the network management platform.
        
        Returns:
            Dict with health status, component states, and any active alerts.
        """
        health = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "unknown",
            "components": {},
            "alerts": []
        }
        
        # Check main API
        try:
            resp = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            health["components"]["api"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "response_time_ms": resp.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            health["components"]["api"] = {"status": "offline", "error": str(e)}
            health["alerts"].append(f"API unreachable: {e}")
        
        # Check AI maintenance engine
        try:
            resp = requests.get(f"{self.api_base_url}/api/ai_maintenance/self_healing", timeout=5)
            data = resp.json() if resp.status_code == 200 else {}
            health["components"]["ai_engine"] = {
                "status": "healthy" if data.get("available") else "offline",
                "registered_remediations": data.get("registered_remediations", 0)
            }
        except Exception as e:
            health["components"]["ai_engine"] = {"status": "offline", "error": str(e)}
        
        # Determine overall status
        statuses = [c.get("status", "unknown") for c in health["components"].values()]
        if all(s == "healthy" for s in statuses):
            health["status"] = "healthy"
        elif any(s == "offline" for s in statuses):
            health["status"] = "degraded"
        else:
            health["status"] = "partial"
            
        return health
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent errors from the platform logs.
        
        Args:
            limit: Maximum number of errors to retrieve
            
        Returns:
            List of error entries with timestamps and details.
        """
        errors = []
        log_paths = [
            "log/error.log",
            "meraki_clu_debug.log"
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()[-limit*2:]  # Read extra to filter
                        for line in lines:
                            if 'ERROR' in line or 'Exception' in line:
                                errors.append({
                                    "source": log_path,
                                    "message": line.strip(),
                                    "severity": "error"
                                })
                except Exception as e:
                    errors.append({
                        "source": log_path,
                        "message": f"Could not read log: {e}",
                        "severity": "warning"
                    })
        
        return errors[:limit]
    
    def analyze_network_topology(self, network_id: str) -> Dict[str, Any]:
        """
        Analyze network topology for potential issues.
        
        Args:
            network_id: Meraki network ID to analyze
            
        Returns:
            Analysis results with device counts and potential issues.
        """
        try:
            resp = requests.get(
                f"{self.api_base_url}/api/topology/{network_id}",
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "network_id": network_id,
                    "device_count": len(data.get("devices", [])),
                    "client_count": len(data.get("clients", [])),
                    "topology_valid": True,
                    "issues": []
                }
        except Exception as e:
            return {
                "network_id": network_id,
                "topology_valid": False,
                "error": str(e)
            }


class NetworkHealer:
    """Skills for self-healing network issues."""
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        self.knowledge_base_path = "data/healer_knowledge_base.json"
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the healer knowledge base."""
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"fixes": {}}
    
    def find_known_fix(self, error_pattern: str) -> Optional[Dict[str, Any]]:
        """
        Search knowledge base for a known fix matching the error pattern.
        
        Args:
            error_pattern: Error message or pattern to match
            
        Returns:
            Fix details if found, None otherwise.
        """
        kb = self._load_knowledge_base()
        error_lower = error_pattern.lower()
        
        for category, fixes in kb.get("fixes", {}).items():
            for fix in fixes:
                if fix.get("pattern", "").lower() in error_lower:
                    return {
                        "category": category,
                        "pattern": fix["pattern"],
                        "fix": fix["fix"],
                        "auto_remediable": fix.get("auto_remediable", False),
                        "severity": fix.get("severity", "medium")
                    }
        return None
    
    def execute_remediation(self, action: str) -> Dict[str, Any]:
        """
        Execute a self-healing remediation action.
        
        Args:
            action: Name of the remediation action to execute
            
        Returns:
            Result of the remediation attempt.
        """
        try:
            resp = requests.post(
                f"{self.api_base_url}/api/ai_maintenance/remediate",
                json={"action": action},
                timeout=30
            )
            return resp.json()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    def reset_http_session(self) -> Dict[str, Any]:
        """Reset HTTP sessions to clear stale connections."""
        return self.execute_remediation("reset_http_session")
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear application caches."""
        return self.execute_remediation("clear_cache")
    
    def reconnect_api(self) -> Dict[str, Any]:
        """Force reconnection to external APIs."""
        return self.execute_remediation("reconnect_api")


class NetworkTeacher:
    """Skills for teaching the agent new knowledge."""
    
    def __init__(self, knowledge_base_path: str = "data/healer_knowledge_base.json"):
        self.knowledge_base_path = knowledge_base_path
        
    def teach_fix(self, error_pattern: str, fix_description: str, 
                  category: str = "general", severity: str = "medium",
                  auto_remediable: bool = False) -> Dict[str, Any]:
        """
        Teach the system a new error fix.
        
        Args:
            error_pattern: Pattern to match in errors
            fix_description: How to fix this error
            category: Category for organization (e.g., 'ssl_errors', 'api_errors')
            severity: 'low', 'medium', 'high', or 'critical'
            auto_remediable: Whether this fix can be auto-applied
            
        Returns:
            Confirmation of the learning.
        """
        # Load existing knowledge base
        kb = {"fixes": {}}
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    kb = json.load(f)
            except Exception:
                pass
        
        # Ensure category exists
        if category not in kb["fixes"]:
            kb["fixes"][category] = []
        
        # Add new fix
        new_fix = {
            "pattern": error_pattern,
            "fix": fix_description,
            "severity": severity,
            "auto_remediable": auto_remediable,
            "learned_at": datetime.utcnow().isoformat() + "Z"
        }
        kb["fixes"][category].append(new_fix)
        
        # Save knowledge base
        os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
        with open(self.knowledge_base_path, 'w') as f:
            json.dump(kb, f, indent=2)
        
        return {
            "success": True,
            "message": f"Learned fix for pattern: {error_pattern}",
            "category": category,
            "total_fixes": sum(len(v) for v in kb["fixes"].values())
        }
    
    def list_knowledge(self) -> Dict[str, Any]:
        """
        List all knowledge in the knowledge base.
        
        Returns:
            Summary of stored knowledge.
        """
        if not os.path.exists(self.knowledge_base_path):
            return {"categories": {}, "total_fixes": 0}
        
        try:
            with open(self.knowledge_base_path, 'r') as f:
                kb = json.load(f)
                
            summary = {
                "categories": {},
                "total_fixes": 0
            }
            
            for category, fixes in kb.get("fixes", {}).items():
                summary["categories"][category] = len(fixes)
                summary["total_fixes"] += len(fixes)
            
            return summary
        except Exception as e:
            return {"error": str(e)}


# Convenience function for AutoGen Studio skill registration
def get_autogen_skills() -> Dict[str, Any]:
    """
    Get all available AutoGen skills for registration.
    
    Returns:
        Dictionary of skill instances ready for use.
    """
    return {
        "diagnostics": NetworkDiagnostics(),
        "healer": NetworkHealer(),
        "teacher": NetworkTeacher()
    }
