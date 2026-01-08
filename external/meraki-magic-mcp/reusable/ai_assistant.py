"""
AI-Assisted Application Assistant

Provides AI-powered functions for:
- Audit: Analyze code, configuration, and system state
- Repair: Fix issues and errors automatically
- Update: Update code and dependencies
- Optimize: Improve performance and efficiency
- Learn: Build knowledge base from codebase and documentation
"""

import os
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from secure_key_manager import SecureKeyManager
from agent_framework_wrapper import AgentFrameworkWrapper, AgentBackend

logger = logging.getLogger(__name__)


class AIAssistant:
    """
    AI-Assisted Application Assistant
    
    Provides high-level functions for audit, repair, update, optimize, and learn operations.
    """
    
    def __init__(self, app_name: str = "network_observability",
                 backend: AgentBackend = AgentBackend.OPENAI,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Assistant.
        
        Args:
            app_name: Application name for key management
            backend: AI backend to use
            config: Additional configuration
        """
        self.app_name = app_name
        self.key_manager = SecureKeyManager(app_name=app_name)
        self.agent = AgentFrameworkWrapper(
            backend=backend,
            api_key_manager=self.key_manager,
            config=config
        )
        self.knowledge_base_path = Path.home() / f".{app_name}_knowledge_base.json"
    
    def audit(self, target: str, audit_type: str = "code") -> Dict[str, Any]:
        """
        Audit code, configuration, or system state.
        
        Args:
            target: Path to file/directory or configuration to audit
            audit_type: Type of audit (code, config, security, performance, dependencies)
            
        Returns:
            Audit results dictionary
        """
        if not self.agent.is_available():
            return {"error": "Agent framework not available"}
        
        # Read target content
        if os.path.isfile(target):
            with open(target, 'r') as f:
                content = f.read()
        elif os.path.isdir(target):
            # Analyze directory structure
            content = self._analyze_directory(target)
        else:
            return {"error": f"Target not found: {target}"}
        
        # Build audit prompt based on type
        prompts = {
            "code": f"Audit the following code for bugs, security issues, best practices, and improvements:\n\n{content}",
            "config": f"Audit the following configuration for errors, security issues, and best practices:\n\n{content}",
            "security": f"Perform a security audit of the following code/configuration:\n\n{content}",
            "performance": f"Analyze the following code for performance issues and optimization opportunities:\n\n{content}",
            "dependencies": f"Review dependencies and suggest updates or security patches:\n\n{content}"
        }
        
        prompt = prompts.get(audit_type, prompts["code"])
        
        try:
            response = self.agent.chat(
                prompt,
                system_prompt="You are an expert code auditor. Provide detailed, actionable feedback."
            )
            
            return {
                "target": target,
                "audit_type": audit_type,
                "status": "success",
                "findings": response,
                "recommendations": self._extract_recommendations(response)
            }
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {"error": str(e)}
    
    def repair(self, issue_description: str, code_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Repair issues in code or configuration.
        
        Args:
            issue_description: Description of the issue to fix
            code_path: Path to code file to repair (optional)
            
        Returns:
            Repair results with suggested fixes
        """
        if not self.agent.is_available():
            return {"error": "Agent framework not available"}
        
        code_content = ""
        if code_path and os.path.exists(code_path):
            with open(code_path, 'r') as f:
                code_content = f.read()
        

        code_section = ""
        if code_content:
            code_section = f"Code to repair:\n```python\n{code_content}\n```"

        prompt = f"""
        Issue to fix: {issue_description}
        
        {code_section}
        
        Please provide:
        1. Root cause analysis
        2. Step-by-step fix
        3. Corrected code (if applicable)
        4. Testing recommendations
        """
        
        try:
            response = self.agent.chat(
                prompt,
                system_prompt="You are an expert software engineer. Provide clear, tested solutions."
            )
            
            return {
                "issue": issue_description,
                "code_path": code_path,
                "status": "success",
                "fix": response,
                "suggested_changes": self._extract_code_changes(response)
            }
        except Exception as e:
            logger.error(f"Repair failed: {e}")
            return {"error": str(e)}
    
    def update(self, update_type: str = "dependencies", target: Optional[str] = None) -> Dict[str, Any]:
        """
        Update code, dependencies, or configuration.
        
        Args:
            update_type: Type of update (dependencies, code, config, api)
            target: Specific target to update (optional)
            
        Returns:
            Update recommendations and changes
        """
        if not self.agent.is_available():
            return {"error": "Agent framework not available"}
        
        prompts = {
            "dependencies": "Analyze current dependencies and suggest updates for security patches, bug fixes, and new features. Consider compatibility.",
            "code": "Review code for deprecated patterns and suggest modern alternatives.",
            "config": "Review configuration for outdated settings and suggest updates.",
            "api": "Review API usage and suggest updates for breaking changes or new features."
        }
        
        prompt = prompts.get(update_type, prompts["dependencies"])
        
        if target and os.path.exists(target):
            with open(target, 'r') as f:
                content = f.read()
            prompt += f"\n\nTarget file:\n{content}"
        
        try:
            response = self.agent.chat(
                prompt,
                system_prompt="You are an expert in software maintenance and updates."
            )
            
            return {
                "update_type": update_type,
                "target": target,
                "status": "success",
                "recommendations": response,
                "action_items": self._extract_action_items(response)
            }
        except Exception as e:
            logger.error(f"Update analysis failed: {e}")
            return {"error": str(e)}
    
    def optimize(self, target: str, optimization_type: str = "performance") -> Dict[str, Any]:
        """
        Optimize code, configuration, or system.
        
        Args:
            target: Path to code/configuration to optimize
            optimization_type: Type of optimization (performance, memory, security, cost)
            
        Returns:
            Optimization recommendations
        """
        if not self.agent.is_available():
            return {"error": "Agent framework not available"}
        
        if not os.path.exists(target):
            return {"error": f"Target not found: {target}"}
        
        with open(target, 'r') as f:
            content = f.read()
        
        prompts = {
            "performance": f"Analyze and optimize the following code for performance:\n\n{content}",
            "memory": f"Analyze and optimize the following code for memory usage:\n\n{content}",
            "security": f"Analyze and optimize the following code for security:\n\n{content}",
            "cost": f"Analyze and optimize the following code for cost efficiency:\n\n{content}"
        }
        
        prompt = prompts.get(optimization_type, prompts["performance"])
        
        try:
            response = self.agent.chat(
                prompt,
                system_prompt="You are an expert in software optimization. Provide specific, measurable improvements."
            )
            
            return {
                "target": target,
                "optimization_type": optimization_type,
                "status": "success",
                "recommendations": response,
                "expected_improvements": self._extract_improvements(response)
            }
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {"error": str(e)}
    
    def learn(self, source: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Learn from codebase, documentation, or examples.
        
        Args:
            source: Path to code/documentation or topic to learn about
            topic: Specific topic to focus on (optional)
            
        Returns:
            Learned knowledge and insights
        """
        if not self.agent.is_available():
            return {"error": "Agent framework not available"}
        
        # Read source content
        if os.path.exists(source):
            if os.path.isfile(source):
                with open(source, 'r') as f:
                    content = f.read()
            elif os.path.isdir(source):
                content = self._analyze_directory(source)
            else:
                content = source  # Treat as text input
        else:
            content = source  # Treat as topic/query
        
        prompt = f"""
        Learn and extract knowledge from the following:
        
        {content}
        
        {f"Focus on: {topic}" if topic else ""}
        
        Please provide:
        1. Key concepts and patterns
        2. Architecture insights
        3. Best practices identified
        4. Potential improvements
        5. Documentation suggestions
        """
        
        try:
            response = self.agent.chat(
                prompt,
                system_prompt="You are a knowledge extraction expert. Identify patterns, insights, and best practices."
            )
            
            # Store in knowledge base
            knowledge = {
                "source": source,
                "topic": topic,
                "insights": response,
                "timestamp": str(Path(source).stat().st_mtime) if os.path.exists(source) else None
            }
            
            self._save_to_knowledge_base(knowledge)
            
            return {
                "source": source,
                "topic": topic,
                "status": "success",
                "knowledge": response,
                "stored": True
            }
        except Exception as e:
            logger.error(f"Learning failed: {e}")
            return {"error": str(e)}
    
    def _analyze_directory(self, directory: str) -> str:
        """Analyze directory structure and key files"""
        try:
            files = []
            for root, dirs, filenames in os.walk(directory):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, directory)
                    files.append(rel_path)
            
            return f"Directory structure:\n" + "\n".join(files[:50])  # Limit to 50 files
        except Exception as e:
            logger.error(f"Directory analysis failed: {e}")
            return f"Error analyzing directory: {e}"
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        # Simple extraction - can be enhanced with NLP
        recommendations = []
        for line in response.split('\n'):
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                recommendations.append(line.strip())
        return recommendations
    
    def _extract_code_changes(self, response: str) -> Dict[str, str]:
        """Extract code changes from response"""
        # Look for code blocks
        changes = {}
        in_code_block = False
        current_code = []
        current_lang = None
        
        for line in response.split('\n'):
            if line.strip().startswith('```'):
                if in_code_block:
                    if current_lang:
                        changes[current_lang] = '\n'.join(current_code)
                    current_code = []
                    current_lang = None
                else:
                    current_lang = line.strip()[3:].strip() or 'python'
                in_code_block = not in_code_block
            elif in_code_block:
                current_code.append(line)
        
        return changes
    
    def _extract_action_items(self, response: str) -> List[str]:
        """Extract action items from response"""
        action_items = []
        for line in response.split('\n'):
            if any(keyword in line.lower() for keyword in ['update', 'change', 'replace', 'install', 'upgrade']):
                if line.strip().startswith('-') or line.strip()[0].isdigit():
                    action_items.append(line.strip())
        return action_items
    
    def _extract_improvements(self, response: str) -> Dict[str, str]:
        """Extract expected improvements from response"""
        improvements = {}
        for line in response.split('\n'):
            if any(keyword in line.lower() for keyword in ['improve', 'reduce', 'increase', 'optimize']):
                improvements[line[:50]] = line
        return improvements
    
    def _save_to_knowledge_base(self, knowledge: Dict[str, Any]):
        """Save learned knowledge to persistent storage"""
        import json
        try:
            # Load existing knowledge base
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, 'r') as f:
                    kb = json.load(f)
            else:
                kb = {"entries": []}
            
            # Add new entry
            kb["entries"].append(knowledge)
            
            # Keep only last 100 entries
            if len(kb["entries"]) > 100:
                kb["entries"] = kb["entries"][-100:]
            
            # Save
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(kb, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save to knowledge base: {e}")


def main():
    """Example usage"""
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent framework not available. Please configure API keys.")
        return
    
    print("AI Assistant ready!")
    print(f"Backend: {assistant.agent.get_backend_name()}")
    
    # Example: Audit a file
    # result = assistant.audit("app/main.py", audit_type="code")
    # print(result)
    
    # Example: Learn from codebase
    # result = assistant.learn("app/", topic="architecture")
    # print(result)


if __name__ == "__main__":
    main()
