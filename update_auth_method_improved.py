#!/usr/bin/env python3
"""
Improved script to update FortiGate API authentication method in test files
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
    if 'params' in content and 'access_token' in content:
        logger.info(f"Checking file: {file_path}")
        
        # Keep track if we made any changes
        made_changes = False
        
        # For test files that have both methods (for comparison)
        if 'test_with_query_param' in content and 'test_with_auth_header' in content:
            logger.info(f"File {file_path} has both authentication methods for testing purposes. Not modifying.")
            return False
        
        # For files that use query parameter in requests
        lines = content.split('\n')
        updated_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for lines setting up params with access_token
            if re.search(r'params\s*=\s*\{.*"access_token"', line) or re.search(r"params\s*=\s*\{.*'access_token'", line):
                # Extract the token variable
                token_match = re.search(r'"access_token":\s*([^,}]+)', line)
                if not token_match:
                    token_match = re.search(r"'access_token':\s*([^,}]+)", line)
                
                if token_match:
                    token_var = token_match.group(1).strip()
                    
                    # Skip this line (params definition)
                    updated_lines.append(f"# UPDATED: Removed query parameter authentication")
                    
                    # Look ahead for headers definition
                    for j in range(i+1, min(i+5, len(lines))):
                        if 'headers' in lines[j]:
                            # Found headers, update it to include Authorization
                            if re.search(r'headers\s*=\s*\{\s*\}', lines[j]):
                                # Empty headers
                                updated_lines.append(f'    headers = {{"Authorization": f"Bearer {token_var}"}}')
                            elif re.search(r'headers\s*=\s*\{[^}]+\}', lines[j]):
                                # Headers with content
                                headers_line = lines[j]
                                # Remove closing brace
                                headers_line = headers_line.rstrip('}')
                                if headers_line.endswith(','):
                                    updated_lines.append(f'{headers_line} "Authorization": f"Bearer {token_var}"}}')
                                else:
                                    updated_lines.append(f'{headers_line}, "Authorization": f"Bearer {token_var}"}}')
                            else:
                                # Multi-line headers, more complex to handle
                                updated_lines.append(lines[j])
                                logger.warning(f"Complex headers format in {file_path}, manual review needed")
                            
                            i = j  # Skip to after headers
                            made_changes = True
                            break
                    else:
                        # No headers found, add them
                        updated_lines.append(f'    headers = {{"Accept": "application/json", "Authorization": f"Bearer {token_var}"}}')
                        made_changes = True
                else:
                    # Couldn't extract token, just keep the line
                    updated_lines.append(line)
            
            # Look for requests.get calls with params
            elif 'requests.get' in line and 'params=params' in line:
                # Remove params from the request
                updated_line = line.replace('params=params, ', '')
                updated_line = updated_line.replace(', params=params', '')
                updated_lines.append(updated_line)
                made_changes = True
            else:
                updated_lines.append(line)
            
            i += 1
        
        if made_changes:
            # Write the updated content back to the file
            with open(file_path, 'w') as f:
                f.write('\n'.join(updated_lines))
            
            logger.info(f"Updated file: {file_path}")
            return True
        else:
            logger.info(f"No changes needed in: {file_path}")
            return False
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