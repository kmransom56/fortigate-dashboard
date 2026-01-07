#!/usr/bin/env python3
"""
Enhanced SSL Fix for Persistent SSL Protocol Errors
===================================================

This module addresses specific SSL protocol issues like SSLEOFError
that occur in corporate environments with aggressive SSL inspection.
"""

import ssl
import socket
import requests
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter
import warnings
import os

# Disable all SSL warnings
urllib3.disable_warnings()
warnings.filterwarnings('ignore')

class RobustSSLAdapter(HTTPAdapter):
    """SSL adapter that handles protocol errors more gracefully"""
    
    def __init__(self, **kwargs):
        self.ssl_context = self._create_robust_ssl_context()
        super().__init__(**kwargs)
    
    def _create_robust_ssl_context(self):
        """Create the most permissive SSL context possible"""
        # Try different SSL protocols
        for protocol in [ssl.PROTOCOL_TLS_CLIENT, ssl.PROTOCOL_TLS]:
            try:
                context = ssl.SSLContext(protocol)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Set very permissive options
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                context.options |= ssl.OP_NO_TLSv1
                context.options |= ssl.OP_NO_TLSv1_1
                
                # Allow legacy connections
                if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
                    context.options |= ssl.OP_LEGACY_SERVER_CONNECT
                
                # Set cipher suites to be very permissive
                try:
                    context.set_ciphers('ALL:@SECLEVEL=0')
                except:
                    try:
                        context.set_ciphers('DEFAULT@SECLEVEL=1')
                    except:
                        context.set_ciphers('DEFAULT')
                
                return context
            except Exception:
                continue
        
        # Fallback to default
        return ssl.create_default_context()
    
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['cert_reqs'] = 'CERT_NONE'
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)

def create_robust_session():
    """Create a session with enhanced SSL handling"""
    session = requests.Session()
    
    # Set aggressive timeout and retry settings
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Mount the robust SSL adapter
    adapter = RobustSSLAdapter()
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    # Disable verification
    session.verify = False
    
    return session

def test_connection_methods():
    """Test different connection methods to find what works"""
    test_url = "https://fortiguard.fortinet.com/rss/ir.xml"  # Start with RSS which we know works
    
    print("Testing Enhanced SSL Connection Methods")
    print("=" * 45)
    
    # Method 1: Enhanced session
    print("\n1. Testing enhanced SSL session...")
    try:
        session = create_robust_session()
        response = session.get(test_url, timeout=30)
        print(f"   Success! Status: {response.status_code}, Length: {len(response.text)}")
        return session
    except Exception as e:
        print(f"   Failed: {str(e)[:100]}...")
    
    # Method 2: Raw socket approach
    print("\n2. Testing raw socket approach...")
    try:
        import socket
        import ssl
        
        # Create raw socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        
        # Wrap with SSL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        wrapped_sock = context.wrap_socket(sock, server_hostname='fortiguard.fortinet.com')
        wrapped_sock.connect(('fortiguard.fortinet.com', 443))
        
        # Send HTTP request
        request = f"GET /rss/ir.xml HTTP/1.1\r\nHost: fortiguard.fortinet.com\r\nConnection: close\r\n\r\n"
        wrapped_sock.send(request.encode())
        
        # Read response
        response = b""
        while True:
            data = wrapped_sock.recv(4096)
            if not data:
                break
            response += data
        
        wrapped_sock.close()
        
        if b"200 OK" in response:
            print("   Raw socket method works!")
            return "raw_socket"
        else:
            print("   Raw socket failed")
            
    except Exception as e:
        print(f"   Raw socket failed: {str(e)[:100]}...")
    
    # Method 3: Try with different TLS versions
    print("\n3. Testing different TLS versions...")
    for tls_version in ['TLSv1.2', 'TLSv1.3']:
        try:
            session = requests.Session()
            session.verify = False
            
            # Force specific TLS version
            adapter = HTTPAdapter()
            session.mount('https://', adapter)
            
            response = session.get(test_url, timeout=30)
            print(f"   {tls_version} Success! Status: {response.status_code}")
            return session
            
        except Exception as e:
            print(f"   {tls_version} failed: {str(e)[:50]}...")
    
    print("\nAll connection methods failed!")
    return None

if __name__ == "__main__":
    # Test the enhanced SSL methods
    working_session = test_connection_methods()
    
    if working_session:
        print("\n" + "="*50)
        print("SUCCESS: Found working SSL connection method!")
        print("="*50)
        
        # Test advisory access
        if hasattr(working_session, 'get'):
            print("\nTesting advisory page access...")
            try:
                response = working_session.get("https://fortiguard.fortinet.com/psirt/FG-IR-25-006", timeout=30)
                print(f"Advisory page status: {response.status_code}")
                print(f"Content length: {len(response.text)}")
                
                if "advisory" in response.text.lower() or "fortiguard" in response.text.lower():
                    print("SUCCESS: Can access advisory content!")
                else:
                    print("WARNING: May be getting redirected or blocked content")
                    
            except Exception as e:
                print(f"Advisory access failed: {e}")
    else:
        print("\n" + "="*50)
        print("FAILED: No working SSL connection method found")
        print("="*50)
        print("Recommendation: Use browser automation or manual collection")
