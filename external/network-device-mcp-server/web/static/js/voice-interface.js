/**
 * Voice Interface for Network Device Dashboard
 * Web Speech API integration for voice recognition and text-to-speech
 */

class VoiceInterface {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.isEnabled = false;
        this.currentVoice = null;
        this.voiceCommands = {};
        
        this.init();
    }

    /**
     * Initialize voice interface
     */
    init() {
        // Check for Web Speech API support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Web Speech API not supported in this browser');
            this.showVoiceUnsupportedMessage();
            return;
        }

        this.setupSpeechRecognition();
        this.setupSpeechSynthesis();
        this.setupVoiceCommands();
        this.createVoiceUI();
        
        console.log('Voice interface initialized successfully');
    }

    /**
     * Setup speech recognition
     */
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition settings
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Event handlers
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateVoiceUI();
            this.speak('Listening for command');
            console.log('Voice recognition started');
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateVoiceUI();
            console.log('Voice recognition ended');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            console.log('Voice command received:', transcript);
            this.processVoiceCommand(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateVoiceUI();
            
            switch(event.error) {
                case 'no-speech':
                    this.speak('No speech detected. Please try again.');
                    break;
                case 'network':
                    this.speak('Network error. Please check your connection.');
                    break;
                case 'not-allowed':
                    this.speak('Microphone access denied. Please enable microphone permissions.');
                    break;
                default:
                    this.speak('Voice recognition error. Please try again.');
            }
        };
    }

    /**
     * Setup speech synthesis
     */
    setupSpeechSynthesis() {
        // Wait for voices to load
        const loadVoices = () => {
            const voices = this.synthesis.getVoices();
            // Prefer English voices
            this.currentVoice = voices.find(voice => 
                voice.lang.startsWith('en') && voice.name.includes('Google')
            ) || voices.find(voice => 
                voice.lang.startsWith('en')
            ) || voices[0];
        };

        if (this.synthesis.getVoices().length > 0) {
            loadVoices();
        } else {
            this.synthesis.onvoiceschanged = loadVoices;
        }
    }

    /**
     * Setup voice command mappings
     */
    setupVoiceCommands() {
        this.voiceCommands = {
            // Navigation commands
            'show overview': () => this.executeNavigation('overview'),
            'go to overview': () => this.executeNavigation('overview'),
            'show dashboard': () => this.executeNavigation('overview'),
            
            'show investigation': () => this.executeNavigation('investigation'),
            'open investigation': () => this.executeNavigation('investigation'),
            'investigate store': () => this.executeNavigation('investigation'),
            
            'show fortianalyzer': () => this.executeNavigation('fortianalyzer'),
            'open fortianalyzer': () => this.executeNavigation('fortianalyzer'),
            'show logs': () => this.executeNavigation('fortianalyzer'),
            
            'show web filters': () => this.executeNavigation('webfilters'),
            'open web filters': () => this.executeNavigation('webfilters'),
            'show filters': () => this.executeNavigation('webfilters'),
            
            'show log analysis': () => this.executeNavigation('log-analysis'),
            'search logs': () => this.executeNavigation('log-analysis'),
            'analyze logs': () => this.executeNavigation('log-analysis'),
            
            // Brand navigation
            'show buffalo wild wings': () => this.executeNavigation('brand-BWW'),
            'show bww': () => this.executeNavigation('brand-BWW'),
            'show arbys': () => this.executeNavigation('brand-ARBYS'),
            'show arby\'s': () => this.executeNavigation('brand-ARBYS'),
            'show sonic': () => this.executeNavigation('brand-SONIC'),
            
            // Investigation commands
            'investigate bww': () => this.executeInvestigation('BWW'),
            'investigate buffalo wild wings': () => this.executeInvestigation('BWW'),
            'investigate arbys': () => this.executeInvestigation('ARBYS'),
            'investigate arby\'s': () => this.executeInvestigation('ARBYS'),
            'investigate sonic': () => this.executeInvestigation('SONIC'),
            
            // FortiAnalyzer commands
            'show threat intelligence': () => this.executeFortiAnalyzerAction('threats'),
            'show threats': () => this.executeFortiAnalyzerAction('threats'),
            'show analytics': () => this.executeFortiAnalyzerAction('analytics'),
            'generate report': () => this.executeFortiAnalyzerAction('report'),
            'security report': () => this.executeFortiAnalyzerAction('report'),
            
            // Web Filters commands
            'start web filter server': () => this.executeWebFiltersAction('start'),
            'stop web filter server': () => this.executeWebFiltersAction('stop'),
            'show policies': () => this.executeWebFiltersAction('policies'),
            'show ssl status': () => this.executeWebFiltersAction('ssl'),
            
            // System commands
            'refresh data': () => this.executeSystemAction('refresh'),
            'refresh': () => this.executeSystemAction('refresh'),
            'check connection': () => this.executeSystemAction('connection'),
            'help': () => this.executeSystemAction('help'),
            'what can you do': () => this.executeSystemAction('help'),
            
            // Status commands
            'what is the status': () => this.executeSystemAction('status'),
            'system status': () => this.executeSystemAction('status'),
            'health check': () => this.executeSystemAction('health')
        };
    }

    /**
     * Process voice command
     */
    processVoiceCommand(transcript) {
        console.log('Processing voice command:', transcript);
        
        // Check for exact matches first
        if (this.voiceCommands[transcript]) {
            this.speak('Command recognized');
            this.voiceCommands[transcript]();
            return;
        }
        
        // Check for partial matches
        const matchingCommands = Object.keys(this.voiceCommands).filter(command => 
            transcript.includes(command) || command.includes(transcript)
        );
        
        if (matchingCommands.length > 0) {
            this.speak('Command recognized');
            this.voiceCommands[matchingCommands[0]]();
            return;
        }
        
        // Check for store investigation patterns
        const storeInvestigationMatch = transcript.match(/investigate\s+(bww|buffalo wild wings|arbys?|arby'?s|sonic)\s+store\s+(\d+)/);
        if (storeInvestigationMatch) {
            const brand = this.normalizeBrandName(storeInvestigationMatch[1]);
            const storeId = storeInvestigationMatch[2];
            this.executeStoreInvestigation(brand, storeId);
            return;
        }
        
        // Check for log search patterns
        const logSearchMatch = transcript.match(/search\s+(?:for\s+)?(.+?)(?:\s+in\s+(.+?))?$/);
        if (logSearchMatch) {
            const query = logSearchMatch[1];
            const timeframe = this.parseTimeframe(logSearchMatch[2]) || '24h';
            this.executeLogSearch(query, timeframe);
            return;
        }
        
        // Command not recognized
        this.speak('Command not recognized. Say "help" for available commands.');
        console.log('Unrecognized voice command:', transcript);
    }

    /**
     * Execute navigation command
     */
    executeNavigation(sectionId) {
        this.speak(`Navigating to ${sectionId.replace('-', ' ')}`);
        showSection(sectionId);
    }

    /**
     * Execute investigation command
     */
    executeInvestigation(brand) {
        this.speak(`Opening investigation for ${this.getBrandDisplayName(brand)}`);
        showSection('investigation');
        document.getElementById('investigationBrand').value = brand;
    }

    /**
     * Execute store investigation
     */
    executeStoreInvestigation(brand, storeId) {
        this.speak(`Investigating ${this.getBrandDisplayName(brand)} store ${storeId}`);
        showSection('investigation');
        document.getElementById('investigationBrand').value = brand;
        document.getElementById('investigationStore').value = storeId;
        // Auto-run investigation
        setTimeout(() => runInvestigation(), 500);
    }

    /**
     * Execute FortiAnalyzer action
     */
    executeFortiAnalyzerAction(action) {
        showSection('fortianalyzer');
        
        switch(action) {
            case 'threats':
                this.speak('Loading threat intelligence');
                setTimeout(() => showThreatIntelligence(), 500);
                break;
            case 'analytics':
                this.speak('Loading log analytics');
                setTimeout(() => showLogAnalytics(), 500);
                break;
            case 'report':
                this.speak('Generating security report');
                setTimeout(() => generateSecurityReport(), 500);
                break;
        }
    }

    /**
     * Execute Web Filters action
     */
    executeWebFiltersAction(action) {
        showSection('webfilters');
        
        switch(action) {
            case 'start':
                this.speak('Starting web filters server');
                setTimeout(() => startWebFiltersServer(), 500);
                break;
            case 'stop':
                this.speak('Stopping web filters server');
                setTimeout(() => stopWebFiltersServer(), 500);
                break;
            case 'policies':
                this.speak('Loading web filtering policies');
                setTimeout(() => viewWebFilteringPolicies(), 500);
                break;
            case 'ssl':
                this.speak('Checking SSL certificate status');
                setTimeout(() => viewSSLCertificateStatus(), 500);
                break;
        }
    }

    /**
     * Execute log search
     */
    executeLogSearch(query, timeframe) {
        this.speak(`Searching logs for ${query} in the ${timeframe}`);
        showSection('log-analysis');
        document.getElementById('logSearchQuery').value = query;
        document.getElementById('logSearchTimeframe').value = timeframe;
        setTimeout(() => searchLogs(), 500);
    }

    /**
     * Execute system action
     */
    executeSystemAction(action) {
        switch(action) {
            case 'refresh':
                this.speak('Refreshing dashboard data');
                refreshData();
                break;
            case 'connection':
                this.speak('Checking connection status');
                checkConnection();
                break;
            case 'status':
                this.announceSystemStatus();
                break;
            case 'health':
                this.announceHealthStatus();
                break;
            case 'help':
                this.announceVoiceHelp();
                break;
        }
    }

    /**
     * Announce system status
     */
    announceSystemStatus() {
        const status = connectionStatus === 'connected' ? 'connected and operational' : 'disconnected';
        this.speak(`System status: ${status}`);
    }

    /**
     * Announce health status
     */
    announceHealthStatus() {
        // Get current section stats
        const currentSectionName = currentSection.replace('-', ' ');
        this.speak(`Currently viewing ${currentSectionName}. System is ${connectionStatus === 'connected' ? 'healthy' : 'experiencing connection issues'}.`);
    }

    /**
     * Announce voice help
     */
    announceVoiceHelp() {
        const helpText = `Voice commands available: Navigate with "show overview" or "show investigation". 
        Investigate stores with "investigate BWW store 155". 
        Search logs with "search for SQL injection". 
        Control web filters with "start web filter server". 
        Get help anytime by saying "help".`;
        this.speak(helpText);
    }

    /**
     * Text-to-speech function
     */
    speak(text, options = {}) {
        if (this.isSpeaking) {
            this.synthesis.cancel();
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure utterance
        utterance.voice = this.currentVoice;
        utterance.rate = options.rate || 0.9;
        utterance.pitch = options.pitch || 1;
        utterance.volume = options.volume || 0.8;
        
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateVoiceUI();
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateVoiceUI();
        };
        
        this.synthesis.speak(utterance);
        console.log('Speaking:', text);
    }

    /**
     * Start listening for voice commands
     */
    startListening() {
        if (!this.recognition) {
            this.speak('Voice recognition not available');
            return;
        }
        
        if (this.isListening) {
            this.stopListening();
            return;
        }
        
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            this.speak('Error starting voice recognition');
        }
    }

    /**
     * Stop listening for voice commands
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    /**
     * Toggle voice interface on/off
     */
    toggleVoice() {
        this.isEnabled = !this.isEnabled;
        this.updateVoiceUI();
        
        if (this.isEnabled) {
            this.speak('Voice interface enabled');
        } else {
            this.speak('Voice interface disabled');
            this.stopListening();
        }
    }

    /**
     * Create voice UI controls
     */
    createVoiceUI() {
        const voiceContainer = document.createElement('div');
        voiceContainer.id = 'voiceContainer';
        voiceContainer.className = 'voice-container';
        
        voiceContainer.innerHTML = `
            <div class="voice-controls">
                <button id="voiceToggle" class="voice-btn voice-toggle" onclick="voiceInterface.toggleVoice()" title="Toggle Voice Interface">
                    <i class="fas fa-microphone"></i>
                </button>
                <button id="voiceListen" class="voice-btn voice-listen" onclick="voiceInterface.startListening()" title="Start Voice Command" disabled>
                    <i class="fas fa-microphone-alt"></i>
                </button>
                <button id="voiceStop" class="voice-btn voice-stop" onclick="voiceInterface.stopSpeaking()" title="Stop Speaking">
                    <i class="fas fa-volume-mute"></i>
                </button>
                <button id="voiceHelp" class="voice-btn voice-help" onclick="voiceInterface.announceVoiceHelp()" title="Voice Help">
                    <i class="fas fa-question-circle"></i>
                </button>
            </div>
            <div class="voice-status" id="voiceStatus">
                <span class="status-text">Voice Disabled</span>
                <div class="voice-indicator"></div>
            </div>
        `;
        
        // Insert voice controls into header
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            headerActions.insertBefore(voiceContainer, headerActions.firstChild);
        }
        
        this.updateVoiceUI();
    }

    /**
     * Update voice UI state
     */
    updateVoiceUI() {
        const toggleBtn = document.getElementById('voiceToggle');
        const listenBtn = document.getElementById('voiceListen');
        const statusElement = document.getElementById('voiceStatus');
        const statusText = statusElement?.querySelector('.status-text');
        const indicator = statusElement?.querySelector('.voice-indicator');
        
        if (!toggleBtn) return;
        
        // Update toggle button
        toggleBtn.className = `voice-btn voice-toggle ${this.isEnabled ? 'enabled' : 'disabled'}`;
        toggleBtn.querySelector('i').className = this.isEnabled ? 'fas fa-microphone' : 'fas fa-microphone-slash';
        
        // Update listen button
        if (listenBtn) {
            listenBtn.disabled = !this.isEnabled;
            listenBtn.className = `voice-btn voice-listen ${this.isListening ? 'listening' : ''}`;
        }
        
        // Update status
        if (statusText && indicator) {
            if (!this.isEnabled) {
                statusText.textContent = 'Voice Disabled';
                indicator.className = 'voice-indicator disabled';
            } else if (this.isListening) {
                statusText.textContent = 'Listening...';
                indicator.className = 'voice-indicator listening';
            } else if (this.isSpeaking) {
                statusText.textContent = 'Speaking...';
                indicator.className = 'voice-indicator speaking';
            } else {
                statusText.textContent = 'Voice Ready';
                indicator.className = 'voice-indicator ready';
            }
        }
    }

    /**
     * Stop speaking
     */
    stopSpeaking() {
        if (this.isSpeaking) {
            this.synthesis.cancel();
            this.isSpeaking = false;
            this.updateVoiceUI();
        }
    }

    /**
     * Show unsupported message
     */
    showVoiceUnsupportedMessage() {
        const message = document.createElement('div');
        message.className = 'voice-unsupported-message';
        message.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                Voice commands are not supported in this browser. Please use Chrome, Edge, or Safari for voice features.
            </div>
        `;
        
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            headerActions.insertBefore(message, headerActions.firstChild);
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
}

// Initialize voice interface when page loads
let voiceInterface;
document.addEventListener('DOMContentLoaded', function() {
    voiceInterface = new VoiceInterface();
});

// Global functions for voice integration
function announceToast(message, type) {
    if (voiceInterface && voiceInterface.isEnabled) {
        // Announce important toasts
        if (type === 'error' || type === 'success') {
            voiceInterface.speak(message);
        }
    }
}

function announceLoading(text) {
    if (voiceInterface && voiceInterface.isEnabled && text) {
        voiceInterface.speak(text);
    }
}

function announceNavigationChange(sectionName) {
    if (voiceInterface && voiceInterface.isEnabled) {
        voiceInterface.speak(`Now viewing ${sectionName.replace('-', ' ')} section`);
    }
}