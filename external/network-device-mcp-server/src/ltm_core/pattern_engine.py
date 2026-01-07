"""
Pattern Recognition Engine for Network Intelligence
Advanced pattern detection and analysis for network security events
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib
import logging
import re
from enum import Enum

from .ltm_memory import LTMMemorySystem, NetworkEvent, LearningPattern

class PatternType(Enum):
    """Types of patterns the engine can detect"""
    SECURITY_SEQUENCE = "security_sequence"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONFIGURATION_DRIFT = "configuration_drift"
    BRAND_CORRELATION = "brand_correlation"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    DEVICE_FAILURE = "device_failure"
    ATTACK_CAMPAIGN = "attack_campaign"
    POLICY_VIOLATION = "policy_violation"

@dataclass
class PatternMatch:
    """Represents a detected pattern match"""
    pattern_id: str
    pattern_type: PatternType
    confidence: float
    severity: str
    description: str
    affected_entities: List[str]  # stores, devices, brands
    time_window: Tuple[datetime, datetime]
    supporting_events: List[str]  # event IDs
    recommendations: List[str]
    metadata: Dict[str, Any]

@dataclass
class ThreatSignature:
    """Security threat signature for pattern matching"""
    signature_id: str
    name: str
    description: str
    indicators: List[str]  # IOCs, patterns, regexes
    severity: str
    attack_type: str
    mitigation_steps: List[str]

class PatternRecognitionEngine:
    """
    Advanced pattern recognition for network security events
    Detects complex multi-event patterns and attack campaigns
    """
    
    def __init__(self, ltm_memory: LTMMemorySystem, config: Dict[str, Any] = None):
        """
        Initialize Pattern Recognition Engine
        
        Args:
            ltm_memory: LTM memory system instance
            config: Configuration parameters
        """
        self.ltm_memory = ltm_memory
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Pattern detection thresholds
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.max_time_window = self.config.get('max_time_window_hours', 24)
        self.min_event_count = self.config.get('min_event_count', 3)
        
        # Load threat signatures
        self.threat_signatures = self._load_threat_signatures()
        
        # Pattern detection algorithms
        self.detectors = {
            PatternType.SECURITY_SEQUENCE: self._detect_security_sequence,
            PatternType.PERFORMANCE_DEGRADATION: self._detect_performance_degradation,
            PatternType.CONFIGURATION_DRIFT: self._detect_configuration_drift,
            PatternType.BRAND_CORRELATION: self._detect_brand_correlation,
            PatternType.TEMPORAL_ANOMALY: self._detect_temporal_anomaly,
            PatternType.DEVICE_FAILURE: self._detect_device_failure,
            PatternType.ATTACK_CAMPAIGN: self._detect_attack_campaign,
            PatternType.POLICY_VIOLATION: self._detect_policy_violation
        }
    
    def analyze_patterns(self, 
                        events: List[NetworkEvent] = None,
                        pattern_types: List[PatternType] = None,
                        time_window_hours: int = None) -> List[PatternMatch]:
        """
        Analyze events for patterns
        
        Args:
            events: Events to analyze (if None, fetches recent events)
            pattern_types: Types of patterns to detect
            time_window_hours: Time window for analysis
            
        Returns:
            List of detected patterns
        """
        try:
            # Get events to analyze
            if events is None:
                time_window = time_window_hours or self.max_time_window
                cutoff_time = datetime.now() - timedelta(hours=time_window)
                events = self._fetch_recent_events(cutoff_time)
            
            if not events:
                self.logger.warning("No events to analyze for patterns")
                return []
            
            # Determine pattern types to detect
            if pattern_types is None:
                pattern_types = list(PatternType)
            
            detected_patterns = []
            
            # Run each pattern detector
            for pattern_type in pattern_types:
                if pattern_type in self.detectors:
                    try:
                        patterns = self.detectors[pattern_type](events)
                        detected_patterns.extend(patterns)
                    except Exception as e:
                        self.logger.error(f"Error detecting {pattern_type}: {e}")
            
            # Sort patterns by confidence and severity
            detected_patterns.sort(key=lambda p: (self._severity_weight(p.severity), p.confidence), reverse=True)
            
            # Store detected patterns in LTM
            self._store_patterns(detected_patterns)
            
            self.logger.info(f"Detected {len(detected_patterns)} patterns from {len(events)} events")
            
            return detected_patterns
            
        except Exception as e:
            self.logger.error(f"Error in pattern analysis: {e}")
            return []
    
    def _detect_security_sequence(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect sequences of security events that indicate coordinated attacks"""
        patterns = []
        
        # Group events by store and time
        store_events = defaultdict(list)
        for event in events:
            if event.event_type == 'security_incident':
                store_events[f"{event.brand}_{event.store_id}"].append(event)
        
        # Look for event sequences in each store
        for store_key, store_event_list in store_events.items():
            if len(store_event_list) < self.min_event_count:
                continue
            
            # Sort events by timestamp
            store_event_list.sort(key=lambda e: e.timestamp)
            
            # Detect escalating severity patterns
            severity_sequence = [e.severity for e in store_event_list]
            if self._is_escalating_sequence(severity_sequence):
                
                time_span = store_event_list[-1].timestamp - store_event_list[0].timestamp
                if time_span.total_seconds() <= self.max_time_window * 3600:
                    
                    pattern = PatternMatch(
                        pattern_id=self._generate_pattern_id("security_sequence", store_key),
                        pattern_type=PatternType.SECURITY_SEQUENCE,
                        confidence=0.85,
                        severity="high",
                        description=f"Escalating security incident sequence detected at {store_key}",
                        affected_entities=[store_key],
                        time_window=(store_event_list[0].timestamp, store_event_list[-1].timestamp),
                        supporting_events=[e.event_id for e in store_event_list],
                        recommendations=[
                            "Immediate security assessment required",
                            "Review incident timeline for attack progression",
                            "Check for lateral movement indicators",
                            "Implement enhanced monitoring"
                        ],
                        metadata={
                            "sequence_length": len(store_event_list),
                            "time_span_minutes": time_span.total_seconds() / 60,
                            "severity_progression": severity_sequence
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_performance_degradation(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect performance degradation patterns"""
        patterns = []
        
        # Look for performance issues across brands
        perf_events = [e for e in events if e.event_type == 'performance_issue']
        
        # Group by brand and analyze trends
        brand_performance = defaultdict(list)
        for event in perf_events:
            brand_performance[event.brand].append(event)
        
        for brand, brand_events in brand_performance.items():
            if len(brand_events) < self.min_event_count:
                continue
            
            # Check for increasing frequency over time
            brand_events.sort(key=lambda e: e.timestamp)
            
            # Calculate event frequency in time windows
            time_windows = self._split_into_time_windows(brand_events, hours=4)
            frequencies = [len(window) for window in time_windows]
            
            # Detect increasing trend
            if self._is_increasing_trend(frequencies):
                pattern = PatternMatch(
                    pattern_id=self._generate_pattern_id("performance_degradation", brand),
                    pattern_type=PatternType.PERFORMANCE_DEGRADATION,
                    confidence=0.75,
                    severity="medium",
                    description=f"Performance degradation trend detected for {brand}",
                    affected_entities=[brand],
                    time_window=(brand_events[0].timestamp, brand_events[-1].timestamp),
                    supporting_events=[e.event_id for e in brand_events],
                    recommendations=[
                        f"Investigate {brand} network infrastructure",
                        "Check bandwidth utilization and device resources",
                        "Review recent configuration changes",
                        "Consider capacity planning assessment"
                    ],
                    metadata={
                        "event_count": len(brand_events),
                        "frequency_trend": frequencies,
                        "affected_stores": len(set(e.store_id for e in brand_events))
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_configuration_drift(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect configuration drift patterns"""
        patterns = []
        
        config_events = [e for e in events if e.event_type == 'configuration_change']
        
        # Group by device and analyze changes
        device_changes = defaultdict(list)
        for event in config_events:
            device_key = f"{event.brand}_{event.store_id}_{event.device_name}"
            device_changes[device_key].append(event)
        
        for device_key, changes in device_changes.items():
            if len(changes) >= 3:  # Multiple config changes
                
                # Check for rapid configuration changes (potential drift)
                changes.sort(key=lambda e: e.timestamp)
                time_span = changes[-1].timestamp - changes[0].timestamp
                
                if time_span.total_seconds() <= 7200:  # Within 2 hours
                    pattern = PatternMatch(
                        pattern_id=self._generate_pattern_id("config_drift", device_key),
                        pattern_type=PatternType.CONFIGURATION_DRIFT,
                        confidence=0.8,
                        severity="medium",
                        description=f"Configuration drift detected on {device_key}",
                        affected_entities=[device_key],
                        time_window=(changes[0].timestamp, changes[-1].timestamp),
                        supporting_events=[e.event_id for e in changes],
                        recommendations=[
                            "Review configuration change history",
                            "Validate current configuration against standards",
                            "Check for unauthorized changes",
                            "Implement configuration backup and rollback"
                        ],
                        metadata={
                            "change_count": len(changes),
                            "time_span_minutes": time_span.total_seconds() / 60
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_brand_correlation(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect correlated events across different brands"""
        patterns = []
        
        # Group events by type and time windows
        time_windows = self._create_time_windows(events, window_size_minutes=30)
        
        for window_start, window_events in time_windows.items():
            # Group by event type
            event_types = defaultdict(lambda: defaultdict(list))
            
            for event in window_events:
                event_types[event.event_type][event.brand].append(event)
            
            # Look for same event type across multiple brands
            for event_type, brand_events in event_types.items():
                if len(brand_events) >= 2:  # At least 2 brands affected
                    
                    total_events = sum(len(events) for events in brand_events.values())
                    if total_events >= self.min_event_count:
                        
                        affected_brands = list(brand_events.keys())
                        all_events = []
                        for brand_event_list in brand_events.values():
                            all_events.extend(brand_event_list)
                        
                        pattern = PatternMatch(
                            pattern_id=self._generate_pattern_id("brand_correlation", f"{event_type}_{window_start.isoformat()}"),
                            pattern_type=PatternType.BRAND_CORRELATION,
                            confidence=0.9,
                            severity="high" if event_type == 'security_incident' else "medium",
                            description=f"Correlated {event_type} events across brands: {', '.join(affected_brands)}",
                            affected_entities=affected_brands,
                            time_window=(window_start, window_start + timedelta(minutes=30)),
                            supporting_events=[e.event_id for e in all_events],
                            recommendations=[
                                "Investigate potential coordinated attack or system-wide issue",
                                f"Review {event_type} patterns across all brands",
                                "Check for common infrastructure or vendors",
                                "Implement cross-brand monitoring alerts"
                            ],
                            metadata={
                                "brands_affected": len(affected_brands),
                                "total_events": total_events,
                                "event_type": event_type
                            }
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_anomaly(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect temporal anomalies in event patterns"""
        patterns = []
        
        if len(events) < 10:  # Need sufficient data
            return patterns
        
        # Analyze events by hour of day
        hourly_counts = defaultdict(int)
        for event in events:
            hour = event.timestamp.hour
            hourly_counts[hour] += 1
        
        # Calculate baseline (average events per hour)
        if hourly_counts:
            baseline = sum(hourly_counts.values()) / len(hourly_counts)
            
            # Find hours with significantly higher activity
            anomalous_hours = []
            for hour, count in hourly_counts.items():
                if count > baseline * 3:  # 3x threshold
                    anomalous_hours.append((hour, count))
            
            if anomalous_hours:
                # Get events from anomalous hours
                anomaly_events = []
                for event in events:
                    if any(event.timestamp.hour == hour for hour, _ in anomalous_hours):
                        anomaly_events.append(event)
                
                if anomaly_events:
                    pattern = PatternMatch(
                        pattern_id=self._generate_pattern_id("temporal_anomaly", f"hours_{len(anomalous_hours)}"),
                        pattern_type=PatternType.TEMPORAL_ANOMALY,
                        confidence=0.8,
                        severity="medium",
                        description=f"Temporal anomaly detected: unusually high activity during {len(anomalous_hours)} hour(s)",
                        affected_entities=list(set(f"{e.brand}_{e.store_id}" for e in anomaly_events)),
                        time_window=(min(e.timestamp for e in anomaly_events), 
                                   max(e.timestamp for e in anomaly_events)),
                        supporting_events=[e.event_id for e in anomaly_events],
                        recommendations=[
                            "Investigate cause of increased activity",
                            "Check for scheduled maintenance or updates",
                            "Review user activity patterns",
                            "Consider implementing time-based monitoring"
                        ],
                        metadata={
                            "anomalous_hours": dict(anomalous_hours),
                            "baseline_events_per_hour": baseline,
                            "total_anomaly_events": len(anomaly_events)
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_device_failure(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect device failure patterns"""
        patterns = []
        
        # Look for multiple events from the same device
        device_events = defaultdict(list)
        for event in events:
            device_key = f"{event.brand}_{event.store_id}_{event.device_name}"
            device_events[device_key].append(event)
        
        for device_key, device_event_list in device_events.items():
            if len(device_event_list) >= 5:  # Multiple issues from same device
                
                # Check for increasing severity or frequency
                device_event_list.sort(key=lambda e: e.timestamp)
                
                # Look for pattern suggesting device failure
                critical_events = [e for e in device_event_list if e.severity in ['critical', 'high']]
                
                if len(critical_events) >= 2:
                    pattern = PatternMatch(
                        pattern_id=self._generate_pattern_id("device_failure", device_key),
                        pattern_type=PatternType.DEVICE_FAILURE,
                        confidence=0.85,
                        severity="high",
                        description=f"Potential device failure pattern detected: {device_key}",
                        affected_entities=[device_key],
                        time_window=(device_event_list[0].timestamp, device_event_list[-1].timestamp),
                        supporting_events=[e.event_id for e in device_event_list],
                        recommendations=[
                            f"Immediate inspection of {device_key} required",
                            "Check device health and resource utilization",
                            "Prepare replacement device if necessary",
                            "Review device maintenance schedule"
                        ],
                        metadata={
                            "total_events": len(device_event_list),
                            "critical_events": len(critical_events),
                            "event_types": list(set(e.event_type for e in device_event_list))
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_attack_campaign(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect coordinated attack campaigns"""
        patterns = []
        
        security_events = [e for e in events if e.event_type == 'security_incident']
        
        # Match against threat signatures
        for signature in self.threat_signatures:
            matching_events = []
            
            for event in security_events:
                # Check if event matches signature indicators
                for indicator in signature.indicators:
                    if self._matches_indicator(event, indicator):
                        matching_events.append(event)
                        break
            
            if len(matching_events) >= 2:  # Multiple matches for signature
                pattern = PatternMatch(
                    pattern_id=self._generate_pattern_id("attack_campaign", signature.signature_id),
                    pattern_type=PatternType.ATTACK_CAMPAIGN,
                    confidence=0.9,
                    severity=signature.severity,
                    description=f"Attack campaign detected: {signature.name}",
                    affected_entities=list(set(f"{e.brand}_{e.store_id}" for e in matching_events)),
                    time_window=(min(e.timestamp for e in matching_events),
                               max(e.timestamp for e in matching_events)),
                    supporting_events=[e.event_id for e in matching_events],
                    recommendations=signature.mitigation_steps,
                    metadata={
                        "signature_id": signature.signature_id,
                        "attack_type": signature.attack_type,
                        "matching_indicators": len([i for i in signature.indicators 
                                                  if any(self._matches_indicator(e, i) for e in matching_events)])
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_policy_violation(self, events: List[NetworkEvent]) -> List[PatternMatch]:
        """Detect policy violation patterns"""
        patterns = []
        
        # Look for repeated violations of the same type
        violation_patterns = defaultdict(list)
        
        for event in events:
            # Check if event indicates a policy violation
            if any(keyword in event.description.lower() for keyword in 
                   ['blocked', 'denied', 'violation', 'policy', 'unauthorized']):
                
                # Create violation signature
                violation_key = f"{event.brand}_{event.event_type}"
                violation_patterns[violation_key].append(event)
        
        for violation_key, violation_events in violation_patterns.items():
            if len(violation_events) >= 5:  # Repeated violations
                
                pattern = PatternMatch(
                    pattern_id=self._generate_pattern_id("policy_violation", violation_key),
                    pattern_type=PatternType.POLICY_VIOLATION,
                    confidence=0.7,
                    severity="medium",
                    description=f"Repeated policy violations detected: {violation_key}",
                    affected_entities=list(set(f"{e.brand}_{e.store_id}" for e in violation_events)),
                    time_window=(min(e.timestamp for e in violation_events),
                               max(e.timestamp for e in violation_events)),
                    supporting_events=[e.event_id for e in violation_events],
                    recommendations=[
                        "Review and update security policies",
                        "Investigate source of violations",
                        "Consider user training or policy clarification",
                        "Implement preventive controls"
                    ],
                    metadata={
                        "violation_count": len(violation_events),
                        "affected_stores": len(set(e.store_id for e in violation_events))
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _fetch_recent_events(self, cutoff_time: datetime) -> List[NetworkEvent]:
        """Fetch recent events from LTM memory"""
        try:
            # Use the search functionality to get recent events
            events = self.ltm_memory.search_similar_events(limit=1000)  # Get recent events
            
            # Filter by time
            recent_events = []
            for event in events:
                if event.timestamp >= cutoff_time:
                    recent_events.append(event)
            
            return recent_events
            
        except Exception as e:
            self.logger.error(f"Error fetching recent events: {e}")
            return []
    
    def _load_threat_signatures(self) -> List[ThreatSignature]:
        """Load threat signatures for attack detection"""
        return [
            ThreatSignature(
                signature_id="sql_injection_campaign",
                name="SQL Injection Campaign",
                description="Coordinated SQL injection attacks",
                indicators=["sql injection", "union select", "drop table", "'or'1'='1"],
                severity="critical",
                attack_type="web_application",
                mitigation_steps=[
                    "Block source IPs immediately",
                    "Update WAF rules",
                    "Patch vulnerable applications",
                    "Review database security"
                ]
            ),
            ThreatSignature(
                signature_id="malware_campaign",
                name="Malware Distribution Campaign",
                description="Coordinated malware distribution",
                indicators=["malware", "trojan", "virus", "ransomware"],
                severity="critical",
                attack_type="malware",
                mitigation_steps=[
                    "Isolate infected systems",
                    "Update antivirus signatures",
                    "Block malicious domains",
                    "Implement endpoint protection"
                ]
            ),
            ThreatSignature(
                signature_id="brute_force_campaign",
                name="Brute Force Attack Campaign",
                description="Coordinated credential brute forcing",
                indicators=["brute force", "failed login", "authentication failure"],
                severity="high",
                attack_type="credential_attack",
                mitigation_steps=[
                    "Implement account lockout policies",
                    "Enable MFA",
                    "Block attacking IPs",
                    "Monitor authentication logs"
                ]
            )
        ]
    
    def _generate_pattern_id(self, pattern_type: str, identifier: str) -> str:
        """Generate unique pattern ID"""
        combined = f"{pattern_type}_{identifier}_{datetime.now().isoformat()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _is_escalating_sequence(self, severity_sequence: List[str]) -> bool:
        """Check if severity sequence is escalating"""
        severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        weights = [severity_weights.get(s, 1) for s in severity_sequence]
        
        # Check for generally increasing trend
        increasing_count = 0
        for i in range(1, len(weights)):
            if weights[i] >= weights[i-1]:
                increasing_count += 1
        
        return increasing_count / (len(weights) - 1) > 0.7 if len(weights) > 1 else False
    
    def _split_into_time_windows(self, events: List[NetworkEvent], hours: int) -> List[List[NetworkEvent]]:
        """Split events into time windows"""
        if not events:
            return []
        
        events.sort(key=lambda e: e.timestamp)
        windows = []
        current_window = []
        window_start = events[0].timestamp
        
        for event in events:
            if event.timestamp - window_start <= timedelta(hours=hours):
                current_window.append(event)
            else:
                if current_window:
                    windows.append(current_window)
                current_window = [event]
                window_start = event.timestamp
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _is_increasing_trend(self, values: List[int]) -> bool:
        """Check if values show increasing trend"""
        if len(values) < 3:
            return False
        
        # Simple trend analysis
        increasing_pairs = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increasing_pairs += 1
        
        return increasing_pairs / (len(values) - 1) > 0.6
    
    def _create_time_windows(self, events: List[NetworkEvent], window_size_minutes: int) -> Dict[datetime, List[NetworkEvent]]:
        """Create time windows for event analysis"""
        windows = defaultdict(list)
        
        for event in events:
            # Round timestamp to window boundary
            window_start = event.timestamp.replace(
                minute=(event.timestamp.minute // window_size_minutes) * window_size_minutes,
                second=0,
                microsecond=0
            )
            windows[window_start].append(event)
        
        return windows
    
    def _matches_indicator(self, event: NetworkEvent, indicator: str) -> bool:
        """Check if event matches threat indicator"""
        search_text = f"{event.description} {' '.join(event.tags)}".lower()
        return indicator.lower() in search_text
    
    def _severity_weight(self, severity: str) -> int:
        """Get numeric weight for severity"""
        weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return weights.get(severity.lower(), 1)
    
    def _store_patterns(self, patterns: List[PatternMatch]):
        """Store detected patterns in LTM memory"""
        for pattern in patterns:
            try:
                # Convert pattern to learning pattern format
                learning_pattern = LearningPattern(
                    pattern_id=pattern.pattern_id,
                    pattern_type=pattern.pattern_type.value,
                    confidence=pattern.confidence,
                    frequency=1,  # New pattern
                    last_seen=datetime.now(),
                    conditions={
                        "pattern_type": pattern.pattern_type.value,
                        "affected_entities": pattern.affected_entities,
                        "time_window": [pattern.time_window[0].isoformat(), pattern.time_window[1].isoformat()]
                    },
                    outcomes={
                        "severity": pattern.severity,
                        "description": pattern.description,
                        "supporting_events_count": len(pattern.supporting_events)
                    },
                    recommendations=pattern.recommendations
                )
                
                # Store in LTM (would need to add this method to LTMMemorySystem)
                # For now, we'll log the pattern detection
                self.logger.info(f"Pattern detected: {pattern.description} (confidence: {pattern.confidence})")
                
            except Exception as e:
                self.logger.error(f"Error storing pattern {pattern.pattern_id}: {e}")

def create_pattern_engine(ltm_memory: LTMMemorySystem, config: Dict[str, Any] = None) -> PatternRecognitionEngine:
    """Factory function to create PatternRecognitionEngine"""
    return PatternRecognitionEngine(ltm_memory, config)