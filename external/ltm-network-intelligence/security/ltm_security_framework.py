# security/ltm_security_framework.py
# Comprehensive Security Framework with LTM integration

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import hashlib
import secrets
import base64
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Cryptography imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("Cryptography library not available - install with: pip install cryptography")

# Database for audit logging
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("AsyncPG not available - install with: pip install asyncpg")

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_INCIDENT = "security_incident"
    POLICY_VIOLATION = "policy_violation"
    SYSTEM_EVENT = "system_event"
    COMPLIANCE_CHECK = "compliance_check"

class ComplianceStandard(Enum):
    """Supported compliance standards"""
    SOX = "sox"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    NIST = "nist"

@dataclass
class SecurityEvent:
    """Security event structure"""
    event_id: str
    event_type: SecurityEventType
    timestamp: str
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    resource_accessed: Optional[str]
    action_attempted: str
    success: bool
    risk_level: str  # low, medium, high, critical
    details: Dict[str, Any]
    compliance_tags: List[ComplianceStandard] = None
    
    def __post_init__(self):
        if self.compliance_tags is None:
            self.compliance_tags = []

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str
    standard: ComplianceStandard
    rule_name: str
    description: str
    severity: str
    check_function: str
    parameters: Dict[str, Any]
    enabled: bool = True
    
@dataclass
class SecurityAlert:
    """Security alert structure"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    timestamp: str
    affected_systems: List[str]
    indicators: Dict[str, Any]
    recommended_actions: List[str]
    false_positive_probability: float = 0.0

class LTMSecurityManager:
    """Comprehensive security manager with LTM integration"""
    
    def __init__(self, config_path: str = "security/security_config.json"):
        self.config_path = config_path
        self.config = {}
        self.ltm_client = None
        
        # Security components
        self.encryption_key = None
        self.audit_db_pool = None
        self.compliance_rules = {}
        self.threat_detection_models = {}
        
        # State tracking
        self.initialized = False
        self.encryption_enabled = False
        self.audit_logging_enabled = False
        self.active_sessions = {}
        
    async def initialize(self, ltm_client) -> Dict[str, Any]:
        """Initialize security manager with LTM integration"""
        self.ltm_client = ltm_client
        
        initialization_result = {
            "component": "LTM Security Manager",
            "timestamp": datetime.now().isoformat(),
            "encryption_status": "disabled",
            "audit_logging_status": "disabled",
            "compliance_rules_loaded": 0,
            "threat_models_loaded": 0,
            "overall_status": "failed"
        }
        
        try:
            # Load configuration
            await self._load_security_config()
            
            # Initialize encryption
            if self.config.get("encryption_enabled", True) and CRYPTOGRAPHY_AVAILABLE:
                encryption_result = await self._initialize_encryption()
                initialization_result["encryption_status"] = encryption_result["status"]
                self.encryption_enabled = encryption_result["success"]
            
            # Initialize audit logging
            if self.config.get("audit_logging", True):
                audit_result = await self._initialize_audit_logging()
                initialization_result["audit_logging_status"] = audit_result["status"]
                self.audit_logging_enabled = audit_result["success"]
            
            # Load compliance rules
            compliance_result = await self._load_compliance_rules()
            initialization_result["compliance_rules_loaded"] = compliance_result["rules_loaded"]
            
            # Initialize threat detection
            threat_result = await self._initialize_threat_detection()
            initialization_result["threat_models_loaded"] = threat_result["models_loaded"]
            
            # Set overall status
            if self.encryption_enabled or self.audit_logging_enabled:
                initialization_result["overall_status"] = "partial_success"
                self.initialized = True
                
                if self.encryption_enabled and self.audit_logging_enabled:
                    initialization_result["overall_status"] = "success"
            
            # Record initialization in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Security Manager initialized: {initialization_result['overall_status']}, encryption: {self.encryption_enabled}, audit: {self.audit_logging_enabled}",
                    tags=["security", "initialization", "compliance"],
                    metadata=initialization_result
                )
            
            logger.info(f"Security Manager initialization: {initialization_result['overall_status']}")
            return initialization_result
            
        except Exception as e:
            logger.error(f"Security Manager initialization failed: {e}")
            initialization_result["error"] = str(e)
            return initialization_result

    async def _load_security_config(self):
        """Load security configuration"""
        try:
            import os
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default security configuration
                self.config = {
                    "encryption_enabled": True,
                    "audit_logging": True,
                    "compliance_standards": ["PCI_DSS", "ISO27001", "GDPR"],
                    "password_policy": {
                        "min_length": 12,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_numbers": True,
                        "require_symbols": True,
                        "max_age_days": 90
                    },
                    "session_management": {
                        "timeout_minutes": 30,
                        "concurrent_sessions_limit": 3,
                        "require_2fa": True
                    },
                    "threat_detection": {
                        "enabled": True,
                        "anomaly_threshold": 0.8,
                        "learning_enabled": True
                    },
                    "audit_db_config": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "ltm_audit",
                        "user": "audit_user",
                        "password": "secure_audit_password"
                    },
                    "compliance_monitoring": {
                        "real_time_checks": True,
                        "daily_reports": True,
                        "alert_on_violations": True
                    }
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Security config loading failed: {e}")
            self.config = {}

    async def _initialize_encryption(self) -> Dict[str, Any]:
        """Initialize encryption capabilities"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {"success": False, "status": "cryptography_unavailable"}
            
            # Generate or load encryption key
            key_file = "security/encryption.key"
            import os
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                # Generate new encryption key
                self.encryption_key = Fernet.generate_key()
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                os.chmod(key_file, 0o600)  # Restrict access
            
            # Test encryption
            fernet = Fernet(self.encryption_key)
            test_message = b"LTM Security Test"
            encrypted = fernet.encrypt(test_message)
            decrypted = fernet.decrypt(encrypted)
            
            if decrypted == test_message:
                logger.info("✓ Encryption initialized successfully")
                return {"success": True, "status": "enabled"}
            else:
                return {"success": False, "status": "encryption_test_failed"}
                
        except Exception as e:
            logger.error(f"Encryption initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    async def _initialize_audit_logging(self) -> Dict[str, Any]:
        """Initialize audit logging database"""
        try:
            if not ASYNCPG_AVAILABLE:
                logger.info("Using file-based audit logging fallback")
                return {"success": True, "status": "file_fallback"}
            
            # Connect to audit database
            db_config = self.config.get("audit_db_config", {})
            connection_string = f"postgresql://{db_config.get('user', 'audit_user')}:{db_config.get('password', 'password')}@{db_config.get('host', 'localhost')}:{db_config.get('port', 5432)}/{db_config.get('database', 'ltm_audit')}"
            
            try:
                self.audit_db_pool = await asyncpg.create_pool(connection_string)
                
                # Create audit tables if they don't exist
                await self._create_audit_tables()
                
                logger.info("✓ Audit logging database initialized")
                return {"success": True, "status": "database_enabled"}
                
            except Exception as db_error:
                logger.warning(f"Database audit logging failed, using file fallback: {db_error}")
                return {"success": True, "status": "file_fallback"}
                
        except Exception as e:
            logger.error(f"Audit logging initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    async def _create_audit_tables(self):
        """Create audit logging tables"""
        if not self.audit_db_pool:
            return
            
        async with self.audit_db_pool.acquire() as conn:
            # Security events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id VARCHAR(100) PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    user_id VARCHAR(100),
                    session_id VARCHAR(100),
                    source_ip INET,
                    resource_accessed TEXT,
                    action_attempted TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    details JSONB,
                    compliance_tags VARCHAR(50)[],
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Compliance violations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    violation_id VARCHAR(100) PRIMARY KEY,
                    rule_id VARCHAR(100) NOT NULL,
                    standard VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    affected_systems TEXT[],
                    violation_details JSONB,
                    remediation_status VARCHAR(50) DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Security alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id VARCHAR(100) PRIMARY KEY,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    affected_systems TEXT[],
                    indicators JSONB,
                    recommended_actions TEXT[],
                    status VARCHAR(50) DEFAULT 'open',
                    false_positive_probability DECIMAL(3,2) DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_violations_standard ON compliance_violations(standard)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity)")

    async def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules for different standards"""
        rules_loaded = 0
        
        try:
            # PCI DSS Rules
            pci_rules = [
                ComplianceRule(
                    rule_id="pci_001",
                    standard=ComplianceStandard.PCI_DSS,
                    rule_name="Password Complexity",
                    description="Passwords must meet complexity requirements",
                    severity="high",
                    check_function="check_password_complexity",
                    parameters={"min_length": 8, "require_mixed_case": True}
                ),
                ComplianceRule(
                    rule_id="pci_002",
                    standard=ComplianceStandard.PCI_DSS,
                    rule_name="Data Encryption at Rest",
                    description="Sensitive data must be encrypted when stored",
                    severity="critical",
                    check_function="check_encryption_at_rest",
                    parameters={"required_algorithms": ["AES-256"]}
                ),
                ComplianceRule(
                    rule_id="pci_003",
                    standard=ComplianceStandard.PCI_DSS,
                    rule_name="Access Logging",
                    description="All access to cardholder data must be logged",
                    severity="high",
                    check_function="check_access_logging",
                    parameters={"log_retention_days": 365}
                )
            ]
            
            # ISO 27001 Rules
            iso_rules = [
                ComplianceRule(
                    rule_id="iso_001",
                    standard=ComplianceStandard.ISO27001,
                    rule_name="Information Security Policy",
                    description="Information security policy must be defined and implemented",
                    severity="high",
                    check_function="check_security_policy",
                    parameters={"policy_review_frequency": 365}
                ),
                ComplianceRule(
                    rule_id="iso_002", 
                    standard=ComplianceStandard.ISO27001,
                    rule_name="Asset Management",
                    description="All information assets must be inventoried and classified",
                    severity="medium",
                    check_function="check_asset_management",
                    parameters={"classification_required": True}
                )
            ]
            
            # GDPR Rules
            gdpr_rules = [
                ComplianceRule(
                    rule_id="gdpr_001",
                    standard=ComplianceStandard.GDPR,
                    rule_name="Data Protection by Design",
                    description="Privacy protection must be built into system design",
                    severity="high",
                    check_function="check_privacy_by_design",
                    parameters={"privacy_impact_assessment": True}
                ),
                ComplianceRule(
                    rule_id="gdpr_002",
                    standard=ComplianceStandard.GDPR,
                    rule_name="Data Breach Notification",
                    description="Data breaches must be reported within 72 hours",
                    severity="critical",
                    check_function="check_breach_notification",
                    parameters={"notification_deadline_hours": 72}
                )
            ]
            
            # Store all rules
            all_rules = pci_rules + iso_rules + gdpr_rules
            for rule in all_rules:
                self.compliance_rules[rule.rule_id] = rule
                rules_loaded += 1
                
            logger.info(f"✓ Loaded {rules_loaded} compliance rules")
            
        except Exception as e:
            logger.error(f"Compliance rules loading failed: {e}")
        
        return {"rules_loaded": rules_loaded}

    async def _initialize_threat_detection(self) -> Dict[str, Any]:
        """Initialize threat detection models"""
        models_loaded = 0
        
        try:
            # Simple anomaly detection model (placeholder for ML models)
            self.threat_detection_models = {
                "login_anomaly": {
                    "type": "statistical",
                    "baseline_threshold": 3.0,  # Standard deviations
                    "learning_enabled": True,
                    "detection_confidence": 0.85
                },
                "data_access_pattern": {
                    "type": "pattern_matching",
                    "suspicious_patterns": [
                        "bulk_data_access",
                        "unusual_time_access",
                        "privilege_escalation"
                    ],
                    "detection_confidence": 0.75
                },
                "configuration_tampering": {
                    "type": "rule_based",
                    "critical_configs": [
                        "security_policies",
                        "user_permissions",
                        "network_settings"
                    ],
                    "detection_confidence": 0.90
                }
            }
            
            models_loaded = len(self.threat_detection_models)
            logger.info(f"✓ Initialized {models_loaded} threat detection models")
            
        except Exception as e:
            logger.error(f"Threat detection initialization failed: {e}")
        
        return {"models_loaded": models_loaded}

    async def log_security_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """Log security event with compliance tagging"""
        try:
            log_result = {
                "event_id": event.event_id,
                "logged": False,
                "database_logged": False,
                "file_logged": False,
                "ltm_recorded": False
            }
            
            # Log to database if available
            if self.audit_db_pool:
                try:
                    async with self.audit_db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO security_events 
                            (event_id, event_type, timestamp, user_id, session_id, source_ip, 
                             resource_accessed, action_attempted, success, risk_level, details, compliance_tags)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        """, 
                        event.event_id, event.event_type.value, event.timestamp, event.user_id,
                        event.session_id, event.source_ip, event.resource_accessed, 
                        event.action_attempted, event.success, event.risk_level,
                        json.dumps(event.details), [s.value for s in event.compliance_tags]
                        )
                        
                    log_result["database_logged"] = True
                    
                except Exception as db_error:
                    logger.warning(f"Database logging failed: {db_error}")
                    
            # Fallback to file logging
            if not log_result["database_logged"]:
                try:
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "event": asdict(event)
                    }
                    
                    import os
                    os.makedirs("logs", exist_ok=True)
                    with open(f"logs/security_audit.log", 'a') as f:
                        f.write(json.dumps(log_entry) + "\n")
                        
                    log_result["file_logged"] = True
                    
                except Exception as file_error:
                    logger.error(f"File logging failed: {file_error}")
            
            # Record in LTM for learning
            if self.ltm_client:
                try:
                    ltm_content = f"Security event: {event.action_attempted} - {event.event_type.value} - {'Success' if event.success else 'Failed'} - Risk: {event.risk_level}"
                    
                    await self.ltm_client.record_message(
                        role="security",
                        content=ltm_content,
                        tags=["security_event", event.event_type.value, event.risk_level] + [s.value for s in event.compliance_tags],
                        metadata={
                            "event_id": event.event_id,
                            "success": event.success,
                            "risk_level": event.risk_level,
                            "user_id": event.user_id
                        }
                    )
                    
                    log_result["ltm_recorded"] = True
                    
                except Exception as ltm_error:
                    logger.warning(f"LTM logging failed: {ltm_error}")
            
            log_result["logged"] = log_result["database_logged"] or log_result["file_logged"]
            
            # Check for threat patterns
            if event.risk_level in ["high", "critical"]:
                await self._analyze_threat_patterns(event)
            
            return log_result
            
        except Exception as e:
            logger.error(f"Security event logging failed: {e}")
            return {"event_id": event.event_id, "logged": False, "error": str(e)}

    async def _analyze_threat_patterns(self, event: SecurityEvent):
        """Analyze security event for threat patterns"""
        try:
            # Simple threat detection logic
            threats_detected = []
            
            # Check for repeated failed login attempts
            if event.event_type == SecurityEventType.AUTHENTICATION and not event.success:
                # In a real implementation, this would query recent events
                threats_detected.append({
                    "threat_type": "brute_force_attempt",
                    "confidence": 0.7,
                    "description": "Repeated authentication failures detected"
                })
            
            # Check for privilege escalation attempts
            if "admin" in event.action_attempted.lower() or "privilege" in event.action_attempted.lower():
                threats_detected.append({
                    "threat_type": "privilege_escalation",
                    "confidence": 0.8,
                    "description": "Potential privilege escalation attempt"
                })
            
            # Check for unusual data access patterns
            if event.event_type == SecurityEventType.DATA_ACCESS and event.risk_level == "high":
                threats_detected.append({
                    "threat_type": "data_exfiltration",
                    "confidence": 0.6,
                    "description": "Unusual data access pattern detected"
                })
            
            # Generate security alerts for detected threats
            for threat in threats_detected:
                if threat["confidence"] > 0.7:
                    alert = SecurityAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type=threat["threat_type"],
                        severity="high" if threat["confidence"] > 0.8 else "medium",
                        title=f"Threat Detected: {threat['threat_type']}",
                        description=threat["description"],
                        timestamp=datetime.now().isoformat(),
                        affected_systems=[event.resource_accessed] if event.resource_accessed else [],
                        indicators={
                            "user_id": event.user_id,
                            "source_ip": event.source_ip,
                            "confidence": threat["confidence"]
                        },
                        recommended_actions=[
                            "Investigate user activity",
                            "Review access logs",
                            "Consider blocking source IP if necessary"
                        ],
                        false_positive_probability=1.0 - threat["confidence"]
                    )
                    
                    await self._create_security_alert(alert)
                    
        except Exception as e:
            logger.error(f"Threat pattern analysis failed: {e}")

    async def _create_security_alert(self, alert: SecurityAlert):
        """Create and store security alert"""
        try:
            # Store in database if available
            if self.audit_db_pool:
                async with self.audit_db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO security_alerts 
                        (alert_id, alert_type, severity, title, description, timestamp,
                         affected_systems, indicators, recommended_actions, false_positive_probability)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    alert.alert_id, alert.alert_type, alert.severity, alert.title,
                    alert.description, alert.timestamp, alert.affected_systems,
                    json.dumps(alert.indicators), alert.recommended_actions,
                    alert.false_positive_probability
                    )
            
            # Record in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="security",
                    content=f"Security alert generated: {alert.title} - Severity: {alert.severity}",
                    tags=["security_alert", alert.alert_type, alert.severity],
                    metadata=asdict(alert)
                )
                
            logger.warning(f"Security Alert Generated: {alert.title} (Severity: {alert.severity})")
            
        except Exception as e:
            logger.error(f"Security alert creation failed: {e}")

    async def check_compliance(self, standard: ComplianceStandard, check_scope: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform compliance check for specified standard"""
        try:
            compliance_result = {
                "standard": standard.value,
                "timestamp": datetime.now().isoformat(),
                "checks_performed": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "violations": [],
                "overall_compliance": "unknown"
            }
            
            # Get rules for the specified standard
            relevant_rules = [rule for rule in self.compliance_rules.values() if rule.standard == standard and rule.enabled]
            
            for rule in relevant_rules:
                check_result = await self._perform_compliance_check(rule, check_scope or {})
                compliance_result["checks_performed"] += 1
                
                if check_result["passed"]:
                    compliance_result["checks_passed"] += 1
                else:
                    compliance_result["checks_failed"] += 1
                    compliance_result["violations"].append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "severity": rule.severity,
                        "description": check_result.get("violation_description", rule.description),
                        "remediation_suggestions": check_result.get("remediation_suggestions", [])
                    })
            
            # Calculate overall compliance
            if compliance_result["checks_performed"] > 0:
                compliance_percentage = (compliance_result["checks_passed"] / compliance_result["checks_performed"]) * 100
                
                if compliance_percentage >= 95:
                    compliance_result["overall_compliance"] = "compliant"
                elif compliance_percentage >= 80:
                    compliance_result["overall_compliance"] = "mostly_compliant"
                elif compliance_percentage >= 60:
                    compliance_result["overall_compliance"] = "partially_compliant"
                else:
                    compliance_result["overall_compliance"] = "non_compliant"
                    
                compliance_result["compliance_percentage"] = compliance_percentage
            
            # Record compliance check in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="compliance",
                    content=f"Compliance check completed: {standard.value} - {compliance_result['overall_compliance']} ({compliance_result['checks_passed']}/{compliance_result['checks_performed']} checks passed)",
                    tags=["compliance_check", standard.value, compliance_result["overall_compliance"]],
                    metadata=compliance_result
                )
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return {"standard": standard.value, "error": str(e)}

    async def _perform_compliance_check(self, rule: ComplianceRule, scope: Dict[str, Any]) -> Dict[str, Any]:
        """Perform individual compliance rule check"""
        try:
            # This is a simplified implementation - real checks would be more complex
            check_result = {
                "rule_id": rule.rule_id,
                "passed": False,
                "violation_description": "",
                "remediation_suggestions": []
            }
            
            if rule.check_function == "check_password_complexity":
                # Mock password policy check
                min_length = rule.parameters.get("min_length", 8)
                # In real implementation, this would check actual password policies
                check_result["passed"] = True  # Assume compliant for demo
                
            elif rule.check_function == "check_encryption_at_rest":
                # Mock encryption check
                required_algs = rule.parameters.get("required_algorithms", [])
                # Check if encryption is enabled
                check_result["passed"] = self.encryption_enabled
                if not check_result["passed"]:
                    check_result["violation_description"] = "Data encryption at rest is not enabled"
                    check_result["remediation_suggestions"] = ["Enable encryption at rest", "Use AES-256 encryption"]
                    
            elif rule.check_function == "check_access_logging":
                # Mock access logging check
                check_result["passed"] = self.audit_logging_enabled
                if not check_result["passed"]:
                    check_result["violation_description"] = "Access logging is not properly configured"
                    check_result["remediation_suggestions"] = ["Enable audit logging", "Configure log retention"]
                    
            elif rule.check_function == "check_security_policy":
                # Mock security policy check
                check_result["passed"] = True  # Assume policy exists
                
            elif rule.check_function == "check_asset_management":
                # Mock asset management check
                check_result["passed"] = True  # Assume assets are managed
                
            elif rule.check_function == "check_privacy_by_design":
                # Mock privacy by design check
                check_result["passed"] = True  # Assume privacy controls exist
                
            elif rule.check_function == "check_breach_notification":
                # Mock breach notification check
                check_result["passed"] = True  # Assume notification procedures exist
                
            else:
                # Unknown check function
                check_result["passed"] = False
                check_result["violation_description"] = f"Unknown check function: {rule.check_function}"
            
            return check_result
            
        except Exception as e:
            logger.error(f"Individual compliance check failed: {e}")
            return {"rule_id": rule.rule_id, "passed": False, "error": str(e)}

    async def encrypt_sensitive_data(self, data: Union[str, bytes], context: str = "") -> Dict[str, Any]:
        """Encrypt sensitive data"""
        try:
            if not self.encryption_enabled or not CRYPTOGRAPHY_AVAILABLE:
                return {"success": False, "error": "Encryption not available"}
                
            fernet = Fernet(self.encryption_key)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            encrypted_data = fernet.encrypt(data)
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Log encryption event
            if context:
                event = SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SecurityEventType.DATA_ACCESS,
                    timestamp=datetime.now().isoformat(),
                    user_id="system",
                    session_id=None,
                    source_ip=None,
                    resource_accessed=context,
                    action_attempted="data_encryption",
                    success=True,
                    risk_level="low",
                    details={"operation": "encryption", "data_size": len(data)},
                    compliance_tags=[ComplianceStandard.PCI_DSS, ComplianceStandard.GDPR]
                )
                await self.log_security_event(event)
            
            return {
                "success": True,
                "encrypted_data": encrypted_b64,
                "encryption_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data encryption failed: {e}")
            return {"success": False, "error": str(e)}

    async def decrypt_sensitive_data(self, encrypted_data: str, context: str = "") -> Dict[str, Any]:
        """Decrypt sensitive data"""
        try:
            if not self.encryption_enabled or not CRYPTOGRAPHY_AVAILABLE:
                return {"success": False, "error": "Encryption not available"}
                
            fernet = Fernet(self.encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_data.decode('utf-8')
            
            # Log decryption event
            if context:
                event = SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SecurityEventType.DATA_ACCESS,
                    timestamp=datetime.now().isoformat(),
                    user_id="system",
                    session_id=None,
                    source_ip=None,
                    resource_accessed=context,
                    action_attempted="data_decryption",
                    success=True,
                    risk_level="medium",
                    details={"operation": "decryption"},
                    compliance_tags=[ComplianceStandard.PCI_DSS, ComplianceStandard.GDPR]
                )
                await self.log_security_event(event)
            
            return {
                "success": True,
                "decrypted_data": decrypted_str,
                "decryption_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data decryption failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_security_report(self, timeframe_hours: int = 24, standards: List[ComplianceStandard] = None) -> Dict[str, Any]:
        """Generate comprehensive security and compliance report"""
        try:
            report = {
                "report_type": "security_compliance",
                "timeframe_hours": timeframe_hours,
                "generation_timestamp": datetime.now().isoformat(),
                "executive_summary": {},
                "security_events": {},
                "compliance_status": {},
                "security_alerts": {},
                "recommendations": []
            }
            
            # Get security events summary
            if self.audit_db_pool:
                try:
                    async with self.audit_db_pool.acquire() as conn:
                        # Count security events by risk level
                        events_result = await conn.fetch("""
                            SELECT risk_level, COUNT(*) as count
                            FROM security_events 
                            WHERE timestamp > NOW() - INTERVAL '%s hours'
                            GROUP BY risk_level
                        """, timeframe_hours)
                        
                        report["security_events"] = {
                            "summary": dict(events_result),
                            "total_events": sum(dict(events_result).values())
                        }
                        
                        # Get security alerts summary  
                        alerts_result = await conn.fetch("""
                            SELECT severity, COUNT(*) as count
                            FROM security_alerts
                            WHERE timestamp > NOW() - INTERVAL '%s hours'
                            GROUP BY severity
                        """, timeframe_hours)
                        
                        report["security_alerts"] = {
                            "summary": dict(alerts_result),
                            "total_alerts": sum(dict(alerts_result).values())
                        }
                        
                except Exception as db_error:
                    logger.warning(f"Database query failed: {db_error}")
                    report["security_events"] = {"error": "Database unavailable"}
                    report["security_alerts"] = {"error": "Database unavailable"}
            
            # Perform compliance checks
            standards_to_check = standards or [ComplianceStandard.PCI_DSS, ComplianceStandard.ISO27001, ComplianceStandard.GDPR]
            
            compliance_results = {}
            for standard in standards_to_check:
                compliance_check = await self.check_compliance(standard)
                compliance_results[standard.value] = compliance_check
                
            report["compliance_status"] = compliance_results
            
            # Generate executive summary
            total_events = report["security_events"].get("total_events", 0)
            total_alerts = report["security_alerts"].get("total_alerts", 0)
            
            compliant_standards = len([r for r in compliance_results.values() if r.get("overall_compliance") == "compliant"])
            total_standards = len(compliance_results)
            
            report["executive_summary"] = {
                "security_posture": "good" if total_alerts < 5 else "fair" if total_alerts < 20 else "poor",
                "total_security_events": total_events,
                "total_security_alerts": total_alerts,
                "compliance_score": f"{compliant_standards}/{total_standards}",
                "overall_risk_level": "low" if total_alerts < 3 else "medium" if total_alerts < 10 else "high"
            }
            
            # Generate recommendations
            if total_alerts > 10:
                report["recommendations"].append({
                    "priority": "high",
                    "category": "threat_response",
                    "title": "High Alert Volume Detected",
                    "description": "Review and investigate security alerts to reduce false positives and address real threats"
                })
            
            non_compliant = [s for s, r in compliance_results.items() if r.get("overall_compliance") != "compliant"]
            if non_compliant:
                report["recommendations"].append({
                    "priority": "medium",
                    "category": "compliance",
                    "title": "Address Compliance Gaps",
                    "description": f"Work on compliance for: {', '.join(non_compliant)}"
                })
            
            # Record report generation in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="security",
                    content=f"Security report generated: {report['executive_summary']['overall_risk_level']} risk, {total_events} events, {total_alerts} alerts",
                    tags=["security_report", "compliance", report["executive_summary"]["overall_risk_level"]],
                    metadata=report["executive_summary"]
                )
            
            return report
            
        except Exception as e:
            logger.error(f"Security report generation failed: {e}")
            return {"error": str(e)}

    async def get_security_status(self) -> Dict[str, Any]:
        """Get current security manager status"""
        return {
            "initialized": self.initialized,
            "encryption_enabled": self.encryption_enabled,
            "audit_logging_enabled": self.audit_logging_enabled,
            "compliance_rules_count": len(self.compliance_rules),
            "threat_models_count": len(self.threat_detection_models),
            "active_sessions": len(self.active_sessions)
        }

    async def cleanup(self):
        """Cleanup security manager resources"""
        try:
            if self.audit_db_pool:
                await self.audit_db_pool.close()
                
            self.active_sessions.clear()
            logger.info("Security Manager cleaned up")
            
        except Exception as e:
            logger.error(f"Security Manager cleanup failed: {e}")