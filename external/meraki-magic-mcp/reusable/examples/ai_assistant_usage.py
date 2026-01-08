#!/usr/bin/env python3
"""
AI Assistant Usage Example

Demonstrates how to use the AI Assistant for audit, repair, update, optimize, and learn operations.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reusable.ai_assistant import AIAssistant
from reusable.agent_framework_wrapper import AgentBackend


def example_audit():
    """Example: Audit code for issues"""
    print("\n=== Audit Example ===")
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent not available. Configure API keys first.")
        return
    
    # Audit a Python file
    result = assistant.audit(
        target="reusable/secure_key_manager.py",
        audit_type="code"
    )
    
    print(f"Status: {result.get('status')}")
    print(f"Findings: {result.get('findings', '')[:200]}...")


def example_repair():
    """Example: Repair an issue"""
    print("\n=== Repair Example ===")
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent not available. Configure API keys first.")
        return
    
    # Repair a hypothetical issue
    result = assistant.repair(
        issue_description="Function is too slow, needs optimization",
        code_path="reusable/secure_key_manager.py"
    )
    
    print(f"Status: {result.get('status')}")
    print(f"Fix: {result.get('fix', '')[:200]}...")


def example_update():
    """Example: Update dependencies"""
    print("\n=== Update Example ===")
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent not available. Configure API keys first.")
        return
    
    # Analyze for updates
    result = assistant.update(
        update_type="dependencies",
        target="requirements.txt"  # If exists
    )
    
    print(f"Status: {result.get('status')}")
    print(f"Recommendations: {result.get('recommendations', '')[:200]}...")


def example_optimize():
    """Example: Optimize code"""
    print("\n=== Optimize Example ===")
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent not available. Configure API keys first.")
        return
    
    # Optimize for performance
    result = assistant.optimize(
        target="reusable/secure_key_manager.py",
        optimization_type="performance"
    )
    
    print(f"Status: {result.get('status')}")
    print(f"Recommendations: {result.get('recommendations', '')[:200]}...")


def example_learn():
    """Example: Learn from codebase"""
    print("\n=== Learn Example ===")
    assistant = AIAssistant(app_name="network_observability")
    
    if not assistant.agent.is_available():
        print("Agent not available. Configure API keys first.")
        return
    
    # Learn from the reusable package
    result = assistant.learn(
        source="reusable/",
        topic="architecture and design patterns"
    )
    
    print(f"Status: {result.get('status')}")
    print(f"Knowledge: {result.get('knowledge', '')[:200]}...")


def main():
    """Run all examples"""
    print("=" * 60)
    print("AI Assistant Usage Examples")
    print("=" * 60)
    
    # Check if agent is available
    assistant = AIAssistant(app_name="network_observability")
    if not assistant.agent.is_available():
        print("\n⚠️  Agent framework not available.")
        print("Please configure API keys:")
        print("  1. Set OPENAI_API_KEY environment variable, or")
        print("  2. Use SecureKeyManager to save your API key")
        print("\nExample:")
        print("  from reusable.secure_key_manager import SecureKeyManager")
        print("  km = SecureKeyManager(app_name='network_observability')")
        print("  km.save_key('openai_api_key', 'sk-...', env_var_name='OPENAI_API_KEY')")
        return
    
    print(f"\n✓ Agent ready (Backend: {assistant.agent.get_backend_name()})")
    
    # Run examples
    example_audit()
    example_repair()
    example_update()
    example_optimize()
    example_learn()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
