# monitoring/ltm_performance_monitor.py
# Advanced Performance Monitoring with LTM integration and predictive analytics

import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
import time
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading

# Optional dependencies for advanced monitoring
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available - install with: pip install prometheus-client")

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Performance metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """Performance metric structure"""
    metric_id: str
    metric_name: str
    metric_type: MetricType
    value: float
    timestamp: str
    labels: Dict[str, str]
    unit: str
    description: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class PerformanceAlert:
    """Performance alert structure"""
    alert_id: str
    metric_name: str
    severity: AlertSeverity
    threshold_value: float
    current_value: float
    message: str
    timestamp: str
    resolved: bool = False
    resolution_timestamp: Optional[str] = None

@dataclass
class SystemHealthMetrics:
    """System health metrics collection"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    timestamp: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class LTMPerformanceMonitor:
    """Advanced performance monitoring with LTM learning and predictive analytics"""
    
    def __init__(self, ltm_client, config_path: str = "monitoring/performance_config.json"):
        self.ltm_client = ltm_client
        self.config_path = config_path
        self.config = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.metrics_store = {}
        self.alert_rules = {}
        self.active_alerts = {}
        self.performance_history = []
        
        # Collection intervals
        self.collection_interval = 10  # seconds
        self.history_retention_hours = 168  # 7 days
        
        # Prometheus metrics (if available)
        self.prometheus_registry = None
        self.prometheus_metrics = {}
        
        # Background tasks
        self.monitoring_task = None
        self.analysis_task = None
        
        # Performance baselines and anomaly detection
        self.performance_baselines = {}
        self.anomaly_threshold = 2.0  # standard deviations
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize performance monitoring system"""
        initialization_result = {
            "component": "LTM Performance Monitor",
            "timestamp": datetime.now().isoformat(),
            "config_loaded": False,
            "prometheus_status": "unavailable",
            "monitoring_rules": 0,
            "alert_rules": 0,
            "overall_status": "failed"
        }
        
        try:
            # Load configuration
            await self._load_monitoring_config()
            initialization_result["config_loaded"] = True
            
            # Initialize Prometheus if available
            if PROMETHEUS_AVAILABLE:
                prometheus_result = await self._initialize_prometheus()
                initialization_result["prometheus_status"] = prometheus_result["status"]
            
            # Setup monitoring rules and alerts
            await self._setup_monitoring_rules()
            initialization_result["monitoring_rules"] = len(self.metrics_store)
            
            await self._setup_alert_rules()
            initialization_result["alert_rules"] = len(self.alert_rules)
            
            # Initialize performance baselines
            await self._initialize_performance_baselines()
            
            initialization_result["overall_status"] = "success"
            
            # Record initialization in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="monitoring",
                    content=f"Performance Monitor initialized: {len(self.alert_rules)} alert rules, {len(self.metrics_store)} metrics configured",
                    tags=["monitoring", "initialization", "performance"],
                    metadata=initialization_result
                )
            
            logger.info("✓ Performance Monitor initialized successfully")
            return initialization_result
            
        except Exception as e:
            logger.error(f"Performance Monitor initialization failed: {e}")
            initialization_result["error"] = str(e)
            return initialization_result

    async def _load_monitoring_config(self):
        """Load performance monitoring configuration"""
        try:
            import os
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default configuration
                self.config = {
                    "collection_interval": 10,
                    "history_retention_hours": 168,
                    "anomaly_detection": {
                        "enabled": True,
                        "threshold_stddev": 2.0,
                        "minimum_samples": 30
                    },
                    "system_monitoring": {
                        "cpu_enabled": True,
                        "memory_enabled": True,
                        "disk_enabled": True,
                        "network_enabled": True,
                        "load_average_enabled": True
                    },
                    "ltm_monitoring": {
                        "track_response_times": True,
                        "track_memory_usage": True,
                        "track_session_stats": True
                    },
                    "platform_monitoring": {
                        "api_gateway_metrics": True,
                        "mcp_server_metrics": True,
                        "knowledge_graph_metrics": True,
                        "security_metrics": True
                    },
                    "alerting": {
                        "enabled": True,
                        "email_notifications": False,
                        "webhook_notifications": False,
                        "ltm_learning": True
                    },
                    "prometheus": {
                        "enabled": True,
                        "port": 8003,
                        "endpoint": "/metrics"
                    }
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            # Update instance variables from config
            self.collection_interval = self.config.get("collection_interval", 10)
            self.history_retention_hours = self.config.get("history_retention_hours", 168)
            self.anomaly_threshold = self.config.get("anomaly_detection", {}).get("threshold_stddev", 2.0)
                    
        except Exception as e:
            logger.error(f"Monitoring config loading failed: {e}")
            self.config = {}

    async def _initialize_prometheus(self) -> Dict[str, Any]:
        """Initialize Prometheus metrics collection"""
        try:
            if not PROMETHEUS_AVAILABLE:
                return {"status": "unavailable", "reason": "prometheus_client not installed"}
            
            # Create custom registry
            self.prometheus_registry = CollectorRegistry()
            
            # Define Prometheus metrics
            self.prometheus_metrics = {
                # System metrics
                "system_cpu_percent": Gauge('ltm_system_cpu_percent', 'System CPU usage percentage', registry=self.prometheus_registry),
                "system_memory_percent": Gauge('ltm_system_memory_percent', 'System memory usage percentage', registry=self.prometheus_registry),
                "system_disk_percent": Gauge('ltm_system_disk_percent', 'System disk usage percentage', registry=self.prometheus_registry),
                "system_load_average": Gauge('ltm_system_load_average', 'System load average', ['period'], registry=self.prometheus_registry),
                
                # LTM metrics
                "ltm_response_time": Histogram('ltm_response_time_seconds', 'LTM response time in seconds', ['operation'], registry=self.prometheus_registry),
                "ltm_memory_usage": Gauge('ltm_memory_usage_bytes', 'LTM memory usage in bytes', registry=self.prometheus_registry),
                "ltm_session_count": Gauge('ltm_active_sessions', 'Number of active LTM sessions', registry=self.prometheus_registry),
                
                # Platform metrics
                "api_requests_total": Counter('ltm_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'], registry=self.prometheus_registry),
                "api_request_duration": Histogram('ltm_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'], registry=self.prometheus_registry),
                "mcp_tool_calls": Counter('ltm_mcp_tool_calls_total', 'Total MCP tool calls', ['tool_name', 'status'], registry=self.prometheus_registry),
                
                # Security metrics
                "security_events_total": Counter('ltm_security_events_total', 'Total security events', ['event_type', 'severity'], registry=self.prometheus_registry),
                "compliance_score": Gauge('ltm_compliance_score', 'Compliance score percentage', ['standard'], registry=self.prometheus_registry),
                
                # Performance alerts
                "active_alerts": Gauge('ltm_active_alerts', 'Number of active performance alerts', ['severity'], registry=self.prometheus_registry)
            }
            
            # Start Prometheus HTTP server
            prometheus_config = self.config.get("prometheus", {})
            if prometheus_config.get("enabled", True):
                prometheus_port = prometheus_config.get("port", 8003)
                start_http_server(prometheus_port, registry=self.prometheus_registry)
                logger.info(f"✓ Prometheus metrics server started on port {prometheus_port}")
            
            return {"status": "initialized", "port": prometheus_port, "metrics_count": len(self.prometheus_metrics)}
            
        except Exception as e:
            logger.error(f"Prometheus initialization failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _setup_monitoring_rules(self):
        """Setup monitoring rules and metrics collection"""
        try:
            # System monitoring rules
            if self.config.get("system_monitoring", {}).get("cpu_enabled", True):
                self.metrics_store["system_cpu"] = {
                    "name": "System CPU Usage",
                    "type": MetricType.GAUGE,
                    "unit": "percent",
                    "collector": self._collect_cpu_metrics,
                    "history": []
                }
            
            if self.config.get("system_monitoring", {}).get("memory_enabled", True):
                self.metrics_store["system_memory"] = {
                    "name": "System Memory Usage", 
                    "type": MetricType.GAUGE,
                    "unit": "percent",
                    "collector": self._collect_memory_metrics,
                    "history": []
                }
            
            if self.config.get("system_monitoring", {}).get("disk_enabled", True):
                self.metrics_store["system_disk"] = {
                    "name": "System Disk Usage",
                    "type": MetricType.GAUGE,
                    "unit": "percent", 
                    "collector": self._collect_disk_metrics,
                    "history": []
                }
            
            if self.config.get("system_monitoring", {}).get("network_enabled", True):
                self.metrics_store["network_io"] = {
                    "name": "Network I/O",
                    "type": MetricType.COUNTER,
                    "unit": "bytes",
                    "collector": self._collect_network_metrics,
                    "history": []
                }
            
            # LTM monitoring rules
            if self.config.get("ltm_monitoring", {}).get("track_response_times", True):
                self.metrics_store["ltm_response_time"] = {
                    "name": "LTM Response Time",
                    "type": MetricType.HISTOGRAM,
                    "unit": "milliseconds",
                    "collector": self._collect_ltm_response_times,
                    "history": []
                }
            
            if self.config.get("ltm_monitoring", {}).get("track_session_stats", True):
                self.metrics_store["ltm_session_stats"] = {
                    "name": "LTM Session Statistics",
                    "type": MetricType.GAUGE,
                    "unit": "count",
                    "collector": self._collect_ltm_session_stats,
                    "history": []
                }
            
            logger.info(f"✓ Setup {len(self.metrics_store)} monitoring rules")
            
        except Exception as e:
            logger.error(f"Monitoring rules setup failed: {e}")

    async def _setup_alert_rules(self):
        """Setup performance alert rules"""
        try:
            # CPU alert rules
            self.alert_rules["cpu_high"] = {
                "metric": "system_cpu",
                "condition": "greater_than",
                "threshold": 80.0,
                "severity": AlertSeverity.HIGH,
                "message": "High CPU usage detected"
            }
            
            self.alert_rules["cpu_critical"] = {
                "metric": "system_cpu",
                "condition": "greater_than",
                "threshold": 95.0,
                "severity": AlertSeverity.CRITICAL,
                "message": "Critical CPU usage detected"
            }
            
            # Memory alert rules
            self.alert_rules["memory_high"] = {
                "metric": "system_memory",
                "condition": "greater_than",
                "threshold": 85.0,
                "severity": AlertSeverity.HIGH,
                "message": "High memory usage detected"
            }
            
            self.alert_rules["memory_critical"] = {
                "metric": "system_memory",
                "condition": "greater_than",
                "threshold": 95.0,
                "severity": AlertSeverity.CRITICAL,
                "message": "Critical memory usage detected"
            }
            
            # Disk alert rules
            self.alert_rules["disk_high"] = {
                "metric": "system_disk",
                "condition": "greater_than",
                "threshold": 85.0,
                "severity": AlertSeverity.HIGH,
                "message": "High disk usage detected"
            }
            
            # LTM alert rules
            self.alert_rules["ltm_response_slow"] = {
                "metric": "ltm_response_time",
                "condition": "greater_than",
                "threshold": 5000.0,  # 5 seconds
                "severity": AlertSeverity.MEDIUM,
                "message": "LTM response time is slow"
            }
            
            # Anomaly detection alerts
            self.alert_rules["performance_anomaly"] = {
                "metric": "system_performance",
                "condition": "anomaly_detected",
                "threshold": self.anomaly_threshold,
                "severity": AlertSeverity.MEDIUM,
                "message": "Performance anomaly detected"
            }
            
            logger.info(f"✓ Setup {len(self.alert_rules)} alert rules")
            
        except Exception as e:
            logger.error(f"Alert rules setup failed: {e}")

    async def _initialize_performance_baselines(self):
        """Initialize performance baselines for anomaly detection"""
        try:
            # Initialize empty baselines - these will be populated as data is collected
            self.performance_baselines = {
                "system_cpu": {"mean": 0, "std": 0, "samples": []},
                "system_memory": {"mean": 0, "std": 0, "samples": []},
                "system_disk": {"mean": 0, "std": 0, "samples": []},
                "ltm_response_time": {"mean": 0, "std": 0, "samples": []}
            }
            
            logger.info("✓ Performance baselines initialized")
            
        except Exception as e:
            logger.error(f"Performance baselines initialization failed: {e}")

    async def start(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        try:
            self.monitoring_active = True
            
            # Start monitoring tasks
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.analysis_task = asyncio.create_task(self._analysis_loop())
            
            # Record start in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="monitoring",
                    content=f"Performance monitoring started with {self.collection_interval}s collection interval",
                    tags=["monitoring", "start", "performance"],
                    metadata={"collection_interval": self.collection_interval}
                )
            
            logger.info("✓ Performance monitoring started")
            
        except Exception as e:
            logger.error(f"Performance monitoring start failed: {e}")
            self.monitoring_active = False

    async def stop(self):
        """Stop performance monitoring"""
        if not self.monitoring_active:
            return
        
        try:
            self.monitoring_active = False
            
            # Cancel monitoring tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
                
            if self.analysis_task:
                self.analysis_task.cancel()
            
            # Record stop in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="monitoring",
                    content="Performance monitoring stopped",
                    tags=["monitoring", "stop", "performance"]
                )
            
            logger.info("✓ Performance monitoring stopped")
            
        except Exception as e:
            logger.error(f"Performance monitoring stop failed: {e}")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect all metrics
                await self._collect_all_metrics()
                
                # Update Prometheus metrics
                if PROMETHEUS_AVAILABLE and self.prometheus_metrics:
                    await self._update_prometheus_metrics()
                
                # Check alert conditions
                await self._check_alert_conditions()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _analysis_loop(self):
        """Analysis and learning loop (runs less frequently)"""
        analysis_interval = 300  # 5 minutes
        
        while self.monitoring_active:
            try:
                # Update performance baselines
                await self._update_performance_baselines()
                
                # Detect anomalies
                await self._detect_performance_anomalies()
                
                # Generate performance insights
                await self._generate_performance_insights()
                
                # Wait for next analysis
                await asyncio.sleep(analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                await asyncio.sleep(analysis_interval)

    async def _collect_all_metrics(self):
        """Collect all configured metrics"""
        try:
            current_metrics = {}
            
            for metric_id, metric_config in self.metrics_store.items():
                try:
                    collector = metric_config["collector"]
                    metric_data = await collector()
                    
                    if metric_data:
                        current_metrics[metric_id] = metric_data
                        
                        # Store in history
                        metric_config["history"].append({
                            "timestamp": datetime.now().isoformat(),
                            "data": metric_data
                        })
                        
                        # Limit history size
                        max_history = int(self.history_retention_hours * 3600 / self.collection_interval)
                        if len(metric_config["history"]) > max_history:
                            metric_config["history"] = metric_config["history"][-max_history:]
                
                except Exception as e:
                    logger.error(f"Metric collection failed for {metric_id}: {e}")
            
            # Store current metrics
            self.performance_history.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": current_metrics
            })
            
            # Limit performance history
            max_history = int(self.history_retention_hours * 3600 / self.collection_interval)
            if len(self.performance_history) > max_history:
                self.performance_history = self.performance_history[-max_history:]
                
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")

    async def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CPU metrics collection failed: {e}")
            return {}

    async def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        try:
            memory = psutil.virtual_memory()
            
            return {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory metrics collection failed: {e}")
            return {}

    async def _collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk metrics"""
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Disk metrics collection failed: {e}")
            return {}

    async def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network metrics"""
        try:
            net_io = psutil.net_io_counters()
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Network metrics collection failed: {e}")
            return {}

    async def _collect_ltm_response_times(self) -> Dict[str, Any]:
        """Collect LTM response time metrics"""
        try:
            if not self.ltm_client:
                return {}
            
            # Get LTM session stats
            stats = await self.ltm_client.get_session_stats()
            
            return {
                "session_id": stats.get("session_id"),
                "mode": stats.get("mode", "unknown"),
                "conversation_active": stats.get("conversation_active", False),
                "local_memory_count": stats.get("local_memory_count", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LTM response time collection failed: {e}")
            return {}

    async def _collect_ltm_session_stats(self) -> Dict[str, Any]:
        """Collect LTM session statistics"""
        try:
            if not self.ltm_client:
                return {}
            
            stats = await self.ltm_client.get_session_stats()
            
            return {
                "active_sessions": 1 if stats.get("conversation_active") else 0,
                "memory_entries": stats.get("local_memory_count", 0),
                "session_mode": stats.get("mode", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LTM session stats collection failed: {e}")
            return {}

    async def _update_prometheus_metrics(self):
        """Update Prometheus metrics with current values"""
        try:
            if not PROMETHEUS_AVAILABLE or not self.prometheus_metrics:
                return
                
            # Get latest metrics
            if not self.performance_history:
                return
                
            latest_metrics = self.performance_history[-1]["metrics"]
            
            # Update system metrics
            if "system_cpu" in latest_metrics:
                cpu_data = latest_metrics["system_cpu"]
                self.prometheus_metrics["system_cpu_percent"].set(cpu_data.get("cpu_percent", 0))
            
            if "system_memory" in latest_metrics:
                memory_data = latest_metrics["system_memory"]
                self.prometheus_metrics["system_memory_percent"].set(memory_data.get("percent", 0))
            
            if "system_disk" in latest_metrics:
                disk_data = latest_metrics["system_disk"]
                self.prometheus_metrics["system_disk_percent"].set(disk_data.get("percent", 0))
            
            # Update LTM metrics
            if "ltm_session_stats" in latest_metrics:
                ltm_data = latest_metrics["ltm_session_stats"]
                self.prometheus_metrics["ltm_session_count"].set(ltm_data.get("active_sessions", 0))
            
            # Update alert metrics
            for severity in AlertSeverity:
                alert_count = len([alert for alert in self.active_alerts.values() 
                                 if alert.severity == severity and not alert.resolved])
                self.prometheus_metrics["active_alerts"].labels(severity=severity.value).set(alert_count)
                
        except Exception as e:
            logger.error(f"Prometheus metrics update failed: {e}")

    async def _check_alert_conditions(self):
        """Check all alert conditions and trigger alerts if necessary"""
        try:
            if not self.performance_history:
                return
                
            latest_metrics = self.performance_history[-1]["metrics"]
            
            for rule_id, rule_config in self.alert_rules.items():
                try:
                    metric_name = rule_config["metric"]
                    condition = rule_config["condition"]
                    threshold = rule_config["threshold"]
                    severity = rule_config["severity"]
                    message = rule_config["message"]
                    
                    # Check if metric data is available
                    if metric_name not in latest_metrics:
                        continue
                    
                    metric_data = latest_metrics[metric_name]
                    triggered = False
                    current_value = None
                    
                    # Evaluate condition
                    if condition == "greater_than":
                        if metric_name == "system_cpu":
                            current_value = metric_data.get("cpu_percent", 0)
                        elif metric_name == "system_memory":
                            current_value = metric_data.get("percent", 0)
                        elif metric_name == "system_disk":
                            current_value = metric_data.get("percent", 0)
                        
                        if current_value is not None and current_value > threshold:
                            triggered = True
                    
                    elif condition == "anomaly_detected":
                        # Anomaly detection logic
                        anomaly_detected = await self._check_for_anomaly(metric_name)
                        if anomaly_detected:
                            triggered = True
                            current_value = "anomaly"
                    
                    # Handle alert
                    if triggered:
                        await self._trigger_alert(rule_id, metric_name, severity, threshold, current_value, message)
                    else:
                        # Check if we should resolve existing alert
                        await self._resolve_alert(rule_id)
                
                except Exception as e:
                    logger.error(f"Alert condition check failed for {rule_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Alert conditions check failed: {e}")

    async def _trigger_alert(self, rule_id: str, metric_name: str, severity: AlertSeverity, 
                           threshold: float, current_value: Any, message: str):
        """Trigger a performance alert"""
        try:
            # Check if alert is already active
            if rule_id in self.active_alerts and not self.active_alerts[rule_id].resolved:
                return  # Alert already active
            
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                metric_name=metric_name,
                severity=severity,
                threshold_value=threshold,
                current_value=current_value,
                message=message,
                timestamp=datetime.now().isoformat()
            )
            
            self.active_alerts[rule_id] = alert
            
            # Log alert
            logger.warning(f"Performance Alert: {message} (Current: {current_value}, Threshold: {threshold})")
            
            # Record in LTM for learning
            if self.ltm_client and self.config.get("alerting", {}).get("ltm_learning", True):
                await self.ltm_client.record_message(
                    role="monitoring",
                    content=f"Performance alert triggered: {message}. Current value: {current_value}, Threshold: {threshold}",
                    tags=["alert", "performance", severity.value, metric_name],
                    metadata=asdict(alert)
                )
            
        except Exception as e:
            logger.error(f"Alert triggering failed: {e}")

    async def _resolve_alert(self, rule_id: str):
        """Resolve a performance alert if conditions are no longer met"""
        try:
            if rule_id in self.active_alerts and not self.active_alerts[rule_id].resolved:
                alert = self.active_alerts[rule_id]
                alert.resolved = True
                alert.resolution_timestamp = datetime.now().isoformat()
                
                logger.info(f"Performance Alert Resolved: {alert.message}")
                
                # Record resolution in LTM
                if self.ltm_client:
                    await self.ltm_client.record_message(
                        role="monitoring",
                        content=f"Performance alert resolved: {alert.message}",
                        tags=["alert_resolved", "performance", alert.severity.value],
                        metadata={"alert_id": alert.alert_id, "duration": "calculated"}
                    )
                    
        except Exception as e:
            logger.error(f"Alert resolution failed: {e}")

    async def _update_performance_baselines(self):
        """Update performance baselines for anomaly detection"""
        try:
            min_samples = self.config.get("anomaly_detection", {}).get("minimum_samples", 30)
            
            for metric_name, baseline in self.performance_baselines.items():
                if metric_name in self.metrics_store:
                    metric_history = self.metrics_store[metric_name]["history"]
                    
                    if len(metric_history) < min_samples:
                        continue
                    
                    # Extract values for baseline calculation
                    values = []
                    for entry in metric_history[-100:]:  # Use last 100 samples
                        data = entry["data"]
                        
                        if metric_name == "system_cpu":
                            values.append(data.get("cpu_percent", 0))
                        elif metric_name == "system_memory":
                            values.append(data.get("percent", 0))
                        elif metric_name == "system_disk":
                            values.append(data.get("percent", 0))
                    
                    if values and len(values) >= min_samples:
                        baseline["mean"] = statistics.mean(values)
                        baseline["std"] = statistics.stdev(values) if len(values) > 1 else 0
                        baseline["samples"] = values[-50:]  # Keep last 50 samples
                        
        except Exception as e:
            logger.error(f"Performance baselines update failed: {e}")

    async def _check_for_anomaly(self, metric_name: str) -> bool:
        """Check if current metric value is anomalous"""
        try:
            if metric_name not in self.performance_baselines:
                return False
                
            baseline = self.performance_baselines[metric_name]
            if baseline["std"] == 0 or len(baseline["samples"]) < 10:
                return False
                
            # Get current value
            if not self.performance_history:
                return False
                
            latest_metrics = self.performance_history[-1]["metrics"]
            if metric_name not in latest_metrics:
                return False
                
            current_data = latest_metrics[metric_name]
            
            if metric_name == "system_cpu":
                current_value = current_data.get("cpu_percent", 0)
            elif metric_name == "system_memory":
                current_value = current_data.get("percent", 0)
            elif metric_name == "system_disk":
                current_value = current_data.get("percent", 0)
            else:
                return False
            
            # Check if value is outside threshold
            z_score = abs(current_value - baseline["mean"]) / baseline["std"]
            return z_score > self.anomaly_threshold
            
        except Exception as e:
            logger.error(f"Anomaly detection failed for {metric_name}: {e}")
            return False

    async def _detect_performance_anomalies(self):
        """Detect performance anomalies across all metrics"""
        try:
            anomalies_detected = []
            
            for metric_name in self.performance_baselines.keys():
                if await self._check_for_anomaly(metric_name):
                    anomalies_detected.append(metric_name)
            
            if anomalies_detected and self.ltm_client:
                await self.ltm_client.record_message(
                    role="monitoring",
                    content=f"Performance anomalies detected in metrics: {', '.join(anomalies_detected)}",
                    tags=["anomaly_detection", "performance", "analysis"],
                    metadata={"anomalous_metrics": anomalies_detected}
                )
                
        except Exception as e:
            logger.error(f"Performance anomaly detection failed: {e}")

    async def _generate_performance_insights(self):
        """Generate performance insights and trends"""
        try:
            if len(self.performance_history) < 10:
                return
            
            insights = []
            
            # Analyze trends over last hour
            recent_data = self.performance_history[-60:]  # Last hour if 1min intervals
            
            if recent_data:
                # CPU trend analysis
                cpu_values = [entry["metrics"].get("system_cpu", {}).get("cpu_percent", 0) 
                            for entry in recent_data if "system_cpu" in entry["metrics"]]
                
                if len(cpu_values) >= 5:
                    if NUMPY_AVAILABLE:
                        trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]
                    else:
                        # Simple trend calculation
                        trend = (cpu_values[-1] - cpu_values[0]) / len(cpu_values)
                    
                    if trend > 1.0:
                        insights.append("CPU usage is trending upward")
                    elif trend < -1.0:
                        insights.append("CPU usage is trending downward")
                
                # Memory trend analysis
                memory_values = [entry["metrics"].get("system_memory", {}).get("percent", 0)
                               for entry in recent_data if "system_memory" in entry["metrics"]]
                
                if len(memory_values) >= 5:
                    if NUMPY_AVAILABLE:
                        trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0]
                    else:
                        trend = (memory_values[-1] - memory_values[0]) / len(memory_values)
                    
                    if trend > 0.5:
                        insights.append("Memory usage is steadily increasing")
                    elif trend < -0.5:
                        insights.append("Memory usage is decreasing")
            
            # Record insights in LTM
            if insights and self.ltm_client:
                await self.ltm_client.record_message(
                    role="monitoring",
                    content=f"Performance insights generated: {'; '.join(insights)}",
                    tags=["performance_insights", "trends", "analysis"],
                    metadata={"insights": insights, "analysis_window": "1_hour"}
                )
                
        except Exception as e:
            logger.error(f"Performance insights generation failed: {e}")

    async def _cleanup_old_data(self):
        """Clean up old performance data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
            
            # Clean up performance history
            self.performance_history = [
                entry for entry in self.performance_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
            
            # Clean up metric histories
            for metric_config in self.metrics_store.values():
                metric_config["history"] = [
                    entry for entry in metric_config["history"]
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
                ]
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Generate performance dashboard data"""
        try:
            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": self.monitoring_active,
                "collection_interval": self.collection_interval,
                "current_metrics": {},
                "system_health": {},
                "ltm_performance": {},
                "alert_summary": {},
                "performance_trends": {}
            }
            
            # Current metrics
            if self.performance_history:
                latest = self.performance_history[-1]
                dashboard["current_metrics"] = latest["metrics"]
            
            # System health calculation
            if dashboard["current_metrics"]:
                cpu_percent = dashboard["current_metrics"].get("system_cpu", {}).get("cpu_percent", 0)
                memory_percent = dashboard["current_metrics"].get("system_memory", {}).get("percent", 0)
                disk_percent = dashboard["current_metrics"].get("system_disk", {}).get("percent", 0)
                
                health_score = 100
                health_factors = []
                
                if cpu_percent > 80:
                    health_score -= 20
                    health_factors.append("high_cpu")
                if memory_percent > 85:
                    health_score -= 25
                    health_factors.append("high_memory")
                if disk_percent > 85:
                    health_score -= 15
                    health_factors.append("high_disk")
                
                dashboard["system_health"] = {
                    "score": max(0, health_score),
                    "status": "excellent" if health_score > 90 else "good" if health_score > 70 else "fair" if health_score > 50 else "poor",
                    "factors": health_factors
                }
            
            # LTM performance
            if "ltm_session_stats" in dashboard["current_metrics"]:
                ltm_stats = dashboard["current_metrics"]["ltm_session_stats"]
                dashboard["ltm_performance"] = {
                    "active_sessions": ltm_stats.get("active_sessions", 0),
                    "memory_entries": ltm_stats.get("memory_entries", 0),
                    "session_mode": ltm_stats.get("session_mode", "unknown")
                }
            
            # Alert summary
            active_alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
            dashboard["alert_summary"] = {
                "total_active": len(active_alerts),
                "by_severity": {
                    "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                    "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
                    "medium": len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
                    "low": len([a for a in active_alerts if a.severity == AlertSeverity.LOW])
                }
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Performance dashboard generation failed: {e}")
            return {"error": str(e)}

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "collection_interval": self.collection_interval,
            "metrics_configured": len(self.metrics_store),
            "alert_rules_configured": len(self.alert_rules),
            "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
            "prometheus_enabled": PROMETHEUS_AVAILABLE and self.prometheus_metrics,
            "history_entries": len(self.performance_history)
        }