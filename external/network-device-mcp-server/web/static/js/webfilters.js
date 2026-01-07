/**
 * Web Filters Dashboard Functions
 * Handles web filtering policies, SSL certificates, and content analysis
 */

/**
 * Load Web Filters dashboard data
 */
async function loadWebFiltersData() {
    const content = document.getElementById('webfiltersContent');
    
    try {
        showLoading(true, 'Loading Web Filters data...');
        
        // Check web filters status
        const statusResponse = await apiCall('/api/webfilters/status');
        
        if (statusResponse.success) {
            renderWebFiltersDashboard(statusResponse);
        } else {
            content.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load Web Filters status: ${statusResponse.error}
                </div>
            `;
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        content.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-times-circle"></i>
                Error loading Web Filters data: ${error.message}
            </div>
        `;
        console.error('Error loading Web Filters data:', error);
    }
}

/**
 * Render Web Filters dashboard
 */
function renderWebFiltersDashboard(statusData) {
    const content = document.getElementById('webfiltersContent');
    
    content.innerHTML = `
        <div class="webfilters-dashboard">
            <!-- Application Status -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-info-circle"></i> Application Status</h3>
                </div>
                <div class="card-content">
                    <div class="status-grid">
                        <div class="status-item">
                            <div class="status-label">Application Ready:</div>
                            <div class="status-value ${statusData.application_ready ? 'success' : 'error'}">
                                <i class="fas ${statusData.application_ready ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                                ${statusData.application_ready ? 'Ready' : 'Not Ready'}
                            </div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">Server Running:</div>
                            <div class="status-value ${statusData.server_running ? 'success' : 'warning'}">
                                <i class="fas ${statusData.server_running ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                                ${statusData.server_running ? 'Running' : 'Stopped'}
                            </div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">Server URL:</div>
                            <div class="status-value">
                                <a href="${statusData.server_url}" target="_blank">${statusData.server_url}</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="server-actions">
                        ${!statusData.server_running ? `
                            <button class="btn btn-success" onclick="startWebFiltersServer()">
                                <i class="fas fa-play"></i>
                                Start Server
                            </button>
                        ` : `
                            <button class="btn btn-danger" onclick="stopWebFiltersServer()">
                                <i class="fas fa-stop"></i>
                                Stop Server
                            </button>
                        `}
                    </div>
                </div>
            </div>

            <!-- Available Features -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-cogs"></i> Available Features</h3>
                </div>
                <div class="card-content">
                    <div class="features-grid">
                        ${statusData.features.map(feature => `
                            <div class="feature-card ${feature.available ? 'available' : 'unavailable'}">
                                <div class="feature-status">
                                    <i class="fas ${feature.available ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                                </div>
                                <div class="feature-info">
                                    <h4>${feature.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                                    <p>${feature.description}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-bolt"></i> Quick Actions</h3>
                </div>
                <div class="card-content">
                    <div class="quick-actions-grid">
                        <button class="action-btn" onclick="viewWebFilteringPolicies()" ${!statusData.server_running ? 'disabled' : ''}>
                            <i class="fas fa-shield-alt"></i>
                            <span>View Policies</span>
                        </button>
                        <button class="action-btn" onclick="viewWebFilterAnalytics()" ${!statusData.server_running ? 'disabled' : ''}>
                            <i class="fas fa-chart-line"></i>
                            <span>Filter Analytics</span>
                        </button>
                        <button class="action-btn" onclick="viewSSLCertificateStatus()" ${!statusData.server_running ? 'disabled' : ''}>
                            <i class="fas fa-certificate"></i>
                            <span>SSL Status</span>
                        </button>
                        <button class="action-btn" onclick="searchWebFilterLogs()" ${!statusData.server_running ? 'disabled' : ''}>
                            <i class="fas fa-search"></i>
                            <span>Search Logs</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Store Web Filter Configuration -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-store"></i> Store Configuration</h3>
                </div>
                <div class="card-content">
                    <div class="store-config-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="webfilterBrand">Brand:</label>
                                <select id="webfilterBrand" class="form-control">
                                    <option value="">Select Brand</option>
                                    <option value="BWW">Buffalo Wild Wings</option>
                                    <option value="ARBYS">Arby's</option>
                                    <option value="SONIC">Sonic Drive-In</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="webfilterStoreId">Store ID:</label>
                                <input type="text" id="webfilterStoreId" class="form-control" placeholder="e.g., 155">
                            </div>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" onclick="viewStoreWebFilters()" ${!statusData.server_running ? 'disabled' : ''}>
                                <i class="fas fa-eye"></i>
                                View Store Configuration
                            </button>
                        </div>
                    </div>
                    
                    <div id="storeConfigResults" class="store-config-results" style="display: none;">
                        <!-- Results will be populated here -->
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Start Web Filters server
 */
async function startWebFiltersServer() {
    try {
        showLoading(true, 'Starting Web Filters server...');
        
        const response = await apiCall('/api/webfilters/server/start', {
            method: 'POST'
        });
        
        if (response.success) {
            showToast('Web Filters server started successfully', 'success');
            // Reload the dashboard to reflect the new status
            await loadWebFiltersData();
        } else {
            showToast(`Failed to start server: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error starting Web Filters server', 'error');
        console.error('Error starting server:', error);
    }
}

/**
 * Stop Web Filters server
 */
async function stopWebFiltersServer() {
    try {
        showLoading(true, 'Stopping Web Filters server...');
        
        const response = await apiCall('/api/webfilters/server/stop', {
            method: 'POST'
        });
        
        if (response.success) {
            showToast('Web Filters server stopped', 'info');
            // Reload the dashboard to reflect the new status
            await loadWebFiltersData();
        } else {
            showToast(`Failed to stop server: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error stopping Web Filters server', 'error');
        console.error('Error stopping server:', error);
    }
}

/**
 * View web filtering policies
 */
async function viewWebFilteringPolicies() {
    try {
        showLoading(true, 'Loading web filtering policies...');
        
        const response = await apiCall('/api/webfilters/policies');
        
        if (response.success) {
            renderWebFilteringPoliciesModal(response);
        } else {
            showToast(`Failed to load policies: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error loading web filtering policies', 'error');
        console.error('Error loading policies:', error);
    }
}

/**
 * View web filter analytics
 */
async function viewWebFilterAnalytics() {
    try {
        showLoading(true, 'Loading web filter analytics...');
        
        const response = await apiCall('/api/webfilters/analytics?timeframe=24h');
        
        if (response.success) {
            renderWebFilterAnalyticsModal(response);
        } else {
            showToast(`Failed to load analytics: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error loading web filter analytics', 'error');
        console.error('Error loading analytics:', error);
    }
}

/**
 * View SSL certificate status
 */
async function viewSSLCertificateStatus() {
    try {
        showLoading(true, 'Loading SSL certificate status...');
        
        const response = await apiCall('/api/webfilters/ssl/status');
        
        if (response.success) {
            renderSSLCertificateStatusModal(response);
        } else {
            showToast(`Failed to load SSL status: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error loading SSL certificate status', 'error');
        console.error('Error loading SSL status:', error);
    }
}

/**
 * Search web filter logs
 */
function searchWebFilterLogs() {
    // Navigate to the unified log analysis section
    showSection('log-analysis');
    // Pre-select Web Filters as the log source
    document.getElementById('logSearchSource').value = 'webfilters';
}

/**
 * View store web filters configuration
 */
async function viewStoreWebFilters() {
    const brand = document.getElementById('webfilterBrand').value;
    const storeId = document.getElementById('webfilterStoreId').value;
    
    if (!brand || !storeId) {
        showToast('Please select both brand and store ID', 'warning');
        return;
    }
    
    try {
        showLoading(true, 'Loading store web filter configuration...');
        
        const response = await apiCall(`/api/webfilters/${brand}/${storeId}`);
        
        if (response.success) {
            renderStoreWebFilterResults(response);
        } else {
            showToast(`Failed to load store configuration: ${response.error}`, 'error');
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error loading store web filter configuration', 'error');
        console.error('Error loading store configuration:', error);
    }
}

/**
 * Render store web filter results
 */
function renderStoreWebFilterResults(data) {
    const resultsContainer = document.getElementById('storeConfigResults');
    
    resultsContainer.innerHTML = `
        <div class="store-results">
            <div class="results-header">
                <h4>Web Filter Configuration</h4>
                <div class="store-info">
                    <span class="store-name">${data.device_name}</span>
                    <span class="store-brand">${data.brand}</span>
                </div>
            </div>
            
            <div class="config-tabs">
                <button class="tab-btn active" onclick="showWebFilterTab('policies')">
                    <i class="fas fa-shield-alt"></i>
                    Active Policies
                </button>
                <button class="tab-btn" onclick="showWebFilterTab('categories')">
                    <i class="fas fa-ban"></i>
                    Blocked Categories
                </button>
                <button class="tab-btn" onclick="showWebFilterTab('exceptions')">
                    <i class="fas fa-check"></i>
                    Exceptions
                </button>
                <button class="tab-btn" onclick="showWebFilterTab('effectiveness')">
                    <i class="fas fa-chart-pie"></i>
                    Effectiveness
                </button>
            </div>

            <div id="webfilter-policies" class="tab-content active">
                <div class="policies-list">
                    ${(data.active_policies || []).map(policy => `
                        <div class="policy-item">
                            <div class="policy-name">${policy}</div>
                        </div>
                    `).join('') || '<p>No active policies found</p>'}
                </div>
            </div>

            <div id="webfilter-categories" class="tab-content">
                <div class="categories-list">
                    ${(data.blocked_categories || []).map(category => `
                        <div class="category-item">
                            <div class="category-name">${category}</div>
                        </div>
                    `).join('') || '<p>No blocked categories found</p>'}
                </div>
            </div>

            <div id="webfilter-exceptions" class="tab-content">
                <div class="exceptions-list">
                    ${(data.allowed_exceptions || []).map(exception => `
                        <div class="exception-item">
                            <div class="exception-name">${exception}</div>
                        </div>
                    `).join('') || '<p>No exceptions configured</p>'}
                </div>
            </div>

            <div id="webfilter-effectiveness" class="tab-content">
                <div class="effectiveness-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${data.filter_effectiveness?.block_rate || 'N/A'}</div>
                        <div class="metric-label">Block Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.filter_effectiveness?.total_requests || 'N/A'}</div>
                        <div class="metric-label">Total Requests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.filter_effectiveness?.blocked_requests || 'N/A'}</div>
                        <div class="metric-label">Blocked Requests</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.style.display = 'block';
}

/**
 * Show web filter tab
 */
function showWebFilterTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and content
    event.target.classList.add('active');
    document.getElementById(`webfilter-${tabName}`).classList.add('active');
}

/**
 * Modal rendering functions
 */
function renderWebFilteringPoliciesModal(data) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content large">
            <div class="modal-header">
                <h2><i class="fas fa-shield-alt"></i> Web Filtering Policies</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="policies-summary">
                    <p><strong>Total Policies:</strong> ${data.total_policies || 0}</p>
                    <p><strong>Query Time:</strong> ${new Date(data.query_time).toLocaleString()}</p>
                </div>
                
                <div class="policies-list">
                    ${(data.policies || []).map(policy => `
                        <div class="policy-card">
                            <h4>${policy.name || 'Unnamed Policy'}</h4>
                            <p>${policy.description || 'No description available'}</p>
                        </div>
                    `).join('') || '<p>No policies found</p>'}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function renderWebFilterAnalyticsModal(data) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content large">
            <div class="modal-header">
                <h2><i class="fas fa-chart-line"></i> Web Filter Analytics</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="analytics-summary">
                    <div class="summary-metrics">
                        <div class="metric">
                            <div class="metric-value">${data.analytics?.total_requests || 0}</div>
                            <div class="metric-label">Total Requests</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.analytics?.blocked_requests || 0}</div>
                            <div class="metric-label">Blocked Requests</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.analytics?.block_rate || 0}%</div>
                            <div class="metric-label">Block Rate</div>
                        </div>
                    </div>
                </div>
                
                <div class="top-blocked">
                    <h3>Top Blocked Categories</h3>
                    <div class="blocked-categories-list">
                        ${(data.analytics?.top_blocked_categories || []).map(category => `
                            <div class="blocked-category">
                                <span class="category-name">${category.name}</span>
                                <span class="category-count">${category.count}</span>
                            </div>
                        `).join('') || '<p>No blocked categories data</p>'}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function renderSSLCertificateStatusModal(data) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content large">
            <div class="modal-header">
                <h2><i class="fas fa-certificate"></i> SSL Certificate Status</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="ssl-status-grid">
                    <div class="status-section">
                        <h3>Certificate Management</h3>
                        <div class="status-items">
                            <div class="status-item">
                                <span class="label">Certificates Managed:</span>
                                <span class="value">${data.ssl_status?.certificates_managed || 0}</span>
                            </div>
                            <div class="status-item">
                                <span class="label">Expiring Soon:</span>
                                <span class="value">${data.ssl_status?.expiring_soon?.length || 0}</span>
                            </div>
                            <div class="status-item">
                                <span class="label">Auto Renewal:</span>
                                <span class="value ${data.ssl_status?.auto_renewal_enabled ? 'success' : 'warning'}">
                                    ${data.ssl_status?.auto_renewal_enabled ? 'Enabled' : 'Disabled'}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="status-section">
                        <h3>Vault Integration</h3>
                        <div class="status-items">
                            <div class="status-item">
                                <span class="label">Connection:</span>
                                <span class="value ${data.vault_integration?.connected ? 'success' : 'error'}">
                                    ${data.vault_integration?.connected ? 'Connected' : 'Disconnected'}
                                </span>
                            </div>
                            <div class="status-item">
                                <span class="label">Secrets Count:</span>
                                <span class="value">${data.vault_integration?.secrets_count || 0}</span>
                            </div>
                            <div class="status-item">
                                <span class="label">Last Sync:</span>
                                <span class="value">${data.vault_integration?.last_sync || 'Never'}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${data.ssl_status?.expiring_soon?.length > 0 ? `
                    <div class="expiring-certificates">
                        <h3>Expiring Soon</h3>
                        <div class="certificates-list">
                            ${data.ssl_status.expiring_soon.map(cert => `
                                <div class="certificate-item warning">
                                    <span class="cert-name">${cert.name}</span>
                                    <span class="cert-expiry">${cert.expires}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}