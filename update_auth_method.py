#!/usr/bin/env python3
"""
Script to update FortiGate API authentication method in test files
from query parameter to Authorization header.
"""

import os
import re
import glob
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_file(file_path):
    """Update a file to use Authorization header instead of query parameter."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file uses query parameter authentication
    if 'params={"access_token"' in content or "params={'access_token'" in content:
        logger.info(f"Updating file: {file_path}")
        
        # Pattern to match query parameter authentication setup
        pattern = r'(url\s*=\s*f?"[^"]*")\s*\n\s*params\s*=\s*\{"access_token":\s*([^}]*)\}\s*\n\s*headers\s*=\s*\{([^}]*)\}'
        
        # Replacement with Authorization header
        replacement = r'\1\n    headers = {\3, "Authorization": f"Bearer \2"}'
        
        # Apply the replacement
        updated_content = re.sub(pattern, replacement, content)
        
        # Remove any remaining query parameter authentication
        updated_content = re.sub(r'params={"access_token":[^}]*}', '', updated_content)
        updated_content = re.sub(r"params={'access_token':[^}]*}", '', updated_content)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Updated file: {file_path}")
        return True
    else:
        logger.info(f"No query parameter authentication found in: {file_path}")
        return False

def main():
    """Main function to update all test files."""
    # Find all Python test files
    test_files = glob.glob('test_*.py')
    
    logger.info(f"Found {len(test_files)} test files")
    
    # Update each file
    updated_count = 0
    for file_path in test_files:
        if update_file(file_path):
            updated_count += 1
    
    logger.info(f"Updated {updated_count} files")

if __name__ == "__main__":
    main()