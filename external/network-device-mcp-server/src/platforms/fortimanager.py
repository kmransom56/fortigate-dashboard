"""
FortiManager API Manager  
Handles communication with FortiManager for centralized management
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)

class FortiManagerManager:
    def __init__(self):
        self.timeout = 30.0
        self.session_id = None
    
    async def _login(self, host: str, username: str, password: str) -> str:
        """Login to FortiManager and get session ID"""
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
                logger.info(f"Successfully logged into FortiManager at {host}")
                return session_id
            else:
                error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Login failed")
                raise Exception(f"FortiManager login failed: {error_msg}")
    
    async def _make_request(self, host: str, username: str, password: str, method: str, params: dict) -> dict:
        """Make JSON-RPC request to FortiManager"""
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
    
    async def get_managed_devices(self, host: str, username: str, password: str, adom: str = "root") -> list:
        """Get list of devices managed by FortiManager"""
        try:
            params = {
                "url": f"/dvmdb/adom/{adom}/device"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            devices = []
            if "result" in result and result["result"]:
                device_data = result["result"][0].get("data", [])
                
                for device in device_data:
                    devices.append({
                        "name": device.get("name", ""),
                        "serial": device.get("sn", ""),
                        "platform": device.get("platform_str", ""),
                        "version": device.get("os_ver", ""),
                        "ip": device.get("ip", ""),
                        "status": "online" if device.get("conn_mode") == 1 else "offline",
                        "last_checkin": device.get("last_checked", ""),
                        "adom": adom
                    })
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting managed devices from {host}: {e}")
            raise
    
    async def get_adoms(self, host: str, username: str, password: str) -> list:
        """Get list of ADOMs (Administrative Domains)"""
        try:
            params = {
                "url": "/dvmdb/adom"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            adoms = []
            if "result" in result and result["result"]:
                adom_data = result["result"][0].get("data", [])
                
                for adom in adom_data:
                    adoms.append({
                        "name": adom.get("name", ""),
                        "desc": adom.get("desc", ""),
                        "create_time": adom.get("create_time", ""),
                        "mig_mr": adom.get("mig_mr", 0),
                        "mr": adom.get("mr", 0)
                    })
            
            return adoms
            
        except Exception as e:
            logger.error(f"Error getting ADOMs from {host}: {e}")
            raise
    
    async def get_policy_packages(self, host: str, username: str, password: str, adom: str = "root") -> list:
        """Get policy packages in an ADOM"""
        try:
            params = {
                "url": f"/pm/pkg/adom/{adom}"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            packages = []
            if "result" in result and result["result"]:
                package_data = result["result"][0].get("data", [])
                
                for package in package_data:
                    packages.append({
                        "name": package.get("name", ""),
                        "type": package.get("type", ""),
                        "scope member": package.get("scope member", []),
                        "uuid": package.get("uuid", "")
                    })
            
            return packages
            
        except Exception as e:
            logger.error(f"Error getting policy packages from {host}: {e}")
            raise
    
    async def install_policy_package(self, host: str, username: str, password: str, adom: str, package: str, devices: list) -> dict:
        """Install policy package to specified devices"""
        try:
            # Prepare the scope (target devices)
            scope = []
            for device in devices:
                scope.append({
                    "name": device,
                    "vdom": "root"  # Default VDOM, adjust as needed
                })
            
            params = {
                "url": "/securityconsole/install/package",
                "data": {
                    "adom": adom,
                    "pkg": package,
                    "scope": scope
                }
            }
            
            result = await self._make_request(host, username, password, "exec", params)
            
            if "result" in result and result["result"]:
                task_data = result["result"][0].get("data", {})
                return {
                    "status": "started",
                    "task_id": task_data.get("taskid", ""),
                    "message": "Policy installation started",
                    "target_devices": devices
                }
            else:
                return {
                    "status": "error", 
                    "message": "Failed to start policy installation"
                }
            
        except Exception as e:
            logger.error(f"Error installing policy package on {host}: {e}")
            raise
    
    async def get_task_status(self, host: str, username: str, password: str, task_id: str) -> dict:
        """Get status of a task (like policy installation)"""
        try:
            params = {
                "url": f"/task/task/{task_id}"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            if "result" in result and result["result"]:
                task_data = result["result"][0].get("data", {})
                return {
                    "task_id": task_id,
                    "state": task_data.get("state", "unknown"),
                    "percent": task_data.get("percent", 0),
                    "line": task_data.get("line", []),
                    "history": task_data.get("history", [])
                }
            
            return {"task_id": task_id, "state": "not_found"}
            
        except Exception as e:
            logger.error(f"Error getting task status from {host}: {e}")
            raise
    
    async def get_device_config(self, host: str, username: str, password: str, device_name: str, adom: str = "root") -> dict:
        """Get configuration of a specific device"""
        try:
            params = {
                "url": f"/pm/config/device/{device_name}/vdom/root"
            }
            
            result = await self._make_request(host, username, password, "get", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting device config from {host}: {e}")
            raise
    
    async def create_policy_package(self, host: str, username: str, password: str, adom: str, package_name: str, target_devices: list) -> dict:
        """Create a new policy package"""
        try:
            scope_members = []
            for device in target_devices:
                scope_members.append({
                    "name": device,
                    "vdom": "root"
                })
            
            params = {
                "url": f"/pm/pkg/adom/{adom}",
                "data": {
                    "name": package_name,
                    "type": "pkg",
                    "scope member": scope_members
                }
            }
            
            result = await self._make_request(host, username, password, "add", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating policy package on {host}: {e}")
            raise
    
    async def logout(self, host: str) -> dict:
        """Logout from FortiManager"""
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