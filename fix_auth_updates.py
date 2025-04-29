#!/usr/bin/env python3
"""
Script to fix issues in the updated authentication files.
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

def fix_file(file_path):
    """Fix issues in the updated files."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if this is a file we updated
    if '# UPDATED: Removed query parameter authentication' in content:
        logger.info(f"Fixing file: {file_path}")
        
        # Fix 1: Correct the token variable in Authorization header
        # Look for "Authorization": f"Bearer API_TOKEN" and replace with "Authorization": f"Bearer {API_TOKEN}"
        content = re.sub(
            r'"Authorization":\s*f"Bearer\s+API_TOKEN"', 
            '"Authorization": f"Bearer {API_TOKEN}"', 
            content
        )
        
        # Fix 2: Remove references to params variable that no longer exists
        content = re.sub(
            r'\s*logger\.info\(f"With params: \{params\}"\)\s*', 
            '\n', 
            content
        )
        
        # Write the fixed content back to the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Fixed file: {file_path}")
        return True
    else:
        logger.info(f"No fixes needed for: {file_path}")
        return False

def main():
    """Main function to fix all updated test files."""
    # Find all Python test files
    test_files = glob.glob('test_*.py')
    
    logger.info(f"Found {len(test_files)} test files")
    
    # Fix each file
    fixed_count = 0
    for file_path in test_files:
        if fix_file(file_path):
            fixed_count += 1
    
    logger.info(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()