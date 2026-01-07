# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive LTM (Long Term Memory) Enhanced Network Intelligence Platform that transforms traditional network management into an intelligent, learning-based system. This repository serves as the unified orchestration layer that connects and enhances multiple existing repositories:

- `netai-troubleshooter` - AI-assisted network troubleshooting with Neo4j, Milvus, and LLMs
- `network-device-mcp-server` - Enhanced MCP server for FortiGate, FortiManager, and Cisco Meraki devices
- `FortiGate-Enterprise-Platform` - Enterprise-grade FortiGate management
- `ai-research-platform` - Multi-agent AI development environment
- `network_device_utils` - Core network utility functions

## Development Environment Setup

### Prerequisites
```bash
# System requirements
Python 3.8+ (3.10+ recommended)
Docker & Docker Compose (for Neo4j, Milvus)
Node.js 16+ (for Power Automate integrations)
Redis server (for caching and rate limiting)
PostgreSQL (for audit logging)
8GB+ RAM, 20GB+ disk space
```

### Quick Setup
```bash
# Clone and setup main environment
git clone <this-repo> ltm-network-intelligence
cd ltm-network-intelligence

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Install comprehensive dependencies
pip install -r requirements_enhanced.txt

# Start infrastructure services
docker-compose up -d

# Initialize LTM system
python unified_network_intelligence.py --initialize

# Start the platform
python unified_network_intelligence.py
```

### Development Dependencies
```bash
# Core LTM and networking
pip install aiofiles asyncio-mqtt python-dotenv
pip install neo4j pymilvus aiofiles python-jose[cryptography]
pip install httpx fastapi uvicorn redis psutil
pip install asyncpg bcrypt cryptography

# AI/ML components
pip install sentence-transformers scikit-learn pandas numpy
pip install openai anthropic  # For LLM integrations

# Security and compliance
pip install jwt bcrypt cryptography

# Development tools
pip install pytest pytest-asyncio black flake8
pip install jupyter notebook  # For analysis and visualization
```

## Architecture Components

### 1. Unified Network Intelligence Platform (`unified_network_intelligence.py`)
The main orchestration class that coordinates all subsystems:
```python
class UnifiedNetworkIntelligencePlatform:
    - ltm_client: LTMClient  # Long term memory system
    - mcp_server: LTMEnhancedNetworkMCPServer  # Enhanced MCP server
    - network_intelligence: NetworkIntelligenceEngine  # AI analysis
    - pa_bridge: PowerAutomateBridge  # Power Automate integration
    - kg_bridge: KnowledgeGraphBridge  # Neo4j + Milvus integration
    - security_manager: LTMSecurityManager  # Security and compliance
    - performance_monitor: LTMPerformanceMonitor  # Performance tracking
```

### 2. LTM Integration Layer (`ltm_integration/`)
Core memory and intelligence components:
- `ltm_client.py` - LTM system client with local fallback
- `network_intelligence.py` - AI-powered network analysis engine
- `power_automate_bridge.py` - Power Automate workflow automation
- `knowledge_graph_bridge.py` - Neo4j + Milvus integration

### 3. Security Framework (`security/ltm_security_framework.py`)
Comprehensive security and compliance system:
- Encryption management with security level assessment
- Audit logging with compliance reporting (SOX, PCI-DSS, GDPR, ISO27001)
- Role-based access control with LTM context
- Automated security violation detection

### 4. Performance Monitoring (`monitoring/ltm_performance_monitor.py`)
Advanced performance monitoring with predictive analytics:
- Real-time metrics collection (system, application, LTM-specific)
- Intelligent alerting with LTM learning
- Performance trend analysis and anomaly detection
- Predictive maintenance recommendations

### 5. API Gateway (`api_gateway/ltm_api_gateway.py`)
Secure API gateway with comprehensive features:
- JWT authentication and authorization
- Rate limiting with Redis backend
- Request context tracking
- LTM-enhanced responses

## Key Development Commands

### Core Operations
```bash
# Start full platform
python unified_network_intelligence.py

# Start with specific components
python unified_network_intelligence.py --components mcp,ltm,security

# Initialize LTM memories with network context
python -m ltm_integration.ltm_client --initialize --domain=network

# Run enhanced MCP server
python network-device-mcp-server/src/main_ltm.py

# Start API gateway
python api_gateway/ltm_api_gateway.py

# Run performance monitoring
python monitoring/ltm_performance_monitor.py
```

### Testing and Validation
```bash
# Comprehensive integration tests
python tests/test_ltm_integration.py

# Test individual components
python tests/test_network_intelligence.py
python tests/test_security_framework.py
python tests/test_performance_monitor.py

# Load testing
python tests/load_test_api_gateway.py

# Security audit
python security/audit_security_posture.py
```

### Database Management
```bash
# Start infrastructure
docker-compose up -d neo4j milvus redis postgresql

# Initialize Neo4j schema
python -c "from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge; import asyncio; asyncio.run(KnowledgeGraphBridge().initialize())"

# Check database health
python tools/check_database_health.py
```

### Deployment and Production
```bash
# Production deployment
./start_production.sh

# Health check
curl http://localhost:8001/health

# View metrics
curl http://localhost:8001/metrics

# Generate reports
python reports/generate_executive_dashboard.py
```

## Core Implementation Patterns

### 1. LTM-Enhanced Network Operations
```python
# Pattern: Memory-enhanced device analysis
async def analyze_device_with_memory(device_id, device_type):
    # Retrieve historical context
    historical_data = await ltm_client.search_memories(
        query=f"{device_type} {device_id} performance patterns",
        tags=["device_analysis", device_type, "historical"]
    )
    
    # Current status with learned optimizations
    current_status = await get_device_status_optimized(device_id, historical_data)
    
    # Generate intelligent insights
    insights = await network_intelligence.analyze_with_context(
        current_status, historical_data
    )
    
    # Record new learnings
    await ltm_client.record_message(
        role="system",
        content=f"Device analysis: {insights['summary']}",
        tags=["learning", device_type, "analysis"]
    )
    
    return insights
```

### 2. Cross-Platform Knowledge Correlation
```python
# Pattern: Multi-system data fusion
async def correlate_cross_platform_data(issue_description):
    # Gather data from all systems
    mcp_data = await mcp_server.get_current_infrastructure()
    kg_insights = await kg_bridge.analyze_issue_impact(affected_devices, issue_description)
    ltm_patterns = await ltm_client.search_memories(query=issue_description)
    
    # Intelligent correlation
    correlation = await network_intelligence.correlate_multi_source_data(
        mcp_data, kg_insights, ltm_patterns
    )
    
    return correlation
```

### 3. Adaptive Security Policies
```python
# Pattern: Learning-based security
async def apply_adaptive_security(user_context, operation):
    # Assess risk with historical patterns
    risk_assessment = await security_manager.assess_operation_risk(
        operation, user_context
    )
    
    # Apply learned security policies
    security_result = await security_manager.apply_adaptive_policies(
        risk_assessment, user_context
    )
    
    return security_result
```

### 4. Intelligent Performance Optimization
```python
# Pattern: Performance learning and adaptation
async def optimize_performance_with_learning():
    # Collect comprehensive metrics
    metrics = await performance_monitor.get_comprehensive_metrics()
    
    # Analyze with historical context
    analysis = await performance_analyzer.analyze_with_history(metrics)
    
    # Apply learned optimizations
    optimizations = await apply_learned_optimizations(analysis)
    
    return optimizations
```

## Configuration Management

### Environment Variables
```bash
# LTM Configuration
LTM_SERVER_URL=http://localhost:8000
LTM_MEMORY_LIMIT=5000
LTM_LEARNING_ENABLED=true

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_HOST=localhost
REDIS_PORT=6379

# Security Configuration
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY_PATH=security/master.key
AUDIT_DB_HOST=localhost

# API Configuration
API_PORT=8001
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=true
```

### Configuration Files
```bash
config/
├── unified_config.json          # Main platform configuration
├── devices_enhanced.json        # Enhanced device configurations with LTM tags
├── security_policies.json       # Security policies and compliance rules
├── alert_rules.json            # Performance alert rules
├── power_automate_workflows.json # Workflow templates
└── ltm_personas.json           # LTM persona configurations
```

## Key Integration Points

### Network Device Management Enhancement
- **Predictive Maintenance**: Learn failure patterns and predict issues before they occur
- **Intelligent Troubleshooting**: Cross-reference similar issues for faster resolution
- **Adaptive Monitoring**: Adjust alert thresholds based on learned patterns
- **Context-Aware Documentation**: Generate and maintain living network documentation

### Power Automate Workflow Intelligence
- **Workflow Learning**: Track workflow effectiveness and optimize automatically
- **Business Context Integration**: Correlate network events with business impact
- **Adaptive Triggers**: Learn optimal trigger conditions for different scenarios
- **ROI Tracking**: Measure and report automation value and effectiveness

### Security and Compliance Automation
- **Adaptive Threat Detection**: Learn from security patterns and evolve detection
- **Compliance Automation**: Generate compliance reports with AI insights
- **Risk Assessment**: Continuous risk evaluation with historical context
- **Incident Response**: Learn from past incidents to improve response times

## Performance Optimization

### System Requirements
- **CPU**: 4+ cores for concurrent LTM processing
- **Memory**: 8GB+ for in-memory caches and ML models
- **Storage**: SSD recommended for Neo4j and log storage
- **Network**: Low latency connection to network devices

### Scaling Patterns
```python
# Horizontal scaling pattern
async def scale_ltm_processing():
    # Distribute LTM operations across multiple instances
    # Use Redis for coordination and shared state
    # Implement circuit breakers for resilience
    
# Vertical scaling pattern  
async def optimize_memory_usage():
    # Implement intelligent memory management
    # Use LRU cache for frequently accessed memories
    # Archive old memories to reduce active memory footprint
```

## Troubleshooting Guide

### Common Issues
1. **LTM Initialization Failures**: Check database connectivity and permissions
2. **Memory Search Performance**: Verify Milvus index configuration
3. **API Response Latency**: Check Redis connectivity and query optimization
4. **Security Violations**: Review audit logs and user permissions
5. **Performance Alerts**: Analyze metric trends and threshold configuration

### Debug Commands
```bash
# Enable debug logging
export LTM_LOG_LEVEL=DEBUG

# Test database connections
python tools/test_database_connections.py

# Validate LTM functionality
python tools/validate_ltm_integration.py

# Check system health
python tools/system_health_check.py
```

## Business Impact Metrics

Track these KPIs to demonstrate platform value:
- **Network Uptime Improvement**: Target >99.9%
- **Mean Time to Resolution (MTTR)**: Target <30 minutes
- **False Alert Reduction**: Target >80% reduction
- **Predictive Maintenance Accuracy**: Target >90%
- **Automation ROI**: Track cost savings and efficiency gains

## Future Development Roadmap

### Phase 1: Core Enhancement (Current)
- Enhanced LTM integration with network operations
- Advanced security and compliance frameworks
- Intelligent performance monitoring and alerting

### Phase 2: AI/ML Enhancement (Next 3 months)
- Advanced machine learning models for pattern recognition
- Natural language processing for incident reports
- Computer vision for network topology visualization

### Phase 3: Edge Intelligence (Next 6 months)
- Edge deployment capabilities for remote locations
- Federated learning across multiple network environments
- Real-time decision making at network edge

### Phase 4: Advanced Integration (Next 12 months)
- Voice-activated network operations
- Blockchain-based audit trails
- Digital twin modeling for network simulation
- Advanced predictive analytics with business correlation

This platform represents a paradigm shift from reactive network management to proactive, intelligent network operations that continuously learn and adapt to provide optimal performance and business value.