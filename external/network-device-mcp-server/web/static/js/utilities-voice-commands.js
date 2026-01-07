/**
 * Enhanced Utilities Voice Commands
 * Voice command extensions for 30+ network utilities
 */

class UtilitiesVoiceCommands {
    constructor(voiceInterface) {
        this.voiceInterface = voiceInterface;
        this.utilityRegistry = {};
        this.setupUtilitiesCommands();
        this.initializeUtilities();
    }

    /**
     * Initialize utilities registry from server
     */
    async initializeUtilities() {
        try {
            const response = await fetch('/api/utilities/available');
            const data = await response.json();
            
            if (data.success) {
                this.utilityRegistry = data.utilities;
                console.log(`✅ Enhanced Utilities initialized: ${data.utilities_count} tools available`);
                
                // Add dynamic voice commands for each utility
                this.setupDynamicUtilityCommands();
            }
        } catch (error) {
            console.log('Enhanced Utilities not available:', error.message);
        }
    }

    /**
     * Setup core utilities voice command patterns
     */
    setupUtilitiesCommands() {
        // Network Discovery Commands
        this.addCommandPattern(/(?:discover|scan|find)\s+(?:network\s+)?devices?(?:\s+on\s+network\s+(.+?))?(?:\s+using\s+(.+))?/, 
            this.handleNetworkDiscovery.bind(this));

        this.addCommandPattern(/(?:scan|discover|check)\s+snmp\s+(?:devices?|network)?(?:\s+on\s+(.+?))?(?:\s+for\s+(bww|arbys?|sonic))?/,
            this.handleSNMPDiscovery.bind(this));

        this.addCommandPattern(/(?:check|verify|test)\s+snmp\s+(?:on\s+)?(?:device\s+)?(.+?)(?:\s+with\s+community\s+(.+?))?/,
            this.handleSNMPCheck.bind(this));

        // SSL/Security Commands  
        this.addCommandPattern(/(?:check|test|verify|diagnose)\s+ssl\s+(?:on\s+|for\s+)?(?:host\s+)?(.+?)(?:\s+port\s+(\d+))?/,
            this.handleSSLDiagnostics.bind(this));

        this.addCommandPattern(/(?:fix|repair|troubleshoot)\s+ssl\s+(?:on\s+|for\s+)?(.+?)(?:\s+with\s+(.+)\s+mode)?/,
            this.handleSSLFix.bind(this));

        this.addCommandPattern(/(?:create|generate|make)\s+(?:certificate|cert)\s+bundle(?:\s+from\s+(.+?))?(?:\s+to\s+(.+?))?/,
            this.handleCertBundle.bind(this));

        this.addCommandPattern(/(?:fix|repair)\s+zscaler\s+ssl(?:\s+using\s+(.+)\s+config)?/,
            this.handleZscalerSSLFix.bind(this));

        // FortiNet Management Commands
        this.addCommandPattern(/(?:compare|diff)\s+(?:fortigate\s+)?config(?:uration)?s?\s+(?:between\s+)?(.+?)\s+and\s+(.+?)(?:\s+for\s+sections?\s+(.+?))?/,
            this.handleConfigDiff.bind(this));

        this.addCommandPattern(/(?:run|use|execute)\s+fortigate\s+util(?:ity|ities)\s+(.+?)(?:\s+on\s+(?:device\s+)?(.+?))?/,
            this.handleFortiGateUtils.bind(this));

        this.addCommandPattern(/(?:use|call|execute)\s+fortimanager\s+api(?:\s+to\s+(.+?))?(?:\s+on\s+adom\s+(.+?))?(?:\s+for\s+device\s+(.+?))?/,
            this.handleFortiManagerAPI.bind(this));

        this.addCommandPattern(/deploy\s+fortimanager\s+(?:config|settings|policies)(?:\s+using\s+(.+?)\s+deployment)?(?:\s+to\s+devices?\s+(.+?))?/,
            this.handleFortiManagerDeploy.bind(this));

        // Threat Intelligence Commands
        this.addCommandPattern(/(?:scrape|get|fetch)\s+(?:fortiguard|threat\s+intel(?:ligence)?)\s+(?:data\s+)?(?:for\s+(.+?))?(?:\s+from\s+last\s+(.+?))?/,
            this.handleFortiGuardScraper.bind(this));

        this.addCommandPattern(/(?:check|get|fetch)\s+(?:psirt|security\s+advisor(?:y|ies))\s+(?:for\s+(.+?))?(?:\s+severity\s+(.+?))?/,
            this.handlePSIRTTracker.bind(this));

        // Network Analysis Commands
        this.addCommandPattern(/(?:visualize|create|generate)\s+(?:network\s+)?topology(?:\s+from\s+(.+?))?(?:\s+using\s+(.+?)\s+layout)?/,
            this.handleTopologyVisualization.bind(this));

        this.addCommandPattern(/(?:lookup|check|analyze)\s+ip\s+(?:address\s+)?(.+?)(?:\s+with\s+(.+?)\s+detail)?/,
            this.handleIPLookup.bind(this));

        this.addCommandPattern(/(?:lookup|check|find)\s+mac\s+(?:address\s+)?(.+?)(?:\s+using\s+(.+?)\s+lookup)?/,
            this.handleMACLookup.bind(this));

        // Data Processing Commands
        this.addCommandPattern(/(?:convert|process|transform)\s+csv\s+(?:file\s+)?(.+?)(?:\s+to\s+(.+?)\s+format)?(?:\s+with\s+transformations?\s+(.+?))?/,
            this.handleCSVConverter.bind(this));

        this.addCommandPattern(/(?:format|clean|process)\s+json\s+(?:data\s+)?(.+?)(?:\s+using\s+(.+?)\s+format)?/,
            this.handleJSONFormatter.bind(this));

        this.addCommandPattern(/(?:parse|extract)\s+fortinet\s+data(?:\s+from\s+(.+?))?(?:\s+to\s+(.+?)\s+format)?/,
            this.handleFortiNetParser.bind(this));

        // Monitoring & Reporting Commands
        this.addCommandPattern(/(?:generate|create)\s+isp\s+(?:connectivity\s+|performance\s+)?report(?:\s+for\s+(.+?)\s+type)?(?:\s+for\s+period\s+(.+?))?/,
            this.handleISPReport.bind(this));

        this.addCommandPattern(/(?:monitor|check)\s+splunk(?:\s+with\s+query\s+(.+?))?(?:\s+for\s+time\s+range\s+(.+?))?/,
            this.handleSplunkMonitor.bind(this));

        // Meraki Commands
        this.addCommandPattern(/(?:collect|gather|fetch)\s+meraki\s+(?:device\s+)?data(?:\s+for\s+org(?:anization)?\s+(.+?))?(?:\s+network\s+(.+?))?(?:\s+device\s+types?\s+(.+?))?/,
            this.handleMerakiCollector.bind(this));

        // Batch Operations Commands
        this.addCommandPattern(/(?:batch|bulk)\s+(.+?)\s+(?:for|on)\s+(?:ip\s+addresses?\s+|devices?\s+|hosts?\s+)(.+)/,
            this.handleBatchOperation.bind(this));

        // Help and Information Commands
        this.addCommandPattern(/(?:list|show|what)\s+(?:available\s+)?util(?:ity|ities)(?:\s+in\s+category\s+(.+?))?/,
            this.handleListUtilities.bind(this));

        this.addCommandPattern(/(?:help|info|information)\s+(?:with\s+|for\s+)?util(?:ity|ities)?\s+(.+)/,
            this.handleUtilityHelp.bind(this));

        this.addCommandPattern(/(?:what|how)\s+(?:voice\s+)?commands?\s+(?:are\s+available|can\s+i\s+use)(?:\s+for\s+(.+?))?/,
            this.handleVoiceHelp.bind(this));
    }

    /**
     * Setup dynamic commands based on utility registry
     */
    setupDynamicUtilityCommands() {
        if (!this.utilityRegistry) return;

        Object.entries(this.utilityRegistry).forEach(([name, config]) => {
            // Add each voice command from the registry
            config.voice_commands.forEach(command => {
                const pattern = new RegExp(command.replace(/\s+/g, '\\s+'), 'i');
                this.addCommandPattern(pattern, (matches) => {
                    return this.executeUtilityByName(name, this.extractParametersFromSpeech(matches[0]));
                });
            });
        });
    }

    /**
     * Add command pattern to voice interface
     */
    addCommandPattern(pattern, handler) {
        if (this.voiceInterface && this.voiceInterface.addCommandPattern) {
            this.voiceInterface.addCommandPattern(pattern, handler);
        }
    }

    /**
     * Extract parameters from speech input
     */
    extractParametersFromSpeech(speech) {
        const parameters = {};
        
        // Extract common network parameters
        const networkMatch = speech.match(/(?:network|subnet)\s+([0-9.\/]+)/i);
        if (networkMatch) parameters.network = networkMatch[1];

        const ipMatch = speech.match(/(?:ip|host|address)\s+([0-9.]+)/i);
        if (ipMatch) parameters.ip = ipMatch[1] || parameters.host = ipMatch[1];

        const portMatch = speech.match(/port\s+(\d+)/i);
        if (portMatch) parameters.port = parseInt(portMatch[1]);

        const deviceMatch = speech.match(/device\s+([^\s]+)/i);
        if (deviceMatch) parameters.device = deviceMatch[1];

        const brandMatch = speech.match(/(bww|buffalo wild wings|arbys?|arby'?s|sonic)/i);
        if (brandMatch) parameters.brand = this.normalizeBrandName(brandMatch[1]);

        return parameters;
    }

    /**
     * Normalize brand names to standard format
     */
    normalizeBrandName(brand) {
        const brandMap = {
            'bww': 'BWW',
            'buffalo wild wings': 'BWW', 
            'arby': 'ARBYS',
            'arbys': 'ARBYS',
            "arby's": 'ARBYS',
            'sonic': 'SONIC'
        };
        return brandMap[brand.toLowerCase()] || brand.toUpperCase();
    }

    // Command Handlers

    async handleNetworkDiscovery(matches) {
        const network = matches[1] || '192.168.1.0/24';
        const protocols = matches[2] ? matches[2].split(',') : null;
        
        this.voiceInterface.speak('Starting network device discovery...');
        
        try {
            const response = await fetch('/api/utilities/device-discovery', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ network, protocols })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.voiceInterface.speak(`Discovery complete. Found ${result.devices_found || 0} devices on network ${network}.`);
                this.displayUtilityResult('Network Discovery', result);
            } else {
                this.voiceInterface.speak('Network discovery failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('Network discovery encountered an error');
            console.error('Network discovery error:', error);
        }
    }

    async handleSNMPDiscovery(matches) {
        const network = matches[1];
        const brand = this.normalizeBrandName(matches[2] || 'all');
        
        this.voiceInterface.speak('Starting SNMP device discovery...');
        
        try {
            const response = await fetch('/api/utilities/snmp-discovery', {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ network, brand })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.voiceInterface.speak(`SNMP discovery complete. Found ${result.devices_discovered || 0} devices.`);
                this.displayUtilityResult('SNMP Discovery', result);
            } else {
                this.voiceInterface.speak('SNMP discovery failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('SNMP discovery encountered an error');
            console.error('SNMP discovery error:', error);
        }
    }

    async handleSSLDiagnostics(matches) {
        const host = matches[1];
        const port = parseInt(matches[2]) || 443;
        
        this.voiceInterface.speak(`Running SSL diagnostics on ${host} port ${port}...`);
        
        try {
            const response = await fetch('/api/utilities/ssl-diagnostics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const status = result.ssl_status || 'unknown';
                this.voiceInterface.speak(`SSL diagnostics complete. Status: ${status}.`);
                this.displayUtilityResult('SSL Diagnostics', result);
            } else {
                this.voiceInterface.speak('SSL diagnostics failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('SSL diagnostics encountered an error');
            console.error('SSL diagnostics error:', error);
        }
    }

    async handleConfigDiff(matches) {
        const device1 = matches[1];
        const device2 = matches[2];
        const sections = matches[3] ? matches[3].split(',') : null;
        
        this.voiceInterface.speak(`Comparing configurations between ${device1} and ${device2}...`);
        
        try {
            const response = await fetch('/api/utilities/config-diff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device1, device2, sections })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const differences = result.differences_found || 0;
                this.voiceInterface.speak(`Configuration comparison complete. Found ${differences} differences.`);
                this.displayUtilityResult('Config Comparison', result);
            } else {
                this.voiceInterface.speak('Configuration comparison failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('Configuration comparison encountered an error');
            console.error('Config comparison error:', error);
        }
    }

    async handleTopologyVisualization(matches) {
        const dataSource = matches[1] || 'auto-discover';
        const layout = matches[2] || 'auto';
        
        this.voiceInterface.speak('Generating network topology visualization...');
        
        try {
            const response = await fetch('/api/utilities/topology-visualizer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input_data: dataSource, layout })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.voiceInterface.speak('Network topology visualization generated successfully.');
                this.displayUtilityResult('Topology Visualization', result);
            } else {
                this.voiceInterface.speak('Topology visualization failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('Topology visualization encountered an error');
            console.error('Topology visualization error:', error);
        }
    }

    async handleIPLookup(matches) {
        const ipAddress = matches[1];
        const detailLevel = matches[2] || 'standard';
        
        this.voiceInterface.speak(`Looking up IP address ${ipAddress}...`);
        
        try {
            const response = await fetch('/api/utilities/ip-lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_address: ipAddress, detail_level: detailLevel })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const isValid = result.is_valid ? 'valid' : 'invalid';
                const isPrivate = result.is_private ? 'private' : 'public';
                this.voiceInterface.speak(`IP lookup complete. Address is ${isValid} and ${isPrivate}.`);
                this.displayUtilityResult('IP Lookup', result);
            } else {
                this.voiceInterface.speak('IP lookup failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('IP lookup encountered an error');
            console.error('IP lookup error:', error);
        }
    }

    async handleBatchOperation(matches) {
        const operation = matches[1];
        const targets = matches[2].split(',').map(t => t.trim());
        
        this.voiceInterface.speak(`Starting batch ${operation} operation on ${targets.length} targets...`);
        
        try {
            const response = await fetch('/api/utilities/batch-operation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operation, targets })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.voiceInterface.speak(`Batch operation complete. Processed ${result.total_targets || targets.length} targets.`);
                this.displayUtilityResult('Batch Operation', result);
            } else {
                this.voiceInterface.speak('Batch operation failed: ' + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak('Batch operation encountered an error');
            console.error('Batch operation error:', error);
        }
    }

    async handleListUtilities(matches) {
        const category = matches[1];
        
        try {
            const response = await fetch('/api/utilities/available');
            const result = await response.json();
            
            if (result.success) {
                let message;
                if (category) {
                    const categoryUtils = Object.entries(result.utilities)
                        .filter(([name, config]) => config.category === category.toLowerCase())
                        .map(([name, config]) => name);
                    
                    message = categoryUtils.length > 0 
                        ? `${category} utilities: ${categoryUtils.join(', ')}`
                        : `No utilities found in category ${category}`;
                } else {
                    const categories = Object.values(result.categories);
                    message = `${result.utilities_count} utilities available in ${Object.keys(result.categories).length} categories`;
                }
                
                this.voiceInterface.speak(message);
                this.displayUtilityResult('Available Utilities', result);
            } else {
                this.voiceInterface.speak('Unable to get utilities list');
            }
        } catch (error) {
            this.voiceInterface.speak('Error getting utilities list');
            console.error('List utilities error:', error);
        }
    }

    async handleVoiceHelp(matches) {
        const category = matches[1];
        
        try {
            const response = await fetch('/api/utilities/voice-help');
            const result = await response.json();
            
            if (result.success) {
                const totalCommands = result.total_commands || 0;
                this.voiceInterface.speak(`${totalCommands} voice commands available. Check the display for examples.`);
                this.displayUtilityResult('Voice Commands Help', result);
            } else {
                this.voiceInterface.speak('Unable to get voice commands help');
            }
        } catch (error) {
            this.voiceInterface.speak('Error getting voice commands help');
            console.error('Voice help error:', error);
        }
    }

    async executeUtilityByName(utilityName, parameters = {}) {
        this.voiceInterface.speak(`Executing ${utilityName} utility...`);
        
        try {
            const response = await fetch(`/api/utilities/execute/${utilityName}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parameters)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.voiceInterface.speak(`${utilityName} completed successfully.`);
                this.displayUtilityResult(utilityName, result);
            } else {
                this.voiceInterface.speak(`${utilityName} failed: ` + result.error);
            }
        } catch (error) {
            this.voiceInterface.speak(`${utilityName} encountered an error`);
            console.error(`${utilityName} error:`, error);
        }
    }

    /**
     * Display utility results in the UI
     */
    displayUtilityResult(utilityName, result) {
        // Find or create utilities results panel
        let panel = document.getElementById('utilities-results');
        if (!panel) {
            panel = this.createUtilitiesResultsPanel();
        }
        
        // Create result entry
        const resultEntry = document.createElement('div');
        resultEntry.className = 'utility-result';
        resultEntry.innerHTML = `
            <div class="utility-header">
                <h4>${utilityName}</h4>
                <span class="timestamp">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="utility-content">
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
        
        // Add to panel (latest first)
        panel.insertBefore(resultEntry, panel.firstChild);
        
        // Keep only last 10 results
        while (panel.children.length > 10) {
            panel.removeChild(panel.lastChild);
        }
        
        // Show panel if hidden
        panel.style.display = 'block';
    }

    /**
     * Create utilities results panel if it doesn't exist
     */
    createUtilitiesResultsPanel() {
        const panel = document.createElement('div');
        panel.id = 'utilities-results';
        panel.className = 'utilities-results-panel';
        panel.innerHTML = `
            <div class="panel-header">
                <h3>🔧 Utilities Results</h3>
                <button onclick="this.parentElement.parentElement.style.display='none'">×</button>
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .utilities-results-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 400px;
                max-height: 600px;
                overflow-y: auto;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                z-index: 1000;
                display: none;
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background: #2a2a2a;
                border-bottom: 1px solid #333;
            }
            
            .panel-header h3 {
                margin: 0;
                color: #fff;
                font-size: 14px;
            }
            
            .panel-header button {
                background: none;
                border: none;
                color: #fff;
                cursor: pointer;
                font-size: 18px;
            }
            
            .utility-result {
                padding: 10px 15px;
                border-bottom: 1px solid #333;
            }
            
            .utility-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
            }
            
            .utility-header h4 {
                margin: 0;
                color: #4CAF50;
                font-size: 12px;
            }
            
            .timestamp {
                color: #888;
                font-size: 10px;
            }
            
            .utility-content pre {
                background: #0a0a0a;
                padding: 8px;
                border-radius: 4px;
                font-size: 10px;
                color: #ccc;
                max-height: 200px;
                overflow-y: auto;
                margin: 0;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(panel);
        
        return panel;
    }
}

// Auto-initialize when loaded
window.UtilitiesVoiceCommands = UtilitiesVoiceCommands;