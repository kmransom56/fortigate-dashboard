import os
import sys
from app.services.fortigate_service import get_interfaces

# Call the function directly
try:
    print("Calling get_interfaces()...")
    interfaces = get_interfaces()
    print(f"Interfaces: {interfaces}")
except Exception as e:
    print(f"Error: {e}")