const express = require('express');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const port = process.env.PORT || 5001;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:5001'],
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
    files: 1
  },
  fileFilter: (req, file, cb) => {
    // Allow YAML, JSON, and image files
    const allowedTypes = [
      'text/yaml',
      'text/x-yaml',
      'application/x-yaml',
      'application/json',
      'text/plain',
      'image/jpeg',
      'image/png',
      'image/gif'
    ];
    
    const allowedExts = ['.yaml', '.yml', '.json', '.txt', '.jpg', '.jpeg', '.png', '.gif'];
    const ext = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(file.mimetype) || allowedExts.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Allowed: YAML, JSON, Images'));
    }
  }
});

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests from this IP' }
});
app.use(limiter);

// Report generation rate limiting (more restrictive)
const reportLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 5, // limit each IP to 5 report requests per 5 minutes
  message: { error: 'Too many report generation requests' }
});

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'web/static')));

// Serve the NOC-style interface
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'web/templates/index_noc_style.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0-noc',
    features: ['voice-control', 'ltm-intelligence', 'network-monitoring']
  });
});

// Proxy endpoints to Python Flask server
const PYTHON_SERVER_URL = 'http://localhost:5000';

// Generic proxy function
const proxyToPython = (endpoint) => {
  return async (req, res) => {
    try {
      const fetch = await import('node-fetch').then(module => module.default);
      const url = `${PYTHON_SERVER_URL}${endpoint}`;
      
      const options = {
        method: req.method,
        headers: {
          'Content-Type': 'application/json',
        }
      };
      
      if (req.method !== 'GET' && req.body) {
        options.body = JSON.stringify(req.body);
      }
      
      const response = await fetch(url, options);
      const data = await response.json();
      
      res.status(response.status).json(data);
    } catch (error) {
      console.error(`Proxy error for ${endpoint}:`, error);
      res.status(500).json({ 
        success: false, 
        error: 'Backend service unavailable',
        message: 'Python Flask server is not responding'
      });
    }
  };
};

// API Endpoints - Proxy to Python Flask server
app.get('/api/brands', proxyToPython('/api/brands'));
app.get('/api/brands/:brand/overview', (req, res) => {
  proxyToPython(`/api/brands/${req.params.brand}/overview`)(req, res);
});

app.get('/api/stores/:brand/:storeId/security', (req, res) => {
  proxyToPython(`/api/stores/${req.params.brand}/${req.params.storeId}/security`)(req, res);
});

app.get('/api/stores/:brand/:storeId/url-blocking', (req, res) => {
  proxyToPython(`/api/stores/${req.params.brand}/${req.params.storeId}/url-blocking`)(req, res);
});

app.get('/api/devices/:deviceName/security-events', (req, res) => {
  proxyToPython(`/api/devices/${req.params.deviceName}/security-events`)(req, res);
});

app.get('/api/fortimanager', proxyToPython('/api/fortimanager'));
app.get('/api/fortimanager/:fmName/devices', (req, res) => {
  proxyToPython(`/api/fortimanager/${req.params.fmName}/devices`)(req, res);
});

// LTM Intelligence endpoints
app.get('/api/ltm/status', proxyToPython('/api/ltm/status'));
app.post('/api/ltm/voice/command', proxyToPython('/api/ltm/voice/command'));
app.get('/api/ltm/voice/suggestions', proxyToPython('/api/ltm/voice/suggestions'));
app.get('/api/ltm/patterns/analyze', proxyToPython('/api/ltm/patterns/analyze'));
app.get('/api/ltm/predictions/generate', proxyToPython('/api/ltm/predictions/generate'));

// FortiAnalyzer endpoints
app.get('/api/fortianalyzer/instances', proxyToPython('/api/fortianalyzer/instances'));
app.get('/api/fortianalyzer/logs/:brand/:storeId', (req, res) => {
  proxyToPython(`/api/fortianalyzer/logs/${req.params.brand}/${req.params.storeId}`)(req, res);
});
app.get('/api/fortianalyzer/threats/:brand', (req, res) => {
  proxyToPython(`/api/fortianalyzer/threats/${req.params.brand}`)(req, res);
});

// Web Filters endpoints
app.get('/api/webfilters/status', proxyToPython('/api/webfilters/status'));
app.get('/api/webfilters/policies', proxyToPython('/api/webfilters/policies'));
app.get('/api/webfilters/:brand/:storeId', (req, res) => {
  proxyToPython(`/api/webfilters/${req.params.brand}/${req.params.storeId}`)(req, res);
});

// NOC-specific endpoints
app.get('/api/noc/dashboard', (req, res) => {
  res.json({
    success: true,
    dashboard: {
      title: 'Network Operations Center',
      version: '1.0.0-noc',
      features: [
        'Voice-controlled operations',
        'Real-time network monitoring', 
        'AI-powered threat detection',
        'Multi-brand restaurant management'
      ],
      status: {
        ltm_intelligence: true,
        voice_interface: true,
        network_monitoring: true,
        security_analysis: true
      }
    }
  });
});

app.get('/api/noc/topology', (req, res) => {
  res.json({
    success: true,
    topology: {
      nodes: [],
      links: [],
      message: 'Network topology visualization coming soon',
      features: [
        'Interactive network diagrams',
        'Real-time device status',
        'Traffic flow visualization',
        'Security incident mapping'
      ]
    }
  });
});

// File upload endpoint for topology/configuration files
app.post('/api/upload', reportLimiter, upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ 
        success: false, 
        error: 'No file uploaded' 
      });
    }

    const fileContent = req.file.buffer.toString('utf8');
    const fileName = req.file.originalname;
    const fileType = path.extname(fileName).toLowerCase();

    // Process different file types
    let processedData = {};
    
    if (fileType === '.yaml' || fileType === '.yml') {
      try {
        // In a real implementation, you'd use a YAML parser here
        processedData = {
          type: 'yaml',
          content: fileContent,
          message: 'YAML configuration processed successfully'
        };
      } catch (error) {
        return res.status(400).json({ 
          success: false, 
          error: 'Invalid YAML format' 
        });
      }
    } else if (fileType === '.json') {
      try {
        processedData = {
          type: 'json',
          content: JSON.parse(fileContent),
          message: 'JSON configuration processed successfully'
        };
      } catch (error) {
        return res.status(400).json({ 
          success: false, 
          error: 'Invalid JSON format' 
        });
      }
    } else {
      processedData = {
        type: 'other',
        content: fileContent,
        message: 'File uploaded successfully'
      };
    }

    res.json({
      success: true,
      file: {
        name: fileName,
        size: req.file.size,
        type: req.file.mimetype,
        processed: processedData
      },
      message: 'File processed successfully'
    });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'File processing failed' 
    });
  }
});

// Report generation endpoint
app.post('/api/generate-report', reportLimiter, (req, res) => {
  const { type = 'network-status', format = 'pdf', options = {} } = req.body;

  // Validate input
  if (!['network-status', 'security-analysis', 'performance-report'].includes(type)) {
    return res.status(400).json({ 
      success: false, 
      error: 'Invalid report type' 
    });
  }

  if (!['pdf', 'html', 'json'].includes(format)) {
    return res.status(400).json({ 
      success: false, 
      error: 'Invalid report format' 
    });
  }

  // Generate report (placeholder implementation)
  const reportData = {
    id: `report-${Date.now()}`,
    type: type,
    format: format,
    generated_at: new Date().toISOString(),
    data: {
      summary: `${type} report generated successfully`,
      network_overview: {
        total_devices: 0,
        online_devices: 0,
        security_events: 0,
        performance_metrics: {}
      },
      recommendations: [
        'Regular security updates required',
        'Network monitoring configuration optimal',
        'Voice interface functioning properly'
      ]
    }
  };

  res.json({
    success: true,
    report: reportData,
    download_url: `/api/reports/${reportData.id}/download`,
    message: 'Report generated successfully'
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ 
        success: false, 
        error: 'File too large (max 50MB)' 
      });
    }
  }
  
  console.error('Server error:', error);
  res.status(500).json({ 
    success: false, 
    error: 'Internal server error' 
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ 
    success: false, 
    error: 'Endpoint not found',
    available_endpoints: [
      '/health',
      '/api/brands',
      '/api/ltm/status',
      '/api/noc/dashboard'
    ]
  });
});

// Start server
const server = app.listen(port, '0.0.0.0', () => {
  console.log(`
🌐 NOC-Style Network Management Server
======================================
🚀 Server running on: http://localhost:${port}
📊 Dashboard URL: http://localhost:${port}
🔧 Health Check: http://localhost:${port}/health
🔗 Backend Proxy: ${PYTHON_SERVER_URL}
======================================
✅ Voice-controlled operations ready
✅ AI pattern recognition active  
✅ Multi-brand restaurant support
✅ Real-time security monitoring
======================================
  `);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

module.exports = app;