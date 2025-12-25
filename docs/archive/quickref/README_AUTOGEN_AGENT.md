# AutoGen Teachable Agent for FortiGate API Documentation

This directory contains an AutoGen teachable agent system that can automatically generate API documentation, analyze code for errors, and assist with code maintenance.

## Features

- **API Documentation Generation**: Automatically generates comprehensive API documentation from device inventory data
- **Code Analysis**: Analyzes Python files for errors, code quality issues, and potential problems
- **Automatic Fixes**: Attempts to automatically fix common code issues
- **Function Calling**: Uses OpenAI function calling to execute tools
- **Interactive Mode**: Chat with the agent interactively

**Note**: The agent uses `AssistantAgent` with function calling capabilities. If `TeachableAgent` is available in your pyautogen version, it will be used automatically for learning capabilities.

## Installation

1. Install dependencies:
```bash
# Note: Use version 0.2.18 which has teachable agent support
# Newer versions (0.10+) have a different API structure
pip install 'pyautogen==0.2.18'
```

Or using uv:
```bash
# Note: Use version 0.2.18 for teachable agent support
uv pip install 'pyautogen==0.2.18'
```

**Important for zsh users**: Always quote package names with square brackets to prevent glob expansion.

2. Set up API keys (choose one):
```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Azure OpenAI
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

## Usage

### Generate API Documentation

```bash
python autogen_agent.py --task "Generate API documentation from device inventory"
```

### Analyze Code for Errors

```bash
python autogen_agent.py --task "Analyze fortigate_self_api_doc.py for errors and fix them"
```

### Analyze Entire Project

```bash
python autogen_agent.py --task "Analyze all Python files in the project for code quality issues"
```

### Interactive Mode

```bash
python autogen_agent.py --interactive
```

In interactive mode, you can:
- Ask the agent to complete tasks
- Type 'tools' to see available tools
- Type 'exit' or 'quit' to exit

### Advanced Options

```bash
# Use a different model
python autogen_agent.py --task "Generate documentation" --model "gpt-3.5-turbo"

# Adjust temperature
python autogen_agent.py --task "Analyze code" --temperature 0.5

# Reset the agent's learning database
python autogen_agent.py --task "Generate documentation" --reset-db

# Specify custom database path
python autogen_agent.py --task "Generate documentation" --db-path "./custom_db"
```

## Available Tools

The agent has access to the following tools:

1. **run_fortigate_doc_script(command, **kwargs)**
   - Runs fortigate_self_api_doc.py with specified command
   - Commands: sync, query, export, watch, history
   - Example: `run_fortigate_doc_script("sync")`

2. **generate_api_documentation(output_file)**
   - Generates comprehensive API documentation
   - Syncs device inventory and exports to Markdown
   - Example: `generate_api_documentation("docs/API_DOCUMENTATION.md")`

3. **analyze_code_file(file_path)**
   - Analyzes a Python file for errors and issues
   - Checks for syntax errors, code quality, TODOs, etc.
   - Example: `analyze_code_file("fortigate_self_api_doc.py")`

4. **fix_code_issues(file_path, issues)**
   - Automatically fixes code issues
   - Example: `fix_code_issues("file.py", [list of issues])`

5. **analyze_project_code(directory, pattern)**
   - Analyzes all Python files in a directory
   - Example: `analyze_project_code(".", "*.py")`

6. **get_api_endpoint_info(endpoint)**
   - Gets information about API endpoints from documentation
   - Example: `get_api_endpoint_info("monitor/user/device/query")`

## How It Works

1. **Teachable Agent**: Uses AutoGen's TeachableAgent which can learn from examples and store knowledge in a database
2. **Function Calling**: The agent uses OpenAI function calling to invoke tools
3. **Memory**: The agent maintains a database of learned examples and patterns
4. **Code Execution**: The agent can execute Python code through the UserProxyAgent

## Example Tasks

### Generate API Documentation

```bash
python autogen_agent.py --task "Generate comprehensive API documentation from the current device inventory. Include all devices, their ports, and connection details."
```

### Fix Code Errors

```bash
python autogen_agent.py --task "Analyze fortigate_self_api_doc.py for any errors or code quality issues and fix them automatically."
```

### Maintain Documentation

```bash
python autogen_agent.py --task "Update the API documentation with the latest device inventory data and ensure all endpoints are properly documented."
```

### Code Quality Check

```bash
python autogen_agent.py --task "Analyze all Python files in the app/services directory for code quality issues, unused imports, and potential bugs."
```

## Database

The teachable agent stores learned examples in a database directory (default: `./.autogen_teachable_db`). This allows the agent to:

- Remember previous solutions
- Learn from examples you provide
- Improve over time
- Recall similar problems and solutions

To reset the database:
```bash
python autogen_agent.py --reset-db --task "your task"
```

## Integration with fortigate_self_api_doc.py

The agent integrates seamlessly with `fortigate_self_api_doc.py`:

1. The agent can run any command from the script
2. It can sync device inventory
3. It can export topology data
4. It can generate documentation from the exported data

## Troubleshooting

### API Key Issues

If you see authentication errors:
- Verify your API key is set: `echo $OPENAI_API_KEY`
- Check that the key has proper permissions
- For Azure, verify endpoint and API version are correct

### Import Errors

If you see import errors for pyautogen:
```bash
pip install 'pyautogen[teachable]'
```

### Database Issues

If the agent database becomes corrupted:
```bash
python autogen_agent.py --reset-db --task "test"
```

### Timeout Issues

If tasks timeout:
- Increase timeout in `autogen_agent.py` (default: 300 seconds)
- Check network connectivity
- Verify FortiGate API is accessible

## Configuration

You can customize the agent behavior by editing `autogen_agent.py`:

- **Model**: Change default model in `create_teachable_agent()`
- **Temperature**: Adjust creativity (default: 0.7)
- **Database Path**: Change `path_to_db_dir` in teach_config
- **System Message**: Modify the system message for different behavior

## Contributing

To add new tools:

1. Add the function to `agent_tools.py`
2. Register it in `create_agent_tools_config()`
3. Add function definition in `register_agent_tools()`
4. Update this README

## License

Same as the main project.
