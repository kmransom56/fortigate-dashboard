"""
Magentic-One Integration Module - Tools for Microsoft Magentic-One Orchestrator.

This module provides a NetworkPlatformTools class that can be mapped to a
Magentic-One Orchestrator for agentic network management workflows.

Usage with Magentic-One:
    from extras.magentic_one_integration import NetworkPlatformTools
    
    tools = NetworkPlatformTools()
    
    # Map to orchestrator
    orchestrator.register_tool("check_health", tools.check_platform_health)
    orchestrator.register_tool("self_heal", tools.execute_self_healing)
    orchestrator.register_tool("train_agent", tools.train_recovery_agent)
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class NetworkPlatformTools:
    """
    Tool class for Magentic-One Orchestrator integration.
    
    Provides three core capabilities:
    1. check_platform_health - Diagnostics and health monitoring
    2. execute_self_healing - Automated remediation actions
    3. train_recovery_agent - Teaching new fixes to the knowledge base
    """
    
    def __init__(
        self,
        api_base_url: str = "http://localhost:5000",
        llm_url: str = "http://localhost:11434/api/generate",
        llm_model: str = "fortinet-meraki:v4",
        knowledge_base_path: str = "data/healer_knowledge_base.json"
    ):
        """
        Initialize the NetworkPlatformTools.
        
        Args:
            api_base_url: Base URL for the network management API
            llm_url: URL for the LLM endpoint (Ollama)
            llm_model: Name of the fine-tuned model to use
            knowledge_base_path: Path to the healer knowledge base JSON
        """
        self.api_base_url = api_base_url
        self.llm_url = llm_url
        self.llm_model = llm_model
        self.knowledge_base_path = knowledge_base_path
        
    def check_platform_health(self, include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Comprehensive platform health check with AI-powered recommendations.
        
        Args:
            include_recommendations: Whether to include AI recommendations
            
        Returns:
            Health status with component states, metrics, and recommendations.
        """
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": "unknown",
            "components": {},
            "metrics": {},
            "alerts": [],
            "recommendations": []
        }
        
        # Check API health
        try:
            resp = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            result["components"]["api"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "latency_ms": round(resp.elapsed.total_seconds() * 1000, 2)
            }
        except requests.exceptions.ConnectionError:
            result["components"]["api"] = {"status": "offline", "error": "Connection refused"}
            result["alerts"].append("Main API is offline")
        except Exception as e:
            result["components"]["api"] = {"status": "error", "error": str(e)}
        
        # Check AI maintenance engine
        try:
            resp = requests.get(f"{self.api_base_url}/api/ai_maintenance/self_healing", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                result["components"]["ai_engine"] = {
                    "status": "healthy" if data.get("available") else "degraded",
                    "registered_remediations": data.get("registered_remediations", 0),
                    "recent_errors": data.get("recent_errors", 0)
                }
                result["metrics"]["remediation_state"] = data.get("remediation_state", {})
            else:
                result["components"]["ai_engine"] = {"status": "degraded", "http_code": resp.status_code}
        except Exception as e:
            result["components"]["ai_engine"] = {"status": "offline", "error": str(e)}
        
        # Check LLM availability
        try:
            resp = requests.post(
                self.llm_url,
                json={"model": self.llm_model, "prompt": "ping", "max_tokens": 1, "stream": False},
                timeout=10
            )
            result["components"]["llm"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "model": self.llm_model,
                "latency_ms": round(resp.elapsed.total_seconds() * 1000, 2)
            }
        except Exception as e:
            result["components"]["llm"] = {"status": "offline", "model": self.llm_model, "error": str(e)}
            result["alerts"].append(f"LLM ({self.llm_model}) is unavailable")
        
        # Determine overall status
        statuses = [c.get("status") for c in result["components"].values()]
        if all(s == "healthy" for s in statuses):
            result["overall_status"] = "healthy"
        elif any(s == "offline" for s in statuses):
            result["overall_status"] = "critical"
        else:
            result["overall_status"] = "degraded"
        
        # Generate AI recommendations if requested and LLM is available
        if include_recommendations and result["components"].get("llm", {}).get("status") == "healthy":
            result["recommendations"] = self._generate_recommendations(result)
        
        return result
    
    def _generate_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered recommendations based on health data."""
        recommendations = []
        
        # Rule-based recommendations first
        for name, component in health_data.get("components", {}).items():
            if component.get("status") == "offline":
                recommendations.append(f"Restart the {name} service")
            elif component.get("status") == "degraded":
                recommendations.append(f"Investigate {name} performance issues")
            if component.get("latency_ms", 0) > 1000:
                recommendations.append(f"High latency on {name} - check network/resources")
        
        return recommendations
    
    def execute_self_healing(
        self, 
        action: str,
        force: bool = False,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a self-healing action on the platform.
        
        Args:
            action: Name of the remediation action (e.g., 'reset_http_session')
            force: Bypass cooldown check
            timeout: Request timeout in seconds
            
        Returns:
            Result of the healing action with success/failure status.
        """
        result = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": False
        }
        
        try:
            payload = {"action": action}
            if force:
                payload["force"] = True
            
            resp = requests.post(
                f"{self.api_base_url}/api/ai_maintenance/remediate",
                json=payload,
                timeout=timeout
            )
            
            data = resp.json()
            result["success"] = data.get("success", False)
            result["skipped"] = data.get("skipped", False)
            result["cooldown_remaining"] = data.get("cooldown_remaining")
            result["message"] = data.get("message", data.get("error", "Unknown response"))
            
            if data.get("remediation"):
                result["details"] = data["remediation"]
                
        except requests.exceptions.ConnectionError:
            result["error"] = "API connection failed"
            result["message"] = "Unable to connect to the platform API"
        except requests.exceptions.Timeout:
            result["error"] = "Request timeout"
            result["message"] = f"Healing action timed out after {timeout}s"
        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Unexpected error: {e}"
        
        return result
    
    def train_recovery_agent(
        self,
        error_pattern: str,
        fix_description: str,
        category: str = "general",
        severity: str = "medium",
        auto_remediable: bool = False,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Train the recovery agent with a new error fix.
        
        This teaches the system how to handle specific errors by storing
        the pattern and fix in the knowledge base.
        
        Args:
            error_pattern: The error pattern to match
            fix_description: How to fix this error
            category: Category (e.g., 'ssl_errors', 'api_errors', 'docker_errors')
            severity: 'low', 'medium', 'high', or 'critical'
            auto_remediable: Whether this can be auto-fixed
            context: Optional additional context about when this fix applies
            
        Returns:
            Confirmation with knowledge base statistics.
        """
        result = {
            "success": False,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Load existing knowledge base
        kb = {"fixes": {}, "metadata": {"version": "1.0", "last_updated": None}}
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    kb = json.load(f)
            except Exception as e:
                result["warning"] = f"Could not load existing KB: {e}"
        
        # Initialize category if needed
        if "fixes" not in kb:
            kb["fixes"] = {}
        if category not in kb["fixes"]:
            kb["fixes"][category] = []
        
        # Check for duplicate pattern
        for existing in kb["fixes"].get(category, []):
            if existing.get("pattern") == error_pattern:
                result["error"] = "Pattern already exists in knowledge base"
                result["existing_fix"] = existing["fix"]
                return result
        
        # Add new fix
        new_entry = {
            "pattern": error_pattern,
            "fix": fix_description,
            "severity": severity,
            "auto_remediable": auto_remediable,
            "learned_at": datetime.utcnow().isoformat() + "Z"
        }
        if context:
            new_entry["context"] = context
        
        kb["fixes"][category].append(new_entry)
        kb["metadata"] = {
            "version": kb.get("metadata", {}).get("version", "1.0"),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        # Save knowledge base
        try:
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(kb, f, indent=2)
            
            result["success"] = True
            result["message"] = f"Learned fix for: {error_pattern}"
            result["category"] = category
            result["knowledge_base_stats"] = {
                "total_categories": len(kb["fixes"]),
                "total_fixes": sum(len(v) for v in kb["fixes"].values()),
                "category_count": len(kb["fixes"].get(category, []))
            }
        except Exception as e:
            result["error"] = f"Failed to save knowledge base: {e}"
        
        return result
    
    def query_knowledge_base(self, error_text: str) -> Dict[str, Any]:
        """
        Query the knowledge base for a fix matching the error.
        
        Args:
            error_text: Error message to search for
            
        Returns:
            Matching fix if found, or empty result.
        """
        if not os.path.exists(self.knowledge_base_path):
            return {"found": False, "message": "Knowledge base not initialized"}
        
        try:
            with open(self.knowledge_base_path, 'r') as f:
                kb = json.load(f)
            
            error_lower = error_text.lower()
            
            for category, fixes in kb.get("fixes", {}).items():
                for fix in fixes:
                    pattern = fix.get("pattern", "").lower()
                    if pattern and pattern in error_lower:
                        return {
                            "found": True,
                            "category": category,
                            "pattern": fix["pattern"],
                            "fix": fix["fix"],
                            "severity": fix.get("severity", "medium"),
                            "auto_remediable": fix.get("auto_remediable", False),
                            "context": fix.get("context")
                        }
            
            return {"found": False, "message": "No matching fix found"}
            
        except Exception as e:
            return {"found": False, "error": str(e)}


# Convenience function for quick tool instantiation
def create_platform_tools(**kwargs) -> NetworkPlatformTools:
    """
    Factory function to create NetworkPlatformTools with optional overrides.
    
    Args:
        **kwargs: Override default configuration values
        
    Returns:
        Configured NetworkPlatformTools instance.
    """
    return NetworkPlatformTools(**kwargs)
