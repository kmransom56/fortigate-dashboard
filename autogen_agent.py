#!/usr/bin/env python3
"""
AutoGen Teachable Agent for FortiGate API Documentation and Code Maintenance

This script sets up a teachable agent that can:
1. Generate API documentation using fortigate_self_api_doc.py
2. Analyze code for errors and issues
3. Fix code problems automatically
4. Learn from examples and improve over time

Usage:
    python autogen_agent.py --task "Generate API documentation"
    python autogen_agent.py --task "Analyze fortigate_self_api_doc.py for errors"
    python autogen_agent.py --interactive  # Interactive mode
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import autogen
    from autogen.agentchat import AssistantAgent, UserProxyAgent
    # Try to import TeachableAgent if available
    try:
        from autogen.agentchat.teachable_agent import TeachableAgent
        TEACHABLE_AVAILABLE = True
    except ImportError:
        # Use AssistantAgent as fallback - it can still use function calling
        TeachableAgent = AssistantAgent
        TEACHABLE_AVAILABLE = False
except ImportError:
    print("Error: pyautogen is not installed.")
    print("Install it with: pip install 'pyautogen==0.2.18'")
    sys.exit(1)

# Import our agent tools
from agent_tools import (
    run_fortigate_doc_script,
    generate_api_documentation,
    analyze_code_file,
    fix_code_issues,
    analyze_project_code,
    get_api_endpoint_info
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_agent_tools_config() -> Dict[str, Any]:
    """
    Create function map for agent tools
    
    Returns:
        Dictionary mapping function names to callable functions
    """
    return {
        "run_fortigate_doc_script": run_fortigate_doc_script,
        "generate_api_documentation": generate_api_documentation,
        "analyze_code_file": analyze_code_file,
        "fix_code_issues": fix_code_issues,
        "analyze_project_code": analyze_project_code,
        "get_api_endpoint_info": get_api_endpoint_info,
    }


def create_teachable_agent(
    name: str = "fortigate_agent",
    model: str = "gpt-4",
    temperature: float = 0.7,
    max_consecutive_auto_reply: int = 10,
    teach_config: Optional[Dict[str, Any]] = None
):
    """
    Create an agent configured for FortiGate API documentation and code maintenance
    
    Args:
        name: Agent name
        model: LLM model to use
        temperature: Temperature for LLM
        max_consecutive_auto_reply: Maximum consecutive auto-replies
        teach_config: Teachable agent configuration (ignored if TeachableAgent not available)
    
    Returns:
        Configured AssistantAgent or TeachableAgent instance
    """
    # LLM configuration
    llm_config = {
        "model": model,
        "temperature": temperature,
        "timeout": 300,
        "max_tokens": 4096,
    }
    
    # Check for API key in environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "No API key found. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable."
        )
        logger.info("Using default configuration. You may need to configure API keys.")
    else:
        if "AZURE" in api_key or os.getenv("AZURE_OPENAI_ENDPOINT"):
            llm_config["api_type"] = "azure"
            llm_config["api_base"] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            llm_config["api_version"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        llm_config["api_key"] = api_key
    
    # System message for the agent
    system_message = """You are a helpful AI assistant specialized in:
1. Generating and maintaining FortiGate API documentation
2. Analyzing Python code for errors and issues
3. Fixing code problems automatically
4. Learning from examples to improve over time

You have access to several tools:
- run_fortigate_doc_script: Run fortigate_self_api_doc.py commands
- generate_api_documentation: Generate comprehensive API documentation
- analyze_code_file: Analyze a Python file for errors
- fix_code_issues: Automatically fix code issues
- analyze_project_code: Analyze all Python files in a project
- get_api_endpoint_info: Get information about API endpoints

When generating documentation:
- Use the fortigate_self_api_doc.py script to sync device inventory
- Export topology data to JSON
- Generate comprehensive Markdown documentation
- Include device details, port mappings, and connection information

When analyzing code:
- Check for syntax errors
- Identify code quality issues
- Suggest improvements
- Fix issues when possible

Always provide clear, actionable feedback and explanations.
"""
    
    if TEACHABLE_AVAILABLE and teach_config:
        # Use TeachableAgent if available
        agent = TeachableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            teach_config=teach_config,
        )
    else:
        # Use standard AssistantAgent with function calling
        if TEACHABLE_AVAILABLE:
            logger.info("TeachableAgent available but using AssistantAgent (teach_config not provided)")
        else:
            logger.info("TeachableAgent not available, using AssistantAgent with function calling")
        
        agent = AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
        )
    
    return agent


def create_user_proxy_agent(name: str = "user_proxy", human_input_mode: str = "NEVER") -> UserProxyAgent:
    """
    Create a user proxy agent for code execution
    
    Args:
        name: Agent name
        human_input_mode: Human input mode ("NEVER", "ALWAYS", "TERMINATE")
    
    Returns:
        Configured UserProxyAgent instance
    """
    # Import agent tools so they're available in the execution context
    import agent_tools
    
    return UserProxyAgent(
        name=name,
        human_input_mode=human_input_mode,
        max_consecutive_auto_reply=10,
        code_execution_config={
            "work_dir": ".",
            "use_docker": False,
        },
        function_map=create_agent_tools_config(),
    )


def register_agent_tools(agent: TeachableAgent, tools: Dict[str, Any]):
    """
    Register tools with the agent using function calling
    
    Args:
        agent: TeachableAgent instance
        tools: Dictionary of tool functions
    """
    # AutoGen agents can use functions through the llm_config function_map
    # We'll add the tools to the agent's function map
    if hasattr(agent, 'llm_config') and agent.llm_config:
        if 'functions' not in agent.llm_config:
            agent.llm_config['functions'] = []
        
        # Add function definitions for OpenAI function calling
        function_definitions = []
        for tool_name, tool_func in tools.items():
            # Create function definition based on tool name
            if tool_name == "run_fortigate_doc_script":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Run fortigate_self_api_doc.py with specified command and arguments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to run (sync, query, export, watch, history)"},
                            "output": {"type": "string", "description": "Output file path (for export command)"},
                            "port": {"type": "string", "description": "Port name (for query command)"},
                            "mac": {"type": "string", "description": "MAC address (for query/history commands)"},
                            "interval": {"type": "integer", "description": "Interval in seconds (for watch command)"}
                        },
                        "required": ["command"]
                    }
                })
            elif tool_name == "generate_api_documentation":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Generate comprehensive API documentation from device inventory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_file": {"type": "string", "description": "Path to output documentation file"}
                        },
                        "required": []
                    }
                })
            elif tool_name == "analyze_code_file":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Analyze a Python file for errors, issues, and code quality problems",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to Python file to analyze"}
                        },
                        "required": ["file_path"]
                    }
                })
            elif tool_name == "fix_code_issues":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Automatically fix code issues in a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to Python file"},
                            "issues": {"type": "array", "description": "List of issues to fix"}
                        },
                        "required": ["file_path", "issues"]
                    }
                })
            elif tool_name == "analyze_project_code":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Analyze all Python files in a directory for errors and issues",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Directory to analyze"},
                            "pattern": {"type": "string", "description": "File pattern to match (default: *.py)"}
                        },
                        "required": []
                    }
                })
            elif tool_name == "get_api_endpoint_info":
                function_definitions.append({
                    "name": tool_name,
                    "description": "Get information about a specific API endpoint from documentation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {"type": "string", "description": "API endpoint path"}
                        },
                        "required": ["endpoint"]
                    }
                })
        
        agent.llm_config['functions'] = function_definitions
        
        # Register function map for execution
        if 'function_map' not in agent.llm_config:
            agent.llm_config['function_map'] = {}
        agent.llm_config['function_map'].update(tools)


def run_agent_task(
    task: str,
    agent: Optional[AssistantAgent] = None,
    user_proxy: Optional[UserProxyAgent] = None
) -> Dict[str, Any]:
    """
    Run a task with the teachable agent
    
    Args:
        task: Task description
        agent: Optional pre-configured agent
        user_proxy: Optional pre-configured user proxy
    
    Returns:
        Dictionary with task results
    """
    if agent is None:
        agent = create_teachable_agent()
    
    if user_proxy is None:
        user_proxy = create_user_proxy_agent()
    
    # Register tools
    tools = create_agent_tools_config()
    register_agent_tools(agent, tools)
    
    # Create task prompt with tool information
    task_prompt = f"""Task: {task}

You have access to the following Python functions that you can use by writing Python code:

1. run_fortigate_doc_script(command, **kwargs) - Run fortigate_self_api_doc.py
   Example: result = run_fortigate_doc_script("sync")
   Example: result = run_fortigate_doc_script("export", output="docs/topology.json")

2. generate_api_documentation(output_file="docs/API_DOCUMENTATION.md") - Generate API documentation
   Example: result = generate_api_documentation("docs/API_DOCUMENTATION.md")

3. analyze_code_file(file_path) - Analyze a Python file for errors
   Example: result = analyze_code_file("fortigate_self_api_doc.py")

4. fix_code_issues(file_path, issues) - Fix code issues
   Example: result = fix_code_issues("file.py", [list of issues])

5. analyze_project_code(directory=".", pattern="*.py") - Analyze all Python files
   Example: result = analyze_project_code(".", "*.py")

6. get_api_endpoint_info(endpoint) - Get API endpoint information
   Example: result = get_api_endpoint_info("monitor/user/device/query")

To use these functions, write Python code that calls them. The user_proxy will execute the code for you.
Always check the result and provide a summary of what was done.

Please complete the task using the appropriate tools. Provide a summary of what was done.
"""
    
    try:
        # Initiate chat
        user_proxy.initiate_chat(
            agent,
            message=task_prompt,
            max_turns=10,
        )
        
        # Get the last message from the agent
        last_message = agent.chat_messages.get(user_proxy.name, [])
        
        return {
            "success": True,
            "task": task,
            "messages": last_message,
            "agent_name": agent.name
        }
    
    except Exception as e:
        logger.error(f"Error running agent task: {e}", exc_info=True)
        return {
            "success": False,
            "task": task,
            "error": str(e)
        }


def interactive_mode(agent: Optional[AssistantAgent] = None):
    """
    Run agent in interactive mode
    
    Args:
        agent: Optional pre-configured agent
    """
    if agent is None:
        agent = create_teachable_agent()
    
    user_proxy = UserProxyAgent(
        name="user_proxy",
        human_input_mode="ALWAYS",  # Interactive mode
        max_consecutive_auto_reply=10,
        code_execution_config={
            "work_dir": ".",
            "use_docker": False,
        },
    )
    
    tools = create_agent_tools_config()
    register_agent_tools(agent, tools)
    
    print("=" * 60)
    print("FortiGate API Documentation Agent - Interactive Mode")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  - Type a task description to have the agent complete it")
    print("  - Type 'tools' to see available tools")
    print("  - Type 'exit' or 'quit' to exit")
    print("\nExample tasks:")
    print("  - 'Generate API documentation'")
    print("  - 'Analyze fortigate_self_api_doc.py for errors'")
    print("  - 'Fix all code issues in the project'")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'tools':
                print("\nAvailable tools:")
                for tool_name in create_agent_tools_config().keys():
                    print(f"  - {tool_name}")
                continue
            
            # Run task
            result = run_agent_task(user_input, agent, user_proxy)
            
            if result.get("success"):
                print("\n✅ Task completed successfully!")
            else:
                print(f"\n❌ Task failed: {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AutoGen Teachable Agent for FortiGate API Documentation"
    )
    parser.add_argument(
        '--task',
        type=str,
        help='Task description for the agent to complete'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4',
        help='LLM model to use (default: gpt-4)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for LLM (default: 0.7)'
    )
    parser.add_argument(
        '--reset-db',
        action='store_true',
        help='Reset the teachable agent database'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='./.autogen_teachable_db',
        help='Path to teachable agent database directory'
    )
    
    args = parser.parse_args()
    
    # Configure teachable agent
    teach_config = {
        "verbosity": 1,
        "reset_db": args.reset_db,
        "path_to_db_dir": args.db_path,
        "recall_threshold": 1.5,
    }
    
    # Create agent
    agent = create_teachable_agent(
        model=args.model,
        temperature=args.temperature,
        teach_config=teach_config
    )
    
    if args.interactive:
        interactive_mode(agent)
    elif args.task:
        result = run_agent_task(args.task, agent)
        if result.get("success"):
            print("✅ Task completed successfully!")
            print(f"Agent: {result.get('agent_name')}")
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python autogen_agent.py --task 'Generate API documentation'")
        print("  python autogen_agent.py --interactive")


if __name__ == "__main__":
    main()
