import requests
import ssl
import socket
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import subprocess
import json

def diagnose_ssl_errors(mac_address="44:38:39:ff:ef:57"):
    """
    Diagnose specific SSL errors when connecting to MAC lookup APIs
    """
    print(f"🔍 SSL DIAGNOSTIC TOOL FOR MAC: {mac_address}")
    print("=" * 70)
    
    test_urls = [
        f"https://api.macvendors.com/{mac_address}",
        f"https://macvendors.co/api/{mac_address}",
        "https://www.google.com",  # Control test
        "https://httpbin.org/get"  # Control test
    ]
    
    for url in test_urls:
        print(f"\n🌐 Testing: {url}")
        print("-" * 50)
        
        # Test 1: Basic requests
        try:
            response = requests.get(url, timeout=10, verify=True)
            print(f"✅ requests (verify=True): Status {response.status_code}")
            if 'macvendors' in url:
                print(f"   Response: {response.text.strip()}")
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error (verify=True): {str(e)}")
        except requests.exceptions.ConnectionError as e:
            print(f"🚫 Connection Error (verify=True): {str(e)}")
        except Exception as e:
            print(f"❌ Other Error (verify=True): {str(e)}")
        
        # Test 2: No SSL verification
        try:
            urllib3.disable_warnings(InsecureRequestWarning)
            response = requests.get(url, timeout=10, verify=False)
            print(f"✅ requests (verify=False): Status {response.status_code}")
            if 'macvendors' in url:
                print(f"   Response: {response.text.strip()}")
        except Exception as e:
            print(f"❌ Error (verify=False): {str(e)}")
        
        # Test 3: SSL context details
        try:
            hostname = url.split('//')[1].split('/')[0]
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    print(f"✅ SSL Context: {ssock.version()}")
                    print(f"   Cipher: {ssock.cipher()}")
                    cert = ssock.getpeercert()
                    print(f"   Subject: {cert.get('subject', 'Unknown')}")
                    print(f"   Issuer: {cert.get('issuer', 'Unknown')}")
        except Exception as e:
            print(f"🔒 SSL Context Error: {str(e)}")
        
        # Test 4: curl comparison
        try:
            curl_cmd = ['curl', '-v', '-s', '--max-time', '10', url]
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print(f"✅ curl: Success")
                if 'macvendors' in url:
                    print(f"   Response: {result.stdout.strip()}")
            else:
                print(f"❌ curl: Failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"⏰ curl: Timeout")
        except Exception as e:
            print(f"❌ curl Error: {str(e)}")

def get_system_ssl_info():
    """
    Get system SSL/TLS information
    """
    print(f"\n🔧 SYSTEM SSL/TLS INFORMATION")
    print("=" * 50)
    
    # Python SSL info
    print(f"Python SSL version: {ssl.OPENSSL_VERSION}")
    print(f"Python SSL version info: {ssl.OPENSSL_VERSION_INFO}")
    print(f"Default SSL context: {ssl.create_default_context()}")
    
    # Check available ciphers
    try:
        context = ssl.create_default_context()
        print(f"Available ciphers: {len(context.get_ciphers())}")
        print(f"Security level: {context.security_level}")
        print(f"Check hostname: {context.check_hostname}")
        print(f"Verify mode: {context.verify_mode}")
    except Exception as e:
        print(f"Error getting SSL context info: {e}")
    
    # Windows certificate store check (if on Windows)
    try:
        import certifi
        print(f"Certifi CA bundle: {certifi.where()}")
    except ImportError:
        print("Certifi not available")

if __name__ == "__main__":
    import sys
    
    get_system_ssl_info()
    
    mac_address = sys.argv[1] if len(sys.argv) > 1 else "44:38:39:ff:ef:57"
    diagnose_ssl_errors(mac_address)