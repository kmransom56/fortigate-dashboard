#!/usr/bin/env python3
"""
Example usage of the AutoGen teachable agent

This script demonstrates how to use the agent programmatically.
"""

import os
import sys
from autogen_agent import (
    create_teachable_agent,
    create_user_proxy_agent,
    run_agent_task
)

def example_generate_documentation():
    """Example: Generate API documentation"""
    print("=" * 60)
    print("Example 1: Generate API Documentation")
    print("=" * 60)
    
    task = "Generate comprehensive API documentation from device inventory. " \
           "Use the fortigate_self_api_doc.py script to sync the inventory, " \
           "then generate documentation in docs/API_DOCUMENTATION.md"
    
    result = run_agent_task(task)
    
    if result.get("success"):
        print("✅ Documentation generated successfully!")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_analyze_code():
    """Example: Analyze code for errors"""
    print("\n" + "=" * 60)
    print("Example 2: Analyze Code for Errors")
    print("=" * 60)
    
    task = "Analyze the file fortigate_self_api_doc.py for any errors, " \
           "code quality issues, or potential bugs. Provide a detailed report."
    
    result = run_agent_task(task)
    
    if result.get("success"):
        print("✅ Code analysis completed!")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_fix_issues():
    """Example: Fix code issues"""
    print("\n" + "=" * 60)
    print("Example 3: Fix Code Issues")
    print("=" * 60)
    
    task = "Analyze fortigate_self_api_doc.py for code quality issues " \
           "and automatically fix any issues that can be fixed automatically."
    
    result = run_agent_task(task)
    
    if result.get("success"):
        print("✅ Code issues fixed!")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_project_analysis():
    """Example: Analyze entire project"""
    print("\n" + "=" * 60)
    print("Example 4: Analyze Entire Project")
    print("=" * 60)
    
    task = "Analyze all Python files in the app/services directory " \
           "for code quality issues, unused imports, and potential bugs."
    
    result = run_agent_task(task)
    
    if result.get("success"):
        print("✅ Project analysis completed!")
    else:
        print(f"❌ Error: {result.get('error')}")


def main():
    """Run all examples"""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        print("⚠️  Warning: No API key found!")
        print("Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable")
        print("\nContinuing anyway...\n")
    
    print("AutoGen Teachable Agent - Example Usage")
    print("=" * 60)
    print("\nNote: These examples require an OpenAI API key")
    print("Set OPENAI_API_KEY environment variable before running\n")
    
    # Uncomment the examples you want to run:
    
    # example_generate_documentation()
    # example_analyze_code()
    # example_fix_issues()
    # example_project_analysis()
    
    print("\n" + "=" * 60)
    print("To run examples, uncomment them in the main() function")
    print("=" * 60)


if __name__ == "__main__":
    main()
