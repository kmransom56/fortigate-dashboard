#!/bin/bash

# FortiGate Topology Clone Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up FortiGate Topology Clone..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher is required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p src/{backend/{routes,services,middleware,utils},frontend/{components,services,utils,styles},cli}
mkdir -p assets/{physical,logical,assets}
mkdir -p tokens
mkdir -p cache
mkdir -p logs
mkdir -p db
mkdir -p nginx

# Create environment file
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please update .env with your FortiGate credentials"
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
npx playwright install chromium

# Create initial files if they don't exist
echo "📄 Creating initial project files..."

# Backend files
cat > src/backend/routes/topology.js << 'EOF'
const express = require('express');
const router = express.Router();
const FortiGateAuth = require('../services/fortigate-auth');
const logger = require('../utils/logger');

// Get topology data
router.get('/', async (req, res) => {
  try {
    const auth = new FortiGateAuth({
      host: process.env.FORTIGATE_HOST,
      username: process.env.FORTIGATE_USERNAME,
      password: process.env.FORTIGATE_PASSWORD
    });

    const topology = await auth.getTopologyData();
    res.json(topology);
  } catch (error) {
    logger.error('Topology fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch topology data' });
  }
});

// Get device status
router.get('/devices', async (req, res) => {
  try {
    const auth = new FortiGateAuth({
      host: process.env.FORTIGATE_HOST,
      username: process.env.FORTIGATE_USERNAME,
      password: process.env.FORTIGATE_PASSWORD
    });

    const devices = await auth.getDeviceStatus();
    res.json(devices);
  } catch (error) {
    logger.error('Device status fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch device status' });
  }
});

module.exports = router;
EOF

cat > src/backend/routes/auth.js << 'EOF'
const express = require('express');
const router = express.Router();
const FortiGateAuth = require('../services/fortigate-auth');
const logger = require('../utils/logger');

// Test FortiGate connection
router.post('/test', async (req, res) => {
  try {
    const { host, username, password } = req.body;
    
    const auth = new FortiGateAuth({ host, username, password });
    const isValid = await auth.testConnection();
    
    res.json({ success: isValid });
  } catch (error) {
    logger.error('Auth test error:', error);
    res.status(500).json({ error: 'Authentication test failed' });
  }
});

module.exports = router;
EOF

cat > src/backend/routes/assets.js << 'EOF'
const express = require('express');
const router = express.Router();
const fs = require('fs-extra');
const path = require('path');

// Get design tokens
router.get('/tokens', async (req, res) => {
  try {
    const tokensPath = path.join(process.cwd(), 'tokens', 'tokens.json');
    
    if (await fs.pathExists(tokensPath)) {
      const tokens = await fs.readJson(tokensPath);
      res.json(tokens);
    } else {
      res.json({
        colors: {},
        typography: {},
        spacing: {},
        borders: {},
        shadows: {},
        animations: {}
      });
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to load tokens' });
  }
});

module.exports = router;
EOF

cat > src/backend/middleware/errorHandler.js << 'EOF'
const logger = require('../utils/logger');

module.exports = (error, req, res, next) => {
  logger.error('Unhandled error:', error);
  
  res.status(error.status || 500).json({
    error: process.env.NODE_ENV === 'production' 
      ? 'Internal server error' 
      : error.message,
    stack: process.env.NODE_ENV === 'production' 
      ? undefined 
      : error.stack
  });
};
EOF

cat > src/backend/middleware/rateLimiter.js << 'EOF'
const rateLimit = require('express-rate-limit');

module.exports = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: 'Too many requests from this IP'
});
EOF

cat > src/backend/utils/logger.js << 'EOF'
const winston = require('winston');
const path = require('path');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'fortigate-topology' },
  transports: [
    new winston.transports.File({ 
      filename: path.join('logs', 'error.log'), 
      level: 'error' 
    }),
    new winston.transports.File({ 
      filename: path.join('logs', 'combined.log') 
    })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

module.exports = logger;
EOF

# Frontend files
cat > src/frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FortiGate Topology Clone</title>
    <meta name="description" content="FortiGate Security Fabric Topology Visualization">
</head>
<body>
    <div id="app"></div>
</body>
</html>
EOF

cat > src/frontend/services/apiService.js << 'EOF'
export class ApiService {
  constructor() {
    this.baseUrl = '/api';
  }

  async getTopologyData() {
    const response = await fetch(`${this.baseUrl}/topology`);
    if (!response.ok) {
      throw new Error('Failed to fetch topology data');
    }
    return response.json();
  }

  async getDeviceStatus() {
    const response = await fetch(`${this.baseUrl}/topology/devices`);
    if (!response.ok) {
      throw new Error('Failed to fetch device status');
    }
    return response.json();
  }

  async getTokens() {
    const response = await fetch(`${this.baseUrl}/assets/tokens`);
    if (!response.ok) {
      throw new Error('Failed to fetch design tokens');
    }
    return response.json();
  }

  async testAuth(credentials) {
    const response = await fetch(`${this.baseUrl}/auth/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      throw new Error('Authentication test failed');
    }
    
    return response.json();
  }
}
EOF

cat > src/frontend/utils/tokenManager.js << 'EOF'
export class TokenManager {
  constructor() {
    this.tokens = null;
  }

  async loadTokens() {
    try {
      const response = await fetch('/api/assets/tokens');
      this.tokens = await response.json();
    } catch (error) {
      console.error('Failed to load tokens:', error);
      this.tokens = this.getDefaultTokens();
    }
  }

  getTokens() {
    return this.tokens || this.getDefaultTokens();
  }

  applyTokens() {
    if (!this.tokens) return;

    const root = document.documentElement;
    
    // Apply color tokens
    if (this.tokens.colors) {
      for (const [name, value] of Object.entries(this.tokens.colors)) {
        root.style.setProperty(`--token-color-${name}`, value);
      }
    }

    // Apply typography tokens
    if (this.tokens.typography) {
      for (const [name, value] of Object.entries(this.tokens.typography)) {
        root.style.setProperty(`--token-typography-${name}`, value);
      }
    }

    // Apply spacing tokens
    if (this.tokens.spacing) {
      for (const [name, value] of Object.entries(this.tokens.spacing)) {
        root.style.setProperty(`--token-spacing-${name}`, value);
      }
    }
  }

  getDefaultTokens() {
    return {
      colors: {
        'severity-critical': '#d32f2f',
        'severity-high': '#f57c00',
        'severity-medium': '#fbc02d',
        'severity-low': '#388e3c',
        'device-default': '#007bff',
        'link-default': '#6c757d'
      },
      typography: {
        'font-family-primary': 'system-ui, sans-serif'
      },
      spacing: {
        'base': '1rem'
      }
    };
  }
}
EOF

# Create sample topology visualization component
cat > src/frontend/components/TopologyVisualization.js << 'EOF'
import * as d3 from 'd3';

export default class TopologyVisualization {
  constructor(container, options = {}) {
    this.container = container;
    this.options = options;
    this.data = options.data || { nodes: [], links: [] };
    this.view = options.view || 'physical';
    this.grouping = options.grouping || 'device-traffic';
    this.tokens = options.tokens || {};
    
    this.width = container.clientWidth;
    this.height = container.clientHeight;
    
    this.svg = null;
    this.simulation = null;
    
    this.init();
  }

  init() {
    this.svg = d3.select(this.container)
      .append('svg')
      .attr('width', this.width)
      .attr('height', this.height);
    
    this.setupSimulation();
    this.bindEvents();
  }

  setupSimulation() {
    this.simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2));
  }

  render() {
    this.renderLinks();
    this.renderNodes();
    this.simulation.nodes(this.data.nodes);
    this.simulation.force('link').links(this.data.links);
    this.simulation.restart();
  }

  renderNodes() {
    const node = this.svg.selectAll('.topology-node')
      .data(this.data.nodes)
      .join('circle')
      .attr('class', 'topology-node')
      .attr('r', 10)
      .attr('fill', d => this.getNodeColor(d))
      .call(this.drag());

    this.simulation.on('tick', () => {
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    });
  }

  renderLinks() {
    const link = this.svg.selectAll('.topology-link')
      .data(this.data.links)
      .join('line')
      .attr('class', 'topology-link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2);

    this.simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
    });
  }

  getNodeColor(node) {
    const colors = this.tokens.colors || {};
    
    switch (this.grouping) {
      case 'risk':
        return colors[`severity-${node.risk}`] || colors['device-default'] || '#007bff';
      case 'vendor':
        return colors[`vendor-${node.vendor}`] || colors['device-default'] || '#007bff';
      case 'os':
        return colors[`os-${node.os}`] || colors['device-default'] || '#007bff';
      default:
        return colors['device-default'] || '#007bff';
    }
  }

  drag() {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }

  bindEvents() {
    // Implement event handlers
  }

  setView(view) {
    this.view = view;
    this.render();
  }

  setGrouping(grouping) {
    this.grouping = grouping;
    this.render();
  }

  updateData(data) {
    this.data = data;
    this.render();
  }

  handleResize() {
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.svg.attr('width', this.width).attr('height', this.height);
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.restart();
  }
}
EOF

# Create database initialization
cat > db/init.sql << 'EOF'
-- FortiGate Topology Clone Database Schema

CREATE TABLE IF NOT EXISTS topology_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_type VARCHAR(20) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS design_tokens (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, name)
);

CREATE TABLE IF NOT EXISTS scraping_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    duration_ms INTEGER,
    assets_count INTEGER
);

CREATE INDEX idx_topology_timestamp ON topology_snapshots(timestamp);
CREATE INDEX idx_tokens_category ON design_tokens(category);
CREATE INDEX idx_logs_timestamp ON scraping_logs(timestamp);
EOF

# Create nginx configuration
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:3000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            proxy_pass http://app/static/;
        }

        location /assets/ {
            proxy_pass http://app/assets/;
        }
    }
}
EOF

# Create additional config files
cat > babel.config.js << 'EOF'
module.exports = {
  presets: ['@babel/preset-env']
};
EOF

cat > .eslintrc.js << 'EOF'
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  rules: {
    'no-unused-vars': 'warn',
    'no-console': 'off'
  }
};
EOF

cat > .dockerignore << 'EOF'
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
dist
coverage
.nyc_output
EOF

cat > .gitignore << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build output
dist/
build/

# Logs
logs/
*.log

# Cache
.cache/
cache/

# Assets (scraped content)
assets/
tokens/

# Coverage
coverage/
.nyc_output/

# OS generated files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Playwright
test-results/
playwright-report/
playwright/.cache/
EOF

echo "✅ Project setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your FortiGate credentials"
echo "2. Run: npm run dev"
echo "3. Or use Docker: npm run docker:up"
echo ""
echo "CLI Commands:"
echo "- npm run scrape -- --help"
echo "- npm run extract-tokens -- --help"
echo ""
echo "🎉 Happy coding!"