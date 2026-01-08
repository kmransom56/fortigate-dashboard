"""
Simple AI Assistant Interface

Easy-to-use wrapper for common AI operations.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging

from .secure_key_manager import SecureKeyManager
from .agent_framework_wrapper import AgentFrameworkWrapper, AgentBackend
from .config import AIConfig
from .ai_assistant import AIAssistant

logger = logging.getLogger(__name__)


def get_ai_assistant(app_name: str = "network_observability",
                    backend: Optional[AgentBackend] = None,
                    auto_setup: bool = True) -> Optional[AIAssistant]:
    """
    Get an AI Assistant instance with automatic configuration.
    
    Args:
        app_name: Application name
        backend: Specific backend to use (auto-detected if None)
        auto_setup: Automatically configure if not set up
        
    Returns:
        AIAssistant instance or None if setup fails
    """
    # Auto-detect backend if not specified
    if backend is None:
        backend = AIConfig.detect_backend()
        logger.info(f"Auto-detected backend: {backend.value}")
    
    # Get backend config
    backend_config = AIConfig.get_backend_config()
    
    # Initialize key manager
    key_manager = SecureKeyManager(app_name=app_name)
    
    # Check if API key is available
    api_key_env = {
        AgentBackend.OPENAI: "OPENAI_API_KEY",
        AgentBackend.ANTHROPIC: "ANTHROPIC_API_KEY",
        AgentBackend.AUTOGEN: "AUTOGEN_API_KEY",
        AgentBackend.MAGENTIC_ONE: "MAGENTIC_ONE_API_KEY",
    }.get(backend)
    
    if api_key_env:
        api_key = key_manager.get_key(
            f"{backend.value}_api_key",
            env_var_name=api_key_env
        )
        
        if not api_key and auto_setup:
            print(f"\n⚠️  No API key found for {backend.value}")
            print(f"Please set {api_key_env} environment variable or provide API key:")
            api_key_input = input(f"Enter {backend.value} API key (or press Enter to skip): ").strip()
            if api_key_input:
                key_manager.save_key(
                    f"{backend.value}_api_key",
                    api_key_input,
                    env_var_name=api_key_env
                )
                print(f"✓ API key saved")
            else:
                print("Skipping API key setup. You can set it later.")
                return None
    
    # Create assistant
    try:
        assistant = AIAssistant(
            app_name=app_name,
            backend=backend,
            config=backend_config
        )
        
        if assistant.agent.is_available():
            return assistant
        else:
            logger.warning(f"Backend {backend.value} not available")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize assistant: {e}")
        return None


def audit_file(file_path: str, audit_type: str = "code") -> Dict[str, Any]:
    """
    Simple function to audit a file.
    
    Usage:
        result = audit_file("app/main.py", audit_type="security")
    """
    assistant = get_ai_assistant()
    if not assistant:
        return {"error": "AI Assistant not available. Configure API keys first."}
    return assistant.audit(file_path, audit_type)


def repair_code(issue: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to repair code issues.
    
    Usage:
        result = repair_code("Function is too slow", file_path="app/main.py")
    """
    assistant = get_ai_assistant()
    if not assistant:
        return {"error": "AI Assistant not available. Configure API keys first."}
    return assistant.repair(issue, file_path)


def optimize_code(file_path: str, opt_type: str = "performance") -> Dict[str, Any]:
    """
    Simple function to optimize code.
    
    Usage:
        result = optimize_code("app/main.py", opt_type="performance")
    """
    assistant = get_ai_assistant()
    if not assistant:
        return {"error": "AI Assistant not available. Configure API keys first."}
    return assistant.optimize(file_path, opt_type)


def learn_from_codebase(source: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to learn from codebase.
    
    Usage:
        result = learn_from_codebase("app/", topic="architecture")
    """
    assistant = get_ai_assistant()
    if not assistant:
        return {"error": "AI Assistant not available. Configure API keys first."}
    return assistant.learn(source, topic)


def update_dependencies(requirements_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to update dependencies.
    
    Usage:
        result = update_dependencies("requirements.txt")
    """
    assistant = get_ai_assistant()
    if not assistant:
        return {"error": "AI Assistant not available. Configure API keys first."}
    return assistant.update("dependencies", requirements_file)


def configure_backend(backend_name: str = None):
    """
    Interactive backend configuration.
    
    Usage:
        configure_backend()  # Interactive
        configure_backend("openai")  # Direct
    """
    if backend_name:
        try:
            backend = AgentBackend(backend_name.lower())
            AIConfig.set_backend(backend)
            print(f"✓ Backend set to: {backend.value}")
            return
        except ValueError:
            print(f"Invalid backend: {backend_name}")
            return
    
    # Interactive mode
    print("\n=== AI Backend Configuration ===")
    print("\nAvailable backends:")
    for i, backend in enumerate(AIConfig.BACKEND_PRIORITY, 1):
        env_var = {
            AgentBackend.OPENAI: "OPENAI_API_KEY",
            AgentBackend.ANTHROPIC: "ANTHROPIC_API_KEY",
            AgentBackend.AUTOGEN: "AUTOGEN_API_KEY",
            AgentBackend.MAGENTIC_ONE: "MAGENTIC_ONE_API_KEY",
        }.get(backend, None)
        
        available = "✓" if env_var and os.getenv(env_var) else " "
        print(f"  {i}. {available} {backend.value}")
    
    print("\nCurrent backend:", AIConfig.detect_backend().value)
    
    choice = input("\nSelect backend (1-5) or press Enter to keep current: ").strip()
    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(AIConfig.BACKEND_PRIORITY):
                backend = AIConfig.BACKEND_PRIORITY[idx]
                AIConfig.set_backend(backend)
                print(f"✓ Backend set to: {backend.value}")
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m reusable.simple_ai configure  # Configure backend")
        print("  python -m reusable.simple_ai audit <file>  # Audit file")
        print("  python -m reusable.simple_ai repair <issue> [file]  # Repair issue")
        print("  python -m reusable.simple_ai optimize <file>  # Optimize file")
        print("  python -m reusable.simple_ai learn <source>  # Learn from source")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "configure":
        configure_backend()
    elif command == "audit":
        if len(sys.argv) < 3:
            print("Usage: audit <file> [type]")
            sys.exit(1)
        result = audit_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "code")
        print(result.get("findings", result.get("error", "No results")))
    elif command == "repair":
        if len(sys.argv) < 3:
            print("Usage: repair <issue> [file]")
            sys.exit(1)
        result = repair_code(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(result.get("fix", result.get("error", "No results")))
    elif command == "optimize":
        if len(sys.argv) < 3:
            print("Usage: optimize <file> [type]")
            sys.exit(1)
        result = optimize_code(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "performance")
        print(result.get("recommendations", result.get("error", "No results")))
    elif command == "learn":
        if len(sys.argv) < 3:
            print("Usage: learn <source> [topic]")
            sys.exit(1)
        result = learn_from_codebase(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(result.get("knowledge", result.get("error", "No results")))
    else:
        print(f"Unknown command: {command}")
