"""
Cagent Integration Tools
Integration with the 'cagent' local tool for executing specialized agent tasks.

Cagent is a local code generation tool that uses vLLM for zero-cost,
privacy-first agent execution with YAML profile configurations.
"""

import subprocess
import os
import glob
from typing import List, Dict, Any, Optional

# Windows path configuration
CAGENT_HOME = os.path.join(os.path.expanduser("~"), "cagent")
CAGENT_BIN = os.path.join(CAGENT_HOME, "bin", "cagent.exe")
CAGENT_SCRIPT = os.path.join(CAGENT_HOME, "cagent.bat")


class CagentTools:
    """
    Tools for interacting with the local Cagent code generation system.
    
    Cagent enables AI agents to generate code using local LLMs,
    configured via YAML profiles for different agent personalities.
    """
    
    def __init__(self, cagent_home: str = None):
        """
        Initialize CagentTools.
        
        Args:
            cagent_home: Override the default cagent installation path
        """
        self.cagent_home = cagent_home or CAGENT_HOME
        self._validate_installation()
    
    def _validate_installation(self) -> bool:
        """Check if cagent is properly installed."""
        if not os.path.exists(self.cagent_home):
            print(f"⚠️ Cagent home not found: {self.cagent_home}")
            return False
        return True
    
    @staticmethod
    def list_profiles() -> List[Dict[str, Any]]:
        """
        List available cagent YAML profiles.
        
        Returns:
            List of profile info dictionaries with name and path.
        """
        profiles = []
        try:
            # Find all yaml files in cagent home
            patterns = [
                os.path.join(CAGENT_HOME, "*.yaml"),
                os.path.join(CAGENT_HOME, "*.yml"),
                os.path.join(CAGENT_HOME, "profiles", "*.yaml"),
                os.path.join(CAGENT_HOME, "profiles", "*.yml")
            ]
            
            for pattern in patterns:
                for f in glob.glob(pattern):
                    profiles.append({
                        "name": os.path.basename(f),
                        "path": f,
                        "size": os.path.getsize(f)
                    })
                    
        except Exception as e:
            print(f"Error listing profiles: {e}")
        
        return profiles

    @staticmethod
    def get_profile_content(profile_name: str) -> Optional[str]:
        """
        Read the contents of a cagent profile YAML.
        
        Args:
            profile_name: Name of the profile file
            
        Returns:
            Profile YAML content or None if not found.
        """
        profile_path = os.path.join(CAGENT_HOME, profile_name)
        
        # Also check profiles subdirectory
        if not os.path.exists(profile_path):
            profile_path = os.path.join(CAGENT_HOME, "profiles", profile_name)
        
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading profile: {e}"
        
        return None

    @staticmethod
    def run_task(profile: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Run a task using cagent with a specific profile.
        
        Args:
            profile: The YAML config filename (e.g., 'golang_developer.yaml')
            prompt: The instruction for the agent
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with stdout, stderr, and return code.
        """
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "profile": profile,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
        
        # Validate profile existence
        profile_path = os.path.join(CAGENT_HOME, profile)
        if not os.path.exists(profile_path):
            # Check profiles subdirectory
            profile_path = os.path.join(CAGENT_HOME, "profiles", profile)
            if not os.path.exists(profile_path):
                result["stderr"] = f"Error: Profile '{profile}' not found in {CAGENT_HOME}"
                return result

        # Build command - Windows compatible
        if os.path.exists(CAGENT_SCRIPT):
            cmd = [CAGENT_SCRIPT, profile, prompt]
        elif os.path.exists(CAGENT_BIN):
            cmd = [CAGENT_BIN, "run", profile_path, "--prompt", prompt]
        else:
            result["stderr"] = f"Cagent executable not found in {CAGENT_HOME}"
            return result

        try:
            # Run in the cagent directory so relative paths work
            proc_result = subprocess.run(
                cmd, 
                cwd=CAGENT_HOME,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise exception on non-zero
            )
            
            result["stdout"] = proc_result.stdout
            result["stderr"] = proc_result.stderr
            result["return_code"] = proc_result.returncode
            result["success"] = proc_result.returncode == 0
            
        except subprocess.TimeoutExpired:
            result["stderr"] = f"Execution timed out after {timeout}s"
        except Exception as e:
            result["stderr"] = f"Execution failed: {str(e)}"
        
        return result

    @staticmethod
    def create_profile(
        name: str,
        system_prompt: str,
        model: str = "codellama:7b",
        temperature: float = 0.7,
        tools: List[str] = None
    ) -> str:
        """
        Create a new cagent YAML profile.
        
        Args:
            name: Profile name (will be saved as {name}.yaml)
            system_prompt: The system message for the agent
            model: LLM model to use
            temperature: Generation temperature
            tools: List of tool names to include
            
        Returns:
            Path to the created profile.
        """
        import yaml
        
        profile_content = {
            "name": name,
            "model": model,
            "temperature": temperature,
            "system_prompt": system_prompt,
            "tools": tools or [],
            "created_by": "agent_factory"
        }
        
        profiles_dir = os.path.join(CAGENT_HOME, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        
        filepath = os.path.join(profiles_dir, f"{name}.yaml")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(profile_content, f, default_flow_style=False)
        
        print(f"✅ Created profile: {filepath}")
        return filepath


# Pre-defined network-focused profiles
NETWORK_PROFILES = {
    "network_analyst": {
        "system_prompt": "You are a network analyst. Analyze network configurations, topology data, and suggest optimizations.",
        "model": "fortinet-meraki:v4",
        "tools": ["network_diagnostics", "topology_analysis"]
    },
    "code_generator": {
        "system_prompt": "You are a Python code generator specializing in network automation. Generate clean, documented code for network management tasks.",
        "model": "codellama:7b",
        "tools": ["file_operations", "code_execution"]
    }
}


def setup_network_profiles() -> List[str]:
    """
    Create pre-defined network-focused cagent profiles.
    
    Returns:
        List of created profile paths.
    """
    created = []
    for name, config in NETWORK_PROFILES.items():
        path = CagentTools.create_profile(
            name=name,
            system_prompt=config["system_prompt"],
            model=config.get("model", "codellama:7b"),
            tools=config.get("tools", [])
        )
        created.append(path)
    return created
