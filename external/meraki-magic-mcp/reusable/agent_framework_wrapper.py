"""
Agent Framework Wrapper - Reusable AI Agent Framework

A reusable wrapper around the agent framework that can be easily integrated
into other applications.

Usage:
    from reusable.agent_framework_wrapper import AgentFrameworkWrapper, AgentBackend
    
    # Initialize with backend
    agent = AgentFrameworkWrapper(
        backend=AgentBackend.OPENAI,
        api_key_manager=key_manager  # Your SecureKeyManager instance
    )
    
    # Use the agent
    response = agent.chat("Analyze this code for bugs...")
"""

import os
import sys
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from enum import Enum
import logging

# Add parent directory to path to import agents module
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from agents.agent_framework import AgentFramework, AgentBackend as OriginalAgentBackend
except ImportError:
    # Fallback if agents module not available
    AgentFramework = None
    OriginalAgentBackend = None

# Import SecureKeyManager (always available in this package)
try:
    from .secure_key_manager import SecureKeyManager
except ImportError:
    # Fallback for standalone usage
    try:
        from secure_key_manager import SecureKeyManager
    except ImportError:
        # For type hints only
        SecureKeyManager = None

# Import direct client libraries (fallback when agents module missing)
try:
    from openai import OpenAI as OpenAIClient
except ImportError:
    OpenAIClient = None

try:
    from anthropic import Anthropic as AnthropicClient
except ImportError:
    AnthropicClient = None

logger = logging.getLogger(__name__)


class AgentBackend(Enum):
    """Supported agent backends"""
    AUTOGEN = "autogen"
    MAGENTIC_ONE = "magentic_one"
    DOCKER_CAGENT = "docker_cagent"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"  # Local Ollama with LLM/CodeLLaMA
    POWERINFER = "powerinfer"  # PowerInfer with TurboSparse models (fast inference)


class AgentFrameworkWrapper:
    """
    Wrapper around the agent framework for easy reuse in other applications.
    
    This wrapper provides a simplified interface to the agent framework
    and integrates with SecureKeyManager for API key management.
    """
    
    def __init__(self, backend: AgentBackend = AgentBackend.OPENAI,
                 api_key_manager: Optional['SecureKeyManager'] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent framework wrapper.
        
        Args:
            backend: The agent backend to use
            api_key_manager: SecureKeyManager instance for API key management
            config: Additional configuration for the agent
        """
        self.backend = backend
        self.api_key_manager = api_key_manager
        self.config = config or {}
        self.agent_framework = None
        self.ollama_client = None  # For Ollama backend
        self.ollama_client = None  # For Ollama backend
        self.powerinfer_client = None  # For PowerInfer backend
        self.direct_client = None # Fallback direct client
        
        # Handle PowerInfer separately (fastest local inference, no API keys needed)
        if backend == AgentBackend.POWERINFER:
            try:
                from .powerinfer_client import PowerInferClient, PowerInferOllamaWrapper
                
                # Try direct PowerInfer first
                self.powerinfer_client = PowerInferClient(
                    powerinfer_path=self.config.get("powerinfer_path"),
                    model_path=self.config.get("powerinfer_model_path"),
                    base_url=self.config.get("powerinfer_base_url")
                )
                
                # If direct PowerInfer not available, try via Ollama
                if not self.powerinfer_client.is_available():
                    wrapper = PowerInferOllamaWrapper(
                        ollama_base_url=self.config.get("ollama_base_url")
                    )
                    if wrapper.is_available():
                        # Use Ollama wrapper for TurboSparse models
                        self.powerinfer_client = wrapper
                        logger.info(f"PowerInfer via Ollama with models: {wrapper.turbosparse_models}")
                    else:
                        logger.warning("PowerInfer not available (executable not found and no TurboSparse models in Ollama)")
                        self.powerinfer_client = None
                        self.agent_framework = None
                else:
                    logger.info(f"PowerInfer initialized with model: {self.powerinfer_client.model_path}")
                    self.agent_framework = "powerinfer"  # Mark as available
            except ImportError:
                logger.error("PowerInfer client not available")
                self.powerinfer_client = None
                self.agent_framework = None
            except Exception as e:
                logger.error(f"Failed to initialize PowerInfer: {e}")
                self.powerinfer_client = None
                self.agent_framework = None
        
        # Handle Ollama separately (local, no API keys needed)
        elif backend == AgentBackend.OLLAMA:
            try:
                from .ollama_client import OllamaClient
                # Auto-detect Ollama port (tries 11435, then 11434)
                ollama_url = self.config.get("ollama_base_url")  # None = auto-detect
                self.ollama_client = OllamaClient(
                    base_url=ollama_url,
                    model=self.config.get("ollama_model")
                )
                if self.ollama_client.is_available():
                    logger.info(f"Ollama initialized with model: {self.ollama_client.model} at {self.ollama_client.base_url}")
                    self.agent_framework = "ollama"  # Mark as available
                else:
                    logger.warning("Ollama is not available (server not running?)")
                    self.ollama_client = None
                    self.agent_framework = None
            except ImportError:
                logger.error("Ollama client not available")
                self.ollama_client = None
                self.agent_framework = None
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                self.ollama_client = None
                self.agent_framework = None
        else:
            # Map our backend enum to the original
            if OriginalAgentBackend:
                backend_map = {
                    AgentBackend.AUTOGEN: OriginalAgentBackend.AUTOGEN,
                    AgentBackend.MAGENTIC_ONE: OriginalAgentBackend.MAGENTIC_ONE,
                    AgentBackend.DOCKER_CAGENT: OriginalAgentBackend.DOCKER_CAGENT,
                    AgentBackend.OPENAI: OriginalAgentBackend.OPENAI,
                    AgentBackend.ANTHROPIC: OriginalAgentBackend.ANTHROPIC,
                }
                original_backend = backend_map.get(backend, OriginalAgentBackend.OPENAI)
            else:
                original_backend = None
            
            # Set up API keys from key manager
            self._setup_api_keys()
            
            # Initialize the agent framework
            if AgentFramework and original_backend:
                try:
                    self.agent_framework = AgentFramework(original_backend, self.config)
                except Exception as e:
                    logger.error(f"Failed to initialize agent framework: {e}")
                    self.agent_framework = None
            
            # Fallback: Initialize direct clients if framework failed
            if not self.agent_framework and not AgentFramework:
                logger.info(f"Attempting fallback initialization. Backend: {backend}, OpenAIClient available: {OpenAIClient is not None}")
                if backend == AgentBackend.OPENAI and OpenAIClient:
                    api_key = os.environ.get("OPENAI_API_KEY")
                    logger.info(f"OpenAI API Key present: {bool(api_key)}")
                    if api_key:
                        try:
                            self.direct_client = OpenAIClient(api_key=api_key)
                            self.agent_framework = "direct_openai"
                            logger.info("Initialized direct OpenAI client (fallback)")
                        except Exception as e:
                            logger.error(f"Failed to initialize direct OpenAI client: {e}")
                
                elif backend == AgentBackend.ANTHROPIC and AnthropicClient:
                    api_key = os.environ.get("ANTHROPIC_API_KEY")
                    if api_key:
                        try:
                            self.direct_client = AnthropicClient(api_key=api_key)
                            self.agent_framework = "direct_anthropic"
                            logger.info("Initialized direct Anthropic client (fallback)")
                        except Exception as e:
                            logger.error(f"Failed to initialize direct Anthropic client: {e}")
    
    def _setup_api_keys(self):
        """Set up API keys from the key manager"""
        if not self.api_key_manager:
            return
        
        # Common API key names to check
        api_keys = {
            'OPENAI_API_KEY': 'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        }
        
        for key_name, env_var in api_keys.items():
            api_key = self.api_key_manager.get_key(key_name, env_var_name=env_var)
            if api_key:
                os.environ[env_var] = api_key
                logger.info(f"Set {env_var} from key manager")
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Send a chat message to the agent.
        
        Args:
            message: The user message
            system_prompt: Optional system prompt
            
        Returns:
            Agent response or None if failed
        """
        # Handle PowerInfer separately
        if self.backend == AgentBackend.POWERINFER:
            if not self.powerinfer_client:
                logger.error("PowerInfer client not initialized")
                return None
            try:
                return self.powerinfer_client.chat(message, system_prompt=system_prompt)
            except Exception as e:
                logger.error(f"Error in PowerInfer chat: {e}")
                return None
        
        # Handle Ollama separately
        elif self.backend == AgentBackend.OLLAMA:
            if not self.ollama_client:
                logger.error("Ollama client not initialized")
                return None
            try:
                return self.ollama_client.chat(message, system_prompt=system_prompt)
            except Exception as e:
                logger.error(f"Error in Ollama chat: {e}")
                return None
        
        # Handle other backends
        # Handle other backends
        if not self.agent_framework:
            logger.error("Agent framework not initialized")
            return None
        
        # Handle direct clients (fallback)
        if self.agent_framework == "direct_openai":
            try:
                model = self.config.get("model", "gpt-4o")
                msgs = []
                if system_prompt:
                    msgs.append({"role": "system", "content": system_prompt})
                msgs.append({"role": "user", "content": message})
                
                completion = self.direct_client.chat.completions.create(
                    model=model,
                    messages=msgs
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Error in direct OpenAI chat: {e}")
                return None

        if self.agent_framework == "direct_anthropic":
            try:
                model = self.config.get("model", "claude-3-5-sonnet-20241022")
                # Anthropic system prompt is a top-level parameter
                params = {
                    "model": model,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": message}]
                }
                if system_prompt:
                    params["system"] = system_prompt
                    
                resp = self.direct_client.messages.create(**params)
                return resp.content[0].text
            except Exception as e:
                logger.error(f"Error in direct Anthropic chat: {e}")
                return None

        try:
            return self.agent_framework.chat(message, system_prompt)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return None
    
    def analyze_code(self, code: str, task: str = "analyze") -> Optional[str]:
        """
        Analyze code using the agent.
        
        Args:
            code: The code to analyze
            task: Analysis task (e.g., "analyze", "optimize", "debug")
            
        Returns:
            Analysis result or None if failed
        """
        prompt = f"Please {task} the following code:\n\n```python\n{code}\n```"
        return self.chat(prompt)
    
    def is_available(self) -> bool:
        """Check if the agent framework is available and initialized"""
        if self.backend == AgentBackend.POWERINFER:
            return self.powerinfer_client is not None and self.powerinfer_client.is_available()
        elif self.backend == AgentBackend.OLLAMA:
            return self.ollama_client is not None and self.ollama_client.is_available()
        return self.agent_framework is not None
    
    def get_backend_name(self) -> str:
        """Get the name of the current backend"""
        return self.backend.value
