#!/usr/bin/env python3
"""
FortiGate Topology Scraper Management Tool

This script provides a Python interface to the Node.js scraper tools.
"""

import os
import sys
import subprocess
import json
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FortiGateScraperManager:
    """Manages FortiGate topology scraping operations"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.services_dir = self.project_root / "app" / "services"
        
    def check_dependencies(self):
        """Check if required Node.js dependencies are available"""
        try:
            # Check if Node.js is available
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Node.js is not installed or not in PATH")
                return False
                
            logger.info(f"Node.js version: {result.stdout.strip()}")
            
            # Check if npm modules are installed
            package_json_path = self.services_dir / "package.json"
            if not package_json_path.exists():
                logger.warning("No package.json found in services directory")
                return self._create_package_json()
                
            return True
            
        except FileNotFoundError:
            logger.error("Node.js is not installed")
            return False
    
    def _create_package_json(self):
        """Create a basic package.json for the scraper tools"""
        package_json = {
            "name": "fortigate-scraper-tools",
            "version": "1.0.0",
            "description": "FortiGate topology scraping tools",
            "scripts": {
                "scrape": "node scraper.js",
                "scrape-map": "node scrape-fortigate-map.js",
                "extract-tokens": "node token-extractor.js"
            },
            "dependencies": {
                "playwright": "^1.40.0",
                "commander": "^11.1.0",
                "inquirer": "^9.2.0",
                "chalk": "^5.3.0",
                "ora": "^7.0.0",
                "fs-extra": "^11.2.0",
                "css": "^3.0.0",
                "postcss": "^8.4.0",
                "cheerio": "^1.0.0"
            }
        }
        
        package_json_path = self.services_dir / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
            
        logger.info(f"Created package.json at {package_json_path}")
        return True
    
    def install_dependencies(self):
        """Install Node.js dependencies"""
        try:
            logger.info("Installing Node.js dependencies...")
            result = subprocess.run(
                ['npm', 'install'], 
                cwd=self.services_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Dependencies installed successfully")
                return True
            else:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("npm is not installed")
            return False
    
    def run_scraper(self, host, username, password, headless=True, view="both"):
        """Run the advanced FortiGate scraper"""
        scraper_path = self.services_dir / "scraper.js"
        
        if not scraper_path.exists():
            logger.error(f"Scraper not found at {scraper_path}")
            return False
            
        cmd = [
            'node', str(scraper_path), 'scrape',
            '--host', host,
            '--username', username, 
            '--password', password,
            '--view', view
        ]
        
        if headless:
            cmd.extend(['--headless', 'true'])
        
        try:
            logger.info(f"Running scraper for host: {host}")
            result = subprocess.run(cmd, cwd=self.services_dir)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run scraper: {e}")
            return False
    
    def run_simple_scraper(self, host, username, password):
        """Run the simple map scraper"""
        scraper_path = self.services_dir / "scrape-fortigate-map.js"
        
        if not scraper_path.exists():
            logger.error(f"Simple scraper not found at {scraper_path}")
            return False
        
        # Update the scraper script with provided credentials
        self._update_simple_scraper(scraper_path, host, username, password)
        
        try:
            logger.info(f"Running simple scraper for host: {host}")
            result = subprocess.run(['node', str(scraper_path)], cwd=self.services_dir)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run simple scraper: {e}")
            return False
    
    def _update_simple_scraper(self, script_path, host, username, password):
        """Update simple scraper with credentials"""
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace('http://10.208.103.1:2456', f'https://{host}')
        content = content.replace('YOUR_USERNAME', username)
        content = content.replace('YOUR_PASSWORD', password)
        
        with open(script_path, 'w') as f:
            f.write(content)
    
    def extract_tokens(self, input_dir="./assets", output_dir="./tokens"):
        """Extract design tokens from scraped assets"""
        extractor_path = self.services_dir / "token-extractor.js"
        
        if not extractor_path.exists():
            logger.error(f"Token extractor not found at {extractor_path}")
            return False
        
        cmd = [
            'node', str(extractor_path), 'extract',
            '--input-dir', input_dir,
            '--output-dir', output_dir
        ]
        
        try:
            logger.info("Extracting design tokens...")
            result = subprocess.run(cmd, cwd=self.services_dir)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to extract tokens: {e}")
            return False
    
    def test_scraped_data(self):
        """Test the scraped topology service"""
        try:
            from app.services.scraped_topology_service import get_scraped_topology_service
            
            service = get_scraped_topology_service()
            data = service.get_topology_data()
            
            logger.info(f"Scraped topology data:")
            logger.info(f"  Source: {data.get('metadata', {}).get('source', 'unknown')}")
            logger.info(f"  Devices: {len(data.get('devices', []))}")
            logger.info(f"  Connections: {len(data.get('connections', []))}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test scraped data: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="FortiGate Topology Scraper Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup scraper dependencies')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Run advanced scraper')
    scrape_parser.add_argument('--host', required=True, help='FortiGate host')
    scrape_parser.add_argument('--username', required=True, help='FortiGate username')
    scrape_parser.add_argument('--password', required=True, help='FortiGate password')
    scrape_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    scrape_parser.add_argument('--view', choices=['physical', 'logical', 'both'], 
                             default='both', help='View type to scrape')
    
    # Simple scrape command
    simple_parser = subparsers.add_parser('scrape-simple', help='Run simple scraper')
    simple_parser.add_argument('--host', required=True, help='FortiGate host')
    simple_parser.add_argument('--username', required=True, help='FortiGate username')
    simple_parser.add_argument('--password', required=True, help='FortiGate password')
    
    # Extract tokens command
    tokens_parser = subparsers.add_parser('extract-tokens', help='Extract design tokens')
    tokens_parser.add_argument('--input-dir', default='./assets', help='Input directory')
    tokens_parser.add_argument('--output-dir', default='./tokens', help='Output directory')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test scraped data service')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = FortiGateScraperManager()
    
    if args.command == 'setup':
        if not manager.check_dependencies():
            logger.error("Dependencies check failed")
            return 1
        if not manager.install_dependencies():
            logger.error("Failed to install dependencies")
            return 1
        logger.info("Setup completed successfully!")
        
    elif args.command == 'scrape':
        if not manager.check_dependencies():
            logger.error("Dependencies not installed. Run 'setup' first.")
            return 1
        if not manager.run_scraper(args.host, args.username, args.password, 
                                  args.headless, args.view):
            return 1
            
    elif args.command == 'scrape-simple':
        if not manager.check_dependencies():
            logger.error("Dependencies not installed. Run 'setup' first.")
            return 1
        if not manager.run_simple_scraper(args.host, args.username, args.password):
            return 1
            
    elif args.command == 'extract-tokens':
        if not manager.check_dependencies():
            logger.error("Dependencies not installed. Run 'setup' first.")
            return 1
        if not manager.extract_tokens(args.input_dir, args.output_dir):
            return 1
            
    elif args.command == 'test':
        if not manager.test_scraped_data():
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())