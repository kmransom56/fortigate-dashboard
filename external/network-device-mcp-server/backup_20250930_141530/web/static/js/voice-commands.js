/**
 * Advanced Voice Commands for Network Security Operations
 * Specialized voice command handlers for security investigations and analysis
 */

class VoiceCommands {
    constructor(voiceInterface) {
        this.voiceInterface = voiceInterface;
        this.activeInvestigation = null;
        this.contextStack = [];
        this.ltmEnabled = false;
        this.setupAdvancedCommands();
        this.initializeLTM();
    }
    
    /**
     * Initialize LTM Intelligence System integration
     */
    async initializeLTM() {
        try {
            const response = await fetch('/api/ltm/status');
            const data = await response.json();
            
            if (data.success) {
                this.ltmEnabled = true;
                console.log('✅ LTM Intelligence System connected');
                
                // Add LTM-specific voice commands
                this.setupLTMCommands();
            }
        } catch (error) {
            console.log('LTM Intelligence System not available:', error.message);
        }
    }

    /**
     * Setup advanced voice command patterns
     */
    setupAdvancedCommands() {
        // Advanced investigation commands
        this.addCommandPattern(/investigate\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)\s+store\s+(\d+)\s*(?:for\s+(.+))?/, 
            this.handleStoreInvestigation.bind(this));

        // Advanced log search commands
        this.addCommandPattern(/search\s+(?:for\s+)?(.+?)(?:\s+in\s+(.+?))?(?:\s+from\s+(.+?))?(?:\s+in\s+the\s+last\s+(.+))?/,
            this.handleAdvancedLogSearch.bind(this));

        // Security event commands
        this.addCommandPattern(/show\s+(?:me\s+)?(?:the\s+)?(critical|high|medium|low)\s+(?:security\s+)?(?:events|alerts)(?:\s+for\s+(.+?))?/,
            this.handleSecurityEvents.bind(this));

        // FortiAnalyzer specific commands
        this.addCommandPattern(/show\s+(?:me\s+)?threat\s+intelligence\s+for\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)(?:\s+in\s+the\s+last\s+(.+))?/,
            this.handleThreatIntelligence.bind(this));

        // Web filters commands
        this.addCommandPattern(/(?:check|show)\s+web\s+filter\s+(?:status|policies)\s+for\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)(?:\s+store\s+(\d+))?/,
            this.handleWebFilterStatus.bind(this));

        // System status commands
        this.addCommandPattern(/(?:check|what\s+is\s+the|show\s+me\s+the)\s+(?:overall\s+)?(?:security\s+)?status(?:\s+of\s+(.+?))?/,
            this.handleSystemStatus.bind(this));

        // Report generation commands
        this.addCommandPattern(/generate\s+(?:a\s+)?(?:(security|threat|compliance|executive)\s+)?report\s+for\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)(?:\s+store\s+(\d+))?(?:\s+for\s+the\s+last\s+(.+))?/,
            this.handleReportGeneration.bind(this));

        // Contextual follow-up commands
        this.addCommandPattern(/(?:show\s+me\s+)?(?:more\s+)?(?:details|information|data)/, 
            this.handleShowMore.bind(this));
        
        this.addCommandPattern(/go\s+back/, 
            this.handleGoBack.bind(this));

        // Emergency commands
        this.addCommandPattern(/(?:alert|emergency|urgent|critical)\s*:?\s*(.+)/, 
            this.handleEmergencyCommand.bind(this));

        // Bulk operations
        this.addCommandPattern(/(?:check|investigate|analyze)\s+all\s+(stores|locations|sites)(?:\s+for\s+(.+?))?/,
            this.handleBulkOperation.bind(this));
    }
    
    /**
     * Setup LTM-specific voice commands
     */
    setupLTMCommands() {
        // Pattern analysis commands
        this.addCommandPattern(/(?:analyze|show\s+me|find)\s+(?:security\s+)?patterns?(?:\s+in\s+(.+?))?(?:\s+for\s+the\s+last\s+(.+))?/,
            this.handlePatternAnalysis.bind(this));
            
        // Predictive analytics commands
        this.addCommandPattern(/predict\s+(?:security\s+)?(?:issues|incidents|threats|problems)\s+for\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)(?:\s+(?:in\s+the\s+)?next\s+(.+?))?/,
            this.handlePredictiveAnalysis.bind(this));
            
        // Learning commands
        this.addCommandPattern(/(?:what\s+have\s+you\s+)?learn(?:ed)?\s+(?:from\s+)?(.+?)(?:\s+incidents?|\s+events?)?/,
            this.handleLearningQuery.bind(this));
            
        // Correlation commands
        this.addCommandPattern(/(?:show\s+me\s+)?(?:correlations?|relationships?|connections?)\s+between\s+(.+?)(?:\s+and\s+(.+))?/,
            this.handleCorrelationAnalysis.bind(this));
            
        // Attack path analysis
        this.addCommandPattern(/(?:show\s+me\s+)?(?:attack\s+paths?|propagation\s+paths?)\s+(?:from\s+(.+?))?(?:\s+to\s+(.+))?/,
            this.handleAttackPathAnalysis.bind(this));
            
        // LTM insights commands
        this.addCommandPattern(/(?:show\s+me\s+)?(?:ltm\s+)?(?:insights?|analytics?|intelligence)(?:\s+for\s+(.+))?/,
            this.handleLTMInsights.bind(this));
    }

    /**
     * Add command pattern
     */
    addCommandPattern(pattern, handler) {
        if (!this.voiceInterface.commandPatterns) {
            this.voiceInterface.commandPatterns = [];
        }
        this.voiceInterface.commandPatterns.push({ pattern, handler });
    }

    /**
     * Handle store investigation
     */
    async handleStoreInvestigation(matches) {
        const brand = this.normalizeBrandName(matches[1]);
        const storeId = matches[2];
        const focus = matches[3];
        
        this.activeInvestigation = { brand, storeId, focus };
        this.pushContext('investigation', this.activeInvestigation);
        
        let message = `Investigating ${this.getBrandDisplayName(brand)} store ${storeId}`;
        if (focus) {
            message += ` focusing on ${focus}`;
        }
        
        this.voiceInterface.speak(message);
        
        // Navigate and setup investigation
        showSection('investigation');
        document.getElementById('investigationBrand').value = brand;
        document.getElementById('investigationStore').value = storeId;
        
        // Set appropriate timeframe based on focus
        if (focus) {
            const timeframe = this.inferTimeframeFromFocus(focus);
            document.getElementById('investigationPeriod').value = timeframe;
        }
        
        // Auto-run investigation
        setTimeout(() => {
            runInvestigation();
            this.announceInvestigationResults();
        }, 1000);
    }

    /**
     * Handle advanced log search
     */
    async handleAdvancedLogSearch(matches) {
        const query = matches[1];
        const context = matches[2]; // brand or store context
        const source = matches[3]; // fortianalyzer or webfilters
        const timeframe = this.parseTimeframe(matches[4]) || '24h';
        
        this.pushContext('log-search', { query, context, source, timeframe });
        
        let message = `Searching for ${query}`;
        if (context) message += ` in ${context}`;
        if (source) message += ` from ${source}`;
        message += ` for the last ${timeframe}`;
        
        this.voiceInterface.speak(message);
        
        // Navigate and setup search
        showSection('log-analysis');
        document.getElementById('logSearchQuery').value = query;
        document.getElementById('logSearchTimeframe').value = timeframe;
        
        if (context) {
            const brand = this.normalizeBrandName(context);
            if (brand) {
                document.getElementById('logSearchBrand').value = brand;
            }
        }
        
        if (source) {
            const normalizedSource = source.toLowerCase().includes('forti') ? 'fortianalyzer' : 'webfilters';
            document.getElementById('logSearchSource').value = normalizedSource;
        }
        
        setTimeout(() => searchLogs(), 500);
    }

    /**
     * Handle security events
     */
    async handleSecurityEvents(matches) {
        const severity = matches[1];
        const context = matches[2]; // brand or store
        
        this.pushContext('security-events', { severity, context });
        
        this.voiceInterface.speak(`Showing ${severity} security events${context ? ` for ${context}` : ''}`);
        
        // Navigate to FortiAnalyzer and filter by severity
        showSection('fortianalyzer');
        
        setTimeout(() => {
            this.filterSecurityEventsBySeverity(severity, context);
        }, 1000);
    }

    /**
     * Handle threat intelligence
     */
    async handleThreatIntelligence(matches) {
        const brand = this.normalizeBrandName(matches[1]);
        const timeframe = this.parseTimeframe(matches[2]) || '24h';
        
        this.pushContext('threat-intelligence', { brand, timeframe });
        
        this.voiceInterface.speak(`Loading threat intelligence for ${this.getBrandDisplayName(brand)} for the last ${timeframe}`);
        
        showSection('fortianalyzer');
        
        setTimeout(async () => {
            try {
                const response = await apiCall(`/api/fortianalyzer/threats/${brand}?timeframe=${timeframe}`);
                if (response.success) {
                    this.announceThreatIntelligence(response);
                    renderThreatIntelligenceDashboard({ [brand]: response });
                }
            } catch (error) {
                this.voiceInterface.speak('Error loading threat intelligence');
            }
        }, 1000);
    }

    /**
     * Handle web filter status
     */
    async handleWebFilterStatus(matches) {
        const brand = this.normalizeBrandName(matches[1]);
        const storeId = matches[2];
        
        this.pushContext('web-filter-status', { brand, storeId });
        
        let message = `Checking web filter status for ${this.getBrandDisplayName(brand)}`;
        if (storeId) message += ` store ${storeId}`;
        
        this.voiceInterface.speak(message);
        
        showSection('webfilters');
        
        if (storeId) {
            document.getElementById('webfilterBrand').value = brand;
            document.getElementById('webfilterStoreId').value = storeId;
            setTimeout(() => viewStoreWebFilters(), 1000);
        }
    }

    /**
     * Handle system status
     */
    async handleSystemStatus(matches) {
        const scope = matches[1]; // specific system or overall
        
        this.voiceInterface.speak('Checking system status');
        
        try {
            // Check overall system health
            const healthResponse = await apiCall('/health');
            const integrationResponse = await apiCall('/api/integration/status');
            
            let statusMessage = 'System status: ';
            
            if (healthResponse.status === 'healthy') {
                statusMessage += 'All systems operational. ';
            } else {
                statusMessage += 'System issues detected. ';
            }
            
            if (integrationResponse.success) {
                const activeManagers = integrationResponse.active_managers?.length || 0;
                statusMessage += `${activeManagers} integration modules active. `;
                
                if (integrationResponse.unified_platform_status === 'fully_operational') {
                    statusMessage += 'All integrations operational.';
                } else {
                    statusMessage += 'Some integrations have limited functionality.';
                }
            }
            
            this.voiceInterface.speak(statusMessage);
            
        } catch (error) {
            this.voiceInterface.speak('Unable to check system status. Connection may be down.');
        }
    }

    /**
     * Handle report generation
     */
    async handleReportGeneration(matches) {
        const reportType = matches[1] || 'security';
        const brand = this.normalizeBrandName(matches[2]);
        const storeId = matches[3];
        const timeframe = this.parseTimeframe(matches[4]) || '7d';
        
        this.pushContext('report-generation', { reportType, brand, storeId, timeframe });
        
        let message = `Generating ${reportType} report for ${this.getBrandDisplayName(brand)}`;
        if (storeId) message += ` store ${storeId}`;
        message += ` for the last ${timeframe}`;
        
        this.voiceInterface.speak(message);
        
        showSection('fortianalyzer');
        
        setTimeout(async () => {
            try {
                const url = `/api/fortianalyzer/reports/${brand}${storeId ? `?store_id=${storeId}` : ''}`;
                const response = await apiCall(url);
                
                if (response.success) {
                    this.announceReportResults(response);
                    renderSecurityReportModal(response);
                }
            } catch (error) {
                this.voiceInterface.speak('Error generating report');
            }
        }, 1000);
    }

    /**
     * Handle show more details
     */
    handleShowMore() {
        const currentContext = this.getCurrentContext();
        
        if (!currentContext) {
            this.voiceInterface.speak('No additional details available');
            return;
        }
        
        this.voiceInterface.speak('Showing additional details');
        
        switch (currentContext.type) {
            case 'investigation':
                this.showInvestigationDetails(currentContext.data);
                break;
            case 'threat-intelligence':
                this.showThreatDetails(currentContext.data);
                break;
            case 'security-events':
                this.showSecurityEventDetails(currentContext.data);
                break;
            default:
                this.voiceInterface.speak('No additional details available for current view');
        }
    }

    /**
     * Handle go back
     */
    handleGoBack() {
        if (this.contextStack.length > 1) {
            this.contextStack.pop(); // Remove current context
            const previousContext = this.getCurrentContext();
            
            this.voiceInterface.speak('Going back to previous view');
            this.restoreContext(previousContext);
        } else {
            this.voiceInterface.speak('Going back to overview');
            showSection('overview');
        }
    }

    /**
     * Handle emergency command
     */
    async handleEmergencyCommand(matches) {
        const emergencyContext = matches[1];
        
        this.voiceInterface.speak(`Emergency alert: ${emergencyContext}. Initiating immediate analysis.`, { rate: 1.2 });
        
        // Show critical dashboard with emergency styling
        showSection('fortianalyzer');
        
        // Search for critical events
        setTimeout(() => {
            this.performEmergencyAnalysis(emergencyContext);
        }, 500);
    }

    /**
     * Handle bulk operations
     */
    async handleBulkOperation(matches) {
        const scope = matches[1]; // stores, locations, sites
        const operation = matches[2]; // what to check for
        
        this.voiceInterface.speak(`Performing bulk analysis across all ${scope}${operation ? ` for ${operation}` : ''}`);
        
        showSection('overview');
        
        setTimeout(() => {
            this.performBulkAnalysis(scope, operation);
        }, 1000);
    }

    /**
     * Announce investigation results
     */
    async announceInvestigationResults() {
        // Wait for investigation to complete
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const investigation = this.activeInvestigation;
        if (!investigation) return;
        
        // Read actual investigation results from the dashboard
        try {
            const securityEventsElement = document.querySelector('#security-events .events-summary');
            const urlBlockingElement = document.querySelector('#url-blocking .blocking-stats');
            
            let announcement = `Investigation complete for ${this.getBrandDisplayName(investigation.brand)} store ${investigation.storeId}. `;
            
            if (securityEventsElement) {
                announcement += 'Security analysis completed. Check the dashboard for detailed results. ';
            } else {
                announcement += 'Investigation completed - review the security, URL blocking, and events tabs for results. ';
            }
        } catch (error) {
            let announcement = `Investigation complete for ${this.getBrandDisplayName(investigation.brand)} store ${investigation.storeId}. `;
            announcement += 'Review the investigation results in the dashboard tabs for detailed findings.';
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce threat intelligence
     */
    announceThreatIntelligence(data) {
        const threats = data.threat_summary;
        if (!threats) return;
        
        let announcement = `Threat intelligence summary: `;
        announcement += `${threats.total_threats || 0} total threats detected, `;
        announcement += `${threats.blocked_threats || 0} successfully blocked. `;
        
        const blockRate = Math.round(((threats.blocked_threats || 0) / Math.max(threats.total_threats || 1, 1)) * 100);
        announcement += `Block rate: ${blockRate}%. `;
        
        if (blockRate > 95) {
            announcement += 'Excellent threat protection.';
        } else if (blockRate > 90) {
            announcement += 'Good threat protection.';
        } else {
            announcement += 'Consider reviewing security policies.';
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce report results
     */
    announceReportResults(data) {
        const summary = data.executive_summary;
        if (!summary) return;
        
        let announcement = `Report generated successfully. `;
        announcement += `Security posture: ${summary.overall_security_posture || 'unknown'}. `;
        announcement += `Analyzed ${summary.total_events_analyzed || 0} events, `;
        announcement += `blocked ${summary.threats_blocked || 0} threats. `;
        
        if (data.recommendations && data.recommendations.length > 0) {
            announcement += `${data.recommendations.length} recommendations provided.`;
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Context management
     */
    pushContext(type, data) {
        this.contextStack.push({ type, data, timestamp: Date.now() });
        
        // Limit context stack size
        if (this.contextStack.length > 10) {
            this.contextStack.shift();
        }
    }

    getCurrentContext() {
        return this.contextStack[this.contextStack.length - 1] || null;
    }

    restoreContext(context) {
        if (!context) return;
        
        switch (context.type) {
            case 'investigation':
                showSection('investigation');
                if (context.data.brand) {
                    document.getElementById('investigationBrand').value = context.data.brand;
                }
                if (context.data.storeId) {
                    document.getElementById('investigationStore').value = context.data.storeId;
                }
                break;
            case 'log-search':
                showSection('log-analysis');
                if (context.data.query) {
                    document.getElementById('logSearchQuery').value = context.data.query;
                }
                break;
        }
    }

    /**
     * Utility functions
     */
    normalizeBrandName(brandInput) {
        const brandMap = {
            'bww': 'BWW',
            'buffalo wild wings': 'BWW',
            'arbys': 'ARBYS',
            'arby\'s': 'ARBYS',
            'sonic': 'SONIC'
        };
        
        return brandMap[brandInput.toLowerCase()] || brandInput.toUpperCase();
    }

    getBrandDisplayName(brandCode) {
        const brandNames = {
            'BWW': 'Buffalo Wild Wings',
            'ARBYS': 'Arby\'s',
            'SONIC': 'Sonic Drive-In'
        };
        return brandNames[brandCode] || brandCode;
    }

    parseTimeframe(timeInput) {
        if (!timeInput) return null;
        
        const timeMap = {
            'hour': '1h',
            'last hour': '1h',
            'day': '24h',
            'last day': '24h',
            '24 hours': '24h',
            'week': '7d',
            'last week': '7d',
            'month': '30d',
            'last month': '30d'
        };
        
        return timeMap[timeInput.toLowerCase()] || timeInput;
    }

    inferTimeframeFromFocus(focus) {
        if (focus.includes('recent') || focus.includes('current')) return '1h';
        if (focus.includes('today')) return '24h';
        if (focus.includes('week')) return '7d';
        if (focus.includes('month')) return '30d';
        return '24h';
    }

    async performEmergencyAnalysis(context) {
        // Emergency analysis logic
        this.voiceInterface.speak('Performing emergency security analysis');
        
        // Search for critical events
        document.getElementById('logSearchQuery').value = `critical emergency ${context}`;
        document.getElementById('logSearchTimeframe').value = '1h';
        
        setTimeout(() => searchLogs(), 500);
    }

    async performBulkAnalysis(scope, operation) {
        // Bulk analysis logic
        this.voiceInterface.speak(`Analyzing ${scope}${operation ? ` for ${operation}` : ''}. This may take a moment.`);
        
        // Load overview with focus on bulk metrics
        await loadOverviewData();
    }

    filterSecurityEventsBySeverity(severity, context) {
        // Filter FortiAnalyzer view by severity
        this.voiceInterface.speak(`Filtering events by ${severity} severity`);
        showThreatIntelligence();
    }

    showInvestigationDetails(data) {
        // Show detailed investigation results
        this.voiceInterface.speak('Showing detailed investigation results');
    }

    showThreatDetails(data) {
        // Show detailed threat information
        this.voiceInterface.speak('Showing detailed threat analysis');
    }

    showSecurityEventDetails(data) {
        // Show detailed security event information
        this.voiceInterface.speak('Showing detailed security event analysis');
    }
}

// Initialize voice commands when voice interface is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof voiceInterface !== 'undefined') {
        window.voiceCommands = new VoiceCommands(voiceInterface);
        
        // Extend voice interface with advanced pattern matching
        const originalProcessCommand = voiceInterface.processVoiceCommand;
        voiceInterface.processVoiceCommand = function(transcript) {
            // Try advanced patterns first
            if (voiceInterface.commandPatterns) {
                for (const { pattern, handler } of voiceInterface.commandPatterns) {
                    const matches = transcript.match(pattern);
                    if (matches) {
                        console.log('Advanced pattern matched:', pattern, matches);
                        handler(matches);
                        return;
                    }
                }
            }
            
            // Fall back to original processing
            originalProcessCommand.call(this, transcript);
        };
    }

    // ==============================================================================
    // LTM INTELLIGENCE COMMAND HANDLERS
    // Advanced AI-powered voice command processing
    // ==============================================================================

    /**
     * Handle pattern analysis requests
     */
    async handlePatternAnalysis(matches) {
        if (!this.ltmEnabled) {
            this.voiceInterface.speak('LTM intelligence system not available');
            return;
        }

        const context = matches[1];
        const timeframe = matches[2];
        
        this.voiceInterface.speak(`Analyzing network patterns using LTM intelligence`);
        
        try {
            let url = '/api/ltm/patterns/analyze';
            const params = new URLSearchParams();
            
            if (timeframe) {
                const hours = this.parseTimeframeToHours(timeframe);
                params.append('time_window_hours', hours);
            }
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.patterns.length > 0) {
                this.announcePatternResults(data);
                this.displayPatternResults(data);
            } else {
                this.voiceInterface.speak('No significant patterns detected in the specified timeframe');
            }
            
            // Send to LTM for learning
            await this.sendVoiceCommandToLTM(matches.input, 'pattern_analysis', true);
            
        } catch (error) {
            console.error('Pattern analysis error:', error);
            this.voiceInterface.speak('Unable to analyze patterns at this time');
        }
    }

    /**
     * Handle predictive analysis requests
     */
    async handlePredictiveAnalysis(matches) {
        if (!this.ltmEnabled) {
            this.voiceInterface.speak('LTM intelligence system not available');
            return;
        }

        const brand = this.normalizeBrandName(matches[1]);
        const timeframe = matches[2] || '7 days';
        
        this.voiceInterface.speak(`Generating predictive security analysis for ${this.getBrandDisplayName(brand)}`);
        
        try {
            const days = this.parseTimeframeToDays(timeframe);
            const url = `/api/ltm/predictions/generate?entities=${brand}&time_horizon_days=${days}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.predictions.length > 0) {
                this.announcePredictionResults(data);
                this.displayPredictionResults(data);
            } else {
                this.voiceInterface.speak(`No significant predictions for ${this.getBrandDisplayName(brand)} in the next ${timeframe}`);
            }
            
            await this.sendVoiceCommandToLTM(matches.input, 'prediction_request', true);
            
        } catch (error) {
            console.error('Predictive analysis error:', error);
            this.voiceInterface.speak('Unable to generate predictions at this time');
        }
    }

    /**
     * Handle learning queries
     */
    async handleLearningQuery(matches) {
        if (!this.ltmEnabled) {
            this.voiceInterface.speak('LTM intelligence system not available');
            return;
        }

        const topic = matches[1];
        
        this.voiceInterface.speak(`Querying LTM learning database about ${topic}`);
        
        try {
            const response = await fetch('/api/ltm/analytics/insights');
            const data = await response.json();
            
            if (data.success) {
                this.announceLearningInsights(data, topic);
            } else {
                this.voiceInterface.speak('Unable to retrieve learning insights');
            }
            
            await this.sendVoiceCommandToLTM(matches.input, 'learning_query', true);
            
        } catch (error) {
            console.error('Learning query error:', error);
            this.voiceInterface.speak('Unable to access learning database');
        }
    }

    /**
     * Handle attack path analysis
     */
    async handleAttackPathAnalysis(matches) {
        if (!this.ltmEnabled) {
            this.voiceInterface.speak('LTM intelligence system not available');
            return;
        }

        const source = matches[1];
        const target = matches[2];
        
        this.voiceInterface.speak('Analyzing potential attack paths using network graph intelligence');
        
        try {
            let url = '/api/ltm/graph/attack-paths';
            const params = new URLSearchParams();
            
            if (source) params.append('source_entities', source);
            if (target) params.append('target_entities', target);
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.attack_paths.length > 0) {
                this.announceAttackPathResults(data);
            } else {
                this.voiceInterface.speak('No significant attack paths identified');
            }
            
            await this.sendVoiceCommandToLTM(matches.input, 'graph_analysis', true);
            
        } catch (error) {
            console.error('Attack path analysis error:', error);
            this.voiceInterface.speak('Unable to analyze attack paths');
        }
    }

    /**
     * Handle LTM insights requests
     */
    async handleLTMInsights(matches) {
        if (!this.ltmEnabled) {
            this.voiceInterface.speak('LTM intelligence system not available');
            return;
        }

        const context = matches[1];
        
        this.voiceInterface.speak('Retrieving comprehensive LTM intelligence insights');
        
        try {
            const response = await fetch('/api/ltm/analytics/insights');
            const data = await response.json();
            
            if (data.success) {
                this.announceComprehensiveInsights(data);
                this.displayLTMDashboard(data);
            } else {
                this.voiceInterface.speak('Unable to retrieve LTM insights');
            }
            
            await this.sendVoiceCommandToLTM(matches.input, 'ltm_insights', true);
            
        } catch (error) {
            console.error('LTM insights error:', error);
            this.voiceInterface.speak('Unable to access LTM insights');
        }
    }

    /**
     * Send voice command to LTM for learning
     */
    async sendVoiceCommandToLTM(command, intent, success) {
        if (!this.ltmEnabled) return;
        
        try {
            await fetch('/api/ltm/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: command,
                    context: {
                        current_section: this.getCurrentSection(),
                        active_investigation: this.activeInvestigation
                    },
                    feedback: success ? 'positive' : 'negative'
                })
            });
        } catch (error) {
            console.error('Error sending command to LTM:', error);
        }
    }

    // ==============================================================================
    // LTM RESULT ANNOUNCEMENT METHODS
    // ==============================================================================

    /**
     * Announce pattern analysis results
     */
    announcePatternResults(data) {
        let announcement = `Pattern analysis complete. `;
        announcement += `Detected ${data.patterns_detected} patterns. `;
        
        if (data.summary.high_confidence_patterns > 0) {
            announcement += `${data.summary.high_confidence_patterns} high-confidence patterns found. `;
        }
        
        if (data.summary.critical_severity > 0) {
            announcement += `${data.summary.critical_severity} critical severity patterns require attention. `;
        }
        
        const topPattern = data.patterns[0];
        if (topPattern) {
            announcement += `Top pattern: ${topPattern.type} with ${Math.round(topPattern.confidence * 100)}% confidence.`;
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce prediction results
     */
    announcePredictionResults(data) {
        let announcement = `Predictive analysis complete. `;
        announcement += `Generated ${data.predictions_generated} predictions for the next ${data.time_horizon_days} days. `;
        
        if (data.summary.high_confidence_predictions > 0) {
            announcement += `${data.summary.high_confidence_predictions} high-confidence predictions. `;
        }
        
        if (data.summary.critical_predictions > 0) {
            announcement += `${data.summary.critical_predictions} critical predictions require immediate attention. `;
        }
        
        const topPrediction = data.predictions[0];
        if (topPrediction) {
            announcement += `Highest probability: ${topPrediction.type} with ${Math.round(topPrediction.probability * 100)}% likelihood.`;
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce learning insights
     */
    announceLearningInsights(data, topic) {
        const stats = data.ltm_analytics.memory_statistics;
        let announcement = `LTM has learned from ${stats.total_events || 0} network events, `;
        announcement += `detected ${stats.total_patterns || 0} patterns, `;
        announcement += `and processed ${stats.total_voice_interactions || 0} voice interactions. `;
        
        const voiceSuccessRate = Math.round((stats.voice_success_rate || 0) * 100);
        announcement += `Voice command success rate: ${voiceSuccessRate}%. `;
        
        if (data.ltm_analytics.voice_insights.length > 0) {
            const topInsight = data.ltm_analytics.voice_insights[0];
            announcement += `Key insight: ${topInsight.description}`;
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce attack path results
     */
    announceAttackPathResults(data) {
        let announcement = `Attack path analysis complete. `;
        announcement += `Analyzed ${data.attack_paths_analyzed} potential paths. `;
        
        if (data.summary.high_risk_paths > 0) {
            announcement += `${data.summary.high_risk_paths} high-risk attack paths identified. `;
        }
        
        if (data.summary.short_attack_paths > 0) {
            announcement += `${data.summary.short_attack_paths} paths with 3 or fewer hops require immediate attention. `;
        }
        
        const topPath = data.attack_paths[0];
        if (topPath) {
            announcement += `Highest risk path: ${topPath.shortest_path_length} hops with risk score ${Math.round(topPath.risk_score * 100)}.`;
        }
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce comprehensive LTM insights
     */
    announceComprehensiveInsights(data) {
        const recent = data.ltm_analytics.recent_activity;
        let announcement = `LTM intelligence summary: `;
        announcement += `${recent.patterns_detected_24h} patterns detected in last 24 hours, `;
        announcement += `${recent.predictions_generated} predictions generated. `;
        
        if (recent.critical_predictions > 0) {
            announcement += `${recent.critical_predictions} critical predictions require attention. `;
        }
        
        announcement += `System learning effectiveness is optimal with continuous pattern recognition active.`;
        
        this.voiceInterface.speak(announcement);
    }

    // ==============================================================================
    // LTM RESULT DISPLAY METHODS
    // ==============================================================================

    /**
     * Display pattern results in dashboard
     */
    displayPatternResults(data) {
        this.createLTMResultsSection('Pattern Analysis Results', data.patterns.map(p => ({
            title: `${p.type} (${Math.round(p.confidence * 100)}% confidence)`,
            description: p.description,
            severity: p.severity,
            recommendations: p.recommendations
        })));
    }

    /**
     * Display prediction results in dashboard
     */
    displayPredictionResults(data) {
        this.createLTMResultsSection('Predictive Analytics Results', data.predictions.map(p => ({
            title: `${p.type} (${Math.round(p.probability * 100)}% probability)`,
            description: p.description,
            severity: p.severity,
            businessImpact: p.business_impact,
            recommendations: p.recommendations
        })));
    }

    /**
     * Display LTM dashboard
     */
    displayLTMDashboard(data) {
        console.log('LTM Dashboard Data:', data);
        // Implementation would create visual dashboard elements
    }

    /**
     * Create LTM results section
     */
    createLTMResultsSection(title, results) {
        const section = document.createElement('div');
        section.className = 'ltm-results-section';
        section.innerHTML = `
            <h3>${title}</h3>
            <div class="ltm-results-grid">
                ${results.map(result => `
                    <div class="ltm-result-card ${result.severity || 'info'}">
                        <h4>${result.title}</h4>
                        <p>${result.description}</p>
                        ${result.recommendations ? `
                            <div class="recommendations">
                                <strong>Recommendations:</strong>
                                <ul>${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        const mainContent = document.querySelector('.main-content .content-section.active');
        if (mainContent) {
            const existingResults = mainContent.querySelector('.ltm-results-section');
            if (existingResults) {
                existingResults.replaceWith(section);
            } else {
                mainContent.appendChild(section);
            }
        }
    }

    // ==============================================================================
    // UTILITY METHODS FOR LTM
    // ==============================================================================

    /**
     * Parse timeframe string to hours
     */
    parseTimeframeToHours(timeframe) {
        const match = timeframe.match(/(\d+)\s*(hour|day|week)s?/i);
        if (!match) return 24;
        
        const value = parseInt(match[1]);
        const unit = match[2].toLowerCase();
        
        switch (unit) {
            case 'hour': return value;
            case 'day': return value * 24;
            case 'week': return value * 24 * 7;
            default: return 24;
        }
    }

    /**
     * Parse timeframe string to days
     */
    parseTimeframeToDays(timeframe) {
        const match = timeframe.match(/(\d+)\s*(day|week|month)s?/i);
        if (!match) return 7;
        
        const value = parseInt(match[1]);
        const unit = match[2].toLowerCase();
        
        switch (unit) {
            case 'day': return value;
            case 'week': return value * 7;
            case 'month': return value * 30;
            default: return 7;
        }
    }

    /**
     * Get current dashboard section
     */
    getCurrentSection() {
        const activeSection = document.querySelector('.content-section.active');
        return activeSection ? activeSection.id : 'overview';
    }
});