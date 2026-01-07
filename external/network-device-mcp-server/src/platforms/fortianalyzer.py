"""
FortiAnalyzer API Manager  
Handles communication with FortiAnalyzer for log analysis and security reporting
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

class FortiAnalyzerManager:
    def __init__(self):
        self.timeout = 60.0  # Longer timeout for log queries
        self.session_id = None
    
    async def _login(self, host: str, username: str, password: str) -> str:
        """Login to FortiAnalyzer and get session ID"""
        url = f"https://{host}/jsonrpc"
        
        login_data = {
            "id": 1,
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {
                        "user": username,
                        "passwd": password
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            response = await client.post(url, json=login_data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                session_id = result.get("session")
                logger.info(f"Successfully logged into FortiAnalyzer at {host}")
                return session_id
            else:
                error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Login failed")
                raise Exception(f"FortiAnalyzer login failed: {error_msg}")
    
    async def get_security_events_summary(self, host: str, username: str, password: str, 
                                        device_name: str, timeframe: str = "1h", 
                                        event_types: List[str] = None) -> Dict:
        """Get condensed security events summary for message limit efficiency"""
        if event_types is None:
            event_types = ["webfilter", "ips", "antivirus", "application"]
            
        session_id = await self._login(host, username, password)
        
        try:
            # Calculate time range
            now = datetime.now()
            if timeframe == "1h":
                time_from = now - timedelta(hours=1)
            elif timeframe == "24h":
                time_from = now - timedelta(hours=24)
            elif timeframe == "7d":
                time_from = now - timedelta(days=7)
            else:
                time_from = now - timedelta(hours=1)
            
            summary = {
                "device": device_name,
                "timeframe": timeframe,
                "data_sources": {
                    "fortigate_security_logs": await self._get_blocked_traffic_summary(host, session_id, device_name, time_from, now),
                    "web_filter_reports": await self._get_web_filter_summary(host, session_id, device_name, time_from, now),
                    "application_control": await self._get_app_control_summary(host, session_id, device_name, time_from, now),
                    "ips_antivirus": await self._get_ips_av_summary(host, session_id, device_name, time_from, now),
                    "traffic_analytics": await self._get_traffic_analytics(host, session_id, device_name, time_from, now)
                },
                "executive_summary": {
                    "total_security_events": 0,
                    "critical_threats_blocked": 0,
                    "policy_violations": 0,
                    "top_risk_categories": []
                }
            }
            
            # Calculate executive summary from data sources
            total_events = sum([
                summary["data_sources"]["fortigate_security_logs"].get("total_blocked", 0),
                summary["data_sources"]["web_filter_reports"].get("total_filtered", 0),
                summary["data_sources"]["application_control"].get("total_blocked", 0),
                summary["data_sources"]["ips_antivirus"].get("total_threats", 0)
            ])
            
            summary["executive_summary"]["total_security_events"] = total_events
            summary["executive_summary"]["critical_threats_blocked"] = summary["data_sources"]["ips_antivirus"].get("critical_count", 0)
            summary["executive_summary"]["policy_violations"] = summary["data_sources"]["web_filter_reports"].get("policy_violations", 0)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting security events summary: {e}")
            raise
        finally:
            await self._logout(host, session_id)
    
    async def _get_blocked_traffic_summary(self, host: str, session_id: str, device_name: str, 
                                         time_from: datetime, time_to: datetime) -> Dict:
        """Get FortiGate security logs showing blocked traffic"""
        # This would implement the actual FortiAnalyzer API call for security logs
        # For now, returning structured placeholder data
        return {
            "data_source": "FortiGate Security Logs",
            "description": "Shows blocked traffic",
            "total_blocked": 0,  # Would be populated from API
            "top_blocked_services": [
                {"service": "HTTP", "count": 0},
                {"service": "HTTPS", "count": 0}
            ],
            "blocked_by_policy": {
                "firewall_rules": 0,
                "geo_blocking": 0,
                "reputation_filter": 0
            }
        }
    
    async def _get_web_filter_summary(self, host: str, session_id: str, device_name: str,
                                    time_from: datetime, time_to: datetime) -> Dict:
        """Get web filter reports showing filtered URLs"""
        return {
            "data_source": "Web Filter Reports",
            "description": "Displays filtered URLs",
            "total_filtered": 0,
            "policy_violations": 0,
            "top_blocked_categories": [
                {"category": "Social Media", "count": 0},
                {"category": "Streaming", "count": 0},
                {"category": "Gaming", "count": 0}
            ],
            "top_blocked_urls": [
                {"url": "example.com", "category": "Social Media", "count": 0}
            ],
            "user_activity": {
                "unique_users": 0,
                "repeat_offenders": []
            }
        }
    
    async def _get_app_control_summary(self, host: str, session_id: str, device_name: str,
                                     time_from: datetime, time_to: datetime) -> Dict:
        """Get application control logs showing application blocking events"""
        return {
            "data_source": "Application Control Logs",
            "description": "Application blocking events",
            "total_blocked": 0,
            "blocked_applications": [
                {"application": "Facebook", "count": 0},
                {"application": "YouTube", "count": 0},
                {"application": "Netflix", "count": 0}
            ],
            "risk_levels": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
    
    async def _get_ips_av_summary(self, host: str, session_id: str, device_name: str,
                                time_from: datetime, time_to: datetime) -> Dict:
        """Get IPS/Anti-Virus logs showing security event blocking"""
        return {
            "data_source": "IPS/Anti-Virus Logs",
            "description": "Security event blocking",
            "total_threats": 0,
            "critical_count": 0,
            "ips_events": {
                "intrusion_attempts": 0,
                "top_signatures": []
            },
            "antivirus_events": {
                "malware_blocked": 0,
                "virus_signatures": []
            },
            "threat_analysis": {
                "external_attacks": 0,
                "internal_infections": 0,
                "suspected_compromise": 0
            }
        }
    
    async def _get_traffic_analytics(self, host: str, session_id: str, device_name: str,
                                   time_from: datetime, time_to: datetime) -> Dict:
        """Get traffic analytics showing bandwidth and connection data"""
        return {
            "data_source": "Traffic Analytics",
            "description": "Bandwidth and connection data",
            "bandwidth_usage": {
                "total_bytes": 0,
                "average_throughput_mbps": 0,
                "peak_utilization": 0
            },
            "connection_stats": {
                "total_sessions": 0,
                "concurrent_sessions": 0,
                "top_protocols": [
                    {"protocol": "HTTP/HTTPS", "percentage": 0},
                    {"protocol": "DNS", "percentage": 0}
                ]
            },
            "user_analytics": {
                "active_users": 0,
                "top_bandwidth_users": []
            }
        }
    
    async def _logout(self, host: str, session_id: str):
        """Logout from FortiAnalyzer"""
        if not session_id:
            return
            
        url = f"https://{host}/jsonrpc"
        logout_data = {
            "id": 1,
            "method": "exec",
            "params": [{
                "url": "/sys/logout"
            }],
            "session": session_id
        }
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                await client.post(url, json=logout_data)
        except Exception as e:
            logger.error(f"Error during FortiAnalyzer logout: {e}")
    
    async def _make_request(self, host: str, username: str, password: str, method: str, params: dict) -> dict:
        """Make JSON-RPC request to FortiAnalyzer"""
        if not self.session_id:
            self.session_id = await self._login(host, username, password)
        
        url = f"https://{host}/jsonrpc"
        
        request_data = {
            "id": 1,
            "method": method,
            "params": [params],
            "session": self.session_id
        }
        
        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            response = await client.post(url, json=request_data)
            response.raise_for_status()
            result = response.json()
            
            # Check for session timeout
            if result.get("result", [{}])[0].get("status", {}).get("code") == -11:
                logger.info("Session expired, re-authenticating...")
                self.session_id = await self._login(host, username, password)
                request_data["session"] = self.session_id
                response = await client.post(url, json=request_data)
                result = response.json()
            
            return result
    
    def _get_time_range(self, hours: int = 24) -> tuple:
        """Get start and end time for log queries"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    async def get_web_filter_logs(self, host: str, username: str, password: str, 
                                device_name: str = None, device_ip: str = None, 
                                hours: int = 24, limit: int = 1000) -> list:
        """Get web filter logs for URL blocking analysis"""
        try:
            start_time, end_time = self._get_time_range(hours)
            
            # Build filter conditions
            filter_conditions = []
            if device_name:
                filter_conditions.append(f"devname='{device_name}'")
            if device_ip:
                filter_conditions.append(f"devid='{device_ip}'")
            
            # Add action filter for blocked URLs
            filter_conditions.append("action='blocked' or action='denied' or action='warning'")
            
            filter_str = " and ".join(filter_conditions) if filter_conditions else ""
            
            params = {
                "url": "/logview/adom/root/logsearch",
                "data": {
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "device": [],
                    "log_type": "webfilter",
                    "filter": filter_str,
                    "case_sensitive": False,
                    "limit": limit
                }
            }
            
            if device_name:
                params["data"]["device"].append({"devname": device_name})
            
            result = await self._make_request(host, username, password, "add", params)
            
            # Extract session ID for getting results
            if "result" in result and result["result"]:
                session_id = result["result"][0].get("data", {}).get("sid")
                if session_id:
                    return await self._get_log_results(host, username, password, session_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting web filter logs from {host}: {e}")
            raise
    
    async def get_security_events(self, host: str, username: str, password: str,
                                device_name: str = None, device_ip: str = None,
                                hours: int = 24, limit: int = 1000) -> list:
        """Get security events including IPS, antivirus, and application control"""
        try:
            start_time, end_time = self._get_time_range(hours)
            
            filter_conditions = []
            if device_name:
                filter_conditions.append(f"devname='{device_name}'")
            if device_ip:
                filter_conditions.append(f"devid='{device_ip}'")
            
            # Focus on blocked/denied events
            filter_conditions.append("action='deny' or action='block' or action='dropped'")
            
            filter_str = " and ".join(filter_conditions) if filter_conditions else ""
            
            params = {
                "url": "/logview/adom/root/logsearch",
                "data": {
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "device": [],
                    "log_type": "event",  # Security events
                    "filter": filter_str,
                    "case_sensitive": False,
                    "limit": limit
                }
            }
            
            if device_name:
                params["data"]["device"].append({"devname": device_name})
            
            result = await self._make_request(host, username, password, "add", params)
            
            if "result" in result and result["result"]:
                session_id = result["result"][0].get("data", {}).get("sid")
                if session_id:
                    return await self._get_log_results(host, username, password, session_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting security events from {host}: {e}")
            raise
    
    async def get_application_control_logs(self, host: str, username: str, password: str,
                                         device_name: str = None, device_ip: str = None,
                                         hours: int = 24, limit: int = 1000) -> list:
        """Get application control logs for blocked applications"""
        try:
            start_time, end_time = self._get_time_range(hours)
            
            filter_conditions = []
            if device_name:
                filter_conditions.append(f"devname='{device_name}'")
            if device_ip:
                filter_conditions.append(f"devid='{device_ip}'")
            
            # Focus on blocked applications
            filter_conditions.append("action='deny' or action='block'")
            
            filter_str = " and ".join(filter_conditions) if filter_conditions else ""
            
            params = {
                "url": "/logview/adom/root/logsearch",
                "data": {
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "device": [],
                    "log_type": "app-ctrl",
                    "filter": filter_str,
                    "case_sensitive": False,
                    "limit": limit
                }
            }
            
            if device_name:
                params["data"]["device"].append({"devname": device_name})
            
            result = await self._make_request(host, username, password, "add", params)
            
            if "result" in result and result["result"]:
                session_id = result["result"][0].get("data", {}).get("sid")
                if session_id:
                    return await self._get_log_results(host, username, password, session_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting application control logs from {host}: {e}")
            raise
    
    async def get_traffic_logs(self, host: str, username: str, password: str,
                             device_name: str = None, device_ip: str = None,
                             hours: int = 24, limit: int = 1000) -> list:
        """Get traffic logs for bandwidth and connection analysis"""
        try:
            start_time, end_time = self._get_time_range(hours)
            
            filter_conditions = []
            if device_name:
                filter_conditions.append(f"devname='{device_name}'")
            if device_ip:
                filter_conditions.append(f"devid='{device_ip}'")
            
            filter_str = " and ".join(filter_conditions) if filter_conditions else ""
            
            params = {
                "url": "/logview/adom/root/logsearch",
                "data": {
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "device": [],
                    "log_type": "traffic",
                    "filter": filter_str,
                    "case_sensitive": False,
                    "limit": limit
                }
            }
            
            if device_name:
                params["data"]["device"].append({"devname": device_name})
            
            result = await self._make_request(host, username, password, "add", params)
            
            if "result" in result and result["result"]:
                session_id = result["result"][0].get("data", {}).get("sid")
                if session_id:
                    return await self._get_log_results(host, username, password, session_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting traffic logs from {host}: {e}")
            raise
    
    async def _get_log_results(self, host: str, username: str, password: str, session_id: str) -> list:
        """Get the actual log results using the session ID"""
        try:
            params = {
                "url": f"/logview/adom/root/logsearch/{session_id}"
            }
            
            # Wait a moment for the search to complete
            await asyncio.sleep(2)
            
            result = await self._make_request(host, username, password, "get", params)
            
            logs = []
            if "result" in result and result["result"]:
                log_data = result["result"][0].get("data", {}).get("logs", [])
                
                for log_entry in log_data:
                    logs.append({
                        "date": log_entry.get("date", ""),
                        "time": log_entry.get("time", ""),
                        "device": log_entry.get("devname", ""),
                        "source_ip": log_entry.get("srcip", ""),
                        "dest_ip": log_entry.get("dstip", ""),
                        "url": log_entry.get("url", ""),
                        "hostname": log_entry.get("hostname", ""),
                        "service": log_entry.get("service", ""),
                        "action": log_entry.get("action", ""),
                        "reason": log_entry.get("reason", ""),
                        "category": log_entry.get("catdesc", ""),
                        "application": log_entry.get("app", ""),
                        "user": log_entry.get("user", ""),
                        "bytes_sent": log_entry.get("sentbyte", 0),
                        "bytes_received": log_entry.get("rcvdbyte", 0),
                        "duration": log_entry.get("duration", 0),
                        "threat": log_entry.get("attack", ""),
                        "severity": log_entry.get("level", ""),
                        "interface": log_entry.get("dstintf", "")
                    })
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting log results: {e}")
            return []
    
    async def get_url_blocking_summary(self, host: str, username: str, password: str,
                                     device_name: str = None, device_ip: str = None,
                                     hours: int = 24) -> dict:
        """Get comprehensive URL blocking summary for a device"""
        try:
            # Get web filter logs
            web_filter_logs = await self.get_web_filter_logs(
                host, username, password, device_name, device_ip, hours, 500
            )
            
            # Get application control logs  
            app_control_logs = await self.get_application_control_logs(
                host, username, password, device_name, device_ip, hours, 500
            )
            
            # Get security events
            security_events = await self.get_security_events(
                host, username, password, device_name, device_ip, hours, 500
            )
            
            # Analyze the data
            blocked_urls = {}
            blocked_apps = {}
            blocked_categories = {}
            users_affected = set()
            total_blocks = 0
            
            # Process web filter logs
            for log in web_filter_logs:
                total_blocks += 1
                url = log.get("url", "Unknown")
                category = log.get("category", "Unknown")
                user = log.get("user", "Unknown")
                
                if url not in blocked_urls:
                    blocked_urls[url] = {"count": 0, "category": category, "users": set()}
                blocked_urls[url]["count"] += 1
                blocked_urls[url]["users"].add(user)
                
                if category not in blocked_categories:
                    blocked_categories[category] = 0
                blocked_categories[category] += 1
                
                users_affected.add(user)
            
            # Process app control logs
            for log in app_control_logs:
                total_blocks += 1
                app = log.get("application", "Unknown")
                user = log.get("user", "Unknown")
                
                if app not in blocked_apps:
                    blocked_apps[app] = {"count": 0, "users": set()}
                blocked_apps[app]["count"] += 1
                blocked_apps[app]["users"].add(user)
                
                users_affected.add(user)
            
            # Convert sets to lists for JSON serialization
            for url_data in blocked_urls.values():
                url_data["users"] = list(url_data["users"])
            for app_data in blocked_apps.values():
                app_data["users"] = list(app_data["users"])
            
            return {
                "device_name": device_name or device_ip,
                "time_period_hours": hours,
                "total_blocking_events": total_blocks,
                "unique_users_affected": len(users_affected),
                "summary": {
                    "web_filter_blocks": len(web_filter_logs),
                    "app_control_blocks": len(app_control_logs),
                    "security_events": len(security_events)
                },
                "top_blocked_urls": sorted(
                    [{"url": url, **data} for url, data in blocked_urls.items()],
                    key=lambda x: x["count"], reverse=True
                )[:10],
                "top_blocked_apps": sorted(
                    [{"application": app, **data} for app, data in blocked_apps.items()],
                    key=lambda x: x["count"], reverse=True
                )[:10],
                "top_blocked_categories": sorted(
                    [{"category": cat, "count": count} for cat, count in blocked_categories.items()],
                    key=lambda x: x["count"], reverse=True
                )[:10],
                "users_affected": list(users_affected),
                "raw_logs": {
                    "web_filter": web_filter_logs[:20],  # First 20 for details
                    "app_control": app_control_logs[:20],
                    "security_events": security_events[:20]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting URL blocking summary: {e}")
            raise
    
    async def search_blocked_urls(self, host: str, username: str, password: str,
                                device_name: str = None, url_pattern: str = None,
                                hours: int = 24, limit: int = 100) -> list:
        """Search for specific blocked URLs"""
        try:
            start_time, end_time = self._get_time_range(hours)
            
            filter_conditions = []
            if device_name:
                filter_conditions.append(f"devname='{device_name}'")
            if url_pattern:
                filter_conditions.append(f"url like '%{url_pattern}%'")
            
            filter_conditions.append("action='blocked' or action='denied'")
            filter_str = " and ".join(filter_conditions)
            
            params = {
                "url": "/logview/adom/root/logsearch",
                "data": {
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "device": [],
                    "log_type": "webfilter",
                    "filter": filter_str,
                    "case_sensitive": False,
                    "limit": limit
                }
            }
            
            if device_name:
                params["data"]["device"].append({"devname": device_name})
            
            result = await self._make_request(host, username, password, "add", params)
            
            if "result" in result and result["result"]:
                session_id = result["result"][0].get("data", {}).get("sid")
                if session_id:
                    return await self._get_log_results(host, username, password, session_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching blocked URLs: {e}")
            raise
    
    async def get_device_list(self, host: str, username: str, password: str) -> list:
        """Get list of devices reporting to FortiAnalyzer"""
        try:
            params = {
                "url": "/dvmdb/device"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            devices = []
            if "result" in result and result["result"]:
                device_data = result["result"][0].get("data", [])
                
                for device in device_data:
                    devices.append({
                        "name": device.get("name", ""),
                        "serial": device.get("sn", ""),
                        "ip": device.get("ip", ""),
                        "type": device.get("os_type", ""),
                        "version": device.get("os_ver", ""),
                        "status": device.get("tab_status", ""),
                        "last_seen": device.get("last_resync", "")
                    })
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting device list from {host}: {e}")
            raise
    
    async def logout(self, host: str) -> dict:
        """Logout from FortiAnalyzer"""
        try:
            if not self.session_id:
                return {"status": "no_session"}
            
            url = f"https://{host}/jsonrpc"
            
            logout_data = {
                "id": 1,
                "method": "exec",
                "params": [{"url": "/sys/logout"}],
                "session": self.session_id
            }
            
            async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                response = await client.post(url, json=logout_data)
                result = response.json()
                
                self.session_id = None
                return {"status": "logged_out"}
                
        except Exception as e:
            logger.error(f"Error logging out from {host}: {e}")
            return {"status": "error", "message": str(e)}
