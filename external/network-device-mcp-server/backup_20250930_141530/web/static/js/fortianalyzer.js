/**
 * FortiAnalyzer Dashboard Functions
 * Handles FortiAnalyzer log analysis, threat intelligence, and security reporting
 */

/**
 * Load FortiAnalyzer dashboard data
 */
async function loadFortiAnalyzerData() {
    const content = document.getElementById('fortianalyzerContent');
    
    try {
        showLoading(true, 'Loading FortiAnalyzer data...');
        
        // Load FortiAnalyzer instances
        const instancesResponse = await apiCall('/api/fortianalyzer/instances');
        
        if (instancesResponse.success) {
            renderFortiAnalyzerDashboard(instancesResponse.fortianalyzer_instances);
        } else {
            content.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load FortiAnalyzer instances: ${instancesResponse.error}
                </div>
            `;
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        content.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-times-circle"></i>
                Error loading FortiAnalyzer data: ${error.message}
            </div>
        `;
        console.error('Error loading FortiAnalyzer data:', error);
    }
}

/**
 * Render FortiAnalyzer dashboard
 */
function renderFortiAnalyzerDashboard(instances) {
    const content = document.getElementById('fortianalyzerContent');
    
    content.innerHTML = `
        <div class="fortianalyzer-dashboard">
            <!-- FortiAnalyzer Instances -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-server"></i> FortiAnalyzer Instances</h3>
                </div>
                <div class="card-content">
                    <div class="faz-instances-grid">
                        ${instances.map(instance => `
                            <div class="faz-instance-card">
                                <div class="instance-header">
                                    <div class="instance-name">${instance.name}</div>
                                    <div class="instance-status ${instance.status}">
                                        <i class="fas fa-circle"></i>
                                        ${instance.status}
                                    </div>
                                </div>
                                <div class="instance-details">
                                    <div class="detail-item">
                                        <span class="label">Host:</span>
                                        <span class="value">${instance.host}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="label">ADOM:</span>
                                        <span class="value">${instance.adom}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="label">Version:</span>
                                        <span class="value">${instance.version}</span>
                                    </div>
                                </div>
                                <div class="instance-actions">
                                    <button class="btn btn-sm btn-primary" onclick="viewInstanceAnalytics('${instance.name}')">
                                        <i class="fas fa-chart-line"></i>
                                        Analytics
                                    </button>
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
                        <button class="action-btn" onclick="showThreatIntelligence()">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span>Threat Intelligence</span>
                        </button>
                        <button class="action-btn" onclick="showLogAnalytics()">
                            <i class="fas fa-chart-bar"></i>
                            <span>Log Analytics</span>
                        </button>
                        <button class="action-btn" onclick="generateSecurityReport()">
                            <i class="fas fa-file-alt"></i>
                            <span>Security Report</span>
                        </button>
                        <button class="action-btn" onclick="searchSecurityLogs()">
                            <i class="fas fa-search"></i>
                            <span>Search Logs</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Brand Threat Overview -->
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-shield-alt"></i> Brand Threat Overview</h3>
                    <div class="header-actions">
                        <select id="threatTimeframe" onchange="refreshThreatOverview()" class="form-control">
                            <option value="1h">Last Hour</option>
                            <option value="24h" selected>Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                        </select>
                    </div>
                </div>
                <div class="card-content">
                    <div id="threatOverviewContent">
                        <div class="loading-placeholder">
                            <i class="fas fa-spinner fa-spin"></i>
                            Loading threat overview...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Load initial threat overview
    refreshThreatOverview();
}

/**
 * Show threat intelligence for all brands
 */
async function showThreatIntelligence() {
    try {
        showLoading(true, 'Loading threat intelligence...');
        
        const brands = ['BWW', 'ARBYS', 'SONIC'];
        const threatData = {};
        
        // Load threat intelligence for each brand
        for (const brand of brands) {
            const response = await apiCall(`/api/fortianalyzer/threats/${brand}`);
            if (response.success) {
                threatData[brand] = response;
            }
        }
        
        renderThreatIntelligenceDashboard(threatData);
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showToast('Failed to load threat intelligence', 'error');
        console.error('Error loading threat intelligence:', error);
    }
}

/**
 * Render threat intelligence dashboard
 */
function renderThreatIntelligenceDashboard(threatData) {
    const content = document.getElementById('fortianalyzerContent');
    
    content.innerHTML = `
        <div class="threat-intelligence-dashboard">
            <div class="section-header">
                <h2><i class="fas fa-exclamation-triangle"></i> Threat Intelligence Summary</h2>
                <button class="btn btn-secondary" onclick="loadFortiAnalyzerData()">
                    <i class="fas fa-arrow-left"></i>
                    Back to Overview
                </button>
            </div>
            
            <div class="threat-stats-grid">
                ${Object.entries(threatData).map(([brand, data]) => `
                    <div class="brand-threat-card">
                        <div class="brand-header">
                            <h3>${getBrandDisplayName(brand)}</h3>
                            <div class="threat-summary">
                                <span class="threat-count">${data.threat_summary?.total_threats || 0}</span>
                                <span class="threat-label">Total Threats</span>
                            </div>
                        </div>
                        
                        <div class="threat-breakdown">
                            <div class="threat-item">
                                <span class="threat-type">Blocked:</span>
                                <span class="threat-value">${data.threat_summary?.blocked_threats || 0}</span>
                            </div>
                            <div class="threat-item">
                                <span class="threat-type">Malware:</span>
                                <span class="threat-value">${data.threat_summary?.malware_detections || 0}</span>
                            </div>
                            <div class="threat-item">
                                <span class="threat-type">Intrusion:</span>
                                <span class="threat-value">${data.threat_summary?.intrusion_attempts || 0}</span>
                            </div>
                            <div class="threat-item">
                                <span class="threat-type">Web Filter:</span>
                                <span class="threat-value">${data.threat_summary?.web_filtering_blocks || 0}</span>
                            </div>
                        </div>
                        
                        <div class="top-threats">
                            <h4>Top Threats:</h4>
                            ${(data.top_threats || []).slice(0, 3).map(threat => `
                                <div class="threat-entry">
                                    <span class="threat-name">${threat.name}</span>
                                    <span class="threat-count">${threat.count}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="threat-actions">
                            <button class="btn btn-sm btn-primary" onclick="viewBrandThreatDetails('${brand}')">
                                <i class="fas fa-eye"></i>
                                View Details
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Refresh threat overview data
 */
async function refreshThreatOverview() {
    const timeframe = document.getElementById('threatTimeframe')?.value || '24h';
    const content = document.getElementById('threatOverviewContent');
    
    try {
        content.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i> Loading threat overview...</div>';
        
        const brands = ['BWW', 'ARBYS', 'SONIC'];
        const overviewData = [];
        
        for (const brand of brands) {
            const response = await apiCall(`/api/fortianalyzer/threats/${brand}?timeframe=${timeframe}`);
            if (response.success) {
                overviewData.push({
                    brand,
                    data: response
                });
            }
        }
        
        content.innerHTML = `
            <div class="threat-overview-grid">
                ${overviewData.map(({ brand, data }) => `
                    <div class="threat-overview-card">
                        <div class="brand-name">${getBrandDisplayName(brand)}</div>
                        <div class="threat-metrics">
                            <div class="metric">
                                <div class="metric-value">${data.threat_summary?.total_threats || 0}</div>
                                <div class="metric-label">Total Threats</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.threat_summary?.blocked_threats || 0}</div>
                                <div class="metric-label">Blocked</div>
                            </div>
                        </div>
                        <div class="block-rate">
                            Block Rate: ${Math.round(((data.threat_summary?.blocked_threats || 0) / Math.max(data.threat_summary?.total_threats || 1, 1)) * 100)}%
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
    } catch (error) {
        content.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-times-circle"></i>
                Error loading threat overview: ${error.message}
            </div>
        `;
    }
}

/**
 * Show log analytics
 */
async function showLogAnalytics() {
    try {
        showLoading(true, 'Loading log analytics...');
        
        // Load analytics for all brands
        const analyticsResponse = await apiCall('/api/fortianalyzer/analytics');
        
        if (analyticsResponse.success) {
            renderLogAnalyticsDashboard(analyticsResponse.analytics);
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showToast('Failed to load log analytics', 'error');
        console.error('Error loading log analytics:', error);
    }
}

/**
 * Generate security report
 */
async function generateSecurityReport() {
    const brand = prompt('Enter brand code (BWW, ARBYS, SONIC):');
    const storeId = prompt('Enter store ID (optional):');
    
    if (!brand) return;
    
    try {
        showLoading(true, 'Generating security report...');
        
        const url = `/api/fortianalyzer/reports/${brand}${storeId ? `?store_id=${storeId}` : ''}`;
        const response = await apiCall(url);
        
        if (response.success) {
            renderSecurityReportModal(response);
            showToast('Security report generated successfully', 'success');
        } else {
            showToast('Failed to generate security report', 'error');
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showToast('Error generating security report', 'error');
        console.error('Error generating security report:', error);
    }
}

/**
 * Search security logs
 */
function searchSecurityLogs() {
    // Navigate to the unified log analysis section
    showSection('log-analysis');
    // Pre-select FortiAnalyzer as the log source
    document.getElementById('logSearchSource').value = 'fortianalyzer';
}

/**
 * Utility functions
 */
function getBrandDisplayName(brandCode) {
    const brandNames = {
        'BWW': 'Buffalo Wild Wings',
        'ARBYS': "Arby's",
        'SONIC': 'Sonic Drive-In'
    };
    return brandNames[brandCode] || brandCode;
}

function viewInstanceAnalytics(instanceName) {
    showToast(`Loading analytics for ${instanceName}...`, 'info');
    // Implementation for viewing specific instance analytics
}

function viewBrandThreatDetails(brand) {
    showToast(`Loading detailed threat analysis for ${getBrandDisplayName(brand)}...`, 'info');
    // Implementation for detailed threat analysis
}

function renderLogAnalyticsDashboard(analytics) {
    const content = document.getElementById('fortianalyzerContent');
    
    content.innerHTML = `
        <div class="log-analytics-dashboard">
            <div class="section-header">
                <h2><i class="fas fa-chart-bar"></i> Log Analytics</h2>
                <button class="btn btn-secondary" onclick="loadFortiAnalyzerData()">
                    <i class="fas fa-arrow-left"></i>
                    Back to Overview
                </button>
            </div>
            
            <div class="analytics-summary">
                <h3>Analytics Summary</h3>
                <p>Total brands analyzed: ${analytics.total_brands || 0}</p>
                <p>Overall health: ${analytics.overall_health || 'Unknown'}</p>
            </div>
            
            <div class="analytics-recommendations">
                <h4>Recommendations:</h4>
                <ul>
                    ${(analytics.recommendations || []).map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderSecurityReportModal(reportData) {
    // Create modal for security report
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content large">
            <div class="modal-header">
                <h2><i class="fas fa-file-alt"></i> Security Report</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="report-info">
                    <h3>Report Information</h3>
                    <p><strong>Brand:</strong> ${getBrandDisplayName(reportData.report_info?.brand)}</p>
                    <p><strong>Timeframe:</strong> ${reportData.report_info?.timeframe}</p>
                    <p><strong>Generated:</strong> ${new Date(reportData.report_info?.generation_time).toLocaleString()}</p>
                </div>
                
                <div class="executive-summary">
                    <h3>Executive Summary</h3>
                    <p><strong>Security Posture:</strong> ${reportData.executive_summary?.overall_security_posture}</p>
                    <p><strong>Events Analyzed:</strong> ${reportData.executive_summary?.total_events_analyzed}</p>
                    <p><strong>Threats Blocked:</strong> ${reportData.executive_summary?.threats_blocked}</p>
                </div>
                
                <div class="recommendations">
                    <h3>Recommendations</h3>
                    <ul>
                        ${(reportData.recommendations || []).map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}