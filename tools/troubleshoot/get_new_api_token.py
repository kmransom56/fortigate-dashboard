#!/usr/bin/env python3
"""
FortiGate API Token Generator

This script helps you get a new API token for FortiGate authentication.
It uses the working admin session to generate a new token.
"""

import requests
import json
import os
from urllib.parse import urlencode

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FortiGateTokenGenerator:
    def __init__(self):
        self.host = "192.168.0.254"
        self.base_url = f"https://{self.host}"
        self.session = requests.Session()
        self.session.verify = False
        
        # Admin credentials (update these if needed)
        self.admin_user = "admin"
        self.admin_password = "admin"  # Update this with your actual admin password
        
        print(f"🔑 FortiGate API Token Generator")
        print(f"Host: {self.host}")
        print(f"Admin User: {self.admin_user}")
        print("=" * 60)

    def login_admin(self):
        """Login as admin user"""
        print("\n1️⃣ Logging in as admin...")
        
        try:
            login_data = {
                "username": self.admin_user,
                "secretkey": self.admin_password
            }
            
            response = self.session.post(
                f"{self.base_url}/logincheck",
                data=login_data,
                timeout=10,
                allow_redirects=False
            )
            
            print(f"Login Response: HTTP {response.status_code}")
            
            # Check for session cookies
            cookies = self.session.cookies.get_dict()
            print(f"Cookies received: {list(cookies.keys())}")
            
            if response.status_code in [200, 302] and cookies:
                print("✅ Admin login successful")
                return True
            else:
                print("❌ Admin login failed")
                print(f"Response text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False

    def get_api_users(self):
        """Get list of API users"""
        print("\n2️⃣ Getting API users...")
        
        try:
            url = f"{self.base_url}/api/v2/cmdb/system/api-user"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('results', [])
                print(f"✅ Found {len(users)} API users:")
                
                for user in users:
                    print(f"   • {user.get('name', 'Unknown')} - {user.get('comments', 'No description')}")
                
                return users
            else:
                print(f"❌ Failed to get API users: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting API users: {e}")
            return []

    def create_api_user(self, username, password, profile="super_admin"):
        """Create a new API user"""
        print(f"\n3️⃣ Creating API user: {username}")
        
        try:
            url = f"{self.base_url}/api/v2/cmdb/system/api-user"
            
            user_data = {
                "name": username,
                "api-key": password,
                "accprofile": profile,
                "comments": "Created by API Token Generator script"
            }
            
            response = self.session.post(url, json=user_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ API user '{username}' created successfully")
                return True
            else:
                print(f"❌ Failed to create API user: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating API user: {e}")
            return False

    def generate_api_token(self, username):
        """Generate API token for a user"""
        print(f"\n4️⃣ Generating API token for user: {username}")
        
        try:
            # First, get the user's current API key
            url = f"{self.base_url}/api/v2/cmdb/system/api-user/{username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                api_key = user_data.get('results', {}).get('api-key', '')
                
                if api_key:
                    print(f"✅ Found existing API key for {username}")
                    print(f"API Key: {api_key}")
                    return api_key
                else:
                    print(f"❌ No API key found for user {username}")
                    return None
            else:
                print(f"❌ Failed to get user data: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating API token: {e}")
            return None

    def test_api_token(self, token):
        """Test the API token"""
        print(f"\n5️⃣ Testing API token...")
        
        try:
            # Clear session cookies to test pure token auth
            self.session.cookies.clear()
            
            url = f"{self.base_url}/api/v2/monitor/system/status"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ API token works!")
                data = response.json()
                print(f"System status: {data.get('results', {}).get('version', 'Unknown')}")
                return True
            else:
                print(f"❌ API token test failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing API token: {e}")
            return False

    def save_token_to_env(self, token):
        """Save token to environment file"""
        print(f"\n6️⃣ Saving token to environment...")
        
        try:
            env_file = ".env"
            env_content = f"FORTIGATE_API_TOKEN={token}\n"
            
            # Read existing .env file if it exists
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    existing_content = f.read()
                
                # Update or add the token
                lines = existing_content.split('\n')
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('FORTIGATE_API_TOKEN='):
                        lines[i] = env_content.strip()
                        updated = True
                        break
                
                if not updated:
                    lines.append(env_content.strip())
                
                env_content = '\n'.join(lines)
            
            # Write the updated content
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            print(f"✅ Token saved to {env_file}")
            print(f"To use the token, run: export FORTIGATE_API_TOKEN={token}")
            
        except Exception as e:
            print(f"❌ Error saving token: {e}")

    def run_token_generation(self):
        """Run the complete token generation process"""
        print("🚀 Starting API Token Generation...")
        
        # Step 1: Login as admin
        if not self.login_admin():
            print("❌ Cannot proceed without admin access")
            return
        
        # Step 2: Get existing API users
        users = self.get_api_users()
        
        # Step 3: Try to use existing API user or create new one
        api_username = "programaticallydothings"  # Update this if needed
        
        # Check if user exists
        existing_user = None
        for user in users:
            if user.get('name') == api_username:
                existing_user = user
                break
        
        if existing_user:
            print(f"✅ Found existing API user: {api_username}")
        else:
            print(f"❌ API user '{api_username}' not found")
            print("You may need to create this user in the FortiGate GUI first")
            print("Or update the username in this script")
            return
        
        # Step 4: Generate/get API token
        token = self.generate_api_token(api_username)
        
        if token:
            # Step 5: Test the token
            if self.test_api_token(token):
                # Step 6: Save to environment
                self.save_token_to_env(token)
                print(f"\n🎉 SUCCESS! New API token generated and tested")
                print(f"Token: {token}")
            else:
                print(f"\n❌ Token generation failed - token doesn't work")
        else:
            print(f"\n❌ Could not generate API token")

if __name__ == "__main__":
    generator = FortiGateTokenGenerator()
    generator.run_token_generation()