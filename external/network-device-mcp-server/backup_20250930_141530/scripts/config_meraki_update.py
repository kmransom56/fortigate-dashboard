# Updated config.py section for multiple Meraki organizations
    def _load_configuration(self):
        """Load configuration from environment variables"""
        logger.info("Loading configuration from environment variables...")
        
        # FortiManager configurations (existing code)
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
        
        # FortiGate devices (existing code remains same)
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
        
        # Meraki configuration - Updated for multiple organizations
        self.meraki_api_key = os.getenv("MERAKI_API_KEY")
        self.meraki_org_id = os.getenv("MERAKI_ORG_ID")  # Default org
        
        # Load multiple Meraki organizations
        self.meraki_organizations = {}
        meraki_orgs = ["ARBYS", "BWW", "SONIC"]
        
        for org_name in meraki_orgs:
            org_id = os.getenv(f"MERAKI_ORG_ID_{org_name}")
            if org_id:
                self.meraki_organizations[org_name] = org_id
                logger.info(f"Loaded Meraki organization {org_name}: {org_id}")
        
        if self.meraki_api_key:
            logger.info(f"Loaded Meraki configuration with {len(self.meraki_organizations)} organizations")
        
        # Log final count
        logger.info(f"Configuration loaded: {len(self.fortimanager_instances)} FortiManager instances, {len(self.fortigate_devices)} FortiGate devices")
    
    def has_meraki_config(self) -> bool:
        """Check if Meraki configuration is available"""
        return bool(self.meraki_api_key and (self.meraki_org_id or self.meraki_organizations))
    
    def get_meraki_org_id(self, org_name: str = None) -> str:
        """Get Meraki organization ID by name or default"""
        if org_name and org_name.upper() in self.meraki_organizations:
            return self.meraki_organizations[org_name.upper()]
        return self.meraki_org_id or next(iter(self.meraki_organizations.values()), None)
    
    def list_meraki_organizations(self) -> Dict[str, str]:
        """Get all configured Meraki organizations"""
        return self.meraki_organizations.copy()
