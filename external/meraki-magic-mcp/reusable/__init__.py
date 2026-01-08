"""
Reusable Components Package

This package provides reusable components for API key management and AI agent frameworks
that can be easily integrated into other applications.

Modules:
    - secure_key_manager: Secure API key storage and retrieval
    - agent_framework_wrapper: Multi-backend AI agent framework
    - ai_assistant: AI-assisted audit, repair, update, optimize, and learn functions
    - powerinfer: PowerInfer & TurboSparse support (fast local inference, 2-5× speedup)
    - ollama_client: Ollama local LLM support

Quick Start:
    from reusable.simple_ai import get_ai_assistant
    
    # Auto-detects best backend (PowerInfer > Ollama > Cloud APIs)
    assistant = get_ai_assistant(app_name="my_app")
    
    # Use AI features (automatically uses PowerInfer if available)
    result = assistant.audit("code.py", "security")
    result = assistant.repair("bug_description", "file.py")
"""

from .secure_key_manager import SecureKeyManager
from .agent_framework_wrapper import AgentFrameworkWrapper, AgentBackend
from .ai_assistant import AIAssistant
from .config import AIConfig
from .simple_ai import (
    get_ai_assistant,
    audit_file,
    repair_code,
    optimize_code,
    learn_from_codebase,
    update_dependencies,
    configure_backend
)

# Export PowerInfer & TurboSparse components
try:
    from .powerinfer_client import PowerInferClient, PowerInferOllamaWrapper
    from .powerinfer import (
        is_powerinfer_available,
        get_powerinfer_client,
        list_turbosparse_models,
        get_powerinfer_info
    )
    __all__ = [
        'SecureKeyManager',
        'AgentFrameworkWrapper',
        'AgentBackend',
        'AIAssistant',
        'AIConfig',
        'get_ai_assistant',
        'audit_file',
        'repair_code',
        'optimize_code',
        'learn_from_codebase',
        'update_dependencies',
        'configure_backend',
        'PowerInferClient',
        'PowerInferOllamaWrapper',
        'is_powerinfer_available',
        'get_powerinfer_client',
        'list_turbosparse_models',
        'get_powerinfer_info',
    ]
except ImportError:
    __all__ = [
        'SecureKeyManager',
        'AgentFrameworkWrapper',
        'AgentBackend',
        'AIAssistant',
        'AIConfig',
        'get_ai_assistant',
        'audit_file',
        'repair_code',
        'optimize_code',
        'learn_from_codebase',
        'update_dependencies',
        'configure_backend',
    ]

__version__ = '1.3.0'  # Updated for PowerInfer support
