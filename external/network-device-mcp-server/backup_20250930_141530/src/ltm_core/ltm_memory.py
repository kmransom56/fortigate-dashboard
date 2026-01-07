"""
Long-Term Memory System for Network Intelligence
Stores, learns from, and retrieves network management patterns and insights
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class NetworkEvent:
    """Represents a network event for learning"""
    event_id: str
    timestamp: datetime
    event_type: str  # security_incident, performance_issue, configuration_change
    brand: str  # BWW, ARBYS, SONIC
    store_id: str
    device_name: str
    severity: str  # critical, high, medium, low
    description: str
    resolution: Optional[str] = None
    resolution_time: Optional[int] = None  # minutes
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LearningPattern:
    """Represents a learned pattern from network events"""
    pattern_id: str
    pattern_type: str
    confidence: float  # 0.0 to 1.0
    frequency: int
    last_seen: datetime
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    recommendations: List[str]

class LTMMemorySystem:
    """
    Long-Term Memory system for network operations
    Learns from historical data and provides intelligent insights
    """
    
    def __init__(self, db_path: str = None, config: Dict[str, Any] = None):
        """
        Initialize LTM Memory System
        
        Args:
            db_path: Path to SQLite database file
            config: Configuration dictionary
        """
        self.config = config or {}
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'ltm_memory.db'
        )
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Learning parameters
        self.pattern_confidence_threshold = self.config.get('pattern_confidence_threshold', 0.7)
        self.min_pattern_frequency = self.config.get('min_pattern_frequency', 3)
        self.max_memory_age_days = self.config.get('max_memory_age_days', 365)
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Network events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    store_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    resolution TEXT,
                    resolution_time INTEGER,
                    tags TEXT,  -- JSON array
                    metadata TEXT  -- JSON object
                )
            ''')
            
            # Learning patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    frequency INTEGER NOT NULL,
                    last_seen TEXT NOT NULL,
                    conditions TEXT NOT NULL,  -- JSON object
                    outcomes TEXT NOT NULL,    -- JSON object  
                    recommendations TEXT NOT NULL,  -- JSON array
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Voice interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_interactions (
                    interaction_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    command TEXT NOT NULL,
                    intent TEXT,
                    success BOOLEAN NOT NULL,
                    response_time REAL,
                    user_feedback TEXT,
                    context TEXT  -- JSON object
                )
            ''')
            
            # Performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    brand TEXT,
                    store_id TEXT,
                    device_name TEXT,
                    metric_value REAL NOT NULL,
                    threshold_value REAL,
                    status TEXT,
                    metadata TEXT  -- JSON object
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON network_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_brand_store ON network_events(brand, store_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON network_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON learning_patterns(pattern_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_timestamp ON voice_interactions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)')
            
            conn.commit()
    
    def record_event(self, event: NetworkEvent) -> bool:
        """
        Record a network event for learning
        
        Args:
            event: NetworkEvent to record
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO network_events 
                    (event_id, timestamp, event_type, brand, store_id, device_name, 
                     severity, description, resolution, resolution_time, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.brand,
                    event.store_id,
                    event.device_name,
                    event.severity,
                    event.description,
                    event.resolution,
                    event.resolution_time,
                    json.dumps(event.tags),
                    json.dumps(event.metadata)
                ))
                conn.commit()
                
                # Update learning patterns
                self._update_patterns(event)
                
                self.logger.info(f"Recorded network event: {event.event_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error recording event: {e}")
            return False
    
    def search_similar_events(self, 
                            event_type: str = None,
                            brand: str = None,
                            severity: str = None,
                            description_keywords: List[str] = None,
                            limit: int = 10) -> List[NetworkEvent]:
        """
        Search for similar historical events
        
        Args:
            event_type: Type of event to search for
            brand: Brand filter
            severity: Severity filter
            description_keywords: Keywords to search in description
            limit: Maximum number of results
            
        Returns:
            List of similar NetworkEvent objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic query
                conditions = []
                params = []
                
                if event_type:
                    conditions.append('event_type = ?')
                    params.append(event_type)
                
                if brand:
                    conditions.append('brand = ?')
                    params.append(brand)
                
                if severity:
                    conditions.append('severity = ?')
                    params.append(severity)
                
                if description_keywords:
                    keyword_conditions = []
                    for keyword in description_keywords:
                        keyword_conditions.append('description LIKE ?')
                        params.append(f'%{keyword}%')
                    if keyword_conditions:
                        conditions.append(f"({' OR '.join(keyword_conditions)})")
                
                where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
                
                query = f'''
                    SELECT * FROM network_events 
                    {where_clause}
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = NetworkEvent(
                        event_id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        event_type=row[2],
                        brand=row[3],
                        store_id=row[4],
                        device_name=row[5],
                        severity=row[6],
                        description=row[7],
                        resolution=row[8],
                        resolution_time=row[9],
                        tags=json.loads(row[10]) if row[10] else [],
                        metadata=json.loads(row[11]) if row[11] else {}
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            self.logger.error(f"Error searching events: {e}")
            return []
    
    def get_learned_patterns(self, pattern_type: str = None, min_confidence: float = None) -> List[LearningPattern]:
        """
        Retrieve learned patterns from memory
        
        Args:
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of LearningPattern objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                conditions = []
                params = []
                
                if pattern_type:
                    conditions.append('pattern_type = ?')
                    params.append(pattern_type)
                
                if min_confidence is not None:
                    conditions.append('confidence >= ?')
                    params.append(min_confidence)
                
                where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
                
                query = f'''
                    SELECT * FROM learning_patterns 
                    {where_clause}
                    ORDER BY confidence DESC, frequency DESC
                '''
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                patterns = []
                for row in rows:
                    pattern = LearningPattern(
                        pattern_id=row[0],
                        pattern_type=row[1],
                        confidence=row[2],
                        frequency=row[3],
                        last_seen=datetime.fromisoformat(row[4]),
                        conditions=json.loads(row[5]),
                        outcomes=json.loads(row[6]),
                        recommendations=json.loads(row[7])
                    )
                    patterns.append(pattern)
                
                return patterns
                
        except Exception as e:
            self.logger.error(f"Error retrieving patterns: {e}")
            return []
    
    def predict_similar_incidents(self, 
                                 brand: str, 
                                 store_id: str = None, 
                                 event_type: str = None,
                                 lookback_days: int = 30) -> Dict[str, Any]:
        """
        Predict potential similar incidents based on patterns
        
        Args:
            brand: Brand to analyze
            store_id: Optional specific store
            event_type: Optional event type filter
            lookback_days: Days to look back for pattern analysis
            
        Returns:
            Prediction results with confidence scores
        """
        try:
            # Get recent events for pattern matching
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                conditions = ['timestamp >= ?', 'brand = ?']
                params = [cutoff_date.isoformat(), brand]
                
                if store_id:
                    conditions.append('store_id = ?')
                    params.append(store_id)
                
                if event_type:
                    conditions.append('event_type = ?')
                    params.append(event_type)
                
                query = f'''
                    SELECT event_type, severity, COUNT(*) as frequency,
                           AVG(resolution_time) as avg_resolution_time
                    FROM network_events
                    WHERE {' AND '.join(conditions)}
                    GROUP BY event_type, severity
                    ORDER BY frequency DESC
                '''
                
                cursor.execute(query, params)
                pattern_data = cursor.fetchall()
                
                predictions = []
                total_events = sum(row[2] for row in pattern_data)
                
                for row in pattern_data:
                    event_type, severity, frequency, avg_resolution_time = row
                    probability = frequency / total_events if total_events > 0 else 0
                    
                    # Get learned patterns for this event type
                    learned_patterns = self.get_learned_patterns(
                        pattern_type=f"{event_type}_{severity}",
                        min_confidence=0.5
                    )
                    
                    prediction = {
                        'event_type': event_type,
                        'severity': severity,
                        'probability': probability,
                        'frequency': frequency,
                        'avg_resolution_time': avg_resolution_time,
                        'confidence': min(probability * 2, 1.0),  # Scale confidence
                        'learned_patterns': len(learned_patterns),
                        'recommendations': []
                    }
                    
                    # Add recommendations from learned patterns
                    for pattern in learned_patterns:
                        prediction['recommendations'].extend(pattern.recommendations)
                    
                    # Remove duplicates
                    prediction['recommendations'] = list(set(prediction['recommendations']))
                    
                    predictions.append(prediction)
                
                return {
                    'success': True,
                    'brand': brand,
                    'store_id': store_id,
                    'analysis_period': f'last {lookback_days} days',
                    'predictions': predictions[:5],  # Top 5 predictions
                    'total_events_analyzed': total_events,
                    'prediction_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def record_voice_interaction(self, 
                               command: str,
                               intent: str = None,
                               success: bool = True,
                               response_time: float = None,
                               user_feedback: str = None,
                               context: Dict[str, Any] = None) -> str:
        """
        Record a voice interaction for learning voice patterns
        
        Args:
            command: Voice command given
            intent: Detected intent
            success: Whether command was successful
            response_time: Time taken to process command
            user_feedback: Optional user feedback
            context: Additional context information
            
        Returns:
            Interaction ID
        """
        try:
            interaction_id = hashlib.md5(
                f"{datetime.now().isoformat()}_{command}".encode()
            ).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO voice_interactions
                    (interaction_id, timestamp, command, intent, success, 
                     response_time, user_feedback, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction_id,
                    datetime.now().isoformat(),
                    command,
                    intent,
                    success,
                    response_time,
                    user_feedback,
                    json.dumps(context or {})
                ))
                conn.commit()
                
            return interaction_id
            
        except Exception as e:
            self.logger.error(f"Error recording voice interaction: {e}")
            return ""
    
    def get_voice_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights from voice interaction patterns
        
        Returns:
            Voice learning insights and recommendations
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Most common commands
                cursor.execute('''
                    SELECT command, COUNT(*) as frequency, 
                           AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
                           AVG(response_time) as avg_response_time
                    FROM voice_interactions
                    WHERE timestamp >= date('now', '-30 days')
                    GROUP BY command
                    ORDER BY frequency DESC
                    LIMIT 10
                ''')
                
                command_stats = []
                for row in cursor.fetchall():
                    command_stats.append({
                        'command': row[0],
                        'frequency': row[1],
                        'success_rate': row[2],
                        'avg_response_time': row[3]
                    })
                
                # Intent analysis
                cursor.execute('''
                    SELECT intent, COUNT(*) as frequency,
                           AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
                    FROM voice_interactions
                    WHERE intent IS NOT NULL AND timestamp >= date('now', '-30 days')
                    GROUP BY intent
                    ORDER BY frequency DESC
                ''')
                
                intent_stats = []
                for row in cursor.fetchall():
                    intent_stats.append({
                        'intent': row[0],
                        'frequency': row[1],
                        'success_rate': row[2]
                    })
                
                # Overall statistics
                cursor.execute('''
                    SELECT COUNT(*) as total_interactions,
                           AVG(CASE WHEN success THEN 1 ELSE 0 END) as overall_success_rate,
                           AVG(response_time) as avg_response_time
                    FROM voice_interactions
                    WHERE timestamp >= date('now', '-30 days')
                ''')
                
                overall_stats = cursor.fetchone()
                
                return {
                    'success': True,
                    'period': 'last 30 days',
                    'overall_statistics': {
                        'total_interactions': overall_stats[0],
                        'success_rate': overall_stats[1],
                        'avg_response_time': overall_stats[2]
                    },
                    'top_commands': command_stats,
                    'intent_analysis': intent_stats,
                    'recommendations': self._generate_voice_recommendations(command_stats, intent_stats),
                    'analysis_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting voice insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_patterns(self, event: NetworkEvent):
        """Update learning patterns based on new event"""
        try:
            # Create pattern signature
            pattern_signature = f"{event.event_type}_{event.severity}_{event.brand}"
            pattern_id = hashlib.md5(pattern_signature.encode()).hexdigest()
            
            conditions = {
                'event_type': event.event_type,
                'severity': event.severity,
                'brand': event.brand
            }
            
            outcomes = {
                'resolution_provided': event.resolution is not None,
                'resolution_time': event.resolution_time
            }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if pattern exists
                cursor.execute(
                    'SELECT frequency, confidence FROM learning_patterns WHERE pattern_id = ?',
                    (pattern_id,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing pattern
                    frequency = existing[0] + 1
                    confidence = min(existing[1] + 0.1, 1.0)
                    
                    cursor.execute('''
                        UPDATE learning_patterns 
                        SET frequency = ?, confidence = ?, last_seen = ?, updated_at = ?
                        WHERE pattern_id = ?
                    ''', (frequency, confidence, event.timestamp.isoformat(), 
                          datetime.now().isoformat(), pattern_id))
                else:
                    # Create new pattern
                    recommendations = self._generate_pattern_recommendations(event)
                    
                    cursor.execute('''
                        INSERT INTO learning_patterns
                        (pattern_id, pattern_type, confidence, frequency, last_seen,
                         conditions, outcomes, recommendations, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern_id,
                        pattern_signature,
                        0.3,  # Initial confidence
                        1,    # Initial frequency
                        event.timestamp.isoformat(),
                        json.dumps(conditions),
                        json.dumps(outcomes),
                        json.dumps(recommendations),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating patterns: {e}")
    
    def _generate_pattern_recommendations(self, event: NetworkEvent) -> List[str]:
        """Generate recommendations based on event patterns"""
        recommendations = []
        
        if event.event_type == 'security_incident':
            if event.severity in ['critical', 'high']:
                recommendations.append('Immediate security assessment recommended')
                recommendations.append('Review firewall rules and IPS signatures')
            recommendations.append('Monitor similar events across brand locations')
            
        elif event.event_type == 'performance_issue':
            recommendations.append('Check network bandwidth utilization')
            recommendations.append('Review device resource usage')
            
        elif event.event_type == 'configuration_change':
            recommendations.append('Validate configuration against brand standards')
            recommendations.append('Document change for audit trail')
        
        return recommendations
    
    def _generate_voice_recommendations(self, command_stats: List[Dict], intent_stats: List[Dict]) -> List[str]:
        """Generate recommendations for voice interface improvements"""
        recommendations = []
        
        # Check for low success rate commands
        for cmd in command_stats:
            if cmd['success_rate'] < 0.8:
                recommendations.append(f"Improve recognition for '{cmd['command']}' command")
        
        # Check for slow response times
        for cmd in command_stats:
            if cmd['avg_response_time'] and cmd['avg_response_time'] > 2.0:
                recommendations.append(f"Optimize response time for '{cmd['command']}' command")
        
        # Check for popular intents that could be enhanced
        if intent_stats:
            top_intent = intent_stats[0]
            recommendations.append(f"Consider adding more variations for '{top_intent['intent']}' intent")
        
        return recommendations
    
    def cleanup_old_data(self, max_age_days: int = None) -> int:
        """
        Clean up old data beyond retention period
        
        Args:
            max_age_days: Maximum age of data to keep
            
        Returns:
            Number of records cleaned up
        """
        max_age = max_age_days or self.max_memory_age_days
        cutoff_date = datetime.now() - timedelta(days=max_age)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean old events
                cursor.execute('DELETE FROM network_events WHERE timestamp < ?', 
                             (cutoff_date.isoformat(),))
                events_deleted = cursor.rowcount
                
                # Clean old voice interactions  
                cursor.execute('DELETE FROM voice_interactions WHERE timestamp < ?',
                             (cutoff_date.isoformat(),))
                voice_deleted = cursor.rowcount
                
                # Clean old metrics
                cursor.execute('DELETE FROM performance_metrics WHERE timestamp < ?',
                             (cutoff_date.isoformat(),))
                metrics_deleted = cursor.rowcount
                
                conn.commit()
                
                total_deleted = events_deleted + voice_deleted + metrics_deleted
                self.logger.info(f"Cleaned up {total_deleted} old records")
                
                return total_deleted
                
        except Exception as e:
            self.logger.error(f"Error cleaning up data: {e}")
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Events stats
                cursor.execute('SELECT COUNT(*) FROM network_events')
                stats['total_events'] = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT event_type, COUNT(*) 
                    FROM network_events 
                    GROUP BY event_type
                ''')
                stats['events_by_type'] = dict(cursor.fetchall())
                
                # Patterns stats
                cursor.execute('SELECT COUNT(*) FROM learning_patterns')
                stats['total_patterns'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(confidence) FROM learning_patterns')
                avg_confidence = cursor.fetchone()[0]
                stats['avg_pattern_confidence'] = avg_confidence or 0.0
                
                # Voice interactions stats
                cursor.execute('SELECT COUNT(*) FROM voice_interactions')
                stats['total_voice_interactions'] = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT AVG(CASE WHEN success THEN 1 ELSE 0 END) 
                    FROM voice_interactions
                ''')
                voice_success = cursor.fetchone()[0]
                stats['voice_success_rate'] = voice_success or 0.0
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return {}

def create_network_event(event_type: str, brand: str, store_id: str, device_name: str,
                        severity: str, description: str, resolution: str = None,
                        resolution_time: int = None, tags: List[str] = None,
                        metadata: Dict[str, Any] = None) -> NetworkEvent:
    """Helper function to create a NetworkEvent"""
    event_id = hashlib.md5(
        f"{datetime.now().isoformat()}_{brand}_{store_id}_{event_type}".encode()
    ).hexdigest()
    
    return NetworkEvent(
        event_id=event_id,
        timestamp=datetime.now(),
        event_type=event_type,
        brand=brand,
        store_id=store_id,
        device_name=device_name,
        severity=severity,
        description=description,
        resolution=resolution,
        resolution_time=resolution_time,
        tags=tags or [],
        metadata=metadata or {}
    )