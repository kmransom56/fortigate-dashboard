# 🤝 Contributing to LTM Network Intelligence Platform

Thank you for your interest in contributing to the LTM Network Intelligence Platform! This guide will help you get started with contributing to the project.

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Report bugs through GitHub Issues
- Use the bug report template
- Include detailed reproduction steps
- Provide system information and logs

### 💡 Feature Requests
- Suggest new features through GitHub Issues
- Use the feature request template
- Describe the use case and expected behavior
- Consider compatibility with existing integrations

### 📚 Documentation
- Improve existing documentation
- Add examples and tutorials
- Fix typos and clarify instructions
- Translate documentation (future)

### 🔧 Code Contributions
- Fix bugs and implement features
- Improve performance and reliability
- Add tests and improve test coverage
- Enhance integrations with network devices

### 🧪 Testing
- Test new releases and report issues
- Improve test coverage
- Add integration tests
- Test on different platforms and configurations

## 🛠️ Development Setup

### Prerequisites

- **Python 3.8+**
- **Git**
- **Docker and Docker Compose** (recommended)
- **Neo4j, Milvus, Redis** (for native development)

### Setup Steps

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/ltm-network-intelligence-platform.git
   cd ltm-network-intelligence-platform
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv dev-venv
   source dev-venv/bin/activate  # On Windows: dev-venv\\Scripts\\activate

   # Install development dependencies
   pip install -r requirements-dev.txt
   pip install -e .  # Install package in development mode
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Set up local services**
   ```bash
   # Using Docker (recommended)
   docker-compose -f docker-compose.dev.yml up -d

   # Or install services natively (see INSTALLATION.md)
   ```

5. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## 📋 Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black .
isort .

# Check code quality
flake8 .
mypy .

# Run all checks
pre-commit run --all-files
```

### Code Structure

```
ltm-network-intelligence-platform/
├── api_gateway/           # FastAPI gateway and authentication
├── config/                # Configuration files and schemas
├── docs/                  # Documentation
├── ltm_integration/       # Core LTM integration components
├── monitoring/            # Performance monitoring
├── scripts/               # Setup and utility scripts
├── security/              # Security and compliance framework
├── tests/                 # Test suite
└── unified_network_intelligence.py  # Main platform orchestrator
```

### Coding Standards

#### Python Code Style
- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible
- Use async/await for I/O operations

```python
async def example_function(param: str, optional_param: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief description of what the function does.
    
    Args:
        param: Description of the parameter
        optional_param: Description of optional parameter
    
    Returns:
        Dictionary containing the result
    
    Raises:
        ValueError: When param is invalid
    """
    if not param:
        raise ValueError("param cannot be empty")
    
    result = await some_async_operation(param)
    return {"status": "success", "data": result}
```

#### Error Handling
- Use specific exception types
- Log errors with appropriate context
- Provide meaningful error messages
- Handle edge cases gracefully

```python
try:
    result = await risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed for device {device_name}: {e}", exc_info=True)
    raise NetworkDeviceError(f"Failed to connect to {device_name}: {e}") from e
```

#### Logging
- Use structured logging with context
- Include relevant metadata
- Use appropriate log levels

```python
logger.info(
    "Device status retrieved successfully",
    extra={
        "device_name": device_name,
        "device_type": device_type,
        "response_time_ms": response_time,
        "ltm_insights_count": len(insights)
    }
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ltm_integration.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests (requires services)
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

### Writing Tests

#### Unit Tests
```python
import pytest
from unittest.mock import AsyncMock, patch
from ltm_integration.ltm_client import LTMClient

class TestLTMClient:
    
    @pytest.fixture
    async def ltm_client(self):
        client = LTMClient("http://test-server:8000")
        yield client
        await client.cleanup()
    
    @patch('ltm_integration.ltm_client.aiohttp.ClientSession.post')
    async def test_record_message_success(self, mock_post, ltm_client):
        # Arrange
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"id": "msg123", "status": "recorded"}
        )
        
        # Act
        result = await ltm_client.record_message(
            role="test",
            content="Test message",
            tags=["test"]
        )
        
        # Assert
        assert result["id"] == "msg123"
        assert result["status"] == "recorded"
        mock_post.assert_called_once()
```

#### Integration Tests
```python
@pytest.mark.integration
async def test_full_platform_integration():
    # Set up platform with real services
    platform = UnifiedNetworkIntelligencePlatform("config/test_config.json")
    
    try:
        # Initialize platform
        init_result = await platform.initialize(["ltm", "mcp", "kg"])
        assert init_result["overall_status"] == "success"
        
        # Test cross-component functionality
        analysis = await platform.analyze_network_holistically()
        assert len(analysis["systems_contributing"]) >= 2
        
    finally:
        await platform.shutdown()
```

### Test Data and Fixtures

Create test data that's realistic but doesn't expose real credentials:

```python
# tests/fixtures/test_data.py
TEST_DEVICE_CONFIG = {
    "name": "test-fortigate-01",
    "type": "fortigate",
    "host": "192.168.1.1",
    "credentials": {
        "api_key": "test_api_key_do_not_use_in_production"
    }
}

TEST_NETWORK_TOPOLOGY = {
    "devices": [
        {"id": "fw01", "type": "firewall", "connections": ["sw01"]},
        {"id": "sw01", "type": "switch", "connections": ["fw01", "ap01"]},
        {"id": "ap01", "type": "access_point", "connections": ["sw01"]}
    ]
}
```

## 🔄 Contribution Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # Or for bug fixes: git checkout -b bugfix/issue-number
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed
   - Ensure all tests pass

3. **Commit your changes**
   ```bash
   # Stage your changes
   git add .
   
   # Commit with descriptive message
   git commit -m "feat: add support for Cisco ASA device integration
   
   - Add ASADeviceManager class with authentication
   - Implement policy retrieval and status monitoring  
   - Add comprehensive tests for ASA integration
   - Update documentation with ASA setup instructions
   
   Fixes #123"
   ```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): brief description

Detailed description of changes (optional)

Fixes #issue_number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(mcp-server): add support for Palo Alto firewalls
fix(ltm-client): handle connection timeout gracefully
docs(integration): add troubleshooting guide for common issues
test(knowledge-graph): add integration tests for Neo4j queries
```

### Submitting Changes

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**
   - Use the PR template
   - Provide clear description of changes
   - Link related issues
   - Add screenshots for UI changes
   - Request reviews from maintainers

3. **Address Review Feedback**
   - Make requested changes
   - Push updates to the same branch
   - Respond to review comments

## 🎯 Specific Contribution Areas

### Device Integration

Adding support for new network devices:

1. **Create device manager class**
   ```python
   # ltm_integration/devices/your_device_manager.py
   from .base_device_manager import BaseDeviceManager
   
   class YourDeviceManager(BaseDeviceManager):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.device_type = "your_device"
       
       async def authenticate(self) -> bool:
           # Implement authentication logic
           pass
       
       async def get_status(self) -> Dict[str, Any]:
           # Implement status retrieval
           pass
   ```

2. **Add device configuration schema**
   ```python
   # config/schemas/your_device_schema.py
   YOUR_DEVICE_CONFIG_SCHEMA = {
       "type": "object",
       "properties": {
           "host": {"type": "string"},
           "port": {"type": "integer", "default": 443},
           "credentials": {
               "type": "object",
               "properties": {
                   "username": {"type": "string"},
                   "password": {"type": "string"}
               }
           }
       }
   }
   ```

3. **Add tests and documentation**

### LTM Feature Enhancement

Adding new LTM capabilities:

1. **Extend LTM client with new methods**
2. **Add corresponding server endpoints (if applicable)**
3. **Update network intelligence engine**
4. **Add comprehensive tests**
5. **Update documentation**

### Repository Integration

Adding support for new repository types:

1. **Create integration bridge**
2. **Add to integration configuration**
3. **Update setup scripts**
4. **Add integration tests**
5. **Document integration process**

## 🐛 Bug Report Guidelines

When reporting bugs, please include:

### Environment Information
- Operating system and version
- Python version
- Docker version (if using containers)
- Platform version
- Deployment method (Docker, native, etc.)

### Bug Description
- Clear, concise description
- Expected vs actual behavior
- Steps to reproduce
- Screenshots or logs (if applicable)

### System Configuration
```bash
# Include output of debug information script
./scripts/generate_debug_info.sh
```

### Example Bug Report

```markdown
## Bug Description
LTM client fails to connect to server after platform restart

## Environment
- OS: Ubuntu 20.04
- Python: 3.9.7
- Platform Version: 2.0.0
- Deployment: Docker Compose

## Steps to Reproduce
1. Start platform with `docker-compose up -d`
2. Verify platform is working
3. Restart platform with `docker-compose restart`
4. Try to run health check: `python unified_network_intelligence.py --health-check`

## Expected Behavior
Health check should pass and show all components as healthy

## Actual Behavior
LTM client connection fails with timeout error:
```
ConnectionError: Cannot connect to LTM server at http://localhost:8000
```

## Logs
```
[2024-01-01 12:00:00] ERROR - LTM Client initialization failed: Connection timeout
[2024-01-01 12:00:00] ERROR - Platform health check failed: LTM client not available
```

## Additional Context
Issue started after upgrading from version 1.9.0 to 2.0.0
```

## 📚 Documentation Guidelines

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add troubleshooting sections
- Use proper Markdown formatting
- Include relevant screenshots

### Documentation Structure

```markdown
# Title

Brief description of what this document covers.

## Prerequisites
What users need before following this guide.

## Step-by-Step Instructions
1. Clear, numbered steps
2. Include code examples
3. Show expected output

## Troubleshooting
Common issues and solutions.

## See Also
Links to related documentation.
```

### API Documentation

Use docstrings for automatic API documentation generation:

```python
async def analyze_device_performance(
    self, 
    device_data: Dict[str, Any], 
    include_ltm_insights: bool = True
) -> NetworkInsight:
    """
    Analyze device performance data and generate insights.
    
    This function processes device performance metrics and optionally
    enhances them with LTM historical insights and pattern analysis.
    
    Args:
        device_data: Dictionary containing device performance metrics.
            Must include 'device_name', 'metrics', and 'timestamp' keys.
        include_ltm_insights: Whether to include LTM-based historical
            insights in the analysis. Defaults to True.
    
    Returns:
        NetworkInsight object containing:
            - performance_score: Overall performance rating (0-100)
            - insights: List of analysis insights
            - recommendations: List of optimization recommendations
            - ltm_patterns: Historical patterns (if include_ltm_insights=True)
    
    Raises:
        ValueError: If device_data is missing required keys
        NetworkAnalysisError: If analysis fails due to data issues
    
    Example:
        >>> device_data = {
        ...     "device_name": "firewall-01",
        ...     "metrics": {"cpu_usage": 85, "memory_usage": 70},
        ...     "timestamp": "2024-01-01T12:00:00Z"
        ... }
        >>> insight = await analyzer.analyze_device_performance(device_data)
        >>> print(f"Performance score: {insight.performance_score}")
        Performance score: 78
    """
```

## 🏆 Recognition

Contributors will be recognized in:

- **README.md** - Major contributors section
- **CHANGELOG.md** - Credit for specific contributions
- **GitHub Releases** - Contributor mentions
- **Documentation** - Author credits where appropriate

### Hall of Fame

Contributors who make significant impacts will be featured in our Hall of Fame with:
- GitHub profile link
- Brief description of contributions
- Special "Contributor" badge in community

## 📞 Getting Help

### Community Support

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For specific bugs and feature requests
- **Developer Chat**: Join our development chat (link in README)

### Maintainer Contact

For questions about contributing:
- Open a GitHub Discussion with the "contributing" tag
- Mention @kmransom56 in issues for urgent matters

### Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Setting up development environment
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)**: Adding new integrations
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Solving common problems

---

## 🎉 Thank You!

Every contribution, no matter how small, helps make the LTM Network Intelligence Platform better for everyone. We appreciate your time and effort in improving network management for the community!

**Happy Contributing!** 🚀