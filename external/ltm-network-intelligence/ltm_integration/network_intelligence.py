# ltm_integration/network_intelligence.py
# Network Intelligence Engine with LTM integration

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class NetworkInsight:
    """Structured network insight with LTM integration"""
    insight_type: str
    title: str
    description: str
    confidence_score: float
    affected_devices: List[str]
    recommendations: List[str]
    severity: str  # low, medium, high, critical
    timestamp: str = None
    source_systems: List[str] = None
    correlation_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.source_systems is None:
            self.source_systems = []
        if self.correlation_data is None:
            self.correlation_data = {}

@dataclass
class NetworkEvent:
    """Network event structure for LTM processing"""
    event_id: str
    event_type: str
    source_device: str
    description: str
    severity: str
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class NetworkIntelligenceEngine:
    """Enhanced Network Intelligence Engine with LTM learning capabilities"""
    
    def __init__(self, ltm_client):
        self.ltm_client = ltm_client
        self.insights_cache = []
        self.pattern_memory = {}
        self.learning_enabled = True
        self.correlation_threshold = 0.7
        
    async def analyze_device_performance(self, device_data: Dict[str, Any]) -> NetworkInsight:
        """Analyze device performance with LTM-enhanced insights"""
        try:
            device_name = device_data.get("name", "unknown")
            performance_metrics = device_data.get("performance", {})
            
            # Basic performance analysis
            cpu_usage = performance_metrics.get("cpu_percent", 0)
            memory_usage = performance_metrics.get("memory_percent", 0)
            disk_usage = performance_metrics.get("disk_percent", 0)
            
            # Determine severity based on metrics
            severity = self._calculate_performance_severity(cpu_usage, memory_usage, disk_usage)
            confidence_score = 0.8
            
            # Search LTM for similar patterns
            ltm_patterns = await self._search_performance_patterns(device_name, performance_metrics)
            
            # Generate recommendations based on LTM insights
            recommendations = await self._generate_performance_recommendations(
                device_name, performance_metrics, ltm_patterns
            )
            
            # Create insight
            insight = NetworkInsight(
                insight_type="performance_analysis",
                title=f"Performance Analysis: {device_name}",
                description=f"Device showing {severity} performance indicators. CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%",
                confidence_score=confidence_score,
                affected_devices=[device_name],
                recommendations=recommendations,
                severity=severity,
                source_systems=["performance_monitor", "ltm_patterns"],
                correlation_data={
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_usage": disk_usage,
                    "ltm_pattern_matches": len(ltm_patterns)
                }
            )
            
            # Record in LTM for future learning
            if self.learning_enabled:
                await self._record_performance_insight(insight)
            
            return insight
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return NetworkInsight(
                insight_type="performance_analysis",
                title="Performance Analysis Failed",
                description=f"Could not analyze device performance: {str(e)}",
                confidence_score=0.0,
                affected_devices=[device_data.get("name", "unknown")],
                recommendations=["Check device connectivity", "Verify monitoring configuration"],
                severity="unknown"
            )

    def _calculate_performance_severity(self, cpu: float, memory: float, disk: float) -> str:
        """Calculate performance severity based on metrics"""
        max_usage = max(cpu, memory, disk)
        
        if max_usage >= 90:
            return "critical"
        elif max_usage >= 75:
            return "high"
        elif max_usage >= 60:
            return "medium"
        else:
            return "low"

    async def _search_performance_patterns(self, device_name: str, metrics: Dict[str, Any]) -> List[Any]:
        """Search LTM for similar performance patterns"""
        try:
            search_query = f"performance analysis {device_name} CPU memory disk usage patterns"
            patterns = await self.ltm_client.search_memories(
                query=search_query,
                tags=["performance", "analysis", "patterns"],
                limit=10,
                min_relevance=0.6
            )
            return patterns
        except Exception as e:
            logger.warning(f"LTM pattern search failed: {e}")
            return []

    async def _generate_performance_recommendations(self, device_name: str, 
                                                  metrics: Dict[str, Any], 
                                                  ltm_patterns: List[Any]) -> List[str]:
        """Generate performance recommendations using LTM insights"""
        recommendations = []
        
        cpu_usage = metrics.get("cpu_percent", 0)
        memory_usage = metrics.get("memory_percent", 0)
        disk_usage = metrics.get("disk_percent", 0)
        
        # Basic recommendations
        if cpu_usage > 80:
            recommendations.append("Investigate high CPU usage processes")
            recommendations.append("Consider CPU optimization or scaling")
            
        if memory_usage > 80:
            recommendations.append("Check memory leaks and optimize memory usage")
            recommendations.append("Consider increasing available memory")
            
        if disk_usage > 80:
            recommendations.append("Free up disk space by removing unnecessary files")
            recommendations.append("Implement log rotation and cleanup policies")
        
        # LTM-enhanced recommendations
        if ltm_patterns:
            pattern_insights = self._extract_pattern_insights(ltm_patterns)
            recommendations.extend(pattern_insights)
        
        # If no specific issues, provide proactive recommendations
        if not recommendations:
            recommendations = [
                "Performance is within normal parameters",
                "Continue regular monitoring",
                "Consider preventive maintenance scheduling"
            ]
            
        return recommendations[:5]  # Limit to top 5 recommendations

    def _extract_pattern_insights(self, patterns: List[Any]) -> List[str]:
        """Extract actionable insights from LTM patterns"""
        insights = []
        
        # Analyze patterns for common themes
        pattern_content = [p.content.lower() for p in patterns if hasattr(p, 'content')]
        
        if any("reboot" in content for content in pattern_content):
            insights.append("Based on historical patterns, consider scheduled reboot if issues persist")
            
        if any("maintenance" in content for content in pattern_content):
            insights.append("Schedule preventive maintenance based on similar past incidents")
            
        if any("scaling" in content for content in pattern_content):
            insights.append("Historical data suggests resource scaling may be beneficial")
            
        return insights

    async def _record_performance_insight(self, insight: NetworkInsight):
        """Record performance insight in LTM for future learning"""
        try:
            content = f"Performance insight: {insight.title}. {insight.description}. Severity: {insight.severity}. Recommendations: {', '.join(insight.recommendations)}"
            
            await self.ltm_client.record_message(
                role="system",
                content=content,
                tags=["performance", "analysis", "insight", insight.severity],
                metadata={
                    "insight_type": insight.insight_type,
                    "affected_devices": insight.affected_devices,
                    "confidence_score": insight.confidence_score,
                    "correlation_data": insight.correlation_data
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record insight in LTM: {e}")

    async def analyze_network_topology(self, topology_data: Dict[str, Any]) -> NetworkInsight:
        """Analyze network topology changes with LTM insights"""
        try:
            devices = topology_data.get("devices", [])
            connections = topology_data.get("connections", [])
            changes = topology_data.get("changes", [])
            
            # Analyze topology health
            total_devices = len(devices)
            online_devices = len([d for d in devices if d.get("status") == "online"])
            connectivity_ratio = online_devices / total_devices if total_devices > 0 else 0
            
            # Determine severity
            if connectivity_ratio < 0.8:
                severity = "critical"
            elif connectivity_ratio < 0.9:
                severity = "high"
            elif connectivity_ratio < 0.95:
                severity = "medium"
            else:
                severity = "low"
            
            # Search for topology patterns
            ltm_patterns = await self._search_topology_patterns(topology_data)
            
            # Generate topology recommendations
            recommendations = await self._generate_topology_recommendations(
                topology_data, ltm_patterns, connectivity_ratio
            )
            
            insight = NetworkInsight(
                insight_type="topology_analysis",
                title="Network Topology Analysis",
                description=f"Network connectivity at {connectivity_ratio:.1%}. {total_devices} total devices, {online_devices} online.",
                confidence_score=0.9,
                affected_devices=[d.get("name", "unknown") for d in devices if d.get("status") != "online"],
                recommendations=recommendations,
                severity=severity,
                source_systems=["topology_monitor", "ltm_patterns"],
                correlation_data={
                    "total_devices": total_devices,
                    "online_devices": online_devices,
                    "connectivity_ratio": connectivity_ratio,
                    "recent_changes": len(changes)
                }
            )
            
            # Record in LTM
            if self.learning_enabled:
                await self._record_topology_insight(insight, topology_data)
            
            return insight
            
        except Exception as e:
            logger.error(f"Topology analysis failed: {e}")
            return NetworkInsight(
                insight_type="topology_analysis",
                title="Topology Analysis Failed",
                description=f"Could not analyze network topology: {str(e)}",
                confidence_score=0.0,
                affected_devices=[],
                recommendations=["Check topology data source", "Verify network monitoring"],
                severity="unknown"
            )

    async def _search_topology_patterns(self, topology_data: Dict[str, Any]) -> List[Any]:
        """Search LTM for topology patterns"""
        try:
            search_query = "network topology connectivity device status patterns changes"
            patterns = await self.ltm_client.search_memories(
                query=search_query,
                tags=["topology", "connectivity", "network"],
                limit=15,
                min_relevance=0.6
            )
            return patterns
        except Exception as e:
            logger.warning(f"Topology pattern search failed: {e}")
            return []

    async def _generate_topology_recommendations(self, topology_data: Dict[str, Any],
                                               ltm_patterns: List[Any],
                                               connectivity_ratio: float) -> List[str]:
        """Generate topology recommendations"""
        recommendations = []
        
        offline_devices = [d for d in topology_data.get("devices", []) if d.get("status") != "online"]
        changes = topology_data.get("changes", [])
        
        # Basic recommendations based on current state
        if connectivity_ratio < 0.8:
            recommendations.append("Critical: Investigate network connectivity issues immediately")
            recommendations.append("Check core network infrastructure and switches")
            
        if offline_devices:
            recommendations.append(f"Investigate {len(offline_devices)} offline devices")
            for device in offline_devices[:3]:  # Limit to first 3
                recommendations.append(f"Check connectivity to {device.get('name', 'unknown device')}")
        
        if len(changes) > 5:
            recommendations.append("High number of recent topology changes - review change management")
        
        # LTM-enhanced recommendations
        if ltm_patterns:
            for pattern in ltm_patterns[:2]:  # Use top 2 patterns
                if hasattr(pattern, 'content') and "redundancy" in pattern.content.lower():
                    recommendations.append("Consider implementing network redundancy based on historical patterns")
                elif hasattr(pattern, 'content') and "failover" in pattern.content.lower():
                    recommendations.append("Review failover configurations based on past incidents")
        
        return recommendations[:6]

    async def _record_topology_insight(self, insight: NetworkInsight, topology_data: Dict[str, Any]):
        """Record topology insight in LTM"""
        try:
            content = f"Topology analysis: {insight.description}. Affected devices: {len(insight.affected_devices)}. Key recommendations: {', '.join(insight.recommendations[:3])}"
            
            await self.ltm_client.record_message(
                role="system",
                content=content,
                tags=["topology", "network", "connectivity", insight.severity],
                metadata={
                    "insight_type": insight.insight_type,
                    "total_devices": topology_data.get("devices", []),
                    "connectivity_ratio": insight.correlation_data.get("connectivity_ratio"),
                    "topology_changes": len(topology_data.get("changes", []))
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record topology insight: {e}")

    async def correlate_insights(self, insights: List[NetworkInsight]) -> Dict[str, Any]:
        """Correlate multiple insights using LTM patterns"""
        try:
            if not insights:
                return {"correlations": [], "summary": "No insights to correlate"}
            
            correlations = {
                "strong_correlations": [],
                "weak_correlations": [],
                "summary": "",
                "recommended_actions": []
            }
            
            # Group insights by type and severity
            by_type = {}
            by_severity = {"critical": [], "high": [], "medium": [], "low": []}
            
            for insight in insights:
                insight_type = insight.insight_type
                if insight_type not in by_type:
                    by_type[insight_type] = []
                by_type[insight_type].append(insight)
                
                by_severity[insight.severity].append(insight)
            
            # Look for correlations
            if len(by_type.get("performance_analysis", [])) > 1 and len(by_type.get("topology_analysis", [])) > 0:
                correlations["strong_correlations"].append({
                    "types": ["performance_analysis", "topology_analysis"],
                    "description": "Performance issues may be related to network connectivity problems",
                    "confidence": 0.85,
                    "affected_systems": list(set([d for insight in insights for d in insight.affected_devices]))
                })
            
            # Generate summary
            total_insights = len(insights)
            critical_count = len(by_severity["critical"])
            high_count = len(by_severity["high"])
            
            if critical_count > 0:
                correlations["summary"] = f"{critical_count} critical issues identified requiring immediate attention"
            elif high_count > 0:
                correlations["summary"] = f"{high_count} high priority issues found among {total_insights} insights"
            else:
                correlations["summary"] = f"Analysis of {total_insights} insights shows manageable system state"
            
            # Generate recommended actions
            if critical_count > 0:
                correlations["recommended_actions"].extend([
                    "Address critical issues immediately",
                    "Implement emergency response procedures"
                ])
            
            correlations["recommended_actions"].extend([
                "Review all high and medium priority recommendations",
                "Schedule maintenance for identified issues",
                "Monitor affected devices closely"
            ])
            
            # Record correlation analysis in LTM
            if self.learning_enabled:
                await self._record_correlation_analysis(correlations, insights)
            
            return correlations
            
        except Exception as e:
            logger.error(f"Insight correlation failed: {e}")
            return {"correlations": [], "summary": f"Correlation analysis failed: {str(e)}"}

    async def _record_correlation_analysis(self, correlations: Dict[str, Any], insights: List[NetworkInsight]):
        """Record correlation analysis in LTM"""
        try:
            content = f"Correlation analysis: {correlations['summary']}. Found {len(correlations['strong_correlations'])} strong correlations. Recommended actions: {', '.join(correlations['recommended_actions'][:3])}"
            
            await self.ltm_client.record_message(
                role="system",
                content=content,
                tags=["correlation", "analysis", "insights", "summary"],
                metadata={
                    "total_insights": len(insights),
                    "insight_types": list(set([i.insight_type for i in insights])),
                    "severity_distribution": {
                        sev: len([i for i in insights if i.severity == sev])
                        for sev in ["critical", "high", "medium", "low"]
                    },
                    "correlation_count": len(correlations["strong_correlations"])
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record correlation analysis: {e}")

    async def generate_intelligence_report(self, insights: List[NetworkInsight]) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        try:
            # Correlate insights
            correlations = await self.correlate_insights(insights)
            
            # Generate executive summary
            total_insights = len(insights)
            severity_counts = {
                "critical": len([i for i in insights if i.severity == "critical"]),
                "high": len([i for i in insights if i.severity == "high"]),
                "medium": len([i for i in insights if i.severity == "medium"]),
                "low": len([i for i in insights if i.severity == "low"])
            }
            
            # Calculate overall health score
            health_score = self._calculate_network_health_score(severity_counts, total_insights)
            
            # Get LTM trends
            trends = await self._analyze_historical_trends()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "executive_summary": {
                    "total_insights": total_insights,
                    "network_health_score": health_score,
                    "severity_distribution": severity_counts,
                    "overall_status": self._get_overall_status(health_score)
                },
                "insights": [asdict(insight) for insight in insights],
                "correlations": correlations,
                "trends": trends,
                "recommendations": {
                    "immediate_actions": [
                        rec for insight in insights if insight.severity in ["critical", "high"]
                        for rec in insight.recommendations[:2]
                    ][:5],
                    "strategic_actions": correlations.get("recommended_actions", [])[:3]
                }
            }
            
            # Record report generation in LTM
            if self.learning_enabled:
                await self._record_intelligence_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Intelligence report generation failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "executive_summary": {"total_insights": 0, "network_health_score": 0}
            }

    def _calculate_network_health_score(self, severity_counts: Dict[str, int], total_insights: int) -> float:
        """Calculate overall network health score (0-100)"""
        if total_insights == 0:
            return 100.0
        
        # Weighted scoring
        score = 100.0
        score -= severity_counts.get("critical", 0) * 25
        score -= severity_counts.get("high", 0) * 15
        score -= severity_counts.get("medium", 0) * 8
        score -= severity_counts.get("low", 0) * 3
        
        return max(0.0, score)

    def _get_overall_status(self, health_score: float) -> str:
        """Get overall status based on health score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 50:
            return "fair"
        else:
            return "poor"

    async def _analyze_historical_trends(self) -> Dict[str, Any]:
        """Analyze historical trends from LTM"""
        try:
            # Search for trend patterns
            trend_patterns = await self.ltm_client.search_memories(
                query="trends performance topology health patterns over time",
                tags=["trends", "patterns", "historical"],
                limit=20,
                min_relevance=0.5
            )
            
            trends = {
                "performance_trend": "stable",
                "topology_changes": "normal",
                "incident_frequency": "decreasing",
                "pattern_confidence": len(trend_patterns) / 20
            }
            
            # Analyze patterns for trends
            if trend_patterns:
                pattern_content = [p.content.lower() for p in trend_patterns if hasattr(p, 'content')]
                
                if any("increasing" in content for content in pattern_content):
                    trends["performance_trend"] = "degrading"
                elif any("improving" in content for content in pattern_content):
                    trends["performance_trend"] = "improving"
                
                if sum(1 for content in pattern_content if "change" in content) > 10:
                    trends["topology_changes"] = "high"
            
            return trends
            
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            return {"performance_trend": "unknown", "topology_changes": "unknown"}

    async def _record_intelligence_report(self, report: Dict[str, Any]):
        """Record intelligence report generation in LTM"""
        try:
            summary = report["executive_summary"]
            content = f"Intelligence report generated: Health score {summary['network_health_score']:.1f}/100, {summary['total_insights']} insights analyzed, status {summary['overall_status']}"
            
            await self.ltm_client.record_message(
                role="system",
                content=content,
                tags=["intelligence_report", "analysis", "summary"],
                metadata={
                    "health_score": summary["network_health_score"],
                    "total_insights": summary["total_insights"],
                    "severity_distribution": summary["severity_distribution"],
                    "report_timestamp": report["timestamp"]
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record intelligence report: {e}")