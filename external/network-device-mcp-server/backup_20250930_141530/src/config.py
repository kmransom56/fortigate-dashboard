# config.py - Absolute path resolution version
"""
Configuration module with absolute path resolution for MCP server deployment
"""
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class NetworkConfig:
    """Network configuration with absolute path resolution"""
    
    def __init__(self):
        # Establish absolute paths immediately
        self.script_dir = Path(__file__).parent.resolve()
        self.project_root = self.script_dir.parent.resolve()
        self.env_file = self.project_root / ".env"
        
        # Initialize collections
        self.fortimanager_instances = []
        self.fortigate_devices = []
        self.meraki_api_key = None
        self.meraki_org_id = None
        self.backup_path = None
        self.report_path = None
        
        # Load configuration with absolute path resolution
        self._load_dotenv_file()
        self._load_configuration()
        self._setup_absolute_paths()
    
    def _load_dotenv_file(self):
        """Load .env file using absolute path"""
        logger.info(f"Looking for .env file at: {self.env_file}")
        
        if self.env_file.exists():
            try:
                from dotenv import load_dotenv
                result = load_dotenv(self.env_file)
                logger.info(f"Successfully loaded .env file from: {self.env_file}")
                return result
            except ImportError:
                logger.warning("python-dotenv not installed, using system environment variables")
        else:
            logger.warning(f"Environment file not found at: {self.env_file}")
            logger.info("Using system environment variables only")
        
        return False
    
    def _resolve_absolute_path(self, path_str: str) -> Path:
        """Convert any path string to absolute Path object"""
        if not path_str:
            return None
        
        path = Path(path_str)
        if path.is_absolute():
            return path.resolve()
        else:
            # Resolve relative to project root
            return (self.project_root / path).resolve()
    
    def _load_configuration(self):
        """Load configuration from environment variables"""
        logger.info("Loading configuration from environment variables...")
        
        # FortiManager configurations
        fortimanager_configs = [
            ("ARBYS", "FORTIMANAGER_ARBYS"),
            ("BWW", "FORTIMANAGER_BWW"), 
            ("SONIC", "FORTIMANAGER_SONIC")
        ]
        
        for name, prefix in fortimanager_configs:
            host = os.getenv(f"{prefix}_HOST")
            username = os.getenv(f"{prefix}_USERNAME")
            password = os.getenv(f"{prefix}_PASSWORD")
            
            if host and username and password:
                self.fortimanager_instances.append({
                    "name": name,
                    "host": host,
                    "username": username,
                    "password": password,
                    "description": f"{name} FortiManager instance"
                })
                logger.info(f"Loaded FortiManager config for {name}: {host}")
            else:
                logger.warning(f"Incomplete FortiManager config for {name}")
        
        # FortiGate devices
        device_index = 1
        while True:
            name = os.getenv(f"FORTIGATE_DEVICE_{device_index}_NAME")
            host = os.getenv(f"FORTIGATE_DEVICE_{device_index}_HOST")
            token = os.getenv(f"FORTIGATE_DEVICE_{device_index}_TOKEN")
            
            if not (name and host and token):
                break
                
            self.fortigate_devices.append({
                "name": name,
                "host": host,
                "token": token,
                "description": f"FortiGate device {name}"
            })
            logger.info(f"Loaded FortiGate device {name}: {host}")
            device_index += 1
        
        # Meraki configuration
        self.meraki_api_key = os.getenv("MERAKI_API_KEY")
        self.meraki_org_id = os.getenv("MERAKI_ORG_ID")
        
        if self.meraki_api_key:
            logger.info("Loaded Meraki configuration")
        
        # Log final count
        logger.info(f"Configuration loaded: {len(self.fortimanager_instances)} FortiManager instances, {len(self.fortigate_devices)} FortiGate devices")
    
    def _setup_absolute_paths(self):
        """Set up backup and report paths with absolute resolution"""
        # Get paths from environment or use defaults
        backup_str = os.getenv("BACKUP_PATH", "C:\\temp\\network-backups")
        report_str = os.getenv("REPORT_PATH", "C:\\temp\\network-reports")
        
        # Convert to absolute paths
        self.backup_path = self._resolve_absolute_path(backup_str)
        self.report_path = self._resolve_absolute_path(report_str)
        
        # Ensure directories exist
        for path_name, path in [("backup", self.backup_path), ("report", self.report_path)]:
            if path:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Ensured {path_name} directory exists: {path}")
                except Exception as e:
                    logger.error(f"Failed to create {path_name} directory {path}: {e}")
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Public method to convert any path to absolute"""
        return self._resolve_absolute_path(relative_path)
    
    def has_meraki_config(self) -> bool:
        """Check if Meraki configuration is available"""
        return bool(self.meraki_api_key and self.meraki_org_id)
    
    def get_fortimanager_by_name(self, name: str) -> Optional[Dict]:
        """Get FortiManager configuration by name"""
        for fm in self.fortimanager_instances:
            if fm["name"].upper() == name.upper():
                return fm
        return None
    
    def get_fortigate_by_name(self, name: str) -> Optional[Dict]:
        """Get FortiGate configuration by name"""
        for fg in self.fortigate_devices:
            if fg["name"].upper() == name.upper():
                return fg
        return None
    
    def list_fortimanager_names(self) -> List[str]:
        """Get list of available FortiManager names"""
        return [fm["name"] for fm in self.fortimanager_instances]
    
    def list_fortigate_names(self) -> List[str]:
        """Get list of available FortiGate names"""
        return [fg["name"] for fg in self.fortigate_devices]
    
    def validate_config(self) -> Dict:
        """Validate the current configuration"""
        return {
            "fortimanager_instances": len(self.fortimanager_instances),
            "fortigate_devices": len(self.fortigate_devices),
            "meraki_configured": self.has_meraki_config(),
            "backup_path_exists": self.backup_path.exists() if self.backup_path else False,
            "report_path_exists": self.report_path.exists() if self.report_path else False,
            "env_file_found": self.env_file.exists(),
            "project_root": str(self.project_root)
        }
    
    def is_github_deployment(self) -> bool:
        """Check if running in GitHub Actions environment"""
        return bool(os.getenv("GITHUB_ACTIONS") or os.getenv("CI"))
    
    def debug_info(self) -> Dict:
        """Return debugging information about paths and configuration"""
        return {
            "script_dir": str(self.script_dir),
            "project_root": str(self.project_root),
            "env_file": str(self.env_file),
            "env_file_exists": self.env_file.exists(),
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "report_path": str(self.report_path) if self.report_path else None,
            "fortimanager_count": len(self.fortimanager_instances),
            "fortigate_count": len(self.fortigate_devices),
            "current_working_dir": str(Path.cwd()),
            "is_github_deployment": self.is_github_deployment()
        }

    def get_brand_info(self, brand_code: str = None) -> Dict:
        """Get restaurant brand information and device naming patterns"""
        brands = {
            "BWW": {
                "name": "Buffalo Wild Wings",
                "device_prefix": "IBR-BWW",
                "store_format": "{:05d}",  # 5-digit store numbers
                "fortimanager": "BWW",
                "description": "Buffalo Wild Wings restaurants"
            },
            "ARBYS": {
                "name": "Arby's",
                "device_prefix": "IBR-ARBYS", 
                "store_format": "{:05d}",
                "fortimanager": "ARBYS",
                "description": "Arby's restaurants"
            },
            "SONIC": {
                "name": "Sonic Drive-In",
                "device_prefix": "IBR-SONIC",
                "store_format": "{:05d}",
                "fortimanager": "SONIC", 
                "description": "Sonic Drive-In restaurants"
            }
        }
        
        if brand_code:
            return brands.get(brand_code.upper(), {})
        return brands
    
    def build_device_name(self, brand: str, store_id: str) -> str:
        """Build device name from brand and store ID"""
        brand_info = self.get_brand_info(brand.upper())
        if not brand_info:
            # Fallback for unknown brands
            return f"IBR-{brand.upper()}-{store_id.zfill(5)}"
        
        formatted_store = brand_info["store_format"].format(int(store_id))
        return f"{brand_info['device_prefix']}-{formatted_store}"
    
    def detect_brand_from_device(self, device_name: str) -> Optional[str]:
        """Detect brand from device name"""
        device_upper = device_name.upper()
        for brand_code, brand_info in self.get_brand_info().items():
            if brand_info["device_prefix"] in device_upper:
                return brand_code
        return None
    
    def get_fortimanager_for_brand(self, brand: str) -> Optional[Dict]:
        """Get FortiManager instance for a specific brand"""
        brand_info = self.get_brand_info(brand.upper())
        if not brand_info:
            return None
        
        fm_name = brand_info["fortimanager"]
        return self.get_fortimanager_by_name(fm_name)


def get_config() -> NetworkConfig:
    """Get network configuration instance with absolute path resolution"""
    return NetworkConfig()
