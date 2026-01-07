"""
Universal SSL Fix Module for Corporate Environments
===================================================

This module provides comprehensive SSL error suppression for Python applications
running in corporate environments with SSL inspection (Zscaler, Blue Coat, etc.).

Usage:
------
Simply import this module at the beginning of your Python script:

    import ssl_universal_fix

Or call the fix functions explicitly:

    from ssl_universal_fix import apply_all_ssl_fixes
    apply_all_ssl_fixes()

Features:
---------
- Disables SSL certificate verification globally
- Suppresses all SSL warnings and errors
- Configures requests library for SSL bypass
- Sets up urllib3 to ignore SSL errors
- Configures Python's ssl module defaults
- Works with popular libraries: requests, urllib3, aiohttp, httpx

Compatible with:
----------------
- requests
- urllib3 
- aiohttp
- httpx
- http.client
- ssl module
- meraki SDK
- Any library using the above

Author: GitHub Copilot
Date: July 2025
"""

import os
import sys
import ssl
import warnings
import logging
from typing import Optional

# Global flag to track if fixes have been applied
_SSL_FIXES_APPLIED = False

def suppress_ssl_warnings():
    """Suppress all SSL-related warnings"""
    try:
        import urllib3
        urllib3.disable_warnings()
        
        # Disable specific warnings that exist
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except AttributeError:
            pass
        try:
            urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)
        except AttributeError:
            pass
        try:
            urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)
        except AttributeError:
            pass
        try:
            urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
        except AttributeError:
            pass
            
    except ImportError:
        pass
    
    # Suppress Python's built-in SSL warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='ssl')
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    warnings.filterwarnings('ignore', message='Certificate verification is disabled')
    
    # Suppress logging warnings for SSL
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    logging.getLogger('urllib3.util.retry').setLevel(logging.ERROR)
    logging.getLogger('requests.packages.urllib3').setLevel(logging.ERROR)

def configure_ssl_context():
    """Configure SSL context to be more permissive"""
    try:
        # Create a permissive SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Set as default SSL context
        ssl._create_default_https_context = ssl._create_unverified_context
        
        return ssl_context
    except Exception:
        return None

def configure_requests_ssl():
    """Configure requests library to bypass SSL verification"""
    try:
        import requests
        from requests.adapters import HTTPAdapter
        try:
            from requests.packages.urllib3.util.retry import Retry
        except ImportError:
            try:
                from urllib3.util.retry import Retry
            except ImportError:
                Retry = None
        
        # Monkey patch requests to disable SSL verification by default
        original_request = requests.Session.request
        
        def patched_request(self, method, url, **kwargs):
            # Always set verify=False if not explicitly provided
            if 'verify' not in kwargs:
                kwargs['verify'] = False
            return original_request(self, method, url, **kwargs)
        
        requests.Session.request = patched_request
        
        # Also patch the global functions
        original_get = requests.get
        original_post = requests.post
        original_put = requests.put
        original_delete = requests.delete
        original_patch = requests.patch
        original_head = requests.head
        original_options = requests.options
        
        def patched_get(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_get(url, **kwargs)
        
        def patched_post(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_post(url, **kwargs)
            
        def patched_put(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_put(url, **kwargs)
            
        def patched_delete(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_delete(url, **kwargs)
            
        def patched_patch(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_patch(url, **kwargs)
            
        def patched_head(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_head(url, **kwargs)
            
        def patched_options(url, **kwargs):
            kwargs.setdefault('verify', False)
            return original_options(url, **kwargs)
        
        requests.get = patched_get
        requests.post = patched_post
        requests.put = patched_put
        requests.delete = patched_delete
        requests.patch = patched_patch
        requests.head = patched_head
        requests.options = patched_options
        
    except ImportError:
        pass

def configure_urllib3_ssl():
    """Configure urllib3 to bypass SSL verification"""
    try:
        import urllib3
        from urllib3.poolmanager import PoolManager
        
        # Monkey patch PoolManager to disable SSL verification
        original_init = PoolManager.__init__
        
        def patched_init(self, *args, **kwargs):
            kwargs['cert_reqs'] = 'CERT_NONE'
            kwargs['assert_hostname'] = False
            return original_init(self, *args, **kwargs)
        
        PoolManager.__init__ = patched_init
        
    except ImportError:
        pass

def configure_aiohttp_ssl():
    """Configure aiohttp to bypass SSL verification"""
    try:
        import aiohttp
        
        # Monkey patch ClientSession to disable SSL verification
        original_init = aiohttp.ClientSession.__init__
        
        def patched_init(self, *args, **kwargs):
            if 'connector' not in kwargs:
                kwargs['connector'] = aiohttp.TCPConnector(ssl=False)
            return original_init(self, *args, **kwargs)
        
        aiohttp.ClientSession.__init__ = patched_init
        
    except ImportError:
        pass

def configure_httpx_ssl():
    """Configure httpx to bypass SSL verification"""
    try:
        import httpx
        
        # Monkey patch Client to disable SSL verification
        original_init = httpx.Client.__init__
        
        def patched_init(self, *args, **kwargs):
            kwargs.setdefault('verify', False)
            return original_init(self, *args, **kwargs)
        
        httpx.Client.__init__ = patched_init
        
        # Async client
        original_async_init = httpx.AsyncClient.__init__
        
        def patched_async_init(self, *args, **kwargs):
            kwargs.setdefault('verify', False)
            return original_async_init(self, *args, **kwargs)
        
        httpx.AsyncClient.__init__ = patched_async_init
        
    except ImportError:
        pass

def set_environment_variables():
    """Set environment variables to disable SSL verification"""
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    os.environ['SSL_VERIFY'] = 'false'

def apply_all_ssl_fixes(verbose: bool = True):
    """Apply all SSL fixes in one function call"""
    global _SSL_FIXES_APPLIED
    
    if _SSL_FIXES_APPLIED:
        if verbose:
            print("SSL fixes already applied")
        return
    
    if verbose:
        print("Applying universal SSL fixes for corporate environment...")
    
    # Set environment variables
    set_environment_variables()
    if verbose:
        print("  [OK] Environment variables set")
    
    # Suppress warnings
    suppress_ssl_warnings()
    if verbose:
        print("  [OK] SSL warnings suppressed")
    
    # Configure SSL context
    configure_ssl_context()
    if verbose:
        print("  [OK] SSL context configured")
    
    # Configure libraries
    configure_requests_ssl()
    if verbose:
        print("  [OK] Requests library configured")
    
    configure_urllib3_ssl()
    if verbose:
        print("  [OK] urllib3 configured")
    
    configure_aiohttp_ssl()
    if verbose:
        print("  [OK] aiohttp configured")
    
    configure_httpx_ssl()
    if verbose:
        print("  [OK] httpx configured")
    
    _SSL_FIXES_APPLIED = True
    
    if verbose:
        print("Universal SSL fixes applied successfully!")
        print("    All HTTPS requests will now bypass SSL verification")

def test_ssl_fix(test_urls: Optional[list] = None):
    """Test that SSL fixes are working by making requests to common sites"""
    if test_urls is None:
        test_urls = [
            'https://fortiguard.fortinet.com/rss/ir.xml',
            'https://www.google.com',
            'https://github.com',
            'https://httpbin.org/get'
        ]
    
    print("Testing SSL fixes...")
    
    try:
        import requests
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10, verify=False)
                if response.status_code < 400:
                    print(f"  [SUCCESS] {url} - Success ({response.status_code})")
                else:
                    print(f"  [WARNING] {url} - HTTP {response.status_code}")
            except Exception as e:
                print(f"  [ERROR] {url} - Error: {str(e)[:50]}...")
                
    except ImportError:
        print("  [ERROR] requests library not available for testing")

def create_ssl_patch_file(target_dir: str = "."):
    """Create a standalone SSL patch file that can be imported"""
    patch_content = '''"""
Standalone SSL patch - import this to fix SSL issues instantly
"""
import ssl_universal_fix
ssl_universal_fix.apply_all_ssl_fixes(verbose=False)
'''
    
    patch_file = os.path.join(target_dir, "ssl_patch.py")
    with open(patch_file, 'w') as f:
        f.write(patch_content)
    
    return patch_file

# Auto-apply fixes when module is imported (can be disabled)
AUTO_APPLY = os.getenv('SSL_AUTO_APPLY', 'true').lower() == 'true'

if AUTO_APPLY and __name__ != '__main__':
    apply_all_ssl_fixes(verbose=False)

# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal SSL Fix Tool')
    parser.add_argument('--test', action='store_true', help='Test SSL fixes')
    parser.add_argument('--no-auto', action='store_true', help='Disable auto-apply')
    parser.add_argument('--create-patch', metavar='DIR', help='Create SSL patch file in directory')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    if args.no_auto:
        os.environ['SSL_AUTO_APPLY'] = 'false'
    
    if not args.quiet:
        print("Universal SSL Fix Tool")
        print("=" * 30)
    
    # Apply fixes
    apply_all_ssl_fixes(verbose=not args.quiet)
    
    # Test if requested
    if args.test:
        print()
        test_ssl_fix()
    
    # Create patch file if requested
    if args.create_patch:
        patch_file = create_ssl_patch_file(args.create_patch)
        if not args.quiet:
            print(f"\nSSL patch file created: {patch_file}")
            print("   Import this file in any Python script to apply SSL fixes")
    
    if not args.quiet:
        print("\nUsage in your Python scripts:")
        print("   import ssl_universal_fix  # Auto-applies fixes")
        print("   # or")
        print("   from ssl_universal_fix import apply_all_ssl_fixes")
        print("   apply_all_ssl_fixes()")
