"""
AI Healer Service - System Doctor

Internal "System Doctor" agent that uses AutoGen to analyze issues locally
and suggest fixes from the knowledge base.

This service provides automated diagnosis and healing capabilities for the
FortiGate Dashboard platform.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Knowledge base path
KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "healer_knowledge_base.json"
)


class AIHealer:
    """
    System Doctor - Internal AI agent for automated issue diagnosis and healing.

    Uses the knowledge base to suggest fixes for common errors and can
    integrate with AutoGen for more complex analysis.
    """

    def __init__(self, knowledge_base_path: str = None):
        """
        Initialize the AI Healer.

        Args:
            knowledge_base_path: Path to knowledge base JSON file
        """
        self.knowledge_base_path = knowledge_base_path or KNOWLEDGE_BASE_PATH
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the knowledge base from JSON file"""
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load knowledge base: {e}")
                return {"fixes": {}, "metadata": {"version": "1.0"}}
        else:
            logger.info("Knowledge base not found, using empty base")
            return {"fixes": {}, "metadata": {"version": "1.0"}}

    def diagnose(self, error_text: str) -> Dict[str, Any]:
        """
        Diagnose an error and suggest fixes from the knowledge base.

        Args:
            error_text: Error message or log text to analyze

        Returns:
            Diagnosis with suggested fixes
        """
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error_text": error_text,
            "matches_found": [],
            "suggested_fixes": [],
            "auto_remediable": False,
        }

        error_lower = error_text.lower()

        # Search knowledge base for matching patterns
        for category, fixes in self.knowledge_base.get("fixes", {}).items():
            for fix_entry in fixes:
                pattern = fix_entry.get("pattern", "").lower()
                if pattern and pattern in error_lower:
                    match = {
                        "category": category,
                        "pattern": fix_entry.get("pattern"),
                        "fix": fix_entry.get("fix"),
                        "severity": fix_entry.get("severity", "medium"),
                        "auto_remediable": fix_entry.get("auto_remediable", False),
                        "context": fix_entry.get("context"),
                    }
                    result["matches_found"].append(match)
                    result["suggested_fixes"].append(fix_entry.get("fix"))

                    # If any match is auto-remediable, mark as such
                    if fix_entry.get("auto_remediable", False):
                        result["auto_remediable"] = True

        # Sort by severity (critical > high > medium > low)
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        result["matches_found"].sort(
            key=lambda x: severity_order.get(x.get("severity", "medium"), 2),
            reverse=True,
        )

        return result

    def suggest_fix(self, error_text: str) -> Optional[Dict[str, Any]]:
        """
        Get the best suggested fix for an error.

        Args:
            error_text: Error message to analyze

        Returns:
            Best matching fix or None if no match found
        """
        diagnosis = self.diagnose(error_text)

        if diagnosis["matches_found"]:
            # Return the highest severity match
            return diagnosis["matches_found"][0]

        return None

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Returns:
            Statistics including total fixes, categories, etc.
        """
        fixes = self.knowledge_base.get("fixes", {})
        total_fixes = sum(len(category_fixes) for category_fixes in fixes.values())

        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        auto_remediable_count = 0

        for category_fixes in fixes.values():
            for fix in category_fixes:
                severity = fix.get("severity", "medium")
                if severity in severity_counts:
                    severity_counts[severity] += 1
                if fix.get("auto_remediable", False):
                    auto_remediable_count += 1

        return {
            "total_categories": len(fixes),
            "total_fixes": total_fixes,
            "severity_breakdown": severity_counts,
            "auto_remediable_count": auto_remediable_count,
            "last_updated": self.knowledge_base.get("metadata", {}).get("last_updated"),
            "version": self.knowledge_base.get("metadata", {}).get("version", "1.0"),
        }

    def analyze_logs(self, log_path: str, limit: int = 50) -> Dict[str, Any]:
        """
        Analyze log file for errors and suggest fixes.

        Args:
            log_path: Path to log file
            limit: Maximum number of errors to analyze

        Returns:
            Analysis results with suggested fixes
        """
        result = {
            "log_path": log_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "errors_found": [],
            "fixes_suggested": 0,
        }

        if not os.path.exists(log_path):
            result["error"] = "Log file not found"
            return result

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            error_lines = []
            for line in lines:
                if any(
                    keyword in line.upper()
                    for keyword in ["ERROR", "EXCEPTION", "FAILED", "CRITICAL"]
                ):
                    error_lines.append(line.strip())

            # Analyze each error
            for error_line in error_lines[:limit]:
                diagnosis = self.diagnose(error_line)
                if diagnosis["matches_found"]:
                    result["errors_found"].append(
                        {
                            "error": error_line[:200],  # Truncate long errors
                            "suggested_fix": diagnosis["matches_found"][0]["fix"],
                            "severity": diagnosis["matches_found"][0]["severity"],
                            "auto_remediable": diagnosis["auto_remediable"],
                        }
                    )
                    result["fixes_suggested"] += 1

        except Exception as e:
            result["error"] = f"Failed to analyze log: {e}"
            logger.error(f"Error analyzing log {log_path}: {e}")

        return result


# Global instance
_ai_healer = None


def get_ai_healer() -> AIHealer:
    """Get global AI Healer instance"""
    global _ai_healer
    if _ai_healer is None:
        _ai_healer = AIHealer()
    return _ai_healer
