"""
Predictive Analytics Engine for Network Intelligence
Advanced predictive modeling for network security and performance
"""

import numpy as np
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
import math
from enum import Enum
import statistics

from .ltm_memory import LTMMemorySystem, NetworkEvent
from .pattern_engine import PatternRecognitionEngine, PatternMatch, PatternType

class PredictionType(Enum):
    """Types of predictions the engine can make"""
    SECURITY_INCIDENT = "security_incident"
    PERFORMANCE_ISSUE = "performance_issue"
    DEVICE_FAILURE = "device_failure"
    CAPACITY_OVERFLOW = "capacity_overflow"
    COMPLIANCE_VIOLATION = "compliance_violation"
    MAINTENANCE_REQUIRED = "maintenance_required"

@dataclass
class Prediction:
    """Represents a predictive analytics result"""
    prediction_id: str
    prediction_type: PredictionType
    confidence: float  # 0.0 to 1.0
    probability: float  # 0.0 to 1.0
    severity: str
    affected_entity: str  # store, device, brand
    predicted_time_window: Tuple[datetime, datetime]
    description: str
    reasoning: List[str]  # Why this prediction was made
    recommendations: List[str]
    historical_precedent: List[str]  # Similar past events
    risk_factors: Dict[str, float]
    mitigation_actions: List[str]
    business_impact: str
    metadata: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Analysis of historical trends"""
    entity: str
    metric: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0.0 to 1.0
    current_value: float
    predicted_value: float
    confidence_interval: Tuple[float, float]
    time_horizon_days: int

class PredictiveAnalyticsEngine:
    """
    Advanced predictive analytics for network operations
    Uses historical data and patterns to predict future events
    """
    
    def __init__(self, ltm_memory: LTMMemorySystem, pattern_engine: PatternRecognitionEngine = None, config: Dict[str, Any] = None):
        """
        Initialize Predictive Analytics Engine
        
        Args:
            ltm_memory: LTM memory system instance
            pattern_engine: Pattern recognition engine instance
            config: Configuration parameters
        """
        self.ltm_memory = ltm_memory
        self.pattern_engine = pattern_engine
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Prediction parameters
        self.min_confidence = self.config.get('min_prediction_confidence', 0.6)
        self.max_prediction_horizon_days = self.config.get('max_prediction_horizon_days', 30)
        self.min_historical_data_points = self.config.get('min_historical_data_points', 10)
        
        # Risk scoring weights
        self.risk_weights = {
            'frequency': 0.3,
            'severity': 0.25,
            'recency': 0.2,
            'trend': 0.15,
            'pattern_match': 0.1
        }
        
        # Prediction models
        self.predictors = {
            PredictionType.SECURITY_INCIDENT: self._predict_security_incidents,
            PredictionType.PERFORMANCE_ISSUE: self._predict_performance_issues,
            PredictionType.DEVICE_FAILURE: self._predict_device_failures,
            PredictionType.CAPACITY_OVERFLOW: self._predict_capacity_overflow,
            PredictionType.COMPLIANCE_VIOLATION: self._predict_compliance_violations,
            PredictionType.MAINTENANCE_REQUIRED: self._predict_maintenance_needs
        }
    
    def generate_predictions(self, 
                           entities: List[str] = None,
                           prediction_types: List[PredictionType] = None,
                           time_horizon_days: int = 7) -> List[Prediction]:
        """
        Generate predictions for specified entities and types
        
        Args:
            entities: Entities to predict for (stores, devices, brands)
            prediction_types: Types of predictions to generate
            time_horizon_days: How far ahead to predict
            
        Returns:
            List of predictions sorted by risk
        """
        try:
            if prediction_types is None:
                prediction_types = list(PredictionType)
            
            if entities is None:
                entities = self._get_all_entities()
            
            all_predictions = []
            
            # Generate predictions for each type
            for prediction_type in prediction_types:
                if prediction_type in self.predictors:
                    try:
                        predictions = self.predictors[prediction_type](entities, time_horizon_days)
                        all_predictions.extend(predictions)
                    except Exception as e:
                        self.logger.error(f"Error generating {prediction_type} predictions: {e}")
            
            # Filter by minimum confidence
            valid_predictions = [p for p in all_predictions if p.confidence >= self.min_confidence]
            
            # Sort by risk score (confidence * probability * severity weight)
            valid_predictions.sort(key=lambda p: self._calculate_risk_score(p), reverse=True)
            
            self.logger.info(f"Generated {len(valid_predictions)} predictions from {len(all_predictions)} candidates")
            
            return valid_predictions
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}")
            return []
    
    def analyze_trends(self, 
                      entities: List[str] = None,
                      metrics: List[str] = None,
                      lookback_days: int = 30) -> List[TrendAnalysis]:
        """
        Analyze trends in key metrics
        
        Args:
            entities: Entities to analyze
            metrics: Metrics to analyze
            lookback_days: Historical data period
            
        Returns:
            List of trend analyses
        """
        try:
            if metrics is None:
                metrics = ['event_frequency', 'severity_score', 'resolution_time']
            
            if entities is None:
                entities = self._get_all_entities()
            
            trends = []
            
            for entity in entities:
                for metric in metrics:
                    try:
                        trend = self._analyze_entity_trend(entity, metric, lookback_days)
                        if trend:
                            trends.append(trend)
                    except Exception as e:
                        self.logger.error(f"Error analyzing trend for {entity}/{metric}: {e}")
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return []
    
    def _predict_security_incidents(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict security incidents for entities"""
        predictions = []
        
        for entity in entities:
            try:
                # Get historical security events
                brand, store_id = self._parse_entity(entity)
                historical_events = self.ltm_memory.search_similar_events(
                    event_type='security_incident',
                    brand=brand,
                    limit=100
                )
                
                if len(historical_events) < self.min_historical_data_points:
                    continue
                
                # Analyze patterns and frequency
                recent_events = [e for e in historical_events 
                               if e.timestamp >= datetime.now() - timedelta(days=30)]
                
                if not recent_events:
                    continue
                
                # Calculate frequency trend
                frequency_trend = self._calculate_frequency_trend(historical_events, days=30)
                
                # Calculate severity trend
                severity_trend = self._calculate_severity_trend(recent_events)
                
                # Risk factors
                risk_factors = {
                    'historical_frequency': len(recent_events) / 30.0,
                    'severity_escalation': severity_trend,
                    'frequency_trend': frequency_trend,
                    'recent_activity': len([e for e in recent_events if 
                                          e.timestamp >= datetime.now() - timedelta(days=7)]) / 7.0
                }
                
                # Calculate prediction confidence and probability
                confidence = self._calculate_security_confidence(risk_factors, historical_events)
                probability = min(risk_factors['historical_frequency'] * 
                                (1 + max(0, frequency_trend)), 1.0)
                
                if confidence >= self.min_confidence:
                    # Find similar historical events for context
                    similar_events = self._find_similar_events(recent_events[:3])
                    
                    prediction = Prediction(
                        prediction_id=f"security_{entity}_{datetime.now().isoformat()}",
                        prediction_type=PredictionType.SECURITY_INCIDENT,
                        confidence=confidence,
                        probability=probability,
                        severity=self._predict_severity(recent_events),
                        affected_entity=entity,
                        predicted_time_window=(
                            datetime.now() + timedelta(days=1),
                            datetime.now() + timedelta(days=time_horizon_days)
                        ),
                        description=f"Security incident predicted for {entity} based on historical patterns",
                        reasoning=[
                            f"Historical frequency: {risk_factors['historical_frequency']:.2f} events/day",
                            f"Trend direction: {'increasing' if frequency_trend > 0 else 'stable/decreasing'}",
                            f"Recent activity spike: {risk_factors['recent_activity']:.2f} events/day",
                            f"Severity trend: {'escalating' if severity_trend > 0 else 'stable'}"
                        ],
                        recommendations=[
                            "Increase security monitoring for this entity",
                            "Review and update security policies",
                            "Prepare incident response procedures",
                            "Consider proactive security assessment"
                        ],
                        historical_precedent=[e.description for e in similar_events[:3]],
                        risk_factors=risk_factors,
                        mitigation_actions=[
                            "Enable enhanced logging and monitoring",
                            "Review firewall rules and IPS signatures",
                            "Update antivirus definitions",
                            "Brief security team on potential incident"
                        ],
                        business_impact="High" if probability > 0.7 else "Medium",
                        metadata={
                            'historical_event_count': len(historical_events),
                            'recent_event_count': len(recent_events),
                            'prediction_model': 'frequency_trend_analysis'
                        }
                    )
                    predictions.append(prediction)
                    
            except Exception as e:
                self.logger.error(f"Error predicting security incidents for {entity}: {e}")
        
        return predictions
    
    def _predict_performance_issues(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict performance issues for entities"""
        predictions = []
        
        for entity in entities:
            try:
                brand, store_id = self._parse_entity(entity)
                performance_events = self.ltm_memory.search_similar_events(
                    event_type='performance_issue',
                    brand=brand,
                    limit=50
                )
                
                if len(performance_events) < 5:
                    continue
                
                # Analyze performance trends
                recent_events = [e for e in performance_events 
                               if e.timestamp >= datetime.now() - timedelta(days=14)]
                
                if len(recent_events) >= 3:
                    frequency_trend = self._calculate_frequency_trend(performance_events, days=14)
                    
                    # Check resolution times for degradation
                    resolution_times = [e.resolution_time for e in recent_events 
                                      if e.resolution_time is not None]
                    
                    risk_factors = {
                        'frequency_trend': frequency_trend,
                        'recent_frequency': len(recent_events) / 14.0,
                        'resolution_time_trend': self._calculate_resolution_trend(resolution_times),
                        'unresolved_issues': len([e for e in recent_events if not e.resolution])
                    }
                    
                    confidence = min(abs(frequency_trend) * 0.8 + 
                                   risk_factors['recent_frequency'] * 0.2, 0.9)
                    probability = min(risk_factors['recent_frequency'] * 1.5, 0.8)
                    
                    if confidence >= 0.5:
                        prediction = Prediction(
                            prediction_id=f"performance_{entity}_{datetime.now().isoformat()}",
                            prediction_type=PredictionType.PERFORMANCE_ISSUE,
                            confidence=confidence,
                            probability=probability,
                            severity="medium",
                            affected_entity=entity,
                            predicted_time_window=(
                                datetime.now() + timedelta(days=2),
                                datetime.now() + timedelta(days=time_horizon_days)
                            ),
                            description=f"Performance issues predicted for {entity}",
                            reasoning=[
                                f"Frequency trend: {frequency_trend:.2f}",
                                f"Recent issue rate: {risk_factors['recent_frequency']:.2f}/day",
                                f"Unresolved issues: {risk_factors['unresolved_issues']}"
                            ],
                            recommendations=[
                                "Monitor network performance metrics",
                                "Check bandwidth utilization",
                                "Review device resource usage",
                                "Consider capacity planning"
                            ],
                            historical_precedent=[e.description for e in recent_events[:2]],
                            risk_factors=risk_factors,
                            mitigation_actions=[
                                "Proactive performance monitoring",
                                "Resource capacity assessment",
                                "Network optimization review"
                            ],
                            business_impact="Medium",
                            metadata={
                                'prediction_model': 'performance_trend_analysis',
                                'recent_events': len(recent_events)
                            }
                        )
                        predictions.append(prediction)
                        
            except Exception as e:
                self.logger.error(f"Error predicting performance issues for {entity}: {e}")
        
        return predictions
    
    def _predict_device_failures(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict device failures"""
        predictions = []
        
        # Group entities by device
        device_entities = [e for e in entities if '_' in e and len(e.split('_')) >= 3]
        
        for entity in device_entities:
            try:
                parts = entity.split('_')
                brand, store_id = parts[0], parts[1]
                device_name = '_'.join(parts[2:])
                
                # Get all events for this device
                device_events = []
                for event_type in ['performance_issue', 'configuration_change', 'security_incident']:
                    events = self.ltm_memory.search_similar_events(
                        event_type=event_type,
                        brand=brand,
                        limit=50
                    )
                    # Filter for specific device
                    device_specific = [e for e in events if e.device_name == device_name and e.store_id == store_id]
                    device_events.extend(device_specific)
                
                if len(device_events) < 5:
                    continue
                
                # Analyze device health trends
                recent_events = [e for e in device_events 
                               if e.timestamp >= datetime.now() - timedelta(days=21)]
                
                if len(recent_events) >= 3:
                    # Calculate failure risk factors
                    critical_events = [e for e in recent_events if e.severity in ['critical', 'high']]
                    unresolved_events = [e for e in recent_events if not e.resolution]
                    
                    risk_factors = {
                        'event_frequency': len(recent_events) / 21.0,
                        'critical_event_ratio': len(critical_events) / len(recent_events),
                        'unresolved_ratio': len(unresolved_events) / len(recent_events),
                        'event_trend': self._calculate_frequency_trend(device_events, days=21)
                    }
                    
                    # High risk if many critical unresolved events
                    failure_risk = (risk_factors['critical_event_ratio'] * 0.4 + 
                                   risk_factors['unresolved_ratio'] * 0.3 +
                                   risk_factors['event_frequency'] * 0.3)
                    
                    confidence = min(failure_risk * 1.2, 0.95)
                    probability = min(failure_risk, 0.8)
                    
                    if confidence >= 0.6:
                        prediction = Prediction(
                            prediction_id=f"device_failure_{entity}_{datetime.now().isoformat()}",
                            prediction_type=PredictionType.DEVICE_FAILURE,
                            confidence=confidence,
                            probability=probability,
                            severity="high" if failure_risk > 0.7 else "medium",
                            affected_entity=entity,
                            predicted_time_window=(
                                datetime.now() + timedelta(days=1),
                                datetime.now() + timedelta(days=min(time_horizon_days, 14))
                            ),
                            description=f"Device failure risk detected for {device_name} at {brand} store {store_id}",
                            reasoning=[
                                f"Recent event frequency: {risk_factors['event_frequency']:.2f}/day",
                                f"Critical events: {len(critical_events)} of {len(recent_events)}",
                                f"Unresolved issues: {len(unresolved_events)}",
                                f"Event trend: {'increasing' if risk_factors['event_trend'] > 0 else 'stable'}"
                            ],
                            recommendations=[
                                f"Schedule immediate inspection of {device_name}",
                                "Check device health and resource utilization",
                                "Prepare replacement device",
                                "Review device maintenance history"
                            ],
                            historical_precedent=[e.description for e in critical_events[:2]],
                            risk_factors=risk_factors,
                            mitigation_actions=[
                                "Proactive device replacement",
                                "Enhanced monitoring",
                                "Backup configuration",
                                "Spare device preparation"
                            ],
                            business_impact="High" if failure_risk > 0.7 else "Medium",
                            metadata={
                                'device_name': device_name,
                                'total_events': len(device_events),
                                'recent_events': len(recent_events),
                                'prediction_model': 'device_health_analysis'
                            }
                        )
                        predictions.append(prediction)
                        
            except Exception as e:
                self.logger.error(f"Error predicting device failure for {entity}: {e}")
        
        return predictions
    
    def _predict_capacity_overflow(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict capacity overflow situations"""
        predictions = []
        
        # This would typically use performance metrics data
        # For now, we'll use performance events as a proxy
        
        for entity in entities:
            try:
                brand, store_id = self._parse_entity(entity)
                perf_events = self.ltm_memory.search_similar_events(
                    event_type='performance_issue',
                    brand=brand,
                    limit=30
                )
                
                # Look for increasing performance issues
                if len(perf_events) >= 5:
                    recent_events = [e for e in perf_events 
                                   if e.timestamp >= datetime.now() - timedelta(days=14)]
                    
                    if len(recent_events) >= 3:
                        frequency_trend = self._calculate_frequency_trend(perf_events, days=14)
                        
                        if frequency_trend > 0.1:  # Increasing trend
                            risk_factors = {
                                'frequency_trend': frequency_trend,
                                'recent_frequency': len(recent_events) / 14.0
                            }
                            
                            confidence = min(frequency_trend * 2, 0.8)
                            probability = min(risk_factors['recent_frequency'] * 2, 0.7)
                            
                            prediction = Prediction(
                                prediction_id=f"capacity_{entity}_{datetime.now().isoformat()}",
                                prediction_type=PredictionType.CAPACITY_OVERFLOW,
                                confidence=confidence,
                                probability=probability,
                                severity="medium",
                                affected_entity=entity,
                                predicted_time_window=(
                                    datetime.now() + timedelta(days=3),
                                    datetime.now() + timedelta(days=time_horizon_days)
                                ),
                                description=f"Capacity overflow risk for {entity}",
                                reasoning=[
                                    f"Performance issue frequency increasing: {frequency_trend:.2f}",
                                    f"Recent performance events: {len(recent_events)}"
                                ],
                                recommendations=[
                                    "Review bandwidth utilization",
                                    "Assess storage capacity",
                                    "Plan capacity expansion",
                                    "Optimize resource allocation"
                                ],
                                historical_precedent=[],
                                risk_factors=risk_factors,
                                mitigation_actions=[
                                    "Capacity planning assessment",
                                    "Resource optimization",
                                    "Infrastructure scaling"
                                ],
                                business_impact="Medium",
                                metadata={'prediction_model': 'capacity_trend_analysis'}
                            )
                            predictions.append(prediction)
                            
            except Exception as e:
                self.logger.error(f"Error predicting capacity overflow for {entity}: {e}")
        
        return predictions
    
    def _predict_compliance_violations(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict compliance violations"""
        predictions = []
        
        for entity in entities:
            try:
                brand, store_id = self._parse_entity(entity)
                
                # Look for configuration changes and policy violations
                config_events = self.ltm_memory.search_similar_events(
                    event_type='configuration_change',
                    brand=brand,
                    limit=20
                )
                
                # Check for frequent configuration changes (potential drift)
                recent_configs = [e for e in config_events 
                                 if e.timestamp >= datetime.now() - timedelta(days=7)]
                
                if len(recent_configs) >= 3:
                    risk_factors = {
                        'config_change_frequency': len(recent_configs) / 7.0,
                        'recent_changes': len(recent_configs)
                    }
                    
                    # High frequency of config changes might lead to compliance drift
                    if risk_factors['config_change_frequency'] > 0.5:
                        confidence = min(risk_factors['config_change_frequency'] * 0.8, 0.7)
                        probability = min(risk_factors['config_change_frequency'] * 0.6, 0.6)
                        
                        prediction = Prediction(
                            prediction_id=f"compliance_{entity}_{datetime.now().isoformat()}",
                            prediction_type=PredictionType.COMPLIANCE_VIOLATION,
                            confidence=confidence,
                            probability=probability,
                            severity="medium",
                            affected_entity=entity,
                            predicted_time_window=(
                                datetime.now() + timedelta(days=5),
                                datetime.now() + timedelta(days=time_horizon_days)
                            ),
                            description=f"Compliance drift risk for {entity}",
                            reasoning=[
                                f"High configuration change frequency: {risk_factors['config_change_frequency']:.2f}/day",
                                f"Recent changes: {len(recent_configs)} in last 7 days"
                            ],
                            recommendations=[
                                "Review configuration changes against standards",
                                "Implement configuration validation",
                                "Schedule compliance audit",
                                "Update change management procedures"
                            ],
                            historical_precedent=[],
                            risk_factors=risk_factors,
                            mitigation_actions=[
                                "Configuration compliance check",
                                "Change management review",
                                "Policy validation"
                            ],
                            business_impact="Medium",
                            metadata={'prediction_model': 'compliance_drift_analysis'}
                        )
                        predictions.append(prediction)
                        
            except Exception as e:
                self.logger.error(f"Error predicting compliance violations for {entity}: {e}")
        
        return predictions
    
    def _predict_maintenance_needs(self, entities: List[str], time_horizon_days: int) -> List[Prediction]:
        """Predict maintenance requirements"""
        predictions = []
        
        # This is a simplified version - would typically use device age, usage metrics, etc.
        for entity in entities:
            try:
                brand, store_id = self._parse_entity(entity)
                
                # Get all events for the entity
                all_events = []
                for event_type in ['performance_issue', 'configuration_change', 'security_incident']:
                    events = self.ltm_memory.search_similar_events(
                        event_type=event_type,
                        brand=brand,
                        limit=30
                    )
                    if store_id:
                        events = [e for e in events if e.store_id == store_id]
                    all_events.extend(events)
                
                if len(all_events) >= 10:
                    # Calculate maintenance need based on event patterns
                    recent_events = [e for e in all_events 
                                   if e.timestamp >= datetime.now() - timedelta(days=30)]
                    
                    unresolved_events = [e for e in recent_events if not e.resolution]
                    performance_events = [e for e in recent_events if e.event_type == 'performance_issue']
                    
                    risk_factors = {
                        'total_event_rate': len(recent_events) / 30.0,
                        'unresolved_ratio': len(unresolved_events) / max(len(recent_events), 1),
                        'performance_issue_rate': len(performance_events) / 30.0
                    }
                    
                    maintenance_score = (risk_factors['total_event_rate'] * 0.4 +
                                       risk_factors['unresolved_ratio'] * 0.3 +
                                       risk_factors['performance_issue_rate'] * 0.3)
                    
                    if maintenance_score > 0.3:
                        confidence = min(maintenance_score * 1.2, 0.8)
                        probability = min(maintenance_score, 0.7)
                        
                        prediction = Prediction(
                            prediction_id=f"maintenance_{entity}_{datetime.now().isoformat()}",
                            prediction_type=PredictionType.MAINTENANCE_REQUIRED,
                            confidence=confidence,
                            probability=probability,
                            severity="low",
                            affected_entity=entity,
                            predicted_time_window=(
                                datetime.now() + timedelta(days=7),
                                datetime.now() + timedelta(days=time_horizon_days)
                            ),
                            description=f"Preventive maintenance recommended for {entity}",
                            reasoning=[
                                f"Event rate: {risk_factors['total_event_rate']:.2f}/day",
                                f"Unresolved issues: {len(unresolved_events)}",
                                f"Performance issues: {len(performance_events)}"
                            ],
                            recommendations=[
                                "Schedule preventive maintenance",
                                "Review device configurations",
                                "Update software and signatures",
                                "Check hardware health"
                            ],
                            historical_precedent=[],
                            risk_factors=risk_factors,
                            mitigation_actions=[
                                "Preventive maintenance scheduling",
                                "Health check assessment",
                                "Configuration optimization"
                            ],
                            business_impact="Low",
                            metadata={'prediction_model': 'maintenance_need_analysis'}
                        )
                        predictions.append(prediction)
                        
            except Exception as e:
                self.logger.error(f"Error predicting maintenance needs for {entity}: {e}")
        
        return predictions
    
    def _get_all_entities(self) -> List[str]:
        """Get all entities from historical data"""
        try:
            events = self.ltm_memory.search_similar_events(limit=500)
            entities = set()
            
            for event in events:
                # Store-level entity
                entities.add(f"{event.brand}_{event.store_id}")
                # Device-level entity
                entities.add(f"{event.brand}_{event.store_id}_{event.device_name}")
            
            return list(entities)
            
        except Exception as e:
            self.logger.error(f"Error getting entities: {e}")
            return []
    
    def _parse_entity(self, entity: str) -> Tuple[str, Optional[str]]:
        """Parse entity string into brand and store_id"""
        parts = entity.split('_')
        brand = parts[0]
        store_id = parts[1] if len(parts) > 1 else None
        return brand, store_id
    
    def _calculate_frequency_trend(self, events: List[NetworkEvent], days: int) -> float:
        """Calculate frequency trend over time"""
        if len(events) < 3:
            return 0.0
        
        # Split events into two periods
        cutoff = datetime.now() - timedelta(days=days//2)
        recent_events = [e for e in events if e.timestamp >= cutoff]
        older_events = [e for e in events if e.timestamp < cutoff]
        
        recent_rate = len(recent_events) / (days // 2)
        older_rate = len(older_events) / (days // 2)
        
        if older_rate == 0:
            return 1.0 if recent_rate > 0 else 0.0
        
        return (recent_rate - older_rate) / older_rate
    
    def _calculate_severity_trend(self, events: List[NetworkEvent]) -> float:
        """Calculate severity trend"""
        if len(events) < 2:
            return 0.0
        
        severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        events.sort(key=lambda e: e.timestamp)
        weights = [severity_weights.get(e.severity, 1) for e in events]
        
        if len(weights) < 2:
            return 0.0
        
        # Simple trend: compare recent half to older half
        mid = len(weights) // 2
        recent_avg = statistics.mean(weights[mid:])
        older_avg = statistics.mean(weights[:mid])
        
        return (recent_avg - older_avg) / 4.0  # Normalize by max severity
    
    def _calculate_security_confidence(self, risk_factors: Dict[str, float], historical_events: List[NetworkEvent]) -> float:
        """Calculate confidence for security incident prediction"""
        base_confidence = 0.3
        
        # Increase confidence based on risk factors
        if risk_factors['historical_frequency'] > 0.1:  # Regular incidents
            base_confidence += 0.3
        
        if risk_factors['frequency_trend'] > 0.2:  # Increasing trend
            base_confidence += 0.3
        
        if risk_factors['recent_activity'] > risk_factors['historical_frequency']:  # Recent spike
            base_confidence += 0.2
        
        # Historical data quality bonus
        if len(historical_events) >= 20:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _predict_severity(self, events: List[NetworkEvent]) -> str:
        """Predict severity of future events based on historical patterns"""
        if not events:
            return "medium"
        
        severity_counts = Counter(e.severity for e in events)
        most_common = severity_counts.most_common(1)[0][0]
        
        # Trend towards higher severity if recent events are more severe
        recent_severities = [e.severity for e in events[:3]]
        if 'critical' in recent_severities or 'high' in recent_severities:
            return 'high'
        
        return most_common
    
    def _find_similar_events(self, events: List[NetworkEvent]) -> List[NetworkEvent]:
        """Find similar events in history"""
        if not events:
            return []
        
        # Use the first event as template
        template = events[0]
        
        similar = self.ltm_memory.search_similar_events(
            event_type=template.event_type,
            brand=template.brand,
            severity=template.severity,
            limit=5
        )
        
        return similar
    
    def _calculate_resolution_trend(self, resolution_times: List[int]) -> float:
        """Calculate trend in resolution times"""
        if len(resolution_times) < 3:
            return 0.0
        
        # Simple trend analysis
        mid = len(resolution_times) // 2
        recent_avg = statistics.mean(resolution_times[mid:])
        older_avg = statistics.mean(resolution_times[:mid])
        
        return (recent_avg - older_avg) / max(older_avg, 1)
    
    def _analyze_entity_trend(self, entity: str, metric: str, lookback_days: int) -> Optional[TrendAnalysis]:
        """Analyze trend for specific entity and metric"""
        try:
            brand, store_id = self._parse_entity(entity)
            
            events = self.ltm_memory.search_similar_events(
                brand=brand,
                limit=100
            )
            
            if store_id:
                events = [e for e in events if e.store_id == store_id]
            
            # Filter to lookback period
            cutoff = datetime.now() - timedelta(days=lookback_days)
            recent_events = [e for e in events if e.timestamp >= cutoff]
            
            if len(recent_events) < 5:
                return None
            
            # Calculate metric values over time
            if metric == 'event_frequency':
                # Events per day
                current_value = len(recent_events) / lookback_days
                
                # Compare to historical average
                older_events = [e for e in events if e.timestamp < cutoff]
                if older_events:
                    historical_avg = len(older_events) / max((events[0].timestamp - cutoff).days, 1)
                    trend_direction = 'increasing' if current_value > historical_avg * 1.1 else \
                                    'decreasing' if current_value < historical_avg * 0.9 else 'stable'
                    trend_strength = abs(current_value - historical_avg) / max(historical_avg, 0.01)
                else:
                    trend_direction = 'stable'
                    trend_strength = 0.0
                
                predicted_value = current_value * (1 + trend_strength * (1 if trend_direction == 'increasing' else -1))
                
            elif metric == 'severity_score':
                severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                severity_scores = [severity_weights.get(e.severity, 1) for e in recent_events]
                
                if severity_scores:
                    current_value = statistics.mean(severity_scores)
                    trend_direction = 'stable'  # Simplified
                    trend_strength = statistics.stdev(severity_scores) if len(severity_scores) > 1 else 0
                    predicted_value = current_value
                else:
                    return None
                    
            elif metric == 'resolution_time':
                resolution_times = [e.resolution_time for e in recent_events 
                                  if e.resolution_time is not None]
                
                if len(resolution_times) >= 3:
                    current_value = statistics.mean(resolution_times)
                    trend_direction = 'stable'  # Simplified
                    trend_strength = statistics.stdev(resolution_times) / max(current_value, 1)
                    predicted_value = current_value
                else:
                    return None
            else:
                return None
            
            return TrendAnalysis(
                entity=entity,
                metric=metric,
                trend_direction=trend_direction,
                trend_strength=min(trend_strength, 1.0),
                current_value=current_value,
                predicted_value=predicted_value,
                confidence_interval=(
                    predicted_value * 0.8,
                    predicted_value * 1.2
                ),
                time_horizon_days=7
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend for {entity}/{metric}: {e}")
            return None
    
    def _calculate_risk_score(self, prediction: Prediction) -> float:
        """Calculate overall risk score for prediction"""
        severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        severity_weight = severity_weights.get(prediction.severity, 2)
        
        return prediction.confidence * prediction.probability * severity_weight

def create_predictive_engine(ltm_memory: LTMMemorySystem, 
                           pattern_engine: PatternRecognitionEngine = None,
                           config: Dict[str, Any] = None) -> PredictiveAnalyticsEngine:
    """Factory function to create PredictiveAnalyticsEngine"""
    return PredictiveAnalyticsEngine(ltm_memory, pattern_engine, config)