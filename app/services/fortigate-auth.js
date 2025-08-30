const axios = require('axios');
const https = require('https');
const logger = require('../utils/logger');

class FortiGateAuth {
  constructor(config) {
    this.host = config.host;
    this.username = config.username;
    this.password = config.password;
    this.port = config.port || 443;
    this.vdom = config.vdom || 'root';
    this.session = null;
    
    // Create axios instance with custom config
    this.client = axios.create({
      baseURL: `https://${this.host}:${this.port}`,
      timeout: 30000,
      httpsAgent: new https.Agent({
        rejectUnauthorized: false // FortiGate often uses self-signed certs
      })
    });
  }

  async authenticate() {
    try {
      const loginData = {
        username: this.username,
        secretkey: this.password,
        ajax: 1
      };

      const response = await this.client.post('/logincheck', loginData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // Extract session cookie
      const cookies = response.headers['set-cookie'];
      if (cookies) {
        this.session = cookies.find(cookie => cookie.includes('ccsrftoken'));
        logger.info('FortiGate authentication successful');
        return true;
      }

      logger.error('FortiGate authentication failed - no session cookie');
      return false;
    } catch (error) {
      logger.error('FortiGate authentication error:', error.message);
      return false;
    }
  }

  async testConnection() {
    try {
      const response = await this.client.get('/api/v2/monitor/system/status', {
        headers: this.getAuthHeaders()
      });

      return response.status === 200;
    } catch (error) {
      logger.error('FortiGate connection test failed:', error.message);
      return false;
    }
  }

  async makeRequest(endpoint, method = 'GET', data = null) {
    if (!this.session) {
      const authenticated = await this.authenticate();
      if (!authenticated) {
        throw new Error('Authentication failed');
      }
    }

    try {
      const config = {
        method,
        url: endpoint,
        headers: this.getAuthHeaders()
      };

      if (data) {
        config.data = data;
      }

      const response = await this.client.request(config);
      return response.data;
    } catch (error) {
      // Try re-authentication on 401
      if (error.response && error.response.status === 401) {
        this.session = null;
        const authenticated = await this.authenticate();
        if (authenticated) {
          return this.makeRequest(endpoint, method, data);
        }
      }
      throw error;
    }
  }

  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (this.session) {
      headers['Cookie'] = this.session;
    }

    return headers;
  }

  // Topology-specific API methods
  async getTopologyData() {
    try {
      const data = await this.makeRequest('/api/v2/monitor/system/security-fabric/topology');
      return this.normalizeTopologyData(data);
    } catch (error) {
      logger.error('Failed to fetch topology data:', error.message);
      throw error;
    }
  }

  async getDeviceStatus() {
    try {
      const data = await this.makeRequest('/api/v2/monitor/system/security-fabric/devices');
      return data;
    } catch (error) {
      logger.error('Failed to fetch device status:', error.message);
      throw error;
    }
  }

  async getInterfaceStatus() {
    try {
      const data = await this.makeRequest('/api/v2/monitor/system/interface');
      return data;
    } catch (error) {
      logger.error('Failed to fetch interface status:', error.message);
      throw error;
    }
  }

  normalizeTopologyData(rawData) {
    // Normalize FortiGate API data to common topology format
    return {
      nodes: this.extractNodes(rawData),
      links: this.extractLinks(rawData),
      metadata: {
        timestamp: new Date().toISOString(),
        source: 'fortigate',
        version: rawData.version
      }
    };
  }

  extractNodes(data) {
    const nodes = [];
    
    if (data.results && data.results.devices) {
      data.results.devices.forEach(device => {
        nodes.push({
          id: device.serial || device.name,
          name: device.name,
          type: device.type || 'device',
          status: device.status,
          ip: device.ip,
          model: device.model,
          version: device.version,
          risk: device.security_rating || 'unknown',
          vendor: device.vendor || 'fortinet',
          os: device.os_type,
          uptime: device.uptime,
          location: device.location,
          group: device.group || 'default'
        });
      });
    }
    
    return nodes;
  }

  extractLinks(data) {
    const links = [];
    
    if (data.results && data.results.links) {
      data.results.links.forEach(link => {
        links.push({
          id: `${link.source}-${link.target}`,
          source: link.source,
          target: link.target,
          type: link.type || 'connection',
          status: link.status || 'up',
          bandwidth: link.bandwidth,
          utilization: link.utilization,
          latency: link.latency
        });
      });
    }
    
    return links;
  }
}

module.exports = FortiGateAuth;