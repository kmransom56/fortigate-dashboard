"""
Configuration Management for AI Assistant

Provides easy configuration loading and backend selection.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from .agent_framework_wrapper import AgentBackend
except ImportError:
    # Fallback for standalone usage
    from enum import Enum
    class AgentBackend(Enum):
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        AUTOGEN = "autogen"
        MAGENTIC_ONE = "magentic_one"
        DOCKER_CAGENT = "docker_cagent"
        OLLAMA = "ollama"  # Local Ollama with LLM/CodeLLaMA
        POWERINFER = "powerinfer"  # PowerInfer with TurboSparse (fast inference)


class AIConfig:
    """Configuration manager for AI Assistant"""
    
    DEFAULT_CONFIG_FILE = Path.home() / ".network_observability_ai_config.json"
    
    # Default backend priority order (PowerInfer/Ollama first for local, no API keys needed)
    BACKEND_PRIORITY = [
        AgentBackend.POWERINFER,  # Fastest local inference (TurboSparse models)
        AgentBackend.OLLAMA,  # Local, no API keys needed
        AgentBackend.OPENAI,
        AgentBackend.ANTHROPIC,
        AgentBackend.AUTOGEN,
        AgentBackend.MAGENTIC_ONE,
        AgentBackend.DOCKER_CAGENT,
    ]
    
    @staticmethod
    def load_config(config_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file"""
        if config_file is None:
            config_file = AIConfig.DEFAULT_CONFIG_FILE
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_file: Optional[Path] = None):
        """Save configuration to file"""
        if config_file is None:
            config_file = AIConfig.DEFAULT_CONFIG_FILE
        
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    @staticmethod
    def detect_backend() -> Optional[AgentBackend]:
        """Auto-detect available backend from environment variables and local services"""
        # First check for PowerInfer (fastest, no API keys needed)
        if AIConfig._check_powerinfer_available():
            return AgentBackend.POWERINFER
        
        # Then check for local Ollama (no API keys needed)
        if AIConfig._check_ollama_available():
            return AgentBackend.OLLAMA
        
        # Check for API keys in environment
        if os.getenv("OPENAI_API_KEY"):
            return AgentBackend.OPENAI
        elif os.getenv("ANTHROPIC_API_KEY"):
            return AgentBackend.ANTHROPIC
        elif os.getenv("AUTOGEN_API_KEY"):
            return AgentBackend.AUTOGEN
        elif os.getenv("MAGENTIC_ONE_API_KEY"):
            return AgentBackend.MAGENTIC_ONE
        
        # Check config file
        config = AIConfig.load_config()
        if config.get("backend"):
            try:
                return AgentBackend(config["backend"])
            except ValueError:
                pass
        
        # Default to PowerInfer if available, then Ollama, otherwise OpenAI
        if AIConfig._check_powerinfer_available():
            return AgentBackend.POWERINFER
        if AIConfig._check_ollama_available():
            return AgentBackend.OLLAMA
        return AgentBackend.OPENAI
    
    @staticmethod
    def _check_powerinfer_available() -> bool:
        """Check if PowerInfer is available"""
        try:
            from .powerinfer_client import PowerInferClient, PowerInferOllamaWrapper
            
            # Check for direct PowerInfer installation
            client = PowerInferClient()
            if client.is_available():
                return True
            
            # Check for TurboSparse models via Ollama
            wrapper = PowerInferOllamaWrapper()
            if wrapper.is_available():
                return True
        except ImportError:
            pass
        except Exception:
            pass
        return False
    
    @staticmethod
    def _check_ollama_available() -> bool:
        """Check if Ollama is available and running"""
        try:
            import requests
            # Try common Ollama ports (11434 default, 11435 common alternative)
            for port in [11435, 11434]:
                try:
                    response = requests.get(f"http://localhost:{port}/api/tags", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        # If any models are available, Ollama is working
                        if models:
                            return True
                        # Even if no models, if API responds, Ollama is running
                        return True
                except requests.exceptions.ConnectionError:
                    continue
        except Exception:
            pass
        return False
    
    @staticmethod
    def get_backend_config() -> Dict[str, Any]:
        """Get backend-specific configuration"""
        config = AIConfig.load_config()
        return config.get("backend_config", {})
    
    @staticmethod
    def set_backend(backend: AgentBackend, config_file: Optional[Path] = None):
        """Set preferred backend in configuration"""
        config = AIConfig.load_config(config_file)
        config["backend"] = backend.value
        AIConfig.save_config(config, config_file)
    
    @staticmethod
    def list_available_backends() -> list:
        """List backends with available API keys or local services"""
        available = []
        for backend in AIConfig.BACKEND_PRIORITY:
            # Check PowerInfer separately (no API key needed)
            if backend == AgentBackend.POWERINFER:
                if AIConfig._check_powerinfer_available():
                    available.append(backend)
                continue
            
            # Check Ollama separately (no API key needed)
            if backend == AgentBackend.OLLAMA:
                if AIConfig._check_ollama_available():
                    available.append(backend)
                continue
            
            # Check other backends for API keys
            env_var = {
                AgentBackend.OPENAI: "OPENAI_API_KEY",
                AgentBackend.ANTHROPIC: "ANTHROPIC_API_KEY",
                AgentBackend.AUTOGEN: "AUTOGEN_API_KEY",
                AgentBackend.MAGENTIC_ONE: "MAGENTIC_ONE_API_KEY",
                AgentBackend.DOCKER_CAGENT: "DOCKER_CAGENT_API_KEY",
            }.get(backend)
            
            if env_var and os.getenv(env_var):
                available.append(backend)
        
        return available
