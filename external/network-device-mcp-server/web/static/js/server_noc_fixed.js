const express = require('express');
const http = require('http');
const path = require('path');

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
    version: '1.0.0-noc-fixed',
    features: ['voice-control', 'noc-interface', 'simplified-proxy']
  });
});

// Simple proxy to Python Flask server - no external dependencies
app.use('/api', (req, res) => {
  // Parse request body for POST requests
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });
  
  req.on('end', () => {
    const options = {
      hostname: 'localhost',
      port: 5000,
      path: req.originalUrl,
      method: req.method,
      headers: req.headers
    };

    // Remove host header to avoid conflicts
    delete options.headers.host;

    const proxy = http.request(options, (response) => {
      // Set CORS headers
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');

      // Copy status code and headers
      res.writeHead(response.statusCode, response.headers);
      
      // Pipe response back
      response.pipe(res, { end: true });
    });

    proxy.on('error', (err) => {
      console.error('Proxy error:', err);
      res.status(500).json({ 
        success: false, 
        error: 'Backend service unavailable',
        message: 'Make sure Python Flask server is running on port 5000',
        fix: 'Run: python rest_api_server.py'
      });
    });

    // Send request body for POST/PUT requests
    if (body && (req.method === 'POST' || req.method === 'PUT')) {
      proxy.write(body);
    }
    
    proxy.end();
  });
});

// Handle CORS preflight requests
app.options('/api/*', (req, res) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.sendStatus(200);
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: 'Check server logs for details'
  });
});

// Start server
const server = app.listen(port, () => {
  console.log(`
🌐 NOC-Style Network Management Interface - FIXED
========================================
🚀 Server running on: http://localhost:${port}
📊 Backend API: http://localhost:5000
🔧 Health Check: http://localhost:${port}/health
========================================
✅ Professional NOC interface ready
✅ Voice controls integrated  
✅ Clean dark theme applied
✅ Simplified proxy (no external deps)
========================================

📋 STARTUP CHECKLIST:
1. ✅ Node.js server started (port ${port})
2. ⏳ Start Python server: python rest_api_server.py
3. 🌐 Access interface at: http://localhost:${port}

🔧 TROUBLESHOOTING:
- If API calls fail, ensure Python server is running
- Check Python server logs for backend issues
- Use /health endpoint to verify both servers
========================================
  `);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down NOC server...');
  server.close(() => {
    console.log('✅ NOC server stopped');
    process.exit(0);
  });
});

module.exports = app;