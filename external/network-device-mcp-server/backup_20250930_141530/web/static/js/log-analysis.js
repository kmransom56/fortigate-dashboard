/**
 * Unified Log Analysis Functions
 * Handles searching and analyzing logs from FortiAnalyzer and Web Filters
 */

/**
 * Search logs across all sources
 */
async function searchLogs() {
    const query = document.getElementById('logSearchQuery').value.trim();
    const brand = document.getElementById('logSearchBrand').value;
    const timeframe = document.getElementById('logSearchTimeframe').value;
    const source = document.getElementById('logSearchSource').value;
    
    if (!query) {
        showToast('Please enter a search query', 'warning');
        return;
    }
    
    try {
        showLoading(true, 'Searching logs...');
        
        let searchResults = [];
        
        // Search based on selected source
        if (source === 'all' || source === 'fortianalyzer') {
            const fazResults = await searchFortiAnalyzerLogs(query, brand, timeframe);
            if (fazResults.length > 0) {
                searchResults = searchResults.concat(fazResults.map(result => ({
                    ...result,
                    source: 'FortiAnalyzer'
                })));
            }
        }
        
        if (source === 'all' || source === 'webfilters') {
            const wfResults = await searchWebFilterLogsData(query, brand, timeframe);
            if (wfResults.length > 0) {
                searchResults = searchResults.concat(wfResults.map(result => ({
                    ...result,
                    source: 'Web Filters'
                })));
            }
        }
        
        renderLogSearchResults(searchResults, {
            query,
            brand: brand || 'All Brands',
            timeframe,
            source: source === 'all' ? 'All Sources' : source
        });
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showToast('Error searching logs', 'error');
        console.error('Error searching logs:', error);
    }
}

/**
 * Search FortiAnalyzer logs
 */
async function searchFortiAnalyzerLogs(query, brand, timeframe) {
    try {
        const params = new URLSearchParams({
            query,
            timeframe
        });
        
        if (brand) {
            params.append('brand', brand);
        }
        
        const response = await apiCall(`/api/fortianalyzer/search?${params.toString()}`);
        
        if (response.success) {
            return response.results || [];
        } else {
            console.warn('FortiAnalyzer search failed:', response.error);
            return [];
        }
    } catch (error) {
        console.warn('Error searching FortiAnalyzer logs:', error);
        return [];
    }
}

/**
 * Search Web Filters logs
 */
async function searchWebFilterLogsData(query, brand, timeframe) {
    try {
        const params = new URLSearchParams({
            query,
            timeframe
        });
        
        if (brand) {
            params.append('brand', brand);
        }
        
        const response = await apiCall(`/api/webfilters/logs/search?${params.toString()}`);
        
        if (response.success) {
            return response.log_entries || [];
        } else {
            console.warn('Web Filters search failed:', response.error);
            return [];
        }
    } catch (error) {
        console.warn('Error searching Web Filters logs:', error);
        return [];
    }
}

/**
 * Render log search results
 */
function renderLogSearchResults(results, searchParams) {
    const resultsContainer = document.getElementById('logSearchResults');
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No Results Found</h3>
                <p>No log entries found matching your search criteria.</p>
                <div class="search-summary">
                    <p><strong>Query:</strong> ${searchParams.query}</p>
                    <p><strong>Brand:</strong> ${searchParams.brand}</p>
                    <p><strong>Timeframe:</strong> ${searchParams.timeframe}</p>
                    <p><strong>Source:</strong> ${searchParams.source}</p>
                </div>
            </div>
        `;
    } else {
        resultsContainer.innerHTML = `
            <div class="search-results">
                <div class="results-header">
                    <h3>Log Search Results</h3>
                    <div class="results-summary">
                        <span class="results-count">${results.length} entries found</span>
                        <div class="search-params">
                            <span><strong>Query:</strong> ${searchParams.query}</span>
                            <span><strong>Brand:</strong> ${searchParams.brand}</span>
                            <span><strong>Timeframe:</strong> ${searchParams.timeframe}</span>
                            <span><strong>Source:</strong> ${searchParams.source}</span>
                        </div>
                    </div>
                </div>
                
                <div class="results-filters">
                    <div class="filter-group">
                        <label>Filter by Source:</label>
                        <select id="sourceFilter" onchange="filterLogResults()">
                            <option value="">All Sources</option>
                            <option value="FortiAnalyzer">FortiAnalyzer</option>
                            <option value="Web Filters">Web Filters</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Filter by Severity:</label>
                        <select id="severityFilter" onchange="filterLogResults()">
                            <option value="">All Severities</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>
                </div>
                
                <div class="results-list" id="resultsListContent">
                    ${renderLogEntries(results)}
                </div>
                
                <div class="results-actions">
                    <button class="btn btn-secondary" onclick="exportLogResults()">
                        <i class="fas fa-download"></i>
                        Export Results
                    </button>
                    <button class="btn btn-primary" onclick="generateLogAnalysisReport()">
                        <i class="fas fa-file-alt"></i>
                        Generate Report
                    </button>
                </div>
            </div>
        `;
    }
    
    resultsContainer.style.display = 'block';
    
    // Store results for filtering and export
    window.currentLogResults = results;
    window.currentSearchParams = searchParams;
}

/**
 * Render individual log entries
 */
function renderLogEntries(entries) {
    return entries.map(entry => {
        const timestamp = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : 'Unknown';
        const severity = entry.severity || entry.level || 'info';
        const source = entry.source || 'Unknown';
        
        return `
            <div class="log-entry" data-source="${source}" data-severity="${severity}">
                <div class="log-header">
                    <div class="log-timestamp">${timestamp}</div>
                    <div class="log-source">${source}</div>
                    <div class="log-severity severity-${severity}">
                        <i class="fas fa-circle"></i>
                        ${severity.toUpperCase()}
                    </div>
                </div>
                <div class="log-content">
                    <div class="log-message">
                        ${entry.message || entry.matching_entry || entry.description || 'No message'}
                    </div>
                    ${entry.device ? `<div class="log-device">Device: ${entry.device}</div>` : ''}
                    ${entry.src_ip ? `<div class="log-source-ip">Source IP: ${entry.src_ip}</div>` : ''}
                    ${entry.dst_ip ? `<div class="log-dest-ip">Destination IP: ${entry.dst_ip}</div>` : ''}
                    ${entry.action ? `<div class="log-action">Action: ${entry.action}</div>` : ''}
                    ${entry.relevance_score ? `<div class="log-relevance">Relevance: ${Math.round(entry.relevance_score * 100)}%</div>` : ''}
                </div>
                <div class="log-actions">
                    <button class="btn btn-sm btn-outline" onclick="viewLogDetails('${btoa(JSON.stringify(entry))}')">
                        <i class="fas fa-eye"></i>
                        Details
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Filter log results
 */
function filterLogResults() {
    if (!window.currentLogResults) return;
    
    const sourceFilter = document.getElementById('sourceFilter').value;
    const severityFilter = document.getElementById('severityFilter').value;
    
    let filteredResults = window.currentLogResults;
    
    if (sourceFilter) {
        filteredResults = filteredResults.filter(entry => entry.source === sourceFilter);
    }
    
    if (severityFilter) {
        filteredResults = filteredResults.filter(entry => 
            (entry.severity || entry.level || 'info') === severityFilter
        );
    }
    
    const resultsListContent = document.getElementById('resultsListContent');
    resultsListContent.innerHTML = renderLogEntries(filteredResults);
    
    // Update results count
    const resultsCount = document.querySelector('.results-count');
    if (resultsCount) {
        resultsCount.textContent = `${filteredResults.length} entries found`;
    }
}

/**
 * Clear log search
 */
function clearLogSearch() {
    document.getElementById('logSearchQuery').value = '';
    document.getElementById('logSearchBrand').value = '';
    document.getElementById('logSearchTimeframe').value = '24h';
    document.getElementById('logSearchSource').value = 'all';
    
    const resultsContainer = document.getElementById('logSearchResults');
    resultsContainer.style.display = 'none';
    resultsContainer.innerHTML = '';
    
    // Clear stored results
    window.currentLogResults = null;
    window.currentSearchParams = null;
}

/**
 * View detailed log entry
 */
function viewLogDetails(encodedEntry) {
    try {
        const entry = JSON.parse(atob(encodedEntry));
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h2><i class="fas fa-file-alt"></i> Log Entry Details</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="log-details">
                        <div class="detail-section">
                            <h3>Basic Information</h3>
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <span class="label">Timestamp:</span>
                                    <span class="value">${entry.timestamp ? new Date(entry.timestamp).toLocaleString() : 'Unknown'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="label">Source:</span>
                                    <span class="value">${entry.source || 'Unknown'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="label">Severity:</span>
                                    <span class="value severity-${entry.severity || entry.level || 'info'}">
                                        ${(entry.severity || entry.level || 'info').toUpperCase()}
                                    </span>
                                </div>
                                ${entry.device ? `
                                    <div class="detail-item">
                                        <span class="label">Device:</span>
                                        <span class="value">${entry.device}</span>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h3>Message</h3>
                            <div class="log-message-full">
                                ${entry.message || entry.matching_entry || entry.description || 'No message available'}
                            </div>
                        </div>
                        
                        ${(entry.src_ip || entry.dst_ip || entry.action) ? `
                            <div class="detail-section">
                                <h3>Network Information</h3>
                                <div class="detail-grid">
                                    ${entry.src_ip ? `
                                        <div class="detail-item">
                                            <span class="label">Source IP:</span>
                                            <span class="value">${entry.src_ip}</span>
                                        </div>
                                    ` : ''}
                                    ${entry.dst_ip ? `
                                        <div class="detail-item">
                                            <span class="label">Destination IP:</span>
                                            <span class="value">${entry.dst_ip}</span>
                                        </div>
                                    ` : ''}
                                    ${entry.action ? `
                                        <div class="detail-item">
                                            <span class="label">Action:</span>
                                            <span class="value">${entry.action}</span>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="detail-section">
                            <h3>Raw Data</h3>
                            <div class="raw-data">
                                <pre>${JSON.stringify(entry, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        showToast('Error viewing log details', 'error');
        console.error('Error viewing log details:', error);
    }
}

/**
 * Export log results
 */
function exportLogResults() {
    if (!window.currentLogResults || window.currentLogResults.length === 0) {
        showToast('No results to export', 'warning');
        return;
    }
    
    try {
        // Create CSV content
        const headers = ['Timestamp', 'Source', 'Severity', 'Message', 'Device', 'Source IP', 'Destination IP', 'Action'];
        const csvContent = [
            headers.join(','),
            ...window.currentLogResults.map(entry => [
                entry.timestamp ? new Date(entry.timestamp).toISOString() : '',
                entry.source || '',
                entry.severity || entry.level || '',
                `"${(entry.message || entry.matching_entry || entry.description || '').replace(/"/g, '""')}"`,
                entry.device || '',
                entry.src_ip || '',
                entry.dst_ip || '',
                entry.action || ''
            ].join(','))
        ].join('\n');
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `log-search-results-${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Log results exported successfully', 'success');
        
    } catch (error) {
        showToast('Error exporting log results', 'error');
        console.error('Error exporting results:', error);
    }
}

/**
 * Generate log analysis report
 */
function generateLogAnalysisReport() {
    if (!window.currentLogResults || window.currentLogResults.length === 0) {
        showToast('No results to generate report from', 'warning');
        return;
    }
    
    try {
        // Analyze the results
        const analysis = analyzeLogResults(window.currentLogResults);
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h2><i class="fas fa-chart-line"></i> Log Analysis Report</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="report-content">
                        <div class="report-section">
                            <h3>Search Summary</h3>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <span class="label">Query:</span>
                                    <span class="value">${window.currentSearchParams.query}</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Brand:</span>
                                    <span class="value">${window.currentSearchParams.brand}</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Timeframe:</span>
                                    <span class="value">${window.currentSearchParams.timeframe}</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Total Results:</span>
                                    <span class="value">${analysis.totalEntries}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="report-section">
                            <h3>Source Distribution</h3>
                            <div class="distribution-chart">
                                ${Object.entries(analysis.sourceDistribution).map(([source, count]) => `
                                    <div class="distribution-item">
                                        <span class="source-name">${source}</span>
                                        <div class="distribution-bar">
                                            <div class="bar-fill" style="width: ${(count / analysis.totalEntries) * 100}%"></div>
                                            <span class="bar-label">${count}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="report-section">
                            <h3>Severity Analysis</h3>
                            <div class="severity-breakdown">
                                ${Object.entries(analysis.severityDistribution).map(([severity, count]) => `
                                    <div class="severity-item">
                                        <span class="severity-badge severity-${severity}">${severity.toUpperCase()}</span>
                                        <span class="severity-count">${count}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="report-section">
                            <h3>Key Findings</h3>
                            <ul class="findings-list">
                                ${analysis.keyFindings.map(finding => `<li>${finding}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="report-section">
                            <h3>Recommendations</h3>
                            <ul class="recommendations-list">
                                ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        showToast('Error generating analysis report', 'error');
        console.error('Error generating report:', error);
    }
}

/**
 * Analyze log results for reporting
 */
function analyzeLogResults(results) {
    const analysis = {
        totalEntries: results.length,
        sourceDistribution: {},
        severityDistribution: {},
        keyFindings: [],
        recommendations: []
    };
    
    // Analyze source distribution
    results.forEach(entry => {
        const source = entry.source || 'Unknown';
        analysis.sourceDistribution[source] = (analysis.sourceDistribution[source] || 0) + 1;
    });
    
    // Analyze severity distribution
    results.forEach(entry => {
        const severity = entry.severity || entry.level || 'info';
        analysis.severityDistribution[severity] = (analysis.severityDistribution[severity] || 0) + 1;
    });
    
    // Generate key findings
    const criticalCount = analysis.severityDistribution.critical || 0;
    const highCount = analysis.severityDistribution.high || 0;
    
    if (criticalCount > 0) {
        analysis.keyFindings.push(`Found ${criticalCount} critical security events requiring immediate attention`);
    }
    
    if (highCount > 0) {
        analysis.keyFindings.push(`Identified ${highCount} high-severity events that should be reviewed`);
    }
    
    const fazCount = analysis.sourceDistribution['FortiAnalyzer'] || 0;
    const wfCount = analysis.sourceDistribution['Web Filters'] || 0;
    
    if (fazCount > wfCount) {
        analysis.keyFindings.push('Most security events originated from FortiAnalyzer logs');
    } else if (wfCount > fazCount) {
        analysis.keyFindings.push('Most security events originated from Web Filters logs');
    }
    
    // Generate recommendations
    if (criticalCount > 0) {
        analysis.recommendations.push('Immediately investigate and remediate critical security events');
    }
    
    if (highCount > 5) {
        analysis.recommendations.push('Consider reviewing security policies to reduce high-severity events');
    }
    
    analysis.recommendations.push('Continue monitoring security events and maintain regular log analysis');
    
    return analysis;
}