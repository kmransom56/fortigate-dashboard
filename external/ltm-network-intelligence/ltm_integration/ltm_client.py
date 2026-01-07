# ltm_integration/ltm_client.py
# Core LTM client for network intelligence platform

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class LTMMessage:
    """Structured LTM message"""
    role: str
    content: str
    timestamp: str = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LTMSearchResult:
    """LTM search result structure"""
    content: str
    timestamp: str
    relevance_score: float
    tags: List[str]
    metadata: Dict[str, Any]

class LTMClient:
    """Enhanced LTM client for network intelligence operations"""
    
    def __init__(self, server_url: str = "http://localhost:8000", 
                 persona_file: str = "config/network_persona.json",
                 local_fallback: bool = True):
        self.server_url = server_url.rstrip('/')
        self.persona_file = persona_file
        self.local_fallback = local_fallback
        self.session_id = None
        self.conversation_active = False
        self.local_memory = []
        self.persona = {}
        self.session = None
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize LTM client and establish connection"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Load persona
            await self._load_persona()
            
            # Test LTM server connection
            ltm_available = await self._test_ltm_connection()
            
            if ltm_available:
                # Initialize LTM session
                init_result = await self._ltm_initialize()
                if init_result.get("success"):
                    logger.info("✓ LTM client initialized with server connection")
                    return {"status": "success", "mode": "server", "session_id": self.session_id}
            
            if self.local_fallback:
                # Initialize local fallback
                self.session_id = f"local_{uuid.uuid4().hex[:8]}"
                logger.info("✓ LTM client initialized with local fallback")
                return {"status": "success", "mode": "local_fallback", "session_id": self.session_id}
            
            raise Exception("LTM server unavailable and local fallback disabled")
            
        except Exception as e:
            logger.error(f"LTM client initialization failed: {e}")
            if self.local_fallback:
                self.session_id = f"local_{uuid.uuid4().hex[:8]}"
                return {"status": "fallback", "mode": "local_only", "error": str(e)}
            raise

    async def _load_persona(self):
        """Load network intelligence persona"""
        try:
            import os
            if os.path.exists(self.persona_file):
                with open(self.persona_file, 'r') as f:
                    self.persona = json.load(f)
            else:
                # Create default network persona
                self.persona = {
                    "role": "network_intelligence_specialist",
                    "expertise": [
                        "network device management",
                        "FortiGate administration",
                        "Cisco Meraki operations",
                        "network troubleshooting",
                        "performance optimization",
                        "security analysis"
                    ],
                    "personality": {
                        "analytical": True,
                        "detail_oriented": True,
                        "proactive": True,
                        "security_focused": True
                    },
                    "learning_preferences": {
                        "focus_areas": ["device_patterns", "performance_trends", "security_incidents"],
                        "memory_priority": ["critical_events", "optimization_insights", "troubleshooting_patterns"],
                        "correlation_strength": "high"
                    }
                }
                
                # Save default persona
                os.makedirs(os.path.dirname(self.persona_file), exist_ok=True)
                with open(self.persona_file, 'w') as f:
                    json.dump(self.persona, f, indent=2)
                    
        except Exception as e:
            logger.warning(f"Could not load persona: {e}")
            self.persona = {"role": "network_specialist"}

    async def _test_ltm_connection(self) -> bool:
        """Test connection to LTM server"""
        try:
            async with self.session.get(f"{self.server_url}/health", timeout=5) as response:
                return response.status == 200
        except:
            return False

    async def _ltm_initialize(self) -> Dict[str, Any]:
        """Initialize LTM session with server"""
        try:
            payload = {
                "method": "ltm_initialize",
                "params": {
                    "persona": self.persona,
                    "session_config": {
                        "memory_limit": 5000,
                        "learning_enabled": True,
                        "context_awareness": True
                    }
                }
            }
            
            async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                result = await response.json()
                if result.get("success"):
                    self.session_id = result.get("session_id")
                    self.conversation_active = True
                    return result
                else:
                    raise Exception(f"LTM initialization failed: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"LTM server initialization failed: {e}")
            return {"success": False, "error": str(e)}

    async def awaken(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Awaken LTM with current network context"""
        if not self.session_id:
            raise RuntimeError("LTM client not initialized")
            
        try:
            if self.conversation_active:
                logger.info("LTM already awakened")
                return {"success": True, "status": "already_active"}
                
            # Prepare awakening context
            awaken_context = {
                "platform": "Network Intelligence Platform",
                "timestamp": datetime.now().isoformat(),
                "network_context": context or {},
                "persona": self.persona
            }
            
            if self._is_server_mode():
                # Server-based awakening
                payload = {
                    "method": "ltm_awaken", 
                    "params": {
                        "session_id": self.session_id,
                        "context": awaken_context
                    }
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    if result.get("success"):
                        self.conversation_active = True
                        logger.info("✓ LTM awakened with server")
                        return result
                    else:
                        raise Exception(f"LTM awaken failed: {result.get('error')}")
            else:
                # Local fallback awakening
                self.conversation_active = True
                logger.info("✓ LTM awakened with local fallback")
                return {"success": True, "mode": "local", "context": awaken_context}
                
        except Exception as e:
            logger.error(f"LTM awaken failed: {e}")
            return {"success": False, "error": str(e)}

    async def record_message(self, role: str, content: str, 
                           tags: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Record message in LTM"""
        if not self.session_id:
            raise RuntimeError("LTM client not initialized")
            
        message = LTMMessage(
            role=role,
            content=content,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        try:
            if self._is_server_mode() and self.conversation_active:
                # Server-based recording
                payload = {
                    "method": "ltm_record_message",
                    "params": {
                        "session_id": self.session_id,
                        **asdict(message)
                    }
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    if result.get("success"):
                        return result
                    else:
                        # Fallback to local if server fails
                        self.local_memory.append(message)
                        return {"success": True, "mode": "local_fallback"}
            else:
                # Local recording
                self.local_memory.append(message)
                return {"success": True, "mode": "local"}
                
        except Exception as e:
            logger.error(f"LTM record message failed: {e}")
            # Always fallback to local memory
            self.local_memory.append(message)
            return {"success": True, "mode": "local_fallback", "error": str(e)}

    async def search_memories(self, query: str, tags: List[str] = None, 
                            limit: int = 10, min_relevance: float = 0.5) -> List[LTMSearchResult]:
        """Search LTM memories"""
        if not self.session_id:
            raise RuntimeError("LTM client not initialized")
            
        try:
            if self._is_server_mode() and self.conversation_active:
                # Server-based search
                payload = {
                    "method": "ltm_search_memories",
                    "params": {
                        "session_id": self.session_id,
                        "query": query,
                        "tags": tags or [],
                        "limit": limit,
                        "min_relevance": min_relevance
                    }
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    if result.get("success"):
                        memories = result.get("memories", [])
                        return [
                            LTMSearchResult(
                                content=m.get("content", ""),
                                timestamp=m.get("timestamp", ""),
                                relevance_score=m.get("relevance_score", 0.0),
                                tags=m.get("tags", []),
                                metadata=m.get("metadata", {})
                            ) for m in memories
                        ]
            
            # Local search fallback
            return self._search_local_memories(query, tags, limit, min_relevance)
            
        except Exception as e:
            logger.error(f"LTM search failed: {e}")
            return self._search_local_memories(query, tags, limit, min_relevance)

    def _search_local_memories(self, query: str, tags: List[str] = None, 
                              limit: int = 10, min_relevance: float = 0.5) -> List[LTMSearchResult]:
        """Search local memory fallback"""
        results = []
        query_lower = query.lower()
        
        for message in self.local_memory:
            # Simple text matching
            content_match = query_lower in message.content.lower()
            tag_match = not tags or any(tag in message.tags for tag in tags)
            
            if content_match and tag_match:
                # Simple relevance scoring
                relevance = 0.7 if content_match else 0.3
                if tag_match and tags:
                    relevance += 0.2
                    
                if relevance >= min_relevance:
                    results.append(LTMSearchResult(
                        content=message.content,
                        timestamp=message.timestamp,
                        relevance_score=relevance,
                        tags=message.tags,
                        metadata=message.metadata
                    ))
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    async def end_conversation(self) -> Dict[str, Any]:
        """End LTM conversation"""
        if not self.conversation_active:
            return {"success": True, "status": "not_active"}
            
        try:
            if self._is_server_mode():
                payload = {
                    "method": "ltm_end_conversation",
                    "params": {"session_id": self.session_id}
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    self.conversation_active = False
                    return result
            else:
                self.conversation_active = False
                return {"success": True, "mode": "local"}
                
        except Exception as e:
            logger.error(f"LTM end conversation failed: {e}")
            self.conversation_active = False
            return {"success": True, "error": str(e)}

    async def sleep(self) -> Dict[str, Any]:
        """Put LTM to sleep"""
        if not self.conversation_active:
            return {"success": True, "status": "already_sleeping"}
            
        try:
            if self._is_server_mode():
                payload = {
                    "method": "ltm_sleep",
                    "params": {"session_id": self.session_id}
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    if result.get("success"):
                        self.conversation_active = False
                    return result
            else:
                self.conversation_active = False
                return {"success": True, "mode": "local"}
                
        except Exception as e:
            logger.error(f"LTM sleep failed: {e}")
            return {"success": False, "error": str(e)}

    def _is_server_mode(self) -> bool:
        """Check if running in server mode"""
        return self.session and not self.session.closed and "local_" not in str(self.session_id)

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        stats = {
            "session_id": self.session_id,
            "conversation_active": self.conversation_active,
            "local_memory_count": len(self.local_memory),
            "mode": "server" if self._is_server_mode() else "local",
            "persona_loaded": bool(self.persona)
        }
        
        if self._is_server_mode() and self.conversation_active:
            try:
                payload = {
                    "method": "ltm_get_stats",
                    "params": {"session_id": self.session_id}
                }
                
                async with self.session.post(f"{self.server_url}/ltm", json=payload) as response:
                    result = await response.json()
                    if result.get("success"):
                        stats.update(result.get("stats", {}))
            except Exception as e:
                logger.warning(f"Could not get server stats: {e}")
        
        return stats

    async def close(self):
        """Close LTM client and cleanup resources"""
        try:
            if self.conversation_active:
                await self.end_conversation()
                
            if self.session and not self.session.closed:
                await self.session.close()
                
            logger.info("LTM client closed")
        except Exception as e:
            logger.error(f"Error closing LTM client: {e}")