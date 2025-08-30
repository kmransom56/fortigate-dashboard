import './styles/main.css';
import TopologyVisualization from './components/TopologyVisualization';
import { ApiService } from './services/apiService';
import { TokenManager } from './utils/tokenManager';

class App {
  constructor() {
    this.apiService = new ApiService();
    this.tokenManager = new TokenManager();
    this.topology = null;
    this.currentView = 'physical';
    this.currentGrouping = 'device-traffic';
    
    this.init();
  }

  async init() {
    try {
      // Load design tokens
      await this.tokenManager.loadTokens();
      
      // Apply tokens to CSS variables
      this.tokenManager.applyTokens();
      
      // Initialize UI components
      this.initializeUI();
      
      // Load topology data
      await this.loadTopologyData();
      
      // Initialize topology visualization
      this.initializeTopology();
      
      console.log('FortiGate Topology Clone initialized successfully');
    } catch (error) {
      console.error('Failed to initialize application:', error);
      this.showError('Failed to initialize application');
    }
  }

  initializeUI() {
    // Create main layout
    const app = document.getElementById('app');
    app.innerHTML = `
      <div class="topology-app">
        <header class="topology-header">
          <h1>FortiGate Security Fabric Topology</h1>
          <div class="topology-controls">
            <div class="view-selector">
              <button class="view-btn active" data-view="physical">Physical</button>
              <button class="view-btn" data-view="logical">Logical</button>
            </div>
            <div class="grouping-selector">
              <select id="grouping-select">
                <option value="device-traffic">Device Traffic</option>
                <option value="device-count">Device Count</option>
                <option value="os">Operating System</option>
                <option value="vendor">Vendor</option>
                <option value="risk">Security Risk</option>
              </select>
            </div>
            <button id="refresh-btn" class="refresh-btn">
              <span class="refresh-icon">↻</span>
              Refresh
            </button>
          </div>
        </header>
        
        <main class="topology-main">
          <div class="topology-sidebar">
            <div class="legend-panel">
              <h3>Legend</h3>
              <div id="legend-content"></div>
            </div>
            
            <div class="stats-panel">
              <h3>Statistics</h3>
              <div id="stats-content"></div>
            </div>
          </div>
          
          <div class="topology-canvas-container">
            <div id="topology-canvas"></div>
            <div class="topology-overlay">
              <div id="loading-indicator" class="loading hidden">
                <div class="spinner"></div>
                <span>Loading topology...</span>
              </div>
              <div id="error-message" class="error-message hidden"></div>
            </div>
          </div>
        </main>
        
        <div id="tooltip" class="topology-tooltip hidden"></div>
        <div id="context-menu" class="context-menu hidden"></div>
      </div>
    `;

    // Bind event listeners
    this.bindEventListeners();
  }

  bindEventListeners() {
    // View switching
    document.querySelectorAll('.view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.target.dataset.view;
        this.switchView(view);
      });
    });

    // Grouping change
    document.getElementById('grouping-select').addEventListener('change', (e) => {
      this.changeGrouping(e.target.value);
    });

    // Refresh
    document.getElementById('refresh-btn').addEventListener('click', () => {
      this.refreshTopology();
    });

    // Window resize
    window.addEventListener('resize', () => {
      if (this.topology) {
        this.topology.handleResize();
      }
    });
  }

  async loadTopologyData() {
    try {
      this.showLoading(true);
      
      const data = await this.apiService.getTopologyData();
      this.topologyData = data;
      
      this.updateStats(data);
      this.updateLegend();
      
    } catch (error) {
      console.error('Failed to load topology data:', error);
      this.showError('Failed to load topology data');
      throw error;
    } finally {
      this.showLoading(false);
    }
  }

  initializeTopology() {
    const container = document.getElementById('topology-canvas');
    
    this.topology = new TopologyVisualization(container, {
      data: this.topologyData,
      view: this.currentView,
      grouping: this.currentGrouping,
      tokens: this.tokenManager.getTokens(),
      onNodeClick: this.handleNodeClick.bind(this),
      onNodeHover: this.handleNodeHover.bind(this),
      onNodeRightClick: this.handleNodeRightClick.bind(this),
      onBackgroundClick: this.handleBackgroundClick.bind(this)
    });

    this.topology.render();
  }

  switchView(view) {
    if (view === this.currentView) return;

    this.currentView = view;
    
    // Update UI
    document.querySelectorAll('.view-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update topology
    if (this.topology) {
      this.topology.setView(view);
      this.updateLegend();
    }
  }

  changeGrouping(grouping) {
    if (grouping === this.currentGrouping) return;

    this.currentGrouping = grouping;
    
    if (this.topology) {
      this.topology.setGrouping(grouping);
      this.updateLegend();
    }
  }

  async refreshTopology() {
    try {
      await this.loadTopologyData();
      
      if (this.topology) {
        this.topology.updateData(this.topologyData);
      }
      
      this.showMessage('Topology refreshed successfully', 'success');
    } catch (error) {
      console.error('Failed to refresh topology:', error);
      this.showError('Failed to refresh topology');
    }
  }

  updateStats(data) {
    const statsContent = document.getElementById('stats-content');
    const stats = this.calculateStats(data);
    
    statsContent.innerHTML = `
      <div class="stat-item">
        <span class="stat-label">Total Devices</span>
        <span class="stat-value">${stats.totalDevices}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Online</span>
        <span class="stat-value stat-success">${stats.onlineDevices}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Offline</span>
        <span class="stat-value stat-error">${stats.offlineDevices}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">High Risk</span>
        <span class="stat-value stat-warning">${stats.highRiskDevices}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Total Links</span>
        <span class="stat-value">${stats.totalLinks}</span>
      </div>
    `;
  }

  calculateStats(data) {
    const nodes = data.nodes || [];
    const links = data.links || [];
    
    return {
      totalDevices: nodes.length,
      onlineDevices: nodes.filter(n => n.status === 'up').length,
      offlineDevices: nodes.filter(n => n.status === 'down').length,
      highRiskDevices: nodes.filter(n => n.risk === 'high' || n.risk === 'critical').length,
      totalLinks: links.length
    };
  }

  updateLegend() {
    const legendContent = document.getElementById('legend-content');
    const legend = this.getLegendForGrouping(this.currentGrouping);
    
    let legendHtml = '';
    for (const [key, config] of Object.entries(legend)) {
      legendHtml += `
        <div class="legend-item">
          <div class="legend-color" style="background-color: ${config.color}"></div>
          <span class="legend-label">${config.label}</span>
        </div>
      `;
    }
    
    legendContent.innerHTML = legendHtml;
  }

  getLegendForGrouping(grouping) {
    const tokens = this.tokenManager.getTokens();
    
    switch (grouping) {
      case 'risk':
        return {
          critical: { color: tokens.colors['severity-critical'], label: 'Critical' },
          high: { color: tokens.colors['severity-high'], label: 'High' },
          medium: { color: tokens.colors['severity-medium'], label: 'Medium' },
          low: { color: tokens.colors['severity-low'], label: 'Low' }
        };
      case 'vendor':
        return {
          fortinet: { color: tokens.colors['vendor-fortinet'], label: 'Fortinet' },
          cisco: { color: tokens.colors['vendor-cisco'], label: 'Cisco' },
          juniper: { color: tokens.colors['vendor-juniper'], label: 'Juniper' },
          other: { color: tokens.colors['vendor-other'], label: 'Other' }
        };
      case 'os':
        return {
          fortios: { color: tokens.colors['os-fortios'], label: 'FortiOS' },
          ios: { color: tokens.colors['os-ios'], label: 'Cisco IOS' },
          junos: { color: tokens.colors['os-junos'], label: 'Junos' },
          other: { color: tokens.colors['os-other'], label: 'Other' }
        };
      default:
        return {
          device: { color: tokens.colors['device-default'], label: 'Device' },
          link: { color: tokens.colors['link-default'], label: 'Link' }
        };
    }
  }

  handleNodeClick(node, event) {
    console.log('Node clicked:', node);
    // Implement node selection/details
  }

  handleNodeHover(node, event) {
    if (node) {
      this.showTooltip(node, event);
    } else {
      this.hideTooltip();
    }
  }

  handleNodeRightClick(node, event) {
    event.preventDefault();
    this.showContextMenu(node, event);
  }

  handleBackgroundClick(event) {
    this.hideTooltip();
    this.hideContextMenu();
  }

  showTooltip(node, event) {
    const tooltip = document.getElementById('tooltip');
    
    tooltip.innerHTML = `
      <div class="tooltip-header">
        <strong>${node.name}</strong>
      </div>
      <div class="tooltip-content">
        <div>Type: ${node.type}</div>
        <div>Status: ${node.status}</div>
        <div>IP: ${node.ip || 'N/A'}</div>
        <div>Model: ${node.model || 'N/A'}</div>
        <div>Risk: ${node.risk || 'Unknown'}</div>
      </div>
    `;
    
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY - 10 + 'px';
    tooltip.classList.remove('hidden');
  }

  hideTooltip() {
    document.getElementById('tooltip').classList.add('hidden');
  }

  showContextMenu(node, event) {
    const contextMenu = document.getElementById('context-menu');
    
    contextMenu.innerHTML = `
      <div class="context-item" onclick="app.viewNodeDetails('${node.id}')">
        View Details
      </div>
      <div class="context-item" onclick="app.pingNode('${node.id}')">
        Ping Device
      </div>
      <div class="context-item" onclick="app.showNodeLogs('${node.id}')">
        View Logs
      </div>
    `;
    
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
    contextMenu.classList.remove('hidden');
  }

  hideContextMenu() {
    document.getElementById('context-menu').classList.add('hidden');
  }

  showLoading(show) {
    const loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.classList.toggle('hidden', !show);
  }

  showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
    
    setTimeout(() => {
      errorElement.classList.add('hidden');
    }, 5000);
  }

  showMessage(message, type = 'info') {
    // Create temporary message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
      messageDiv.remove();
    }, 3000);
  }

  // Context menu actions
  viewNodeDetails(nodeId) {
    console.log('View details for node:', nodeId);
    this.hideContextMenu();
  }

  pingNode(nodeId) {
    console.log('Ping node:', nodeId);
    this.hideContextMenu();
  }

  showNodeLogs(nodeId) {
    console.log('Show logs for node:', nodeId);
    this.hideContextMenu();
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});

export default App;