import requests
import ssl
import os
import tempfile
import shutil
from typing import Optional

class ZscalerManualSetup:
    """
    Manual Zscaler certificate setup for SSL verification
    
    This provides step-by-step instructions and tools for manually configuring
    Zscaler certificates to fix SSL verification issues in corporate environments.
    """
    
    def __init__(self):
        self.custom_bundle_path = None
    
    def create_instructions(self):
        """
        Display step-by-step instructions for manually obtaining Zscaler certificates
        """
        print("🛡️ MANUAL ZSCALER CERTIFICATE SETUP")
        print("=" * 70)
        print("Since auto-detection didn't find Zscaler certificates, here's how to")
        print("manually obtain and configure them:")
        print()
        
        print("📋 METHOD 1: Export from Browser")
        print("-" * 40)
        print("1. Open Chrome/Edge and visit any HTTPS website")
        print("2. Click the padlock icon in the address bar")
        print("3. Click 'Certificate' or 'Certificate (Valid)'")
        print("4. Go to the 'Certification Path' tab")
        print("5. Look for the root certificate (top of the chain)")
        print("6. Select the root certificate and click 'View Certificate'")
        print("7. Go to 'Details' tab → 'Copy to File' → Export as")
        print("   'Base-64 encoded X.509 (.CER)'")
        print("8. Save as 'zscaler_root.crt' in this directory")
        print()
        
        print("📋 METHOD 2: Windows Certificate Manager")
        print("-" * 40)
        print("1. Press Win + R, type 'certmgr.msc', press Enter")
        print("2. Navigate to: Trusted Root Certification Authorities → Certificates")
        print("3. Look for certificates containing 'Zscaler' or your company name")
        print("4. Right-click the certificate → All Tasks → Export")
        print("5. Choose 'Base-64 encoded X.509 (.CER)'")
        print("6. Save as 'zscaler_root.crt' in this directory")
        print()
        
        print("📋 METHOD 3: PowerShell (Alternative)")
        print("-" * 40)
        print("Run this PowerShell command as Administrator:")
        print("Get-ChildItem -Path 'Cert:\\CurrentUser\\Root' | Where-Object {$_.Subject -like '*Zscaler*'} | Export-Certificate -FilePath .\\zscaler_root.cer")
        print()
        
        print("📋 METHOD 4: Contact IT Team")
        print("-" * 40)
        print("Ask your IT team for:")
        print("- Zscaler root certificate file")
        print("- Corporate SSL inspection certificate")
        print("- Instructions for SSL certificate configuration")
        print()
        
        print("🔧 AFTER OBTAINING THE CERTIFICATE:")
        print("=" * 50)
        print("1. Place the certificate file in this directory as 'zscaler_root.crt'")
        print("2. Run: python zscaler_manual_setup.py configure")
        print("3. Test with: python zscaler_manual_setup.py test")
        
    def configure_certificate(self, cert_path: str = "zscaler_root.crt") -> bool:
        """
        Configure the Zscaler certificate for use with Python requests
        """
        print(f"\n🔧 CONFIGURING ZSCALER CERTIFICATE: {cert_path}")
        print("-" * 60)
        
        if not os.path.exists(cert_path):
            print(f"❌ Certificate file not found: {cert_path}")
            print("Please obtain the Zscaler certificate first (see instructions above)")
            return False
        
        try:
            import certifi
            
            # Get the default CA bundle
            default_bundle = certifi.where()
            print(f"📄 Default CA bundle: {default_bundle}")
            
            # Create custom bundle
            self.custom_bundle_path = os.path.join(os.getcwd(), "custom_ca_bundle.pem")
            
            # Copy default bundle
            shutil.copy2(default_bundle, self.custom_bundle_path)
            print(f"📋 Copied default CA bundle to: {self.custom_bundle_path}")
            
            # Read and validate Zscaler certificate
            with open(cert_path, 'r', encoding='utf-8') as f:
                cert_content = f.read().strip()
            
            # Check if it's a valid certificate format
            if not ("BEGIN CERTIFICATE" in cert_content and "END CERTIFICATE" in cert_content):
                print("❌ Invalid certificate format. Expected PEM format with BEGIN/END CERTIFICATE markers.")
                return False
            
            # Append Zscaler certificate to bundle
            with open(self.custom_bundle_path, 'a', encoding='utf-8') as f:
                f.write('\n\n# Zscaler Corporate Root Certificate\n')
                f.write(cert_content)
                if not cert_content.endswith('\n'):
                    f.write('\n')
            
            print("✅ Successfully created custom CA bundle with Zscaler certificate")
            print(f"📦 Custom bundle location: {self.custom_bundle_path}")
            
            # Set environment variable
            os.environ['REQUESTS_CA_BUNDLE'] = self.custom_bundle_path
            print("✅ Set REQUESTS_CA_BUNDLE environment variable")
            
            return True
            
        except ImportError:
            print("❌ certifi package not available. Install with: pip install certifi")
            return False
        except Exception as e:
            print(f"❌ Error configuring certificate: {e}")
            return False
    
    def test_ssl_connection(self, test_url: str = "https://api.macvendors.com/44:38:39:ff:ef:57") -> bool:
        """
        Test SSL connection with the configured certificate
        """
        print(f"\n🧪 TESTING SSL CONNECTION")
        print("-" * 40)
        print(f"Test URL: {test_url}")
        
        if not self.custom_bundle_path or not os.path.exists(self.custom_bundle_path):
            print("❌ Custom CA bundle not configured. Run configure first.")
            return False
        
        try:
            print("🔍 Testing with custom CA bundle...")
            
            response = requests.get(
                test_url,
                timeout=15,
                verify=self.custom_bundle_path,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; Zscaler-SSL-Test/1.0)'}
            )
            
            if response.status_code == 200:
                print("✅ SUCCESS! SSL verification working with Zscaler certificate")
                print(f"📄 Response: {response.text.strip()}")
                
                # Save configuration for future use
                config_file = "zscaler_config.txt"
                with open(config_file, 'w') as f:
                    f.write(f"REQUESTS_CA_BUNDLE={self.custom_bundle_path}\n")
                    f.write(f"# Use this environment variable in your scripts\n")
                    f.write(f"# export REQUESTS_CA_BUNDLE='{self.custom_bundle_path}'\n")
                
                print(f"💾 Configuration saved to: {config_file}")
                return True
            else:
                print(f"⚠️ SSL connected but HTTP error: {response.status_code}")
                return False
                
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error: {str(e)[:150]}...")
            print("❌ The certificate may not be the correct root certificate")
            print("💡 Try obtaining a different certificate or contact IT")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection Error: {str(e)[:150]}...")
            return False
        except Exception as e:
            print(f"❌ Test failed: {str(e)[:150]}...")
            return False
    
    def create_zscaler_aware_lookup_function(self):
        """
        Create a MAC lookup function that uses the Zscaler-configured SSL
        """
        if not self.custom_bundle_path:
            print("❌ Custom CA bundle not configured")
            return None
        
        def mac_lookup_with_zscaler(mac_address: str) -> Optional[str]:
            """MAC lookup using Zscaler-compatible SSL configuration"""
            try:
                response = requests.get(
                    f"https://api.macvendors.com/{mac_address}",
                    timeout=10,
                    verify=self.custom_bundle_path,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; Zscaler-MAC-Lookup/1.0)'}
                )
                
                if response.status_code == 200:
                    result = response.text.strip()
                    if len(result) > 3 and 'not found' not in result.lower():
                        return result
                
            except Exception as e:
                print(f"❌ Lookup failed: {str(e)[:100]}")
                
            return None
        
        return mac_lookup_with_zscaler
    
    def integration_example(self):
        """
        Show example code for integrating Zscaler SSL configuration
        """
        if not self.custom_bundle_path:
            print("❌ No custom bundle configured")
            return
        
        example_code = f'''
# EXAMPLE: Integrating Zscaler SSL Configuration

import os
import requests

# Method 1: Set environment variable (recommended)
os.environ['REQUESTS_CA_BUNDLE'] = '{self.custom_bundle_path}'

# Now all requests will use the custom bundle
response = requests.get('https://api.macvendors.com/44:38:39:ff:ef:57')

# Method 2: Specify verify parameter for each request
response = requests.get(
    'https://api.macvendors.com/44:38:39:ff:ef:57',
    verify='{self.custom_bundle_path}'
)

# Method 3: Configure session with custom bundle
session = requests.Session()
session.verify = '{self.custom_bundle_path}'
response = session.get('https://api.macvendors.com/44:38:39:ff:ef:57')
'''
        
        print("🔧 INTEGRATION EXAMPLE CODE:")
        print("=" * 50)
        print(example_code)
        
        # Save example to file
        with open('zscaler_integration_example.py', 'w') as f:
            f.write(example_code)
        
        print(f"💾 Example code saved to: zscaler_integration_example.py")

def main():
    import sys
    
    setup = ZscalerManualSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "configure":
            cert_file = sys.argv[2] if len(sys.argv) > 2 else "zscaler_root.crt"
            if setup.configure_certificate(cert_file):
                setup.integration_example()
        
        elif command == "test":
            # Load existing configuration
            if os.path.exists("custom_ca_bundle.pem"):
                setup.custom_bundle_path = os.path.abspath("custom_ca_bundle.pem")
                os.environ['REQUESTS_CA_BUNDLE'] = setup.custom_bundle_path
                setup.test_ssl_connection()
            else:
                print("❌ No configuration found. Run 'configure' first.")
        
        elif command == "lookup":
            mac_address = sys.argv[2] if len(sys.argv) > 2 else "44:38:39:ff:ef:57"
            
            if os.path.exists("custom_ca_bundle.pem"):
                setup.custom_bundle_path = os.path.abspath("custom_ca_bundle.pem")
                lookup_func = setup.create_zscaler_aware_lookup_function()
                
                if lookup_func:
                    print(f"🔍 Looking up MAC: {mac_address}")
                    result = lookup_func(mac_address)
                    if result:
                        print(f"✅ Result: {result}")
                    else:
                        print("❌ Lookup failed")
            else:
                print("❌ No configuration found. Run 'configure' first.")
        
        else:
            print("❌ Unknown command. Use: configure, test, or lookup")
    
    else:
        # Show instructions
        setup.create_instructions()
        
        print("\n🚀 QUICK START:")
        print("=" * 30)
        print("1. python zscaler_manual_setup.py              # Show instructions")
        print("2. python zscaler_manual_setup.py configure    # Configure certificate")
        print("3. python zscaler_manual_setup.py test         # Test configuration")
        print("4. python zscaler_manual_setup.py lookup MAC   # Test MAC lookup")

if __name__ == "__main__":
    main()