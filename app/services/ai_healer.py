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
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
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

    def check_syntax(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Check Python files for syntax errors using the syntax checker.

        Args:
            file_paths: List of file paths or directories to check. Defaults to app/

        Returns:
            Results of syntax check with any errors found
        """
        if file_paths is None:
            file_paths = ["app/"]

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": "syntax_check",
            "files_checked": [],
            "errors_found": [],
            "passed": True,
        }

        try:
            # Get project root
            project_root = Path(__file__).parent.parent.parent
            syntax_checker = project_root / "tools" / "utils" / "check_syntax.py"

            if not syntax_checker.exists():
                result["error"] = f"Syntax checker not found at {syntax_checker}"
                result["passed"] = False
                return result

            # Build command
            cmd = ["python3", str(syntax_checker)] + file_paths

            # Run syntax check
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=60,
            )

            result["returncode"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["passed"] = process.returncode == 0

            # Parse output for errors
            if not result["passed"]:
                lines = process.stdout.split("\n") + process.stderr.split("\n")
                for line in lines:
                    if "❌" in line or "SyntaxError" in line or "IndentationError" in line:
                        result["errors_found"].append(line.strip())

        except subprocess.TimeoutExpired:
            result["error"] = "Syntax check timed out after 60 seconds"
            result["passed"] = False
        except Exception as e:
            result["error"] = f"Failed to run syntax check: {e}"
            result["passed"] = False
            logger.error(f"Error running syntax check: {e}")

        return result

    def format_code(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Format code using Black.

        Args:
            file_paths: List of file paths or directories to format. Defaults to app/

        Returns:
            Results of formatting operation
        """
        if file_paths is None:
            file_paths = ["app/"]

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": "format_code",
            "files_formatted": [],
            "passed": True,
        }

        try:
            # Get project root
            project_root = Path(__file__).parent.parent.parent

            # Build command
            cmd = ["python3", "-m", "black"] + file_paths

            # Run black
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=120,
            )

            result["returncode"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["passed"] = process.returncode == 0

            # Parse files that were reformatted
            for line in process.stdout.split("\n"):
                if "reformatted" in line.lower():
                    result["files_formatted"].append(line.strip())

        except subprocess.TimeoutExpired:
            result["error"] = "Code formatting timed out after 120 seconds"
            result["passed"] = False
        except Exception as e:
            result["error"] = f"Failed to format code: {e}"
            result["passed"] = False
            logger.error(f"Error formatting code: {e}")

        return result

    def lint_code(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Lint code using Flake8.

        Args:
            file_paths: List of file paths or directories to lint. Defaults to app/

        Returns:
            Results of linting with any issues found
        """
        if file_paths is None:
            file_paths = ["app/"]

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": "lint_code",
            "issues_found": [],
            "passed": True,
        }

        try:
            # Get project root
            project_root = Path(__file__).parent.parent.parent

            # Build command
            cmd = [
                "python3",
                "-m",
                "flake8",
            ] + file_paths + [
                "--max-line-length=88",
                "--ignore=E203,W503,E501",
            ]

            # Run flake8
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=120,
            )

            result["returncode"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["passed"] = process.returncode == 0

            # Parse linting issues
            if not result["passed"]:
                for line in process.stdout.split("\n"):
                    if line.strip():
                        result["issues_found"].append(line.strip())

        except subprocess.TimeoutExpired:
            result["error"] = "Linting timed out after 120 seconds"
            result["passed"] = False
        except Exception as e:
            result["error"] = f"Failed to lint code: {e}"
            result["passed"] = False
            logger.error(f"Error linting code: {e}")

        return result

    def run_code_quality_checks(
        self, file_paths: List[str] = None, auto_fix: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive code quality checks (syntax, format, lint).

        Args:
            file_paths: List of file paths or directories to check. Defaults to app/
            auto_fix: Whether to auto-fix formatting issues

        Returns:
            Combined results from all checks
        """
        if file_paths is None:
            file_paths = ["app/"]

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": "code_quality_checks",
            "syntax_check": {},
            "format_check": {},
            "lint_check": {},
            "all_passed": False,
        }

        # Step 1: Check syntax (most important)
        logger.info("Running syntax check...")
        syntax_result = self.check_syntax(file_paths)
        result["syntax_check"] = syntax_result

        if not syntax_result["passed"]:
            result["all_passed"] = False
            logger.warning("Syntax errors found. Fix these before formatting/linting.")
            return result

        # Step 2: Format code (if auto_fix enabled)
        if auto_fix:
            logger.info("Formatting code with Black...")
            format_result = self.format_code(file_paths)
            result["format_check"] = format_result

        # Step 3: Lint code
        logger.info("Linting code with Flake8...")
        lint_result = self.lint_code(file_paths)
        result["lint_check"] = lint_result

        # All checks passed if syntax passed and lint passed
        result["all_passed"] = syntax_result["passed"] and lint_result["passed"]

        return result

    def auto_fix_code_issues(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Automatically fix code issues that can be auto-fixed.

        This runs:
        1. Syntax check (to identify issues)
        2. Code formatting (auto-fixes formatting)
        3. Reports issues that need manual fixing

        Args:
            file_paths: List of file paths or directories to fix. Defaults to app/

        Returns:
            Results of auto-fix operation
        """
        if file_paths is None:
            file_paths = ["app/"]

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": "auto_fix_code_issues",
            "fixed": [],
            "needs_manual_fix": [],
            "passed": False,
        }

        # Run comprehensive checks with auto-fix
        quality_result = self.run_code_quality_checks(file_paths, auto_fix=True)

        # Report what was fixed
        if quality_result["format_check"].get("files_formatted"):
            result["fixed"].extend(
                [
                    f"Formatted: {f}"
                    for f in quality_result["format_check"]["files_formatted"]
                ]
            )

        # Report what needs manual fixing
        if not quality_result["syntax_check"]["passed"]:
            result["needs_manual_fix"].extend(
                [
                    f"Syntax error: {e}"
                    for e in quality_result["syntax_check"].get("errors_found", [])
                ]
            )

        if not quality_result["lint_check"]["passed"]:
            result["needs_manual_fix"].extend(
                [
                    f"Linting issue: {issue}"
                    for issue in quality_result["lint_check"].get("issues_found", [])
                ]
            )

        result["passed"] = quality_result["all_passed"]
        result["quality_check_results"] = quality_result

        return result


# Global instance
_ai_healer = None


def get_ai_healer() -> AIHealer:
    """Get global AI Healer instance"""
    global _ai_healer
    if _ai_healer is None:
        _ai_healer = AIHealer()
    return _ai_healer
