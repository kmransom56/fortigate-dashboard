/**
 * Voice Accessibility Features
 * Enhanced accessibility and hands-free operation capabilities
 */

class VoiceAccessibility {
    constructor(voiceInterface) {
        this.voiceInterface = voiceInterface;
        this.screenReaderMode = false;
        this.verboseMode = false;
        this.keyboardShortcuts = true;
        this.continuousListening = false;
        this.autoAnnouncements = true;
        
        this.setupAccessibilityFeatures();
        this.setupKeyboardShortcuts();
        this.detectUserPreferences();
    }

    /**
     * Setup accessibility features
     */
    setupAccessibilityFeatures() {
        this.createAccessibilityPanel();
        this.setupScreenReaderIntegration();
        this.setupFocusManagement();
        this.setupContinuousListening();
        this.setupContextualHelp();
    }

    /**
     * Create accessibility control panel
     */
    createAccessibilityPanel() {
        const panel = document.createElement('div');
        panel.id = 'accessibilityPanel';
        panel.className = 'accessibility-panel';
        panel.setAttribute('aria-label', 'Voice and Accessibility Controls');
        
        panel.innerHTML = `
            <div class="accessibility-header">
                <h3>Voice & Accessibility</h3>
                <button class="panel-toggle" onclick="voiceAccessibility.togglePanel()" aria-label="Toggle accessibility panel">
                    <i class="fas fa-universal-access"></i>
                </button>
            </div>
            
            <div class="accessibility-content">
                <div class="accessibility-section">
                    <h4>Voice Features</h4>
                    <div class="control-group">
                        <label class="accessibility-toggle">
                            <input type="checkbox" id="screenReaderMode" onchange="voiceAccessibility.toggleScreenReader(this.checked)" aria-describedby="screenReaderHelp">
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Screen Reader Mode</span>
                        </label>
                        <div id="screenReaderHelp" class="control-help">Enhanced voice descriptions for all interface elements</div>
                    </div>
                    
                    <div class="control-group">
                        <label class="accessibility-toggle">
                            <input type="checkbox" id="verboseMode" onchange="voiceAccessibility.toggleVerboseMode(this.checked)" aria-describedby="verboseHelp">
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Verbose Mode</span>
                        </label>
                        <div id="verboseHelp" class="control-help">Detailed voice feedback for all actions</div>
                    </div>
                    
                    <div class="control-group">
                        <label class="accessibility-toggle">
                            <input type="checkbox" id="continuousListening" onchange="voiceAccessibility.toggleContinuousListening(this.checked)" aria-describedby="continuousHelp">
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Continuous Listening</span>
                        </label>
                        <div id="continuousHelp" class="control-help">Always listen for voice commands without button press</div>
                    </div>
                    
                    <div class="control-group">
                        <label class="accessibility-toggle">
                            <input type="checkbox" id="autoAnnouncements" onchange="voiceAccessibility.toggleAutoAnnouncements(this.checked)" aria-describedby="announcementsHelp" checked>
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Auto Announcements</span>
                        </label>
                        <div id="announcementsHelp" class="control-help">Automatic voice announcements for system events</div>
                    </div>
                </div>
                
                <div class="accessibility-section">
                    <h4>Voice Settings</h4>
                    <div class="control-group">
                        <label for="speechRate">Speech Rate</label>
                        <input type="range" id="speechRate" min="0.5" max="2" step="0.1" value="0.9" onchange="voiceAccessibility.updateSpeechRate(this.value)" aria-describedby="speechRateValue">
                        <span id="speechRateValue" class="range-value">0.9x</span>
                    </div>
                    
                    <div class="control-group">
                        <label for="speechVolume">Speech Volume</label>
                        <input type="range" id="speechVolume" min="0.1" max="1" step="0.1" value="0.8" onchange="voiceAccessibility.updateSpeechVolume(this.value)" aria-describedby="speechVolumeValue">
                        <span id="speechVolumeValue" class="range-value">80%</span>
                    </div>
                    
                    <div class="control-group">
                        <label for="voiceSelect">Voice Selection</label>
                        <select id="voiceSelect" onchange="voiceAccessibility.updateVoice(this.value)" aria-describedby="voiceHelp">
                            <option value="">Default Voice</option>
                        </select>
                        <div id="voiceHelp" class="control-help">Choose preferred voice for speech synthesis</div>
                    </div>
                </div>
                
                <div class="accessibility-section">
                    <h4>Keyboard Shortcuts</h4>
                    <div class="shortcuts-list">
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd> - Toggle Voice Interface
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>L</kbd> - Start Listening
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> - Stop Speaking
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>H</kbd> - Voice Help
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd> - Toggle Accessibility Panel
                        </div>
                    </div>
                </div>
                
                <div class="accessibility-section">
                    <h4>Quick Actions</h4>
                    <div class="quick-actions">
                        <button class="accessibility-btn" onclick="voiceAccessibility.announceCurrentPage()" aria-label="Describe current page">
                            <i class="fas fa-eye"></i>
                            Describe Page
                        </button>
                        <button class="accessibility-btn" onclick="voiceAccessibility.announceNavigation()" aria-label="List navigation options">
                            <i class="fas fa-list"></i>
                            Navigation Options
                        </button>
                        <button class="accessibility-btn" onclick="voiceAccessibility.announceVoiceCommands()" aria-label="List available voice commands">
                            <i class="fas fa-microphone"></i>
                            Voice Commands
                        </button>
                        <button class="accessibility-btn" onclick="voiceAccessibility.toggleHighContrast()" aria-label="Toggle high contrast mode">
                            <i class="fas fa-adjust"></i>
                            High Contrast
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Insert panel into page
        document.body.appendChild(panel);
        
        // Load available voices
        this.loadAvailableVoices();
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            if (!this.keyboardShortcuts) return;
            
            // Check for Ctrl+Shift combinations
            if (event.ctrlKey && event.shiftKey) {
                switch (event.key.toLowerCase()) {
                    case 'v':
                        event.preventDefault();
                        this.voiceInterface.toggleVoice();
                        this.announceShortcut('Voice interface toggled');
                        break;
                    case 'l':
                        event.preventDefault();
                        this.voiceInterface.startListening();
                        this.announceShortcut('Voice listening started');
                        break;
                    case 's':
                        event.preventDefault();
                        this.voiceInterface.stopSpeaking();
                        this.announceShortcut('Speech stopped');
                        break;
                    case 'h':
                        event.preventDefault();
                        this.voiceInterface.announceVoiceHelp();
                        break;
                    case 'a':
                        event.preventDefault();
                        this.togglePanel();
                        break;
                }
            }
            
            // Escape key to stop voice
            if (event.key === 'Escape' && this.voiceInterface.isSpeaking) {
                this.voiceInterface.stopSpeaking();
            }
        });
    }

    /**
     * Detect user preferences
     */
    detectUserPreferences() {
        // Check for system accessibility preferences
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            console.log('Reduced motion preference detected');
        }
        
        if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
            this.enableHighContrast();
        }
        
        // Check for screen reader
        this.detectScreenReader();
        
        // Load saved preferences
        this.loadUserPreferences();
    }

    /**
     * Detect screen reader
     */
    detectScreenReader() {
        // Basic screen reader detection
        const hasScreenReader = (
            navigator.userAgent.includes('NVDA') ||
            navigator.userAgent.includes('JAWS') ||
            window.speechSynthesis === undefined ||
            (window.navigator && window.navigator.userAgent && window.navigator.userAgent.includes('aira'))
        );
        
        if (hasScreenReader) {
            this.enableScreenReaderMode();
        }
    }

    /**
     * Screen reader integration
     */
    setupScreenReaderIntegration() {
        // Ensure proper ARIA labels and roles
        this.enhanceAccessibilityMarkup();
        
        // Setup live regions for dynamic content
        this.createLiveRegions();
        
        // Enhanced keyboard navigation
        this.enhanceKeyboardNavigation();
    }

    /**
     * Create live regions for screen readers
     */
    createLiveRegions() {
        // Status live region
        const statusRegion = document.createElement('div');
        statusRegion.id = 'statusLiveRegion';
        statusRegion.setAttribute('aria-live', 'polite');
        statusRegion.setAttribute('aria-atomic', 'true');
        statusRegion.className = 'sr-only';
        document.body.appendChild(statusRegion);
        
        // Alert live region
        const alertRegion = document.createElement('div');
        alertRegion.id = 'alertLiveRegion';
        alertRegion.setAttribute('aria-live', 'assertive');
        alertRegion.setAttribute('aria-atomic', 'true');
        alertRegion.className = 'sr-only';
        document.body.appendChild(alertRegion);
        
        this.statusRegion = statusRegion;
        this.alertRegion = alertRegion;
    }

    /**
     * Enhance accessibility markup
     */
    enhanceAccessibilityMarkup() {
        // Add missing ARIA labels and roles
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            const text = button.textContent.trim() || button.title;
            if (text) {
                button.setAttribute('aria-label', text);
            }
        });
        
        // Enhance navigation
        const nav = document.querySelector('.sidebar');
        if (nav && !nav.getAttribute('role')) {
            nav.setAttribute('role', 'navigation');
            nav.setAttribute('aria-label', 'Main navigation');
        }
        
        // Enhance main content
        const main = document.querySelector('.main-content');
        if (main && !main.getAttribute('role')) {
            main.setAttribute('role', 'main');
        }
    }

    /**
     * Setup continuous listening
     */
    setupContinuousListening() {
        // Implement wake word detection (basic implementation)
        this.wakeWords = ['hey dashboard', 'computer', 'voice command'];
        
        if (this.continuousListening) {
            this.startContinuousListening();
        }
    }

    /**
     * Setup contextual help
     */
    setupContextualHelp() {
        // Add context-sensitive voice help
        document.addEventListener('focusin', (event) => {
            if (this.screenReaderMode && event.target.dataset.voiceHelp) {
                setTimeout(() => {
                    this.voiceInterface.speak(event.target.dataset.voiceHelp);
                }, 500);
            }
        });
    }

    /**
     * Toggle accessibility panel
     */
    togglePanel() {
        const panel = document.getElementById('accessibilityPanel');
        panel.classList.toggle('expanded');
        
        const isExpanded = panel.classList.contains('expanded');
        panel.setAttribute('aria-expanded', isExpanded);
        
        if (this.autoAnnouncements) {
            this.voiceInterface.speak(isExpanded ? 'Accessibility panel opened' : 'Accessibility panel closed');
        }
    }

    /**
     * Toggle screen reader mode
     */
    toggleScreenReader(enabled) {
        this.screenReaderMode = enabled;
        document.body.classList.toggle('screen-reader-mode', enabled);
        
        if (enabled) {
            this.voiceInterface.speak('Screen reader mode enabled. Enhanced voice descriptions activated.');
            this.announceCurrentPage();
        } else {
            this.voiceInterface.speak('Screen reader mode disabled');
        }
        
        this.saveUserPreferences();
    }

    /**
     * Toggle verbose mode
     */
    toggleVerboseMode(enabled) {
        this.verboseMode = enabled;
        
        if (enabled) {
            this.voiceInterface.speak('Verbose mode enabled. Detailed feedback will be provided for all actions.');
        } else {
            this.voiceInterface.speak('Verbose mode disabled');
        }
        
        this.saveUserPreferences();
    }

    /**
     * Toggle continuous listening
     */
    toggleContinuousListening(enabled) {
        this.continuousListening = enabled;
        
        if (enabled) {
            this.voiceInterface.speak('Continuous listening enabled. I will always listen for voice commands.');
            this.startContinuousListening();
        } else {
            this.voiceInterface.speak('Continuous listening disabled');
            this.stopContinuousListening();
        }
        
        this.saveUserPreferences();
    }

    /**
     * Toggle auto announcements
     */
    toggleAutoAnnouncements(enabled) {
        this.autoAnnouncements = enabled;
        
        if (enabled) {
            this.voiceInterface.speak('Auto announcements enabled');
        } else {
            this.voiceInterface.speak('Auto announcements disabled');
        }
        
        this.saveUserPreferences();
    }

    /**
     * Update speech settings
     */
    updateSpeechRate(rate) {
        const rateValue = parseFloat(rate);
        this.voiceInterface.speechRate = rateValue;
        document.getElementById('speechRateValue').textContent = rateValue + 'x';
        
        // Test speech with new rate
        this.voiceInterface.speak('Speech rate updated', { rate: rateValue });
        
        this.saveUserPreferences();
    }

    updateSpeechVolume(volume) {
        const volumeValue = parseFloat(volume);
        this.voiceInterface.speechVolume = volumeValue;
        document.getElementById('speechVolumeValue').textContent = Math.round(volumeValue * 100) + '%';
        
        // Test speech with new volume
        this.voiceInterface.speak('Volume updated', { volume: volumeValue });
        
        this.saveUserPreferences();
    }

    updateVoice(voiceId) {
        const voices = window.speechSynthesis.getVoices();
        const selectedVoice = voices.find(voice => voice.name === voiceId);
        
        if (selectedVoice) {
            this.voiceInterface.currentVoice = selectedVoice;
            this.voiceInterface.speak('Voice updated', { voice: selectedVoice });
        }
        
        this.saveUserPreferences();
    }

    /**
     * Load available voices
     */
    loadAvailableVoices() {
        const voiceSelect = document.getElementById('voiceSelect');
        if (!voiceSelect) return;
        
        const loadVoices = () => {
            const voices = window.speechSynthesis.getVoices();
            voiceSelect.innerHTML = '<option value="">Default Voice</option>';
            
            voices.forEach(voice => {
                if (voice.lang.startsWith('en')) {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    voiceSelect.appendChild(option);
                }
            });
        };
        
        if (window.speechSynthesis.getVoices().length > 0) {
            loadVoices();
        } else {
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    /**
     * Announce current page
     */
    announceCurrentPage() {
        const currentSectionName = currentSection.replace('-', ' ');
        const activeSection = document.getElementById(currentSection);
        
        let announcement = `Currently viewing ${currentSectionName} section. `;
        
        if (activeSection) {
            const header = activeSection.querySelector('h1, h2');
            if (header) {
                announcement += `Section title: ${header.textContent}. `;
            }
            
            const description = activeSection.querySelector('p');
            if (description) {
                announcement += `Description: ${description.textContent}. `;
            }
            
            // Count interactive elements
            const buttons = activeSection.querySelectorAll('button, input, select');
            if (buttons.length > 0) {
                announcement += `This section has ${buttons.length} interactive elements. `;
            }
        }
        
        announcement += 'Say "navigation options" to hear available sections, or "voice commands" for available commands.';
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce navigation options
     */
    announceNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        const sections = Array.from(navButtons).map(btn => {
            return btn.textContent.trim();
        }).filter(text => text);
        
        let announcement = `Available sections: ${sections.join(', ')}. `;
        announcement += 'Say "show" followed by the section name to navigate.';
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Announce available voice commands
     */
    announceVoiceCommands() {
        const commands = [
            'Show overview, investigation, FortiAnalyzer, or web filters',
            'Investigate specific stores like "investigate BWW store 155"',
            'Search logs with "search for SQL injection"',
            'Check system status or generate reports',
            'Control web filter server with start or stop commands'
        ];
        
        let announcement = 'Available voice commands: ';
        announcement += commands.join('. ');
        announcement += '. Say "help" anytime for more detailed assistance.';
        
        this.voiceInterface.speak(announcement);
    }

    /**
     * Toggle high contrast mode
     */
    toggleHighContrast() {
        document.body.classList.toggle('high-contrast');
        const isEnabled = document.body.classList.contains('high-contrast');
        
        this.voiceInterface.speak(isEnabled ? 'High contrast mode enabled' : 'High contrast mode disabled');
    }

    /**
     * Enable screen reader mode
     */
    enableScreenReaderMode() {
        document.getElementById('screenReaderMode').checked = true;
        this.toggleScreenReader(true);
    }

    /**
     * Enable high contrast
     */
    enableHighContrast() {
        document.body.classList.add('high-contrast');
    }

    /**
     * Start continuous listening
     */
    startContinuousListening() {
        // Implement continuous listening with wake words
        if (this.voiceInterface.recognition) {
            this.voiceInterface.recognition.continuous = true;
            this.voiceInterface.recognition.interimResults = true;
        }
    }

    /**
     * Stop continuous listening
     */
    stopContinuousListening() {
        if (this.voiceInterface.recognition) {
            this.voiceInterface.recognition.continuous = false;
            this.voiceInterface.recognition.interimResults = false;
        }
    }

    /**
     * Announce keyboard shortcut activation
     */
    announceShortcut(message) {
        if (this.autoAnnouncements) {
            this.voiceInterface.speak(message);
        }
    }

    /**
     * Update live regions for screen readers
     */
    updateLiveRegion(message, type = 'status') {
        const region = type === 'alert' ? this.alertRegion : this.statusRegion;
        if (region) {
            region.textContent = message;
        }
    }

    /**
     * Enhance keyboard navigation
     */
    enhanceKeyboardNavigation() {
        // Ensure all interactive elements are keyboard accessible
        const focusableElements = document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements.forEach((element, index) => {
            if (!element.getAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
        });
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        const preferences = {
            screenReaderMode: this.screenReaderMode,
            verboseMode: this.verboseMode,
            continuousListening: this.continuousListening,
            autoAnnouncements: this.autoAnnouncements,
            speechRate: this.voiceInterface.speechRate,
            speechVolume: this.voiceInterface.speechVolume,
            selectedVoice: this.voiceInterface.currentVoice?.name
        };
        
        localStorage.setItem('voiceAccessibilityPreferences', JSON.stringify(preferences));
    }

    /**
     * Load user preferences
     */
    loadUserPreferences() {
        try {
            const saved = localStorage.getItem('voiceAccessibilityPreferences');
            if (saved) {
                const preferences = JSON.parse(saved);
                
                // Apply saved preferences
                if (preferences.screenReaderMode) {
                    document.getElementById('screenReaderMode').checked = true;
                    this.toggleScreenReader(true);
                }
                
                if (preferences.verboseMode) {
                    document.getElementById('verboseMode').checked = true;
                    this.toggleVerboseMode(true);
                }
                
                if (preferences.continuousListening) {
                    document.getElementById('continuousListening').checked = true;
                    this.toggleContinuousListening(true);
                }
                
                if (preferences.autoAnnouncements !== undefined) {
                    document.getElementById('autoAnnouncements').checked = preferences.autoAnnouncements;
                    this.toggleAutoAnnouncements(preferences.autoAnnouncements);
                }
                
                if (preferences.speechRate) {
                    document.getElementById('speechRate').value = preferences.speechRate;
                    this.updateSpeechRate(preferences.speechRate);
                }
                
                if (preferences.speechVolume) {
                    document.getElementById('speechVolume').value = preferences.speechVolume;
                    this.updateSpeechVolume(preferences.speechVolume);
                }
                
                if (preferences.selectedVoice) {
                    document.getElementById('voiceSelect').value = preferences.selectedVoice;
                    this.updateVoice(preferences.selectedVoice);
                }
            }
        } catch (error) {
            console.warn('Error loading voice accessibility preferences:', error);
        }
    }
}

// Initialize voice accessibility when voice interface is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof voiceInterface !== 'undefined') {
        window.voiceAccessibility = new VoiceAccessibility(voiceInterface);
        
        // Add CSS class for screen reader styles
        const style = document.createElement('style');
        style.textContent = `
            .sr-only {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
        `;
        document.head.appendChild(style);
    }
});