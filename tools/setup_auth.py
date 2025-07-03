#!/usr/bin/env python3
"""
Configuration utility for FortiGate authentication
"""

import getpass
from pathlib import Path


def setup_authentication():
    """Interactive setup for FortiGate authentication"""
    print("FortiGate Authentication Setup")
    print("=" * 40)

    # Get FortiGate details
    fortigate_ip = input(
        "Enter FortiGate IP address (default: 192.168.0.254): "
    ).strip()
    if not fortigate_ip:
        fortigate_ip = "192.168.0.254"

    print(f"\nFortiGate IP: {fortigate_ip}")

    # Choose authentication method
    print("\nAuthentication Methods:")
    print("1. Session-based (username/password) - Recommended")
    print("2. API Token (static token)")

    while True:
        choice = input("\nSelect authentication method (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Please enter 1 or 2")

    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)

    if choice == "1":
        # Session-based authentication
        print("\n=== Session-based Authentication ===")
        username = input("Enter FortiGate username (default: admin): ").strip()
        if not username:
            username = "admin"

        password = getpass.getpass("Enter FortiGate password: ")

        if not password:
            print("Password cannot be empty!")
            return False

        # Save password to file
        password_file = secrets_dir / "fortigate_password.txt"
        with open(password_file, "w") as f:
            f.write(password)

        print(f"✅ Password saved to {password_file}")

        # Update environment file
        env_content = f"""# FortiGate Configuration
FORTIGATE_HOST=https://{fortigate_ip}
FORTIGATE_USERNAME={username}
"""

        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ Environment file updated")
        print("\n🔧 Session-based authentication configured!")
        print(f"   - FortiGate: {fortigate_ip}")
        print(f"   - Username: {username}")
        print(f"   - Password: saved to {password_file}")

    else:
        # Token-based authentication
        print("\n=== API Token Authentication ===")
        token = getpass.getpass("Enter FortiGate API token: ")

        if not token:
            print("API token cannot be empty!")
            return False

        # Save token to file
        token_file = secrets_dir / "fortigate_api_token.txt"
        with open(token_file, "w") as f:
            f.write(token)

        print(f"✅ API token saved to {token_file}")

        # Update environment file
        env_content = f"""# FortiGate Configuration
FORTIGATE_HOST=https://{fortigate_ip}
"""

        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ Environment file updated")
        print("\n🔧 Token-based authentication configured!")
        print(f"   - FortiGate: {fortigate_ip}")
        print(f"   - Token: saved to {token_file}")

    print("\n🚀 Configuration complete!")
    print("You can now rebuild and restart the Docker containers:")
    print("   docker-compose down")
    print("   docker-compose up --build")

    return True


if __name__ == "__main__":
    try:
        setup_authentication()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
