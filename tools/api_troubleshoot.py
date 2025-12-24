#!/usr/bin/env python3
"""
FortiGate API User & Token Troubleshooting Script

This script performs comprehensive testing of:
1. API user authentication methods
2. Token formats and validation
3. Permission verification
4. Different API endpoints
"""

import requests
import json
import os
from urllib.parse import urlencode
import base64

# Disable SSL warnings for self-signed certificates
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiGateAPITroubleshooter:
    def __init__(self):
        self.host = "192.168.0.254"
        self.base_url = f"https://{self.host}"
        self.session = requests.Session()
        self.session.verify = False

        # Load credentials
        self.admin_user = "admin"
        self.api_user = "programaticallydothings"
        self.password = "!cg@RW%G@o"
        self.api_token = "zpq4gHxqj8dzpGxfkzmskc54Qhbzq3"

        print(f"🔧 FortiGate API Troubleshooter")
        print(f"Host: {self.host}")
        print(f"API User: {self.api_user}")
        print(f"Token: {self.api_token[:10]}...")
        print("=" * 60)

    def test_basic_connectivity(self):
        """Test basic connectivity to FortiGate"""
        print("\n1️⃣ Testing Basic Connectivity")
        print("-" * 40)

        try:
            response = self.session.get(f"{self.base_url}/login", timeout=10)
            print(f"✅ Connection successful: HTTP {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def test_admin_session_login(self):
        """Test admin user session login"""
        print("\n2️⃣ Testing Admin Session Login")
        print("-" * 40)

        try:
            login_data = {"username": self.admin_user, "secretkey": self.password}

            response = self.session.post(
                f"{self.base_url}/logincheck",
                data=login_data,
                timeout=10,
                allow_redirects=False,
            )

            print(f"Login Response: HTTP {response.status_code}")

            # Check for session cookies
            cookies = self.session.cookies.get_dict()
            print(f"Cookies received: {list(cookies.keys())}")

            if response.status_code in [200, 302] and cookies:
                print("✅ Admin session login successful")
                return True
            else:
                print("❌ Admin session login failed")
                return False

        except Exception as e:
            print(f"❌ Admin session login error: {e}")
            return False

    def test_api_user_session_login(self):
        """Test API user session login"""
        print("\n3️⃣ Testing API User Session Login")
        print("-" * 40)

        try:
            # Clear existing cookies
            self.session.cookies.clear()

            login_data = {"username": self.api_user, "secretkey": self.password}

            response = self.session.post(
                f"{self.base_url}/logincheck",
                data=login_data,
                timeout=10,
                allow_redirects=False,
            )

            print(f"Login Response: HTTP {response.status_code}")

            # Check for session cookies
            cookies = self.session.cookies.get_dict()
            print(f"Cookies received: {list(cookies.keys())}")

            if response.status_code in [200, 302] and cookies:
                print("✅ API user session login successful")
                return True
            else:
                print("❌ API user session login failed")
                return False

        except Exception as e:
            print(f"❌ API user session login error: {e}")
            return False

    def test_token_formats(self):
        """Test various API token formats"""
        print("\n4️⃣ Testing API Token Formats")
        print("-" * 40)

        # Clear session cookies to test pure token auth
        self.session.cookies.clear()

        test_endpoints = [
            "monitor/system/status",
            "cmdb/system/interface",
            "monitor/system/interface",
        ]

        token_formats = [
            ("Query Parameter", lambda url, token: f"{url}?access_token={token}"),
            (
                "Authorization Header",
                lambda url, token: (url, {"Authorization": f"Bearer {token}"}),
            ),
            (
                "Authorization Basic",
                lambda url, token: (
                    url,
                    {
                        "Authorization": f"Basic {base64.b64encode(f'{self.api_user}:{token}'.encode()).decode()}"
                    },
                ),
            ),
            ("API Key Header", lambda url, token: (url, {"X-API-Key": token})),
            ("Custom Header", lambda url, token: (url, {"Fortinet-API-Key": token})),
        ]

        results = {}

        for endpoint in test_endpoints:
            print(f"\n📍 Testing endpoint: {endpoint}")
            results[endpoint] = {}

            for format_name, format_func in token_formats:
                try:
                    url = f"{self.base_url}/api/v2/{endpoint}"

                    if isinstance(format_func(url, self.api_token), tuple):
                        test_url, headers = format_func(url, self.api_token)
                        response = self.session.get(
                            test_url, headers=headers, timeout=5
                        )
                    else:
                        test_url = format_func(url, self.api_token)
                        response = self.session.get(test_url, timeout=5)

                    status = response.status_code
                    results[endpoint][format_name] = status

                    if status == 200:
                        print(f"   ✅ {format_name}: HTTP {status}")
                        # Try to parse response
                        try:
                            data = response.json()
                            print(f"      📊 Response keys: {list(data.keys())[:5]}")
                        except:
                            print(
                                f"      📝 Response length: {len(response.text)} chars"
                            )
                    elif status == 401:
                        print(f"   ❌ {format_name}: HTTP {status} (Unauthorized)")
                    else:
                        print(f"   ⚠️ {format_name}: HTTP {status}")

                except Exception as e:
                    results[endpoint][format_name] = f"Error: {str(e)}"
                    print(f"   ❌ {format_name}: Error - {e}")

        return results

    def test_session_api_calls(self):
        """Test API calls with session cookies"""
        print("\n5️⃣ Testing Session-Based API Calls")
        print("-" * 40)

        # First establish admin session
        if self.test_admin_session_login():
            print("\nTesting API calls with admin session:")
            self._test_api_endpoints_with_session("Admin")

        # Then test with API user session
        if self.test_api_user_session_login():
            print("\nTesting API calls with API user session:")
            self._test_api_endpoints_with_session("API User")

    def _test_api_endpoints_with_session(self, session_type):
        """Helper to test API endpoints with current session"""
        test_endpoints = [
            "monitor/system/status",
            "monitor/fortilink/switch",
            "monitor/switch-controller/managed-switch",
            "cmdb/system/interface",
        ]

        for endpoint in test_endpoints:
            try:
                url = f"{self.base_url}/api/v2/{endpoint}"
                response = self.session.get(url, timeout=5)

                if response.status_code == 200:
                    print(f"   ✅ {endpoint}: HTTP {response.status_code}")
                    try:
                        data = response.json()
                        if isinstance(data, dict) and "results" in data:
                            print(f"      📊 Results count: {len(data['results'])}")
                        elif isinstance(data, dict):
                            print(f"      📊 Response keys: {list(data.keys())[:5]}")
                    except:
                        pass
                elif response.status_code == 401:
                    print(
                        f"   ❌ {endpoint}: HTTP {response.status_code} (Unauthorized)"
                    )
                else:
                    print(f"   ⚠️ {endpoint}: HTTP {response.status_code}")

            except Exception as e:
                print(f"   ❌ {endpoint}: Error - {e}")

    def test_token_with_username(self):
        """Test if token needs to be combined with username"""
        print("\n6️⃣ Testing Token + Username Combinations")
        print("-" * 40)

        combinations = [
            ("Token only", self.api_token),
            ("User:Token", f"{self.api_user}:{self.api_token}"),
            ("User|Token", f"{self.api_user}|{self.api_token}"),
            ("User_Token", f"{self.api_user}_{self.api_token}"),
        ]

        test_url = f"{self.base_url}/api/v2/monitor/system/status"

        for combo_name, token_value in combinations:
            try:
                url = f"{test_url}?access_token={token_value}"
                response = self.session.get(url, timeout=5)

                if response.status_code == 200:
                    print(f"   ✅ {combo_name}: HTTP {response.status_code}")
                elif response.status_code == 401:
                    print(
                        f"   ❌ {combo_name}: HTTP {response.status_code} (Unauthorized)"
                    )
                else:
                    print(f"   ⚠️ {combo_name}: HTTP {response.status_code}")

            except Exception as e:
                print(f"   ❌ {combo_name}: Error - {e}")

    def generate_diagnostic_report(self, token_results):
        """Generate a comprehensive diagnostic report"""
        print("\n📋 DIAGNOSTIC REPORT")
        print("=" * 60)

        # Check if any token format worked
        working_formats = []
        for endpoint, formats in token_results.items():
            for format_name, status in formats.items():
                if status == 200:
                    working_formats.append((endpoint, format_name))

        if working_formats:
            print("✅ WORKING TOKEN FORMATS FOUND:")
            for endpoint, format_name in working_formats:
                print(f"   • {endpoint} with {format_name}")
        else:
            print("❌ NO WORKING TOKEN FORMATS FOUND")

        print(f"\n🔍 RECOMMENDATIONS:")

        if not working_formats:
            print("1. Verify API token is correctly generated and associated with user")
            print("2. Check API user permissions in FortiGate GUI:")
            print("   - System > Administrators > REST API Admin")
            print(
                "   - Ensure 'super_admin' profile or custom profile with read permissions"
            )
            print("3. Verify API user account profile includes:")
            print("   - System: Read access")
            print("   - Monitor: Read access")
            print("   - Switch Controller: Read access")
            print("4. Try regenerating the API token")
            print("5. Check if API access is enabled globally in FortiGate")

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🚀 Starting Full API Diagnostic...")

        if not self.test_basic_connectivity():
            return

        self.test_admin_session_login()
        self.test_api_user_session_login()

        token_results = self.test_token_formats()

        self.test_session_api_calls()
        self.test_token_with_username()

        self.generate_diagnostic_report(token_results)

        print(f"\n✅ Diagnostic Complete!")


if __name__ == "__main__":
    troubleshooter = FortiGateAPITroubleshooter()
    troubleshooter.run_full_diagnostic()
