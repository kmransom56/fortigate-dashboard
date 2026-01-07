"""
Voice Learning Engine for Network Intelligence
Advanced voice command learning and natural language processing
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum
import hashlib

from .ltm_memory import LTMMemorySystem

class CommandIntent(Enum):
    """Voice command intents"""
    INVESTIGATION = "investigation"
    NAVIGATION = "navigation" 
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_CHECK = "performance_check"
    SYSTEM_CONTROL = "system_control"
    DATA_QUERY = "data_query"
    REPORT_GENERATION = "report_generation"
    PREDICTION_REQUEST = "prediction_request"
    PATTERN_ANALYSIS = "pattern_analysis"
    HELP_REQUEST = "help_request"

@dataclass
class VoiceCommand:
    """Represents a voice command"""
    command_id: str
    raw_text: str
    normalized_text: str
    intent: CommandIntent
    entities: Dict[str, str]  # brand, store_id, device_name, etc.
    parameters: Dict[str, Any]  # timeframe, analysis_type, etc.
    confidence: float
    timestamp: datetime
    success: bool
    response_time: float
    user_feedback: Optional[str] = None

@dataclass
class CommandPattern:
    """Learned command pattern"""
    pattern_id: str
    pattern_regex: str
    intent: CommandIntent
    entity_extractors: Dict[str, str]  # regex patterns for entities
    parameter_extractors: Dict[str, str]
    examples: List[str]
    confidence: float
    usage_count: int
    success_rate: float
    last_used: datetime

@dataclass
class VoiceInsight:
    """Voice usage insight"""
    insight_type: str
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    confidence: float

class VoiceLearningEngine:
    """
    Advanced voice learning engine for network operations
    Learns from voice interactions to improve recognition and responses
    """
    
    def __init__(self, ltm_memory: LTMMemorySystem, config: Dict[str, Any] = None):
        """
        Initialize Voice Learning Engine
        
        Args:
            ltm_memory: LTM memory system instance
            config: Configuration parameters
        """
        self.ltm_memory = ltm_memory
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Learning parameters
        self.min_pattern_confidence = self.config.get('min_pattern_confidence', 0.7)
        self.min_usage_count = self.config.get('min_usage_count', 3)
        self.learning_rate = self.config.get('learning_rate', 0.1)
        
        # Command patterns storage
        self.command_patterns: Dict[str, CommandPattern] = {}
        self.entity_vocabularies: Dict[str, Set[str]] = defaultdict(set)
        
        # Initialize with base patterns
        self._initialize_base_patterns()
        self._load_entity_vocabularies()
    
    def process_voice_command(self, raw_text: str, context: Dict[str, Any] = None) -> VoiceCommand:
        """
        Process a voice command and extract intent and entities
        
        Args:
            raw_text: Raw voice command text
            context: Additional context information
            
        Returns:
            Processed voice command
        """
        try:
            # Normalize text
            normalized_text = self._normalize_text(raw_text)
            
            # Extract intent and entities
            intent, confidence = self._extract_intent(normalized_text)
            entities = self._extract_entities(normalized_text, intent)
            parameters = self._extract_parameters(normalized_text, intent)
            
            # Create command object
            command = VoiceCommand(
                command_id=self._generate_command_id(raw_text),
                raw_text=raw_text,
                normalized_text=normalized_text,
                intent=intent,
                entities=entities,
                parameters=parameters,
                confidence=confidence,
                timestamp=datetime.now(),
                success=True,  # Will be updated based on execution
                response_time=0.0  # Will be updated
            )
            
            self.logger.debug(f"Processed voice command: {intent.value} - {confidence:.2f}")
            return command
            
        except Exception as e:
            self.logger.error(f"Error processing voice command '{raw_text}': {e}")
            return self._create_fallback_command(raw_text)
    
    def learn_from_interaction(self, command: VoiceCommand, execution_result: Dict[str, Any]):
        """
        Learn from voice command interaction
        
        Args:
            command: The processed voice command
            execution_result: Result of command execution
        """
        try:
            # Update command with execution results
            command.success = execution_result.get('success', False)
            command.response_time = execution_result.get('response_time', 0.0)
            command.user_feedback = execution_result.get('user_feedback')
            
            # Store interaction in LTM
            self.ltm_memory.record_voice_interaction(
                command=command.raw_text,
                intent=command.intent.value,
                success=command.success,
                response_time=command.response_time,
                user_feedback=command.user_feedback,
                context={
                    'entities': command.entities,
                    'parameters': command.parameters,
                    'confidence': command.confidence
                }
            )
            
            # Update patterns based on success/failure
            self._update_patterns(command)
            
            # Learn new entities
            self._learn_entities(command)
            
            # Adapt to user language patterns
            self._adapt_language_patterns(command)
            
            self.logger.debug(f"Learned from interaction: {command.command_id}")
            
        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
    
    def suggest_voice_commands(self, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Suggest voice commands based on context and usage patterns
        
        Args:
            context: Current context (section, brand, etc.)
            
        Returns:
            List of suggested commands
        """
        try:
            suggestions = []
            
            # Get context-aware suggestions
            current_section = context.get('current_section') if context else None
            
            # Base suggestions for each intent
            intent_suggestions = {
                CommandIntent.INVESTIGATION: [
                    "Investigate {brand} store {store_id}",
                    "Check security status for {brand} store {store_id}",
                    "Run security analysis for {brand}"
                ],
                CommandIntent.NAVIGATION: [
                    "Show overview",
                    "Go to FortiAnalyzer", 
                    "Open web filters",
                    "Navigate to investigation"
                ],
                CommandIntent.SECURITY_ANALYSIS: [
                    "Show critical security events",
                    "Search for malware in {brand} logs",
                    "Check threat intelligence for {brand}"
                ],
                CommandIntent.PREDICTION_REQUEST: [
                    "Predict security issues for {brand} next week",
                    "What problems might occur at store {store_id}?",
                    "Show predictive analysis for {brand}"
                ],
                CommandIntent.PATTERN_ANALYSIS: [
                    "Analyze security patterns for {brand}",
                    "What patterns do you see in recent events?",
                    "Show correlation analysis"
                ]
            }
            
            # Section-specific suggestions
            if current_section == 'investigation':
                suggestions.extend([
                    {
                        'command': "Investigate BWW store 155",
                        'description': "Run comprehensive security analysis",
                        'confidence': 0.9
                    },
                    {
                        'command': "Check all stores for security issues", 
                        'description': "Multi-store security assessment",
                        'confidence': 0.8
                    }
                ])
            elif current_section == 'fortianalyzer':
                suggestions.extend([
                    {
                        'command': "Search logs for SQL injection",
                        'description': "Advanced log analysis",
                        'confidence': 0.85
                    },
                    {
                        'command': "Show security events for last 24 hours",
                        'description': "Recent security overview",
                        'confidence': 0.8
                    }
                ])
            
            # Add popular commands from usage patterns
            popular_commands = self._get_popular_commands()
            for cmd in popular_commands[:3]:
                suggestions.append({
                    'command': cmd['example'],
                    'description': f"Popular {cmd['intent']} command",
                    'confidence': cmd['success_rate']
                })
            
            # Personalized suggestions based on user's command history
            if context and context.get('user_preferences'):
                personal_suggestions = self._get_personalized_suggestions(context['user_preferences'])
                suggestions.extend(personal_suggestions)
            
            return suggestions[:10]  # Top 10 suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating voice command suggestions: {e}")
            return []
    
    def analyze_voice_usage_patterns(self) -> List[VoiceInsight]:
        """
        Analyze voice usage patterns and provide insights
        
        Returns:
            List of voice usage insights
        """
        try:
            insights = []
            
            # Get voice interaction data from LTM
            voice_data = self.ltm_memory.get_voice_learning_insights()
            
            if not voice_data.get('success'):
                return insights
            
            # Command frequency analysis
            top_commands = voice_data.get('top_commands', [])
            if top_commands:
                freq_insight = VoiceInsight(
                    insight_type='command_frequency',
                    description=f"Most used command: '{top_commands[0]['command']}' ({top_commands[0]['frequency']} times)",
                    metrics={
                        'top_commands': top_commands[:5],
                        'total_interactions': voice_data.get('overall_statistics', {}).get('total_interactions', 0)
                    },
                    recommendations=self._generate_frequency_recommendations(top_commands),
                    confidence=0.9
                )
                insights.append(freq_insight)
            
            # Success rate analysis
            overall_success = voice_data.get('overall_statistics', {}).get('success_rate', 0)
            if overall_success < 0.8:
                success_insight = VoiceInsight(
                    insight_type='success_rate',
                    description=f"Voice command success rate: {overall_success:.1%}",
                    metrics={
                        'overall_success_rate': overall_success,
                        'failed_commands': [cmd for cmd in top_commands if cmd['success_rate'] < 0.7]
                    },
                    recommendations=[
                        "Review failed commands for pattern improvements",
                        "Consider adding command variations",
                        "Improve error handling for unclear commands"
                    ],
                    confidence=0.85
                )
                insights.append(success_insight)
            
            # Intent analysis
            intent_stats = voice_data.get('intent_analysis', [])
            if intent_stats:
                intent_insight = VoiceInsight(
                    insight_type='intent_distribution',
                    description=f"Most common intent: {intent_stats[0]['intent']}",
                    metrics={'intent_distribution': intent_stats},
                    recommendations=self._generate_intent_recommendations(intent_stats),
                    confidence=0.8
                )
                insights.append(intent_insight)
            
            # Response time analysis
            avg_response_time = voice_data.get('overall_statistics', {}).get('avg_response_time', 0)
            if avg_response_time and avg_response_time > 2.0:
                performance_insight = VoiceInsight(
                    insight_type='performance',
                    description=f"Average response time: {avg_response_time:.1f}s",
                    metrics={'avg_response_time': avg_response_time},
                    recommendations=[
                        "Optimize command processing pipeline",
                        "Cache frequently used responses",
                        "Consider command preprocessing"
                    ],
                    confidence=0.7
                )
                insights.append(performance_insight)
            
            # Pattern learning insights
            pattern_insight = self._analyze_pattern_learning()
            if pattern_insight:
                insights.append(pattern_insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing voice usage patterns: {e}")
            return []
    
    def get_command_suggestions_for_intent(self, intent: CommandIntent) -> List[str]:
        """Get command suggestions for a specific intent"""
        suggestions = []
        
        for pattern in self.command_patterns.values():
            if pattern.intent == intent and pattern.confidence >= self.min_pattern_confidence:
                suggestions.extend(pattern.examples[:2])  # Top 2 examples per pattern
        
        return suggestions[:5]  # Top 5 suggestions
    
    def improve_command_recognition(self, failed_commands: List[Dict[str, Any]]):
        """
        Improve command recognition based on failed commands
        
        Args:
            failed_commands: List of commands that failed recognition
        """
        try:
            for cmd_data in failed_commands:
                command_text = cmd_data.get('text', '')
                intended_intent = cmd_data.get('intended_intent')
                correct_entities = cmd_data.get('correct_entities', {})
                
                if intended_intent and command_text:
                    # Create or update pattern for this command
                    self._create_correction_pattern(command_text, intended_intent, correct_entities)
                    
                    # Update entity vocabularies
                    for entity_type, entity_value in correct_entities.items():
                        self.entity_vocabularies[entity_type].add(entity_value)
            
            self.logger.info(f"Improved recognition for {len(failed_commands)} failed commands")
            
        except Exception as e:
            self.logger.error(f"Error improving command recognition: {e}")
    
    def _initialize_base_patterns(self):
        """Initialize base command patterns"""
        base_patterns = [
            {
                'intent': CommandIntent.INVESTIGATION,
                'patterns': [
                    r'investigate\s+(\w+)\s+store\s+(\d+)',
                    r'check\s+security\s+(?:status\s+)?for\s+(\w+)(?:\s+store\s+(\d+))?',
                    r'analyze\s+(\w+)(?:\s+store\s+(\d+))?',
                    r'run\s+(?:security\s+)?(?:analysis|investigation)\s+for\s+(\w+)(?:\s+store\s+(\d+))?'
                ],
                'examples': [
                    "investigate BWW store 155",
                    "check security status for Arby's store 234",
                    "analyze Sonic store 789",
                    "run security analysis for BWW"
                ]
            },
            {
                'intent': CommandIntent.NAVIGATION,
                'patterns': [
                    r'(?:show|go\s+to|open|navigate\s+to)\s+(\w+)',
                    r'show\s+me\s+(?:the\s+)?(\w+)',
                    r'(?:display|view)\s+(\w+)'
                ],
                'examples': [
                    "show overview",
                    "go to fortianalyzer", 
                    "open web filters",
                    "navigate to investigation"
                ]
            },
            {
                'intent': CommandIntent.SECURITY_ANALYSIS,
                'patterns': [
                    r'(?:show|find|search\s+for)\s+.*(?:security|malware|threats?|incidents?)',
                    r'check\s+(?:threat\s+intelligence|security\s+events)',
                    r'(?:critical|high)\s+(?:security\s+)?(?:events?|alerts?)'
                ],
                'examples': [
                    "show critical security events",
                    "search for malware in BWW logs",
                    "check threat intelligence"
                ]
            },
            {
                'intent': CommandIntent.PREDICTION_REQUEST,
                'patterns': [
                    r'predict\s+.*(?:security|issues?|problems?)',
                    r'what\s+.*(?:might|could|will)\s+(?:happen|occur)',
                    r'(?:show|give\s+me)\s+(?:predictive\s+)?(?:analysis|forecast)'
                ],
                'examples': [
                    "predict security issues for BWW",
                    "what problems might occur next week",
                    "show predictive analysis"
                ]
            },
            {
                'intent': CommandIntent.PATTERN_ANALYSIS,
                'patterns': [
                    r'(?:analyze|show|find)\s+.*patterns?',
                    r'what\s+patterns?\s+do\s+you\s+see',
                    r'(?:show|find)\s+correlation'
                ],
                'examples': [
                    "analyze security patterns",
                    "what patterns do you see in recent events",
                    "show correlation analysis"
                ]
            }
        ]
        
        for pattern_group in base_patterns:
            intent = pattern_group['intent']
            
            for i, pattern_regex in enumerate(pattern_group['patterns']):
                pattern_id = f"{intent.value}_{i}"
                
                command_pattern = CommandPattern(
                    pattern_id=pattern_id,
                    pattern_regex=pattern_regex,
                    intent=intent,
                    entity_extractors={
                        'brand': r'\b(BWW|Arby\'?s|Sonic)\b',
                        'store_id': r'\b(\d{2,4})\b'
                    },
                    parameter_extractors={
                        'timeframe': r'\b(last\s+\w+|yesterday|today|\d+\s+(?:hours?|days?|weeks?))\b'
                    },
                    examples=pattern_group['examples'],
                    confidence=0.8,
                    usage_count=0,
                    success_rate=1.0,
                    last_used=datetime.now()
                )
                
                self.command_patterns[pattern_id] = command_pattern
    
    def _load_entity_vocabularies(self):
        """Load entity vocabularies for better extraction"""
        self.entity_vocabularies['brand'].update(['BWW', 'Buffalo Wild Wings', 'Arbys', "Arby's", 'Sonic', 'Sonic Drive-In'])
        self.entity_vocabularies['device_type'].update(['FortiGate', 'Switch', 'AP', 'Access Point', 'Router', 'Firewall'])
        self.entity_vocabularies['severity'].update(['low', 'medium', 'high', 'critical'])
        self.entity_vocabularies['event_type'].update(['security', 'performance', 'configuration', 'malware', 'intrusion'])
    
    def _normalize_text(self, text: str) -> str:
        """Normalize voice command text"""
        # Convert to lowercase
        text = text.lower()
        
        # Handle common voice recognition errors and variations
        replacements = {
            'buffalo wild wings': 'bww',
            'arby\'s': 'arbys',
            'sonic drive-in': 'sonic',
            'sonic drive in': 'sonic',
            'forty analyzer': 'fortianalyzer',
            'forte analyzer': 'fortianalyzer',
            'forte gate': 'fortigate',
            'forty gate': 'fortigate',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove filler words
        filler_words = ['um', 'uh', 'like', 'you know', 'actually', 'basically']
        words = text.split()
        words = [w for w in words if w not in filler_words]
        
        return ' '.join(words)
    
    def _extract_intent(self, text: str) -> Tuple[CommandIntent, float]:
        """Extract intent from normalized text"""
        best_intent = CommandIntent.HELP_REQUEST
        best_confidence = 0.0
        
        for pattern in self.command_patterns.values():
            match = re.search(pattern.pattern_regex, text, re.IGNORECASE)
            if match:
                confidence = pattern.confidence * (pattern.success_rate * 0.3 + 0.7)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = pattern.intent
        
        # Fallback intent detection based on keywords
        if best_confidence < 0.5:
            intent_keywords = {
                CommandIntent.INVESTIGATION: ['investigate', 'check', 'analyze', 'examine'],
                CommandIntent.NAVIGATION: ['show', 'go', 'open', 'navigate', 'display'],
                CommandIntent.SECURITY_ANALYSIS: ['security', 'malware', 'threat', 'attack'],
                CommandIntent.PREDICTION_REQUEST: ['predict', 'forecast', 'what will', 'might happen'],
                CommandIntent.PATTERN_ANALYSIS: ['pattern', 'correlation', 'trend']
            }
            
            for intent, keywords in intent_keywords.items():
                if any(keyword in text for keyword in keywords):
                    return intent, 0.6
        
        return best_intent, max(best_confidence, 0.3)
    
    def _extract_entities(self, text: str, intent: CommandIntent) -> Dict[str, str]:
        """Extract entities from text"""
        entities = {}
        
        # Brand extraction
        brand_match = re.search(r'\b(bww|buffalo\s+wild\s+wings|arbys|arby\'?s|sonic)\b', text, re.IGNORECASE)
        if brand_match:
            brand = brand_match.group(1).upper()
            if brand in ['BUFFALO WILD WINGS', 'BWW']:
                entities['brand'] = 'BWW'
            elif brand in ['ARBYS', "ARBY'S"]:
                entities['brand'] = 'ARBYS'
            elif brand == 'SONIC':
                entities['brand'] = 'SONIC'
        
        # Store ID extraction
        store_match = re.search(r'\bstore\s+(\d{2,4})\b|\b(\d{2,4})\b', text)
        if store_match:
            entities['store_id'] = store_match.group(1) or store_match.group(2)
        
        # Device name extraction
        device_match = re.search(r'\b(fortigate|fortinet|switch|ap|access\s+point|router|firewall)[-\s]*(\d+)?\b', text, re.IGNORECASE)
        if device_match:
            device_type = device_match.group(1).replace(' ', '')
            device_num = device_match.group(2) or '01'
            entities['device_name'] = f"{device_type}-{device_num}"
        
        # Severity extraction
        severity_match = re.search(r'\b(low|medium|high|critical)\b', text, re.IGNORECASE)
        if severity_match:
            entities['severity'] = severity_match.group(1).lower()
        
        return entities
    
    def _extract_parameters(self, text: str, intent: CommandIntent) -> Dict[str, Any]:
        """Extract parameters from text"""
        parameters = {}
        
        # Timeframe extraction
        timeframe_patterns = [
            (r'\blast\s+(\d+)\s+(hours?|days?|weeks?)\b', lambda m: f"{m.group(1)}{m.group(2)[0]}"),
            (r'\blast\s+(hour|day|week|month)\b', lambda m: f"1{m.group(1)[0]}"),
            (r'\b(yesterday|today)\b', lambda m: "1d" if m.group(1) == "yesterday" else "1h"),
            (r'\bin\s+the\s+last\s+(\d+)\s+(hours?|days?)\b', lambda m: f"{m.group(1)}{m.group(2)[0]}")
        ]
        
        for pattern, formatter in timeframe_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parameters['timeframe'] = formatter(match)
                break
        else:
            parameters['timeframe'] = '24h'  # Default
        
        # Analysis type extraction
        if intent == CommandIntent.SECURITY_ANALYSIS:
            if 'malware' in text:
                parameters['analysis_type'] = 'malware'
            elif 'intrusion' in text or 'attack' in text:
                parameters['analysis_type'] = 'intrusion'
            elif 'vulnerability' in text or 'vuln' in text:
                parameters['analysis_type'] = 'vulnerability'
            else:
                parameters['analysis_type'] = 'general'
        
        # Limit extraction
        limit_match = re.search(r'\b(?:top|first|show\s+me)\s+(\d+)\b', text, re.IGNORECASE)
        if limit_match:
            parameters['limit'] = int(limit_match.group(1))
        
        return parameters
    
    def _generate_command_id(self, text: str) -> str:
        """Generate unique command ID"""
        timestamp = datetime.now().isoformat()
        combined = f"{text}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def _create_fallback_command(self, raw_text: str) -> VoiceCommand:
        """Create fallback command for processing errors"""
        return VoiceCommand(
            command_id=self._generate_command_id(raw_text),
            raw_text=raw_text,
            normalized_text=raw_text.lower(),
            intent=CommandIntent.HELP_REQUEST,
            entities={},
            parameters={},
            confidence=0.1,
            timestamp=datetime.now(),
            success=False,
            response_time=0.0
        )
    
    def _update_patterns(self, command: VoiceCommand):
        """Update patterns based on command success/failure"""
        # Find matching patterns
        for pattern in self.command_patterns.values():
            if pattern.intent == command.intent:
                match = re.search(pattern.pattern_regex, command.normalized_text, re.IGNORECASE)
                if match:
                    # Update pattern statistics
                    pattern.usage_count += 1
                    pattern.last_used = command.timestamp
                    
                    # Update success rate
                    current_rate = pattern.success_rate
                    new_rate = (current_rate * (pattern.usage_count - 1) + (1 if command.success else 0)) / pattern.usage_count
                    pattern.success_rate = new_rate
                    
                    # Update confidence based on success rate
                    if pattern.usage_count >= self.min_usage_count:
                        pattern.confidence = min(pattern.success_rate * 0.9 + 0.1, 0.95)
                    
                    break
    
    def _learn_entities(self, command: VoiceCommand):
        """Learn new entities from successful commands"""
        if command.success:
            for entity_type, entity_value in command.entities.items():
                self.entity_vocabularies[entity_type].add(entity_value)
    
    def _adapt_language_patterns(self, command: VoiceCommand):
        """Adapt to user's language patterns"""
        if command.success and command.confidence > 0.8:
            # Create new pattern from successful command if it's different enough
            normalized_text = command.normalized_text
            
            # Check if this is a new way of expressing the intent
            existing_patterns = [p for p in self.command_patterns.values() if p.intent == command.intent]
            
            is_new_pattern = True
            for pattern in existing_patterns:
                if re.search(pattern.pattern_regex, normalized_text, re.IGNORECASE):
                    is_new_pattern = False
                    break
            
            if is_new_pattern:
                # Create new pattern based on this command
                new_pattern_id = f"learned_{command.intent.value}_{len(existing_patterns)}"
                
                # Generalize the command to create a pattern
                generalized_pattern = self._generalize_command_to_pattern(normalized_text, command.entities)
                
                if generalized_pattern:
                    new_pattern = CommandPattern(
                        pattern_id=new_pattern_id,
                        pattern_regex=generalized_pattern,
                        intent=command.intent,
                        entity_extractors={
                            'brand': r'\b(bww|arbys|sonic)\b',
                            'store_id': r'\b(\d{2,4})\b'
                        },
                        parameter_extractors={
                            'timeframe': r'\b(last\s+\w+|\d+\s+(?:hours?|days?))\b'
                        },
                        examples=[normalized_text],
                        confidence=0.7,
                        usage_count=1,
                        success_rate=1.0,
                        last_used=command.timestamp
                    )
                    
                    self.command_patterns[new_pattern_id] = new_pattern
                    self.logger.info(f"Learned new pattern: {generalized_pattern}")
    
    def _generalize_command_to_pattern(self, text: str, entities: Dict[str, str]) -> Optional[str]:
        """Convert specific command to generalized pattern"""
        pattern = text
        
        # Replace specific entities with regex patterns
        for entity_type, entity_value in entities.items():
            if entity_type == 'brand':
                pattern = pattern.replace(entity_value.lower(), r'(\w+)')
            elif entity_type == 'store_id':
                pattern = pattern.replace(entity_value, r'(\d+)')
        
        # Add word boundaries and make more flexible
        pattern = r'\b' + pattern.replace(' ', r'\s+') + r'\b'
        
        return pattern if pattern != text else None
    
    def _get_popular_commands(self) -> List[Dict[str, Any]]:
        """Get popular commands based on usage patterns"""
        popular = []
        
        for pattern in self.command_patterns.values():
            if pattern.usage_count >= self.min_usage_count:
                popular.append({
                    'intent': pattern.intent.value,
                    'example': pattern.examples[0] if pattern.examples else pattern.pattern_regex,
                    'usage_count': pattern.usage_count,
                    'success_rate': pattern.success_rate,
                    'confidence': pattern.confidence
                })
        
        return sorted(popular, key=lambda x: x['usage_count'] * x['success_rate'], reverse=True)
    
    def _get_personalized_suggestions(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized command suggestions"""
        suggestions = []
        
        # Based on user's most used brands
        preferred_brand = user_preferences.get('preferred_brand', 'BWW')
        
        suggestions.extend([
            {
                'command': f"investigate {preferred_brand} store 155",
                'description': f"Security analysis for your preferred brand: {preferred_brand}",
                'confidence': 0.8
            },
            {
                'command': f"predict security issues for {preferred_brand}",
                'description': f"Predictive analysis for {preferred_brand}",
                'confidence': 0.75
            }
        ])
        
        return suggestions
    
    def _generate_frequency_recommendations(self, top_commands: List[Dict]) -> List[str]:
        """Generate recommendations based on command frequency"""
        recommendations = []
        
        if top_commands:
            most_used = top_commands[0]
            if most_used['success_rate'] < 0.9:
                recommendations.append(f"Improve recognition for '{most_used['command']}' - currently {most_used['success_rate']:.1%} success rate")
        
        # Check for underused features
        all_intents = {p.intent for p in self.command_patterns.values()}
        used_intents = {cmd['command'] for cmd in top_commands}
        
        if len(used_intents) < len(all_intents):
            recommendations.append("Consider exploring voice commands for prediction and pattern analysis")
        
        return recommendations
    
    def _generate_intent_recommendations(self, intent_stats: List[Dict]) -> List[str]:
        """Generate recommendations based on intent usage"""
        recommendations = []
        
        if intent_stats:
            # Check for low success rates in specific intents
            for intent_data in intent_stats:
                if intent_data['success_rate'] < 0.7:
                    recommendations.append(f"Improve {intent_data['intent']} command recognition")
        
        return recommendations
    
    def _analyze_pattern_learning(self) -> Optional[VoiceInsight]:
        """Analyze pattern learning effectiveness"""
        try:
            learned_patterns = [p for p in self.command_patterns.values() if p.pattern_id.startswith('learned_')]
            total_patterns = len(self.command_patterns)
            
            if learned_patterns:
                avg_success_rate = sum(p.success_rate for p in learned_patterns) / len(learned_patterns)
                
                return VoiceInsight(
                    insight_type='pattern_learning',
                    description=f"System has learned {len(learned_patterns)} new command patterns",
                    metrics={
                        'learned_patterns': len(learned_patterns),
                        'total_patterns': total_patterns,
                        'avg_success_rate': avg_success_rate
                    },
                    recommendations=[
                        "Continue using voice commands to improve recognition",
                        "Try variations of commands to expand pattern learning"
                    ],
                    confidence=0.8
                )
        except Exception as e:
            self.logger.error(f"Error analyzing pattern learning: {e}")
        
        return None
    
    def _create_correction_pattern(self, command_text: str, intended_intent: str, correct_entities: Dict[str, str]):
        """Create correction pattern from failed command"""
        try:
            intent_enum = CommandIntent(intended_intent)
            pattern_id = f"correction_{intended_intent}_{len(self.command_patterns)}"
            
            # Create pattern from the command
            generalized_pattern = self._generalize_command_to_pattern(command_text, correct_entities)
            
            if generalized_pattern:
                correction_pattern = CommandPattern(
                    pattern_id=pattern_id,
                    pattern_regex=generalized_pattern,
                    intent=intent_enum,
                    entity_extractors={
                        'brand': r'\b(bww|arbys|sonic)\b',
                        'store_id': r'\b(\d{2,4})\b'
                    },
                    parameter_extractors={
                        'timeframe': r'\b(last\s+\w+|\d+\s+(?:hours?|days?))\b'
                    },
                    examples=[command_text],
                    confidence=0.6,  # Start with lower confidence for corrections
                    usage_count=1,
                    success_rate=1.0,  # Assume correction is right
                    last_used=datetime.now()
                )
                
                self.command_patterns[pattern_id] = correction_pattern
                self.logger.info(f"Created correction pattern for: {command_text}")
                
        except Exception as e:
            self.logger.error(f"Error creating correction pattern: {e}")

def create_voice_learning_engine(ltm_memory: LTMMemorySystem, config: Dict[str, Any] = None) -> VoiceLearningEngine:
    """Factory function to create VoiceLearningEngine"""
    return VoiceLearningEngine(ltm_memory, config)