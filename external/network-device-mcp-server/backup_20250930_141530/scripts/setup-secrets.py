# scripts/setup-secrets.py
"""
Setup script to upload local .env variables to GitHub repository secrets
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def check_github_cli():
    """Verify GitHub CLI is installed and authenticated"""
    try:
        result = subprocess.run(['gh', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ GitHub CLI found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI not found. Install from: https://cli.github.com/")
        return False
    
    # Check authentication
    try:
        subprocess.run(['gh', 'auth', 'status'], 
                      capture_output=True, check=True)
        print("✅ GitHub CLI authenticated")
        return True
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI not authenticated. Run: gh auth login")
        return False

def load_env_file(env_file=".env"):
    """Load environment variables from .env file"""
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"❌ Environment file '{env_file}' not found")
        return None
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:  # Only include non-empty values
                    env_vars[key] = value
    
    print(f"✅ Loaded {len(env_vars)} variables from {env_file}")
    return env_vars

def upload_secret(repo_path, secret_name, secret_value):
    """Upload a single secret to GitHub repository"""
    try:
        cmd = ['gh', 'secret', 'set', secret_name, '--repo', repo_path, '--body', secret_value]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to upload {secret_name}: {e}")
        return False

def list_existing_secrets(repo_path):
    """List existing secrets in the repository"""
    try:
        cmd = ['gh', 'secret', 'list', '--repo', repo_path, '--json', 'name,updatedAt']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        secrets = json.loads(result.stdout)
        return secrets
    except Exception as e:
        print(f"❌ Failed to list secrets: {e}")
        return []

def main():
    if len(sys.argv) < 3:
        print("Usage: python setup-secrets.py <github-username> <repo-name>")
        print("Example: python setup-secrets.py myuser network-device-mcp-server")
        return 1
    
    username, repo_name = sys.argv[1], sys.argv[2]
    repo_path = f"{username}/{repo_name}"
    
    print(f"🔧 Setting up GitHub secrets for {repo_path}")
    print("=" * 60)
    
    # Check prerequisites
    if not check_github_cli():
        return 1
    
    # Load environment variables
    env_vars = load_env_file()
    if not env_vars:
        return 1
    
    # Show existing secrets
    print(f"\n📋 Existing secrets in {repo_path}:")
    existing_secrets = list_existing_secrets(repo_path)
    if existing_secrets:
        for secret in existing_secrets:
            print(f"   - {secret['name']} (updated: {secret['updatedAt']})")
    else:
        print("   (no existing secrets)")
    
    # Show what will be uploaded
    print(f"\n📤 Will upload {len(env_vars)} secrets:")
    for key in env_vars.keys():
        status = "UPDATE" if any(s['name'] == key for s in existing_secrets) else "NEW"
        print(f"   - {key} ({status})")
    
    # Confirm upload
    print(f"\n⚠️  This will upload credentials to GitHub repository: {repo_path}")
    print("⚠️  Make sure this is the correct repository and you have proper permissions!")
    
    confirm = input("\nContinue with upload? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Upload cancelled")
        return 0
    
    # Upload secrets
    print(f"\n🚀 Uploading secrets to {repo_path}...")
    success_count = 0
    
    for key, value in env_vars.items():
        print(f"   Uploading {key}...", end=" ")
        if upload_secret(repo_path, key, value):
            print("✅")
            success_count += 1
        else:
            print("❌")
    
    print(f"\n✅ Successfully uploaded {success_count}/{len(env_vars)} secrets")
    
    if success_count == len(env_vars):
        print("\n🎉 All secrets uploaded successfully!")
        print("\nNext steps:")
        print("1. Verify secrets in GitHub: Settings > Secrets and variables > Actions")
        print("2. Update your MCP server to use the GitHub secrets configuration")
        print("3. Test the server with the new configuration")
    else:
        print(f"\n⚠️  {len(env_vars) - success_count} secrets failed to upload")
        print("Check the errors above and try again")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())