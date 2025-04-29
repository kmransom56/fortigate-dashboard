#!/usr/bin/env python3
"""
Final script to fix remaining issues in the updated authentication files.
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
    """Fix remaining issues in the updated files."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Check if this is a file we updated
    if any('# UPDATED: Removed query parameter authentication' in line for line in lines):
        logger.info(f"Checking file: {file_path}")
        
        # Fix comment indentation and other issues
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix comment indentation
            if '# UPDATED: Removed query parameter authentication' in line:
                fixed_lines.append('    # UPDATED: Removed query parameter authentication\n')
            else:
                fixed_lines.append(line)
            
            i += 1
        
        # Write the fixed content back to the file
        with open(file_path, 'w') as f:
            f.writelines(fixed_lines)
        
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