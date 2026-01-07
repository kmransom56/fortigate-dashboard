# api_gateway/ltm_api_gateway.py
# LTM-integrated API Gateway with authentication, rate limiting, and intelligent routing

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
import jwt
import hashlib
import time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Depends, Security, Request, Response, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available - install with: pip install fastapi uvicorn")

# Redis for caching and rate limiting
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - install with: pip install aioredis")

logger = logging.getLogger(__name__)

class APIEndpointType(Enum):
    """API endpoint types"""
    DEVICE_MANAGEMENT = "device_management"
    NETWORK_ANALYSIS = "network_analysis" 
    SECURITY_OPERATIONS = "security_operations"
    INTELLIGENCE_REPORTING = "intelligence_reporting"
    LTM_OPERATIONS = "ltm_operations"
    COMPLIANCE_MONITORING = "compliance_monitoring"

@dataclass
class APIRequest:
    """API request structure"""
    request_id: str
    endpoint: str
    method: str
    user_id: Optional[str]
    source_ip: str
    timestamp: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    authenticated: bool
    
@dataclass  
class APIResponse:
    """API response structure"""
    request_id: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    cached: bool
    ltm_enhanced: bool
    timestamp: str

@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    rule_id: str
    endpoint_pattern: str
    requests_per_minute: int
    requests_per_hour: int
    burst_allowance: int
    user_specific: bool = False

class LTMAPIGateway:
    """LTM-integrated API Gateway with intelligent request routing"""
    
    def __init__(self, config_path: str = "config/api_gateway_config.json"):
        self.config_path = config_path
        self.config = {}
        self.app = None
        self.ltm_client = None
        self.security_manager = None
        
        # Gateway state
        self.redis_client = None
        self.rate_limit_rules = {}
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
        # JWT configuration
        self.jwt_secret = "ltm-api-gateway-secret-key"
        self.jwt_algorithm = "HS256"
        self.token_expire_minutes = 60
        
        # Security
        self.security_bearer = HTTPBearer() if FASTAPI_AVAILABLE else None
        
    async def initialize(self, ltm_client, security_manager=None) -> Dict[str, Any]:
        """Initialize LTM API Gateway"""
        self.ltm_client = ltm_client
        self.security_manager = security_manager
        
        initialization_result = {
            "component": "LTM API Gateway",
            "timestamp": datetime.now().isoformat(),
            "fastapi_status": "unavailable",
            "redis_status": "unavailable", 
            "endpoints_registered": 0,
            "rate_limits_configured": 0,
            "overall_status": "failed"
        }
        
        try:
            # Load configuration
            await self._load_gateway_config()
            
            # Initialize FastAPI if available
            if FASTAPI_AVAILABLE:
                await self._initialize_fastapi()
                initialization_result["fastapi_status"] = "initialized"
                initialization_result["endpoints_registered"] = len(self.app.routes)
            
            # Initialize Redis for caching and rate limiting
            if REDIS_AVAILABLE:
                redis_result = await self._initialize_redis()
                initialization_result["redis_status"] = redis_result["status"]
            
            # Setup rate limiting rules
            await self._setup_rate_limiting()
            initialization_result["rate_limits_configured"] = len(self.rate_limit_rules)
            
            # Set overall status
            if FASTAPI_AVAILABLE:
                initialization_result["overall_status"] = "success"
                
                # Record initialization in LTM
                if self.ltm_client:
                    await self.ltm_client.record_message(
                        role="system",
                        content=f"API Gateway initialized successfully with {initialization_result['endpoints_registered']} endpoints and {initialization_result['rate_limits_configured']} rate limit rules",
                        tags=["api_gateway", "initialization", "success"],
                        metadata=initialization_result
                    )
            
            logger.info(f"API Gateway initialization: {initialization_result['overall_status']}")
            return initialization_result
            
        except Exception as e:
            logger.error(f"API Gateway initialization failed: {e}")
            initialization_result["error"] = str(e)
            return initialization_result

    async def _load_gateway_config(self):
        """Load API gateway configuration"""
        try:
            import os
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default configuration
                self.config = {
                    "server": {
                        "host": "0.0.0.0",
                        "port": 8002,
                        "workers": 4,
                        "reload": False
                    },
                    "cors": {
                        "allow_origins": ["http://localhost:3000", "https://dashboard.local"],
                        "allow_credentials": True,
                        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
                        "allow_headers": ["*"]
                    },
                    "rate_limiting": {
                        "enabled": True,
                        "default_rpm": 100,
                        "default_rph": 1000,
                        "burst_allowance": 10
                    },
                    "authentication": {
                        "jwt_enabled": True,
                        "require_auth": ["POST", "PUT", "DELETE"],
                        "token_expire_minutes": 60
                    },
                    "caching": {
                        "enabled": True,
                        "default_ttl": 300,
                        "redis_url": "redis://localhost:6379"
                    },
                    "ltm_integration": {
                        "learn_from_requests": True,
                        "intelligent_routing": True,
                        "request_analysis": True
                    }
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
            # Update JWT settings from config
            self.jwt_secret = self.config.get("authentication", {}).get("jwt_secret", self.jwt_secret)
            self.token_expire_minutes = self.config.get("authentication", {}).get("token_expire_minutes", 60)
                    
        except Exception as e:
            logger.error(f"Gateway config loading failed: {e}")
            self.config = {}

    async def _initialize_fastapi(self):
        """Initialize FastAPI application with LTM integration"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available")
            
        self.app = FastAPI(
            title="LTM Network Intelligence API Gateway",
            description="API Gateway with Long Term Memory integration for network intelligence",
            version="2.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Add CORS middleware
        cors_config = self.config.get("cors", {})
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.get("allow_origins", ["*"]),
            allow_credentials=cors_config.get("allow_credentials", True),
            allow_methods=cors_config.get("allow_methods", ["*"]),
            allow_headers=cors_config.get("allow_headers", ["*"])
        )
        
        # Add trusted host middleware
        self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
        
        # Add request/response middleware
        @self.app.middleware("http")
        async def ltm_request_middleware(request: Request, call_next):
            return await self._process_request_with_ltm(request, call_next)
        
        # Setup API endpoints
        await self._setup_api_endpoints()

    async def _initialize_redis(self) -> Dict[str, Any]:
        """Initialize Redis connection for caching and rate limiting"""
        try:
            redis_url = self.config.get("caching", {}).get("redis_url", "redis://localhost:6379")
            self.redis_client = await aioredis.from_url(redis_url)
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("✓ Redis connection established")
            return {"success": True, "status": "connected"}
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    async def _setup_rate_limiting(self):
        """Setup rate limiting rules"""
        try:
            rate_config = self.config.get("rate_limiting", {})
            default_rpm = rate_config.get("default_rpm", 100)
            default_rph = rate_config.get("default_rph", 1000)
            burst_allowance = rate_config.get("burst_allowance", 10)
            
            # Default rate limits
            self.rate_limit_rules = {
                "default": RateLimitRule(
                    rule_id="default",
                    endpoint_pattern="*",
                    requests_per_minute=default_rpm,
                    requests_per_hour=default_rph,
                    burst_allowance=burst_allowance
                ),
                "auth": RateLimitRule(
                    rule_id="auth",
                    endpoint_pattern="/api/auth/*",
                    requests_per_minute=20,
                    requests_per_hour=100,
                    burst_allowance=5,
                    user_specific=True
                ),
                "device_ops": RateLimitRule(
                    rule_id="device_ops",
                    endpoint_pattern="/api/devices/*",
                    requests_per_minute=200,
                    requests_per_hour=2000,
                    burst_allowance=20
                ),
                "intelligence": RateLimitRule(
                    rule_id="intelligence",
                    endpoint_pattern="/api/intelligence/*",
                    requests_per_minute=50,
                    requests_per_hour=500,
                    burst_allowance=10
                )
            }
            
        except Exception as e:
            logger.error(f"Rate limiting setup failed: {e}")

    async def _setup_api_endpoints(self):
        """Setup API endpoints with LTM integration"""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "ltm_connected": self.ltm_client is not None,
                "redis_connected": self.redis_client is not None
            }
        
        # Authentication endpoints
        @self.app.post("/api/auth/login")
        async def login(credentials: Dict[str, str]):
            return await self._handle_login(credentials)
        
        @self.app.post("/api/auth/refresh")
        async def refresh_token(current_user: Dict = Depends(self._get_current_user)):
            return await self._refresh_token(current_user)
        
        # Device management endpoints
        @self.app.get("/api/devices")
        async def get_devices(current_user: Dict = Depends(self._get_current_user_optional)):
            return await self._proxy_to_mcp("get_devices", {}, current_user)
        
        @self.app.get("/api/devices/{device_name}/status")
        async def get_device_status(device_name: str, current_user: Dict = Depends(self._get_current_user_optional)):
            return await self._proxy_to_mcp("get_device_status", {"device_name": device_name}, current_user)
        
        @self.app.post("/api/devices/{device_name}/command")
        async def execute_device_command(device_name: str, command_data: Dict[str, Any], current_user: Dict = Depends(self._get_current_user)):
            return await self._proxy_to_mcp("execute_network_command", {
                "device_name": device_name,
                **command_data
            }, current_user)
        
        # Network analysis endpoints
        @self.app.get("/api/analysis/health")
        async def network_health_analysis(scope: str = "all", current_user: Dict = Depends(self._get_current_user_optional)):
            return await self._proxy_to_mcp("analyze_network_health", {"scope": scope}, current_user)
        
        @self.app.get("/api/analysis/patterns")
        async def search_patterns(query: str, tags: str = "", current_user: Dict = Depends(self._get_current_user_optional)):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
            return await self._proxy_to_mcp("search_network_patterns", {
                "query": query,
                "tags": tag_list
            }, current_user)
        
        # Intelligence reporting endpoints
        @self.app.get("/api/intelligence/report")
        async def generate_intelligence_report(report_type: str = "executive", timeframe: int = 24, current_user: Dict = Depends(self._get_current_user)):
            return await self._proxy_to_mcp("generate_intelligence_report", {
                "report_type": report_type,
                "timeframe_hours": timeframe
            }, current_user)
        
        @self.app.get("/api/intelligence/predictions")
        async def get_predictions(prediction_type: str, device_name: str = None, forecast_hours: int = 24, current_user: Dict = Depends(self._get_current_user)):
            return await self._proxy_to_mcp("get_predictive_insights", {
                "prediction_type": prediction_type,
                "device_name": device_name,
                "forecast_hours": forecast_hours
            }, current_user)
        
        # LTM operations endpoints
        @self.app.get("/api/ltm/memories")
        async def search_ltm_memories(query: str, tags: str = "", limit: int = 10, current_user: Dict = Depends(self._get_current_user)):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
            
            if self.ltm_client:
                memories = await self.ltm_client.search_memories(query, tag_list, limit)
                return {
                    "query": query,
                    "memories": [
                        {
                            "content": m.content,
                            "timestamp": m.timestamp,
                            "relevance_score": m.relevance_score,
                            "tags": m.tags
                        } for m in memories
                    ]
                }
            else:
                raise HTTPException(status_code=503, detail="LTM not available")
        
        @self.app.get("/api/ltm/stats")
        async def get_ltm_stats(current_user: Dict = Depends(self._get_current_user)):
            if self.ltm_client:
                stats = await self.ltm_client.get_session_stats()
                return stats
            else:
                raise HTTPException(status_code=503, detail="LTM not available")
        
        # Gateway statistics endpoint
        @self.app.get("/api/gateway/stats")
        async def get_gateway_stats(current_user: Dict = Depends(self._get_current_user_optional)):
            return {
                "api_stats": self.api_stats,
                "rate_limits": {k: asdict(v) for k, v in self.rate_limit_rules.items()},
                "redis_connected": self.redis_client is not None,
                "ltm_connected": self.ltm_client is not None
            }

    async def _process_request_with_ltm(self, request: Request, call_next):
        """Process request with LTM learning and intelligent routing"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Extract request information
        api_request = APIRequest(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
            user_id=None,  # Will be set after authentication
            source_ip=request.client.host if request.client else "unknown",
            timestamp=datetime.now().isoformat(),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            body=None,  # Will be processed if needed
            authenticated=False
        )
        
        # Check rate limits
        rate_limit_result = await self._check_rate_limits(api_request)
        if not rate_limit_result["allowed"]:
            response = JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": rate_limit_result.get("retry_after", 60)}
            )
            await self._log_api_request(api_request, APIResponse(
                request_id=request_id,
                status_code=429,
                response_time_ms=(time.time() - start_time) * 1000,
                response_size_bytes=len(response.body) if hasattr(response, 'body') else 0,
                cached=False,
                ltm_enhanced=False,
                timestamp=datetime.now().isoformat()
            ))
            return response
        
        # Check cache for GET requests
        cached_response = None
        if request.method == "GET" and self.redis_client:
            cached_response = await self._get_cached_response(api_request)
            if cached_response:
                end_time = time.time()
                await self._log_api_request(api_request, APIResponse(
                    request_id=request_id,
                    status_code=200,
                    response_time_ms=(end_time - start_time) * 1000,
                    response_size_bytes=len(json.dumps(cached_response)),
                    cached=True,
                    ltm_enhanced=True,
                    timestamp=datetime.now().isoformat()
                ))
                return JSONResponse(content=cached_response)
        
        # Process request
        try:
            response = await call_next(request)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Create API response record
            api_response = APIResponse(
                request_id=request_id,
                status_code=response.status_code,
                response_time_ms=response_time,
                response_size_bytes=0,  # Will be calculated
                cached=False,
                ltm_enhanced=True,
                timestamp=datetime.now().isoformat()
            )
            
            # Cache successful GET responses
            if request.method == "GET" and response.status_code == 200 and self.redis_client:
                await self._cache_response(api_request, response)
            
            # Log request/response
            await self._log_api_request(api_request, api_response)
            
            # Update statistics
            self._update_api_stats(api_response)
            
            return response
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"Request processing failed: {e}")
            
            error_response = APIResponse(
                request_id=request_id,
                status_code=500,
                response_time_ms=(end_time - start_time) * 1000,
                response_size_bytes=0,
                cached=False,
                ltm_enhanced=False,
                timestamp=datetime.now().isoformat()
            )
            
            await self._log_api_request(api_request, error_response)
            self._update_api_stats(error_response)
            
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )

    async def _check_rate_limits(self, request: APIRequest) -> Dict[str, Any]:
        """Check rate limits for incoming request"""
        try:
            if not self.config.get("rate_limiting", {}).get("enabled", True):
                return {"allowed": True}
            
            # Find applicable rate limit rule
            applicable_rule = None
            for rule in self.rate_limit_rules.values():
                if rule.endpoint_pattern == "*" or request.endpoint.startswith(rule.endpoint_pattern.replace("*", "")):
                    applicable_rule = rule
                    break
            
            if not applicable_rule:
                applicable_rule = self.rate_limit_rules.get("default")
            
            if not applicable_rule:
                return {"allowed": True}
            
            # Check limits using Redis if available
            if self.redis_client:
                return await self._check_redis_rate_limits(request, applicable_rule)
            else:
                # Fallback to in-memory rate limiting (simplified)
                return {"allowed": True}
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {"allowed": True}  # Allow on error

    async def _check_redis_rate_limits(self, request: APIRequest, rule: RateLimitRule) -> Dict[str, Any]:
        """Check rate limits using Redis"""
        try:
            # Create key based on rule and user/IP
            if rule.user_specific and request.user_id:
                key_base = f"rate_limit:{rule.rule_id}:user:{request.user_id}"
            else:
                key_base = f"rate_limit:{rule.rule_id}:ip:{request.source_ip}"
            
            minute_key = f"{key_base}:minute:{int(time.time() // 60)}"
            hour_key = f"{key_base}:hour:{int(time.time() // 3600)}"
            
            # Get current counts
            minute_count = await self.redis_client.get(minute_key)
            hour_count = await self.redis_client.get(hour_key)
            
            minute_count = int(minute_count) if minute_count else 0
            hour_count = int(hour_count) if hour_count else 0
            
            # Check limits
            if minute_count >= rule.requests_per_minute:
                return {"allowed": False, "reason": "minute_limit", "retry_after": 60}
            
            if hour_count >= rule.requests_per_hour:
                return {"allowed": False, "reason": "hour_limit", "retry_after": 3600}
            
            # Increment counters
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            await pipe.execute()
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return {"allowed": True}

    async def _get_cached_response(self, request: APIRequest) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        try:
            if not self.redis_client:
                return None
                
            cache_key = f"api_cache:{hashlib.md5((request.endpoint + str(request.query_params)).encode()).hexdigest()}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
                
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def _cache_response(self, request: APIRequest, response):
        """Cache response for future use"""
        try:
            if not self.redis_client or response.status_code != 200:
                return
                
            # Only cache certain endpoints
            cacheable_patterns = ["/api/devices", "/api/analysis", "/api/ltm/memories"]
            if not any(pattern in request.endpoint for pattern in cacheable_patterns):
                return
            
            # Extract response body (this is simplified - actual implementation would be more complex)
            cache_key = f"api_cache:{hashlib.md5((request.endpoint + str(request.query_params)).encode()).hexdigest()}"
            ttl = self.config.get("caching", {}).get("default_ttl", 300)
            
            # In a real implementation, you'd extract the actual response content
            # This is a placeholder
            response_data = {"cached": True, "timestamp": datetime.now().isoformat()}
            
            await self.redis_client.setex(cache_key, ttl, json.dumps(response_data))
            
        except Exception as e:
            logger.error(f"Response caching failed: {e}")

    async def _log_api_request(self, request: APIRequest, response: APIResponse):
        """Log API request/response with LTM integration"""
        try:
            # Log to LTM for learning
            if self.ltm_client:
                ltm_content = f"API request: {request.method} {request.endpoint} - Status: {response.status_code} - Response time: {response.response_time_ms:.1f}ms"
                
                tags = ["api_request", request.method.lower(), request.endpoint.split("/")[2] if len(request.endpoint.split("/")) > 2 else "root"]
                if response.status_code >= 400:
                    tags.append("error")
                if response.cached:
                    tags.append("cached")
                
                await self.ltm_client.record_message(
                    role="api_gateway",
                    content=ltm_content,
                    tags=tags,
                    metadata={
                        "request": asdict(request),
                        "response": asdict(response)
                    }
                )
            
            # Log security events for authentication endpoints
            if self.security_manager and "/auth/" in request.endpoint:
                from security.ltm_security_framework import SecurityEvent, SecurityEventType
                
                event = SecurityEvent(
                    event_id=response.request_id,
                    event_type=SecurityEventType.AUTHENTICATION,
                    timestamp=request.timestamp,
                    user_id=request.user_id,
                    session_id=None,
                    source_ip=request.source_ip,
                    resource_accessed=request.endpoint,
                    action_attempted=f"{request.method} {request.endpoint}",
                    success=response.status_code < 400,
                    risk_level="medium" if response.status_code >= 400 else "low",
                    details={"api_gateway": True, "response_time": response.response_time_ms}
                )
                
                await self.security_manager.log_security_event(event)
            
        except Exception as e:
            logger.error(f"API request logging failed: {e}")

    def _update_api_stats(self, response: APIResponse):
        """Update API gateway statistics"""
        try:
            self.api_stats["total_requests"] += 1
            
            if response.status_code < 400:
                self.api_stats["successful_requests"] += 1
            else:
                self.api_stats["failed_requests"] += 1
            
            # Update average response time (simple moving average)
            current_avg = self.api_stats["average_response_time"]
            total_requests = self.api_stats["total_requests"]
            self.api_stats["average_response_time"] = ((current_avg * (total_requests - 1)) + response.response_time_ms) / total_requests
            
        except Exception as e:
            logger.error(f"Stats update failed: {e}")

    async def _handle_login(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Handle user login and JWT token generation"""
        try:
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not username or not password:
                raise HTTPException(status_code=400, detail="Username and password required")
            
            # Simple authentication (in production, use proper user management)
            valid_users = {
                "admin": "admin123",
                "operator": "operator123",
                "viewer": "viewer123"
            }
            
            if username not in valid_users or valid_users[username] != password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Generate JWT token
            payload = {
                "sub": username,
                "role": "admin" if username == "admin" else "user",
                "exp": datetime.utcnow() + timedelta(minutes=self.token_expire_minutes),
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": self.token_expire_minutes * 60,
                "user": {
                    "username": username,
                    "role": payload["role"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise HTTPException(status_code=500, detail="Login processing failed")

    async def _refresh_token(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh JWT token"""
        try:
            payload = {
                "sub": current_user["username"],
                "role": current_user["role"],
                "exp": datetime.utcnow() + timedelta(minutes=self.token_expire_minutes),
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": self.token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(status_code=500, detail="Token refresh failed")

    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(lambda: None)) -> Dict[str, Any]:
        """Get current authenticated user (required)"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        return await self._decode_jwt_token(credentials.credentials)

    async def _get_current_user_optional(self, credentials: HTTPAuthorizationCredentials = Security(lambda: None)) -> Optional[Dict[str, Any]]:
        """Get current authenticated user (optional)"""
        if not credentials:
            return None
        try:
            return await self._decode_jwt_token(credentials.credentials)
        except:
            return None

    async def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            username = payload.get("sub")
            role = payload.get("role")
            
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return {
                "username": username,
                "role": role,
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def _proxy_to_mcp(self, tool_name: str, parameters: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Proxy request to MCP server with LTM enhancement"""
        try:
            # This would integrate with the actual MCP server
            # For now, return a mock response
            
            # Log the proxied request in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="api_gateway",
                    content=f"Proxying to MCP: {tool_name} with parameters {list(parameters.keys())}",
                    tags=["mcp_proxy", tool_name, "api_integration"],
                    metadata={"tool": tool_name, "user": user.get("username") if user else None}
                )
            
            # Mock response - in real implementation, this would call the actual MCP server
            return {
                "success": True,
                "tool": tool_name,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat(),
                "user": user.get("username") if user else "anonymous",
                "ltm_enhanced": True,
                "mock_response": True
            }
            
        except Exception as e:
            logger.error(f"MCP proxy failed: {e}")
            raise HTTPException(status_code=502, detail=f"MCP server error: {str(e)}")

    async def start_server(self):
        """Start the API gateway server"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available - cannot start server")
        
        if not self.app:
            raise RuntimeError("Gateway not initialized")
            
        server_config = self.config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8002)
        workers = server_config.get("workers", 1)
        reload = server_config.get("reload", False)
        
        logger.info(f"Starting LTM API Gateway on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

    def get_app(self):
        """Get FastAPI application instance"""
        return self.app

    async def cleanup(self):
        """Cleanup gateway resources"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                
            logger.info("API Gateway cleaned up")
            
        except Exception as e:
            logger.error(f"API Gateway cleanup failed: {e}")


# Main entry point
async def main():
    """Main function to run the API gateway"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LTM API Gateway")
    parser.add_argument("--config", default="config/api_gateway_config.json", help="Gateway configuration file")
    parser.add_argument("--ltm-server", default="http://localhost:8000", help="LTM server URL")
    
    args = parser.parse_args()
    
    # Initialize LTM client
    from ltm_integration.ltm_client import LTMClient
    ltm_client = LTMClient(args.ltm_server)
    await ltm_client.initialize()
    
    # Create and initialize gateway
    gateway = LTMAPIGateway(args.config)
    init_result = await gateway.initialize(ltm_client)
    
    if init_result["overall_status"] == "success":
        print("✓ LTM API Gateway initialized successfully")
        print(f"Starting server on port {gateway.config.get('server', {}).get('port', 8002)}")
        
        # Start the server
        await gateway.start_server()
    else:
        print(f"✗ Gateway initialization failed: {init_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())