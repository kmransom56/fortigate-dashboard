"""
PowerInfer Client - Fast LLM inference with TurboSparse models
Uses activation sparsity for 2-5x speedup on consumer hardware
"""

import requests
import json
import subprocess
import os
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PowerInferClient:
    """Client for PowerInfer inference engine with TurboSparse models"""
    
    def __init__(self, 
                 powerinfer_path: Optional[str] = None,
                 model_path: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Initialize PowerInfer client
        
        Args:
            powerinfer_path: Path to PowerInfer executable (auto-detected if None)
            model_path: Path to TurboSparse model (auto-detected if None)
            base_url: API base URL if PowerInfer is running as a service
        """
        self.powerinfer_path = powerinfer_path or self._detect_powerinfer()
        self.model_path = model_path or self._detect_model()
        self.base_url = base_url
        self.process = None
    
    def _detect_powerinfer(self) -> Optional[str]:
        """Auto-detect PowerInfer installation"""
        # Common installation paths
        possible_paths = [
            "/usr/local/bin/powerinfer",
            "/opt/powerinfer/powerinfer",
            os.path.expanduser("~/powerinfer/powerinfer"),
            os.path.expanduser("~/PowerInfer/powerinfer"),
            "powerinfer",  # In PATH
        ]
        
        for path in possible_paths:
            if path == "powerinfer":
                # Check if in PATH
                result = subprocess.run(["which", "powerinfer"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            elif os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def _detect_model(self) -> Optional[str]:
        """Auto-detect TurboSparse model"""
        # Common model locations
        possible_locations = [
            os.path.expanduser("~/models/TurboSparse-Mistral-7B"),
            os.path.expanduser("~/models/TurboSparse-Mixtral-47B"),
            os.path.expanduser("~/models/turboSparse-mistral-7b"),
            os.path.expanduser("~/models/turboSparse-mixtral-47b"),
            "/models/TurboSparse-Mistral-7B",
            "/models/TurboSparse-Mixtral-47B",
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                # Check for model files
                if any(os.path.exists(os.path.join(location, f)) 
                      for f in ["model.bin", "ggml-model.bin", "model.gguf"]):
                    return location
        
        return None
    
    def is_available(self) -> bool:
        """Check if PowerInfer is available"""
        # Check if running as API service
        if self.base_url:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                return response.status_code == 200
            except:
                pass
        
        # Check if executable exists
        if self.powerinfer_path:
            if os.path.exists(self.powerinfer_path):
                # Check if it's a valid binary (even if filesystem doesn't support execute bit)
                try:
                    import subprocess
                    result = subprocess.run(
                        ["file", self.powerinfer_path],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    # If file command shows it's an executable, it's available
                    if "ELF" in result.stdout or "executable" in result.stdout.lower():
                        return True
                except:
                    pass
                # Fallback: just check if file exists (for filesystems without execute bit)
                return True
        return False
    
    def chat(self, message: str, system_prompt: Optional[str] = None,
             model: Optional[str] = None) -> Optional[str]:
        """
        Send a chat message to PowerInfer
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            model: Model to use (uses default if None)
            
        Returns:
            Response text or None if failed
        """
        # If base_url is set, use API mode
        if self.base_url:
            return self._chat_api(message, system_prompt, model)
        
        # Otherwise use direct execution
        return self._chat_direct(message, system_prompt, model)
    
    def _chat_api(self, message: str, system_prompt: Optional[str] = None,
                  model: Optional[str] = None) -> Optional[str]:
        """Chat via PowerInfer API"""
        try:
            payload = {
                "prompt": message,
                "model": model or self.model_path,
            }
            
            if system_prompt:
                payload["system_prompt"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            
            logger.error(f"PowerInfer API error: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error calling PowerInfer API: {e}")
            return None
    
    def _chat_direct(self, message: str, system_prompt: Optional[str] = None,
                    model: Optional[str] = None) -> Optional[str]:
        """Chat via direct PowerInfer execution"""
        if not self.powerinfer_path or not self.is_available():
            logger.error("PowerInfer not available")
            return None
        
        model = model or self.model_path
        if not model:
            logger.error("No model specified")
            return None
        
        try:
            # Build prompt
            full_prompt = message
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{message}"
            
            # Run PowerInfer
            cmd = [
                self.powerinfer_path,
                "-m", model,
                "-p", full_prompt,
                "--n-predict", "512",  # Limit response length
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Parse output (PowerInfer outputs to stdout)
                return result.stdout.strip()
            else:
                logger.error(f"PowerInfer error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("PowerInfer timeout")
            return None
        except Exception as e:
            logger.error(f"Error running PowerInfer: {e}")
            return None
    
    def list_models(self) -> List[str]:
        """List available TurboSparse models"""
        models = []
        
        # Check common model directories
        model_dirs = [
            os.path.expanduser("~/models"),
            "/models",
            "/opt/models",
        ]
        
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                for item in os.listdir(model_dir):
                    if "turbosparse" in item.lower() or "turbo" in item.lower():
                        full_path = os.path.join(model_dir, item)
                        if os.path.isdir(full_path):
                            models.append(full_path)
        
        return models


class PowerInferOllamaWrapper:
    """
    Wrapper to use PowerInfer models via Ollama (if PowerInfer models are loaded in Ollama)
    This allows using TurboSparse models through Ollama's API
    """
    
    def __init__(self, ollama_base_url: str = None):
        """Initialize wrapper using Ollama API"""
        if ollama_base_url is None:
            # Try to detect Ollama port
            for port in [11435, 11434]:
                try:
                    test_url = f"http://localhost:{port}/api/tags"
                    response = requests.get(test_url, timeout=1)
                    if response.status_code == 200:
                        ollama_base_url = f"http://localhost:{port}"
                        break
                except:
                    continue
        
        self.base_url = ollama_base_url or "http://localhost:11434"
        self.turbosparse_models = []
        self._detect_turbosparse_models()
    
    def _detect_turbosparse_models(self):
        """Detect TurboSparse models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    name = model.get("name", "").lower()
                    if "turbosparse" in name or "turbo" in name:
                        self.turbosparse_models.append(model.get("name"))
        except:
            pass
    
    def is_available(self) -> bool:
        """Check if TurboSparse models are available via Ollama"""
        return len(self.turbosparse_models) > 0
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Chat using TurboSparse model via Ollama"""
        if not self.turbosparse_models:
            return None
        
        # Use first available TurboSparse model
        model = self.turbosparse_models[0]
        
        try:
            payload = {
                "model": model,
                "messages": []
            }
            
            if system_prompt:
                payload["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            payload["messages"].append({
                "role": "user",
                "content": message
            })
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    return result["message"].get("content", "")
            
            return None
        except Exception as e:
            logger.error(f"Error calling Ollama with TurboSparse: {e}")
            return None
