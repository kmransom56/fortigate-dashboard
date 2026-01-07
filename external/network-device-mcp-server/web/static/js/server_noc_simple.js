const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const port = process.env.PORT || 5001;

// Basic middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'web')));

// Serve the NOC-style interface
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'web/templates/index_noc_style.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.0-noc',
    features: ['voice-control', 'noc-interface']
  });
});

// Simple proxy to Python Flask server
app.use('/api', (req, res) => {
  const http = require('http');
  const options = {
    hostname: 'localhost',
    port: 5000,
    path: req.originalUrl,
    method: req.method,
    headers: req.headers
  };

  const proxy = http.request(options, (response) => {
    res.writeHead(response.statusCode, response.headers);
    response.pipe(res, { end: true });
  });

  req.pipe(proxy, { end: true });

  proxy.on('error', (err) => {
    console.error('Proxy error:', err);
    res.status(500).json({ 
      success: false, 
      error: 'Backend service unavailable' 
    });
  });
});

// Start server
const server = app.listen(port, () => {
  console.log(`
🌐 NOC-Style Network Management Interface
========================================
🚀 Server running on: http://localhost:${port}
📊 Backend API: http://localhost:5000
🔧 Health Check: http://localhost:${port}/health
========================================
✅ Professional NOC interface ready
✅ Voice controls integrated
✅ Clean dark theme applied
========================================
  `);
});

module.exports = app;