import requests
import ssl
import os
import platform
import subprocess
from pathlib import Path
import tempfile
import shutil
from typing import Optional, List

class ZscalerSSLFix:
    """
    Fix SSL certificate verification issues in Zscaler corporate environments
    
    Zscaler intercepts SSL traffic and replaces certificates with its own,
    causing Python requests to fail SSL verification. This class locates
    and configures Zscaler certificates for Python to use.
    """
    
    def __init__(self):
        self.zscaler_cert_path = None
        self.original_ca_bundle = None
        self.custom_ca_bundle = None
        
    def find_zscaler_certificates(self) -> List[str]:
        """
        Find Zscaler certificate files on the system
        """
        potential_paths = []
        
        if platform.system() == "Windows":
            # Common Zscaler certificate locations on Windows
            user_profile = os.environ.get('USERPROFILE', '')
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
            
            zscaler_paths = [
                # Zscaler app data locations
                os.path.join(user_profile, 'AppData', 'Local', 'Zscaler', 'ZscalerOne'),
                os.path.join(user_profile, 'AppData', 'Roaming', 'Zscaler'),
                os.path.join(program_files, 'Zscaler'),
                os.path.join(program_files_x86, 'Zscaler'),
                
                # Common certificate storage locations
                os.path.join(user_profile, '.zscaler'),
                'C:\\ProgramData\\Zscaler',
                'C:\\Zscaler',
                
                # Windows certificate store exports
                os.path.join(user_profile, 'Documents'),
                os.path.join(user_profile, 'Desktop'),
            ]
            
            # Look for certificate files
            cert_extensions = ['.crt', '.cer', '.pem', '.p7b', '.p12', '.pfx']
            
            for base_path in zscaler_paths:
                if os.path.exists(base_path):
                    try:
                        for root, dirs, files in os.walk(base_path):
                            for file in files:
                                if any(file.lower().endswith(ext) for ext in cert_extensions):
                                    if 'zscaler' in file.lower() or 'root' in file.lower():
                                        potential_paths.append(os.path.join(root, file))
                    except (PermissionError, OSError):
                        continue
        
        return potential_paths
    
    def export_windows_certificates(self) -> Optional[str]:
        """
        Export certificates from Windows certificate store that might include Zscaler certs
        """
        try:
            # Create temporary file for certificate export
            temp_cert_file = os.path.join(tempfile.gettempdir(), 'zscaler_certs.pem')
            
            # PowerShell command to export root certificates
            powershell_cmd = f"""
            $certs = Get-ChildItem -Path Cert:\\LocalMachine\\Root | Where-Object {{$_.Subject -like "*Zscaler*" -or $_.Issuer -like "*Zscaler*"}}
            if ($certs) {{
                $certs | ForEach-Object {{
                    $cert = $_
                    $base64 = [System.Convert]::ToBase64String($cert.RawData)
                    "-----BEGIN CERTIFICATE-----" | Out-File -FilePath "{temp_cert_file}" -Append -Encoding ascii
                    for ($i = 0; $i -lt $base64.Length; $i += 64) {{
                        $line = $base64.Substring($i, [Math]::Min(64, $base64.Length - $i))
                        $line | Out-File -FilePath "{temp_cert_file}" -Append -Encoding ascii
                    }}
                    "-----END CERTIFICATE-----" | Out-File -FilePath "{temp_cert_file}" -Append -Encoding ascii
                }}
                Write-Output "Exported Zscaler certificates to {temp_cert_file}"
            }} else {{
                Write-Output "No Zscaler certificates found in Windows certificate store"
            }}
            """
            
            result = subprocess.run(['powershell', '-Command', powershell_cmd], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_cert_file):
                print(f"✅ Exported Zscaler certificates to: {temp_cert_file}")
                return temp_cert_file
            else:
                print(f"❌ Failed to export certificates: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error exporting Windows certificates: {e}")
            
        return None
    
    def create_custom_ca_bundle(self, zscaler_cert_path: str) -> Optional[str]:
        """
        Create a custom CA bundle that includes both system CAs and Zscaler certificates
        """
        try:
            import certifi
            
            # Get the default certifi CA bundle
            default_ca_bundle = certifi.where()
            
            # Create custom bundle file
            custom_bundle_path = os.path.join(tempfile.gettempdir(), 'custom_ca_bundle.pem')
            
            # Copy default CA bundle
            shutil.copy2(default_ca_bundle, custom_bundle_path)
            
            # Append Zscaler certificates
            if os.path.exists(zscaler_cert_path):
                with open(custom_bundle_path, 'a', encoding='utf-8') as bundle_file:
                    bundle_file.write('\n# Zscaler Corporate Certificates\n')
                    
                    with open(zscaler_cert_path, 'r', encoding='utf-8') as zscaler_file:
                        bundle_file.write(zscaler_file.read())
                
                print(f"✅ Created custom CA bundle: {custom_bundle_path}")
                return custom_bundle_path
            else:
                print(f"❌ Zscaler certificate file not found: {zscaler_cert_path}")
                
        except ImportError:
            print("❌ certifi package not available")
        except Exception as e:
            print(f"❌ Error creating custom CA bundle: {e}")
            
        return None
    
    def test_ssl_with_custom_bundle(self, ca_bundle_path: str, test_url: str = "https://api.macvendors.com/44:38:39:ff:ef:57") -> bool:
        """
        Test SSL connection using custom CA bundle
        """
        try:
            print(f"🧪 Testing SSL with custom bundle: {test_url}")
            
            response = requests.get(
                test_url,
                timeout=10,
                verify=ca_bundle_path,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; Zscaler-SSL-Test/1.0)'}
            )
            
            if response.status_code == 200:
                print(f"✅ SSL test successful!")
                print(f"✅ Response: {response.text.strip()}")
                return True
            else:
                print(f"⚠️ SSL connected but HTTP {response.status_code}")
                return False
                
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error: {str(e)[:100]}...")
            return False
        except Exception as e:
            print(f"❌ Test failed: {str(e)[:100]}...")
            return False
    
    def configure_requests_for_zscaler(self) -> Optional[str]:
        """
        Configure requests to work with Zscaler certificates
        """
        print("🔧 CONFIGURING PYTHON REQUESTS FOR ZSCALER")
        print("=" * 60)
        
        # Step 1: Find existing Zscaler certificates
        print("1️⃣ Searching for existing Zscaler certificates...")
        found_certs = self.find_zscaler_certificates()
        
        if found_certs:
            print(f"✅ Found {len(found_certs)} potential certificate files:")
            for cert in found_certs[:5]:  # Show first 5
                print(f"   📄 {cert}")
            
            # Try the first found certificate
            zscaler_cert = found_certs[0]
        else:
            print("❌ No existing Zscaler certificates found")
            
            # Step 2: Try to export from Windows certificate store
            print("2️⃣ Attempting to export Zscaler certificates from Windows...")
            zscaler_cert = self.export_windows_certificates()
        
        if not zscaler_cert:
            print("❌ Could not locate or export Zscaler certificates")
            return None
        
        # Step 3: Create custom CA bundle
        print("3️⃣ Creating custom CA bundle...")
        custom_bundle = self.create_custom_ca_bundle(zscaler_cert)
        
        if not custom_bundle:
            print("❌ Failed to create custom CA bundle")
            return None
        
        # Step 4: Test the configuration
        print("4️⃣ Testing SSL configuration...")
        if self.test_ssl_with_custom_bundle(custom_bundle):
            self.custom_ca_bundle = custom_bundle
            self.zscaler_cert_path = zscaler_cert
            
            print(f"\n🎯 SUCCESS! Zscaler SSL configuration complete")
            print(f"📄 Zscaler cert: {zscaler_cert}")
            print(f"📦 Custom bundle: {custom_bundle}")
            
            return custom_bundle
        else:
            print("❌ SSL test failed with custom bundle")
            return None
    
    def create_zscaler_aware_mac_lookup(self):
        """
        Create MAC lookup function that uses Zscaler-aware SSL configuration
        """
        if not self.custom_ca_bundle:
            print("❌ No custom CA bundle configured. Run configure_requests_for_zscaler() first.")
            return None
        
        def zscaler_mac_lookup(mac_address: str) -> Optional[str]:
            """MAC lookup using Zscaler-compatible SSL configuration"""
            try:
                print(f"🔍 Looking up {mac_address} with Zscaler SSL config...")
                
                response = requests.get(
                    f"https://api.macvendors.com/{mac_address}",
                    timeout=10,
                    verify=self.custom_ca_bundle,  # Use custom bundle with Zscaler certs
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; Zscaler-MAC-Lookup/1.0)'}
                )
                
                if response.status_code == 200:
                    result = response.text.strip()
                    if len(result) > 3 and 'not found' not in result.lower():
                        print(f"✅ Found via Zscaler-SSL: {result}")
                        return result
                
            except requests.exceptions.SSLError as e:
                print(f"🔒 SSL Error (even with Zscaler config): {str(e)[:100]}")
            except Exception as e:
                print(f"❌ Lookup failed: {str(e)[:100]}")
                
            return None
        
        return zscaler_mac_lookup

def demonstrate_zscaler_solution():
    """
    Demonstrate the complete Zscaler SSL solution
    """
    print("🛡️ ZSCALER SSL CERTIFICATE SOLUTION")
    print("=" * 70)
    print("This tool configures Python to use Zscaler certificates for SSL verification")
    print("in corporate environments where Zscaler intercepts SSL traffic.")
    print()
    
    zscaler_fix = ZscalerSSLFix()
    
    # Configure Zscaler SSL
    custom_bundle = zscaler_fix.configure_requests_for_zscaler()
    
    if custom_bundle:
        print("\n🧪 TESTING ZSCALER-AWARE MAC LOOKUP")
        print("=" * 50)
        
        # Create Zscaler-aware MAC lookup function
        mac_lookup = zscaler_fix.create_zscaler_aware_mac_lookup()
        
        if mac_lookup:
            # Test with known MAC
            test_mac = "44:38:39:ff:ef:57"
            result = mac_lookup(test_mac)
            
            if result:
                print(f"\n🎯 SUCCESS! {test_mac} → {result}")
                print("✅ Zscaler SSL configuration is working!")
            else:
                print(f"\n❌ MAC lookup failed even with Zscaler config")
        
        print(f"\n📋 INTEGRATION INSTRUCTIONS:")
        print(f"To use this in your scripts, set the REQUESTS_CA_BUNDLE environment variable:")
        print(f"export REQUESTS_CA_BUNDLE='{custom_bundle}'")
        print(f"or in Python:")
        print(f"os.environ['REQUESTS_CA_BUNDLE'] = '{custom_bundle}'")
        
    else:
        print("\n❌ Could not configure Zscaler SSL. Recommendations:")
        print("1. Check if Zscaler certificates are installed")
        print("2. Try exporting Zscaler root certificate manually")
        print("3. Contact your IT team for the Zscaler CA certificate")
        print("4. Use the curl-based solution as fallback")

def manual_zscaler_cert_instructions():
    """
    Provide manual instructions for obtaining Zscaler certificates
    """
    instructions = """
# MANUAL ZSCALER CERTIFICATE SETUP

## Method 1: Export from Browser
1. Open Chrome/Edge and visit any HTTPS site
2. Click the lock icon → Certificate → Details tab
3. Look for certificates issued by "Zscaler" or your company
4. Export as Base-64 encoded X.509 (.CER)
5. Save as 'zscaler_root.crt'

## Method 2: Windows Certificate Manager
1. Press Win+R, type 'certmgr.msc', press Enter
2. Navigate to Trusted Root Certification Authorities → Certificates
3. Look for certificates with "Zscaler" in the name
4. Right-click → All Tasks → Export
5. Choose Base-64 encoded X.509 (.CER)

## Method 3: PowerShell Export
```powershell
Get-ChildItem -Path Cert:\\LocalMachine\\Root | Where-Object {$_.Subject -like "*Zscaler*"} | Export-Certificate -FilePath C:\\temp\\zscaler.cer -Type CERT
```

## Method 4: Contact IT Team
Ask your IT team for:
- Zscaler root certificate file
- Corporate certificate bundle
- SSL inspection certificate

## Usage in Python:
```python
import os
os.environ['REQUESTS_CA_BUNDLE'] = 'path/to/zscaler_bundle.pem'
# or
import requests
requests.get(url, verify='path/to/zscaler_bundle.pem')
```
"""
    
    with open('zscaler_manual_setup.md', 'w') as f:
        f.write(instructions)
    
    print("📄 Manual setup instructions saved to: zscaler_manual_setup.md")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        manual_zscaler_cert_instructions()
    else:
        demonstrate_zscaler_solution()