"""
FortiManager service for interacting with FortiManager API
"""
import os
import logging
import json
import aiohttp
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

from ...core.config import settings
from ...models.webfilters import (
    WebFilterProfile,
    WebFilterOverride,
    WebFilterLogEntry,
    WebFilterSearchRequest,
    WebFilterSearchResponse,
    WebFilterTestRequest,
    WebFilterTestResult,
    WebFilterBulkUpdateRequest,
    WebFilterBulkUpdateResponse,
    WebFilterStats
)

logger = logging.getLogger(__name__)

class FortiManagerError(Exception):
    """Custom exception for FortiManager API errors"""
    pass

class FortiManagerService:
    """Service for interacting with FortiManager API"""
    
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
        """Initialize FortiManager service with connection details"""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session_id = None
        self.last_login = None
        self.session_timeout = timedelta(minutes=30)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.login()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.logout()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the FortiManager API"""
        if not self.session or not self._is_session_valid():
            await self.login()
        
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
        headers = kwargs.pop('headers', {})
        headers.update({
            'Content-Type': 'application/json',
            'X-CSRFTOKEN': self.csrf_token if hasattr(self, 'csrf_token') else ''
        })
        
        # Add session cookie if available
        cookies = kwargs.pop('cookies', {})
        if self.session_id:
            cookies['ccsrftoken'] = self.csrf_token if hasattr(self, 'csrf_token') else ''
            cookies['ccsrftoken_80_port'] = self.csrf_token if hasattr(self, 'csrf_token') else ''
            cookies['ccsrftoken_443_port'] = self.csrf_token if hasattr(self, 'csrf_token') else ''
            cookies['ccsrftoken_4433_port'] = self.csrf_token if hasattr(self, 'csrf_token') else ''
            cookies['ccsrftoken_10443_port'] = self.csrf_token if hasattr(self, 'csrf_token') else ''
        
        try:
            async with self.session.request(
                method, 
                url, 
                headers=headers, 
                cookies=cookies,
                ssl=not self.verify_ssl,
                **kwargs
            ) as response:
                response.raise_for_status()
                
                # Update CSRF token if present in response
                if 'X-CSRFTOKEN' in response.headers:
                    self.csrf_token = response.headers['X-CSRFTOKEN']
                
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return await response.json()
                return await response.text()
                
        except aiohttp.ClientError as e:
            logger.error(f"FortiManager API request failed: {str(e)}")
            raise FortiManagerError(f"API request failed: {str(e)}")
    
    def _is_session_valid(self) -> bool:
        """Check if the current session is still valid"""
        if not self.last_login or not self.session_id:
            return False
        return (datetime.utcnow() - self.last_login) < self.session_timeout
    
    async def login(self) -> bool:
        """Authenticate with FortiManager and get session token"""
        try:
            if self.session:
                await self.session.close()
            
            self.session = aiohttp.ClientSession()
            
            # Get login page to retrieve CSRF token
            login_url = f"{self.base_url}/logincheck"
            async with self.session.get(
                login_url,
                ssl=not self.verify_ssl,
                allow_redirects=True
            ) as response:
                # Extract CSRF token from cookies
                if 'ccsrftoken' in response.cookies:
                    self.csrf_token = response.cookies['ccsrftoken'].value.split('"')[1]
            
            # Perform login
            data = {
                'username': self.username,
                'secretkey': self.password,
                'ajax': 1
            }
            
            headers = {
                'X-CSRFTOKEN': self.csrf_token,
                'Referer': f"{self.base_url}/"
            }
            
            async with self.session.post(
                f"{self.base_url}/logincheck",
                data=data,
                headers=headers,
                ssl=not self.verify_ssl,
                allow_redirects=False
            ) as response:
                if response.status != 200 or 'Set-Cookie' not in response.headers:
                    raise FortiManagerError("Login failed: Invalid credentials or server error")
                
                # Extract session ID from cookies
                cookies = response.cookies
                if 'ccsrftoken' in cookies:
                    self.csrf_token = cookies['ccsrftoken'].value.split('"')[1]
                
                self.last_login = datetime.utcnow()
                return True
                
        except Exception as e:
            logger.error(f"FortiManager login failed: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            raise FortiManagerError(f"Login failed: {str(e)}")
    
    async def logout(self):
        """Log out from FortiManager"""
        if self.session:
            try:
                await self._request('POST', '/logout')
            except Exception as e:
                logger.warning(f"Error during logout: {str(e)}")
            finally:
                await self.session.close()
                self.session = None
        self.session_id = None
        self.last_login = None
    
    async def get_webfilter_profiles(self, adom: str = 'root') -> List[Dict[str, Any]]:
        """Get all web filter profiles from FortiManager"""
        try:
            endpoint = f"pm/config/device/{adom}/webfilter/profile"
            response = await self._request('GET', endpoint)
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Failed to get web filter profiles: {str(e)}")
            raise FortiManagerError(f"Failed to get web filter profiles: {str(e)}")
    
    async def get_webfilter_entries(self, profile: str, adom: str = 'root') -> Dict[str, Any]:
        """Get web filter entries for a specific profile"""
        try:
            endpoint = f"pm/config/device/{adom}/webfilter/profile/{profile}"
            response = await self._request('GET', endpoint)
            return response.get('data', {})
        except Exception as e:
            logger.error(f"Failed to get web filter entries for profile {profile}: {str(e)}")
            raise FortiManagerError(f"Failed to get web filter entries: {str(e)}")
    
    async def search_webfilters(
        self, 
        query: str, 
        adom: str = 'root',
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Search for web filter entries matching the query
        
        Returns a dictionary with the following structure:
        {
            'webfilter_data': Dict[str, Any],  # Raw web filter data
            'filtered_data': Dict[str, Any],   # Filtered results
            'matches': List[Dict[str, Any]]    # Matching entries
        }
        """
        try:
            # Get all web filter profiles
            profiles = await self.get_webfilter_profiles(adom)
            
            results = {
                'webfilter_data': {'profiles': []},
                'filtered_data': {'applied_filters': {'query': query}, 'result_count': 0},
                'matches': []
            }
            
            # Search through each profile
            for profile in profiles:
                profile_name = profile.get('name')
                if not profile_name:
                    continue
                
                # Get detailed profile data
                try:
                    profile_data = await self.get_webfilter_entries(profile_name, adom)
                    if not profile_data:
                        continue
                        
                    results['webfilter_data']['profiles'].append(profile_data)
                    
                    # Search for matches in the profile
                    matches = self._find_matches_in_profile(profile_data, query)
                    if matches:
                        results['matches'].extend(matches)
                        
                except Exception as e:
                    logger.warning(f"Error processing profile {profile_name}: {str(e)}")
            
            # Update result count
            results['filtered_data']['result_count'] = len(results['matches'])
            
            return results
            
        except Exception as e:
            logger.error(f"Web filter search failed: {str(e)}")
            raise FortiManagerError(f"Search failed: {str(e)}")
    
    def _find_matches_in_profile(self, profile_data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Helper method to find matching entries in a profile"""
        matches = []
        query = query.lower()
        
        # Check if query matches profile name
        if 'name' in profile_data and query in profile_data['name'].lower():
            matches.append({
                'type': 'profile',
                'id': profile_data.get('name'),
                'name': profile_data.get('name'),
                'match_field': 'name',
                'match_value': profile_data.get('name'),
                'data': profile_data
            })
        
        # Check web filter entries if they exist
        if 'web' in profile_data and 'url-filter' in profile_data['web']:
            for entry in profile_data['web']['url-filter']:
                if not isinstance(entry, dict):
                    continue
                    
                # Check URL pattern
                if 'url-pattern' in entry and query in entry['url-pattern'].lower():
                    matches.append({
                        'type': 'url_filter',
                        'id': f"{profile_data.get('name')}_{entry.get('id', '')}",
                        'name': entry.get('name', 'Unnamed Entry'),
                        'match_field': 'url-pattern',
                        'match_value': entry.get('url-pattern'),
                        'action': entry.get('action', 'unknown'),
                        'data': entry
                    })
                
                # Check other fields for matches
                for field, value in entry.items():
                    if field == 'url-pattern':
                        continue
                        
                    if isinstance(value, str) and query in value.lower():
                        matches.append({
                            'type': 'url_filter',
                            'id': f"{profile_data.get('name')}_{entry.get('id', '')}",
                            'name': entry.get('name', 'Unnamed Entry'),
                            'match_field': field,
                            'match_value': value,
                            'action': entry.get('action', 'unknown'),
                            'data': entry
                        })
        
        return matches
    
    async def test_url(
        self, 
        url: str, 
        src_ip: Optional[str] = None, 
        user: Optional[str] = None,
        adom: str = 'root'
    ) -> Dict[str, Any]:
        """Test how a URL would be handled by the web filter"""
        try:
            # This is a simplified example - actual implementation would use the FMG API
            # to test the URL against the web filter policies
            
            # First, get all web filter profiles
            profiles = await self.get_webfilter_profiles(adom)
            
            # Check each profile for matches
            for profile in profiles:
                profile_name = profile.get('name')
                if not profile_name:
                    continue
                
                # Get detailed profile data
                try:
                    profile_data = await self.get_webfilter_entries(profile_name, adom)
                    if not profile_data:
                        continue
                    
                    # Check for URL matches in the profile
                    matches = self._find_matches_in_profile(profile_data, url)
                    if matches:
                        # Return the first matching rule
                        match = matches[0]
                        return {
                            'url': url,
                            'action': match.get('action', 'allow'),
                            'profile': profile_name,
                            'matched_rule': {
                                'id': match.get('id'),
                                'name': match.get('name'),
                                'type': match.get('type'),
                                'match_field': match.get('match_field'),
                                'match_value': match.get('match_value')
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                except Exception as e:
                    logger.warning(f"Error testing URL against profile {profile_name}: {str(e)}")
            
            # If no matches found, return default action
            return {
                'url': url,
                'action': 'allow',  # Default action if no rules match
                'profile': 'default',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"URL test failed: {str(e)}")
            raise FortiManagerError(f"URL test failed: {str(e)}")
    
    async def update_webfilter_entry(
        self, 
        profile: str, 
        entry_id: str, 
        updates: Dict[str, Any],
        adom: str = 'root'
    ) -> bool:
        """Update a web filter entry"""
        try:
            endpoint = f"pm/config/device/{adom}/webfilter/profile/{profile}"
            payload = {
                'data': updates,
                'url': endpoint
            }
            
            response = await self._request('PUT', endpoint, json=payload)
            return response.get('status', {}).get('code', 1) == 0
            
        except Exception as e:
            logger.error(f"Failed to update web filter entry: {str(e)}")
            raise FortiManagerError(f"Update failed: {str(e)}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get FortiManager system status"""
        try:
            response = await self._request('GET', '/api/v2/monitor/system/status')
            return response.get('results', {})
        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            raise FortiManagerError(f"Failed to get system status: {str(e)}")

# Global instance of the FortiManager service
fortimanager_service = None

async def get_fortimanager_service() -> FortiManagerService:
    """Get or create a FortiManager service instance"""
    global fortimanager_service
    
    if fortimanager_service is None or not fortimanager_service._is_session_valid():
        # Load configuration from environment or settings
        base_url = os.getenv('FORTIMANAGER_URL', 'https://fmg.example.com')
        username = os.getenv('FORTIMANAGER_USERNAME', 'admin')
        password = os.getenv('FORTIMANAGER_PASSWORD', '')
        verify_ssl = os.getenv('FORTIMANAGER_VERIFY_SSL', 'true').lower() == 'true'
        
        fortimanager_service = FortiManagerService(
            base_url=base_url,
            username=username,
            password=password,
            verify_ssl=verify_ssl
        )
        
        # Perform initial login
        await fortimanager_service.login()
    
    return fortimanager_service
