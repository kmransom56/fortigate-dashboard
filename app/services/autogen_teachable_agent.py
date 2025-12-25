"""
AutoGen Teachable Agent Service

Provides a teachable agent that can learn from interactions and improve over time.
Integrates with the AI healer knowledge base and platform skills.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import AutoGen
try:
    import autogen
    from autogen.agentchat import AssistantAgent, UserProxyAgent
    try:
        from autogen.agentchat.teachable_agent import TeachableAgent
        TEACHABLE_AVAILABLE = True
    except ImportError:
        # Fallback for versions without TeachableAgent
        TeachableAgent = None
        TEACHABLE_AVAILABLE = False
        logger.warning("TeachableAgent not available in this pyautogen version. Using AssistantAgent.")
except ImportError:
    autogen = None
    TEACHABLE_AVAILABLE = False
    logger.warning("pyautogen not installed. Install with: pip install 'pyautogen==0.2.18'")


class AutoGenTeachableAgentService:
    """
    Service for managing AutoGen teachable agents.
    
    Provides a teachable agent that can:
    - Learn from interactions
    - Store knowledge in the healer knowledge base
    - Use platform skills (diagnostics, healing, teaching)
    - Integrate with the AI healer
    """

    def __init__(
        self,
        knowledge_base_path: str = None,
        model: str = "gpt-4",
        api_key: str = None,
        work_dir: str = None,
    ):
        """
        Initialize the teachable agent service.

        Args:
            knowledge_base_path: Path to knowledge base JSON file
            model: LLM model to use (default: gpt-4)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            work_dir: Working directory for agent files
        """
        if not TEACHABLE_AVAILABLE:
            raise ImportError(
                "pyautogen is not installed or TeachableAgent is not available. "
                "Install with: pip install 'pyautogen==0.2.18'"
            )

        # Set up paths
        project_root = Path(__file__).parent.parent.parent
        self.knowledge_base_path = (
            knowledge_base_path
            or os.path.join(project_root, "app", "data", "healer_knowledge_base.json")
        )
        self.work_dir = work_dir or os.path.join(project_root, "work_dir", "autogen")
        os.makedirs(self.work_dir, exist_ok=True)

        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()

        # Set up LLM config
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning(
                "No OpenAI API key found. Set OPENAI_API_KEY environment variable."
            )

        # Initialize agent (lazy loading)
        self._agent = None
        self._user_proxy = None

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

    def _save_knowledge_base(self) -> bool:
        """Save the knowledge base to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            with open(self.knowledge_base_path, "w") as f:
                json.dump(self.knowledge_base, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")
            return False

    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen"""
        config = {
            "model": self.model,
            "api_key": self.api_key,
            "temperature": 0.7,
        }

        # Check for Azure OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            config.update(
                {
                    "api_type": "azure",
                    "api_key": azure_key,
                    "api_base": azure_endpoint,
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                }
            )

        return config

    def _create_agent(self) -> Any:
        """Create the teachable agent instance"""
        if self._agent is not None:
            return self._agent

        llm_config = self._get_llm_config()

        # Create teachable agent
        if TEACHABLE_AVAILABLE and TeachableAgent:
            self._agent = TeachableAgent(
                name="teachable_agent",
                system_message="""You are a helpful AI assistant that can learn from interactions.
You have access to network management platform skills including:
- Diagnosing network issues
- Healing/fixing problems
- Learning new error fixes
- Code quality checking

When you learn something new, it will be saved to the knowledge base for future use.
Be thorough, helpful, and always try to learn from each interaction.""",
                llm_config=llm_config,
                teach_config={
                    "verbosity": 1,  # 0=quiet, 1=normal, 2=verbose
                    "reset_db": False,  # Don't reset on startup
                    "path_to_db_dir": self.work_dir,
                },
            )
        else:
            # Fallback to AssistantAgent
            self._agent = AssistantAgent(
                name="assistant_agent",
                system_message="""You are a helpful AI assistant for network management.
You can diagnose issues, suggest fixes, and help with code quality.
Note: Learning capabilities are limited without TeachableAgent.""",
                llm_config=llm_config,
            )

        return self._agent

    def _create_user_proxy(self) -> Any:
        """Create user proxy agent"""
        if self._user_proxy is not None:
            return self._user_proxy

        self._user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",  # Set to "ALWAYS" for interactive mode
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": self.work_dir,
                "use_docker": False,  # Set to True if Docker available
            },
        )

        return self._user_proxy

    def _register_platform_skills(self):
        """Register platform skills with the agent"""
        try:
            from extras.autogen_skills import get_autogen_skills

            skills = get_autogen_skills()
            agent = self._create_agent()

            # Register skills as functions
            if hasattr(agent, "register_function"):
                # Register diagnostics
                agent.register_function(
                    func_map={
                        "check_platform_health": skills["diagnostics"].check_platform_health,
                        "get_recent_errors": skills["diagnostics"].get_recent_errors,
                        "analyze_network_topology": skills["diagnostics"].analyze_network_topology,
                    }
                )

                # Register healer
                agent.register_function(
                    func_map={
                        "find_known_fix": skills["healer"].find_known_fix,
                        "execute_remediation": skills["healer"].execute_remediation,
                        "reset_http_session": skills["healer"].reset_http_session,
                        "clear_cache": skills["healer"].clear_cache,
                        "reconnect_api": skills["healer"].reconnect_api,
                    }
                )

                # Register teacher
                agent.register_function(
                    func_map={
                        "teach_fix": skills["teacher"].teach_fix,
                        "list_knowledge": skills["teacher"].list_knowledge,
                    }
                )

            # Also register AI healer code quality methods
            try:
                from app.services.ai_healer import get_ai_healer

                healer = get_ai_healer()
                if hasattr(agent, "register_for_llm"):
                    # AutoGen 0.2.18 style
                    agent.register_for_llm(name="check_syntax")(healer.check_syntax)
                    agent.register_for_llm(name="format_code")(healer.format_code)
                    agent.register_for_llm(name="lint_code")(healer.lint_code)
                    agent.register_for_llm(name="run_code_quality_checks")(
                        healer.run_code_quality_checks
                    )
                    agent.register_for_llm(name="auto_fix_code_issues")(
                        healer.auto_fix_code_issues
                    )
                elif hasattr(agent, "register_function"):
                    # Alternative registration method
                    agent.register_function(
                        func_map={
                            "check_syntax": healer.check_syntax,
                            "format_code": healer.format_code,
                            "lint_code": healer.lint_code,
                            "run_code_quality_checks": healer.run_code_quality_checks,
                            "auto_fix_code_issues": healer.auto_fix_code_issues,
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not register AI healer methods: {e}")

        except Exception as e:
            logger.warning(f"Could not register platform skills: {e}")

    def chat(self, message: str, clear_history: bool = False) -> Dict[str, Any]:
        """
        Chat with the teachable agent.

        Args:
            message: User message to send to the agent
            clear_history: Whether to clear conversation history

        Returns:
            Response from the agent with conversation details
        """
        if not TEACHABLE_AVAILABLE:
            return {
                "error": "AutoGen not available. Install with: pip install 'pyautogen==0.2.18'"
            }

        try:
            agent = self._create_agent()
            user_proxy = self._create_user_proxy()

            # Register platform skills
            self._register_platform_skills()

            # Clear history if requested
            if clear_history and hasattr(agent, "reset"):
                agent.reset()

            # Start conversation
            user_proxy.initiate_chat(
                agent,
                message=message,
                clear_history=clear_history,
            )

            # Get response
            last_message = user_proxy.last_message() if hasattr(user_proxy, "last_message") else None

            return {
                "success": True,
                "message": message,
                "response": last_message.get("content", "") if last_message else "No response",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "conversation_history": len(agent.chat_messages) if hasattr(agent, "chat_messages") else 0,
            }

        except Exception as e:
            logger.error(f"Error in agent chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    def teach(self, error_pattern: str, fix_description: str, category: str = "general",
              severity: str = "medium", auto_remediable: bool = False) -> Dict[str, Any]:
        """
        Teach the agent a new error fix.

        Args:
            error_pattern: Pattern to match in errors
            fix_description: How to fix this error
            category: Category for organization
            severity: Severity level (low, medium, high, critical)
            auto_remediable: Whether this fix can be auto-applied

        Returns:
            Confirmation of the learning
        """
        # Ensure category exists
        if category not in self.knowledge_base.get("fixes", {}):
            self.knowledge_base.setdefault("fixes", {})[category] = []

        # Add new fix
        new_fix = {
            "pattern": error_pattern,
            "fix": fix_description,
            "severity": severity,
            "auto_remediable": auto_remediable,
            "learned_at": datetime.utcnow().isoformat() + "Z",
            "learned_by": "autogen_teachable_agent",
        }

        self.knowledge_base["fixes"][category].append(new_fix)

        # Update metadata
        self.knowledge_base.setdefault("metadata", {})["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # Save knowledge base
        saved = self._save_knowledge_base()

        # Also update agent's memory if it's a TeachableAgent
        if self._agent and hasattr(self._agent, "learn"):
            try:
                self._agent.learn(
                    user_input=f"Error pattern: {error_pattern}",
                    assistant_reply=f"Fix: {fix_description}",
                )
            except Exception as e:
                logger.warning(f"Could not update agent memory: {e}")

        return {
            "success": saved,
            "message": f"Learned fix for pattern: {error_pattern}",
            "category": category,
            "total_fixes": sum(len(v) for v in self.knowledge_base.get("fixes", {}).values()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about learned knowledge"""
        fixes = self.knowledge_base.get("fixes", {})
        total_fixes = sum(len(category_fixes) for category_fixes in fixes.values())

        # Count by category
        category_counts = {cat: len(fixes) for cat, fixes in fixes.items()}

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
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "auto_remediable_count": auto_remediable_count,
            "last_updated": self.knowledge_base.get("metadata", {}).get("last_updated"),
            "agent_memory_entries": self._get_agent_memory_count() if self._agent else 0,
        }

    def _get_agent_memory_count(self) -> int:
        """Get number of entries in agent's memory (if TeachableAgent)"""
        if self._agent and hasattr(self._agent, "memory") and hasattr(self._agent.memory, "count"):
            try:
                return self._agent.memory.count()
            except Exception:
                pass
        return 0

    def reset_memory(self, keep_knowledge_base: bool = True) -> Dict[str, Any]:
        """
        Reset agent memory.

        Args:
            keep_knowledge_base: Whether to keep the knowledge base file

        Returns:
            Confirmation of reset
        """
        if self._agent and hasattr(self._agent, "reset"):
            try:
                self._agent.reset()
                if not keep_knowledge_base:
                    # Clear memory database
                    memory_db = os.path.join(self.work_dir, "memory")
                    if os.path.exists(memory_db):
                        import shutil
                        shutil.rmtree(memory_db)
                return {
                    "success": True,
                    "message": "Agent memory reset",
                    "knowledge_base_preserved": keep_knowledge_base,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }
        return {
            "success": False,
            "error": "Agent not initialized or reset not available",
        }


# Global instance
_teachable_agent_service = None


def get_autogen_teachable_agent_service(
    model: str = None,
    api_key: str = None,
) -> Optional[AutoGenTeachableAgentService]:
    """
    Get global teachable agent service instance.

    Args:
        model: LLM model to use (default: gpt-4)
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

    Returns:
        TeachableAgentService instance or None if AutoGen not available
    """
    global _teachable_agent_service

    if not TEACHABLE_AVAILABLE:
        logger.warning("AutoGen not available. Install with: pip install 'pyautogen==0.2.18'")
        return None

    if _teachable_agent_service is None:
        try:
            _teachable_agent_service = AutoGenTeachableAgentService(
                model=model or "gpt-4",
                api_key=api_key,
            )
        except Exception as e:
            logger.error(f"Failed to initialize teachable agent service: {e}")
            return None

    return _teachable_agent_service
