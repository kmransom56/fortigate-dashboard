#!/usr/bin/env python3
"""
Direct MCP Server Client - Use MCP tools without Claude Desktop
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import NetworkDeviceMCPServer

class DirectMCPClient:
    def __init__(self):
        self.server = NetworkDeviceMCPServer()
    
    async def call_tool(self, tool_name: str, **kwargs):
        """Call any MCP tool directly"""
        try:
            # Get the handler method
            handler_name = f"_handle_{tool_name}" if hasattr(self.server, f"_handle_{tool_name}") else f"_{tool_name}"
            
            # Call the tool using the main server's routing
            result = await self.server._NetworkDeviceMCPServer__handle_call_tool(tool_name, kwargs)
            
            # Extract text content
            if result and hasattr(result[0], 'text'):
                return json.loads(result[0].text)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    # Convenience methods for common operations
    async def analyze_store_blocking(self, brand: str, store_id: str, period: str = "24h"):
        """Analyze URL blocking for any brand/store"""
        return await self.call_tool(
            "analyze_url_blocking_patterns",
            brand=brand,
            store_id=store_id, 
            analysis_period=period,
            export_report=True
        )
    
    async def get_store_health(self, brand: str, store_id: str):
        """Get security health for any brand/store"""
        return await self.call_tool(
            "get_store_security_health",
            brand=brand,
            store_id=store_id
        )
    
    async def get_security_summary(self, device_name: str, timeframe: str = "24h"):
        """Get security event summary"""
        return await self.call_tool(
            "get_security_event_summary", 
            device_name=device_name,
            timeframe=timeframe
        )
    
    async def list_brands(self):
        """List all supported brands"""
        return await self.call_tool("list_supported_brands")
    
    async def get_brand_overview(self, brand: str):
        """Get brand infrastructure overview"""  
        return await self.call_tool("get_brand_store_summary", brand=brand)

# Example usage functions
async def investigate_store(brand: str, store_id: str):
    """Complete store investigation"""
    client = DirectMCPClient()
    
    print(f"🔍 Investigating {brand} Store {store_id}")
    print("=" * 50)
    
    # Get security health
    health = await client.get_store_health(brand, store_id)
    print("\n📊 Security Health:")
    print(json.dumps(health, indent=2))
    
    # Analyze URL blocking
    blocking = await client.analyze_store_blocking(brand, store_id)
    print("\n🌐 URL Blocking Analysis:")
    print(json.dumps(blocking, indent=2))
    
    # Get security events
    device_name = f"IBR-{brand}-{store_id.zfill(5)}"
    events = await client.get_security_summary(device_name)
    print(f"\n🚨 Security Events for {device_name}:")
    print(json.dumps(events, indent=2))

async def brand_overview(brand: str):
    """Get complete brand overview"""
    client = DirectMCPClient()
    
    print(f"🏪 {brand} Brand Overview")
    print("=" * 30)
    
    overview = await client.get_brand_overview(brand)
    print(json.dumps(overview, indent=2))

if __name__ == "__main__":
    # Example: Investigate BWW Store 155
    # asyncio.run(investigate_store("BWW", "155"))
    
    # Example: Get Arby's brand overview  
    # asyncio.run(brand_overview("ARBYS"))
    
    # Example: List all supported brands
    async def main():
        client = DirectMCPClient()
        brands = await client.list_brands()
        print("Supported Brands:")
        print(json.dumps(brands, indent=2))
    
    asyncio.run(main())