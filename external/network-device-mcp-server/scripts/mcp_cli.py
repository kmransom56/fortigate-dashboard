#!/usr/bin/env python3
"""
Command Line Interface for MCP Server
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import NetworkDeviceMCPServer

class MCPCommandLine:
    def __init__(self):
        self.server = NetworkDeviceMCPServer()
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call MCP tool and return result"""
        try:
            result = await self.server._NetworkDeviceMCPServer__handle_call_tool(tool_name, arguments)
            if result and hasattr(result[0], 'text'):
                return json.loads(result[0].text)
            return result
        except Exception as e:
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Network Device MCP Server CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List brands command
    brands_parser = subparsers.add_parser('brands', help='List supported brands')
    
    # Brand overview command
    brand_parser = subparsers.add_parser('brand', help='Get brand overview')
    brand_parser.add_argument('brand', choices=['BWW', 'ARBYS', 'SONIC'], help='Brand code')
    
    # Store security command
    security_parser = subparsers.add_parser('security', help='Get store security health')
    security_parser.add_argument('brand', choices=['BWW', 'ARBYS', 'SONIC'], help='Brand code')
    security_parser.add_argument('store_id', help='Store ID')
    security_parser.add_argument('--no-recommendations', action='store_true', help='Exclude recommendations')
    
    # URL blocking command
    blocking_parser = subparsers.add_parser('blocking', help='Analyze URL blocking')
    blocking_parser.add_argument('brand', choices=['BWW', 'ARBYS', 'SONIC'], help='Brand code')
    blocking_parser.add_argument('store_id', help='Store ID')
    blocking_parser.add_argument('--period', default='24h', help='Analysis period (default: 24h)')
    blocking_parser.add_argument('--no-export', action='store_true', help='Skip report export')
    
    # Security events command
    events_parser = subparsers.add_parser('events', help='Get security events')
    events_parser.add_argument('device_name', help='Device name (e.g., IBR-BWW-00155)')
    events_parser.add_argument('--timeframe', default='24h', help='Timeframe (default: 24h)')
    events_parser.add_argument('--count', type=int, default=10, help='Number of top events (default: 10)')
    
    # FortiManager commands
    fm_parser = subparsers.add_parser('fortimanager', help='FortiManager operations')
    fm_subparsers = fm_parser.add_subparsers(dest='fm_command')
    
    fm_list = fm_subparsers.add_parser('list', help='List FortiManager instances')
    
    fm_devices = fm_subparsers.add_parser('devices', help='Get managed devices')
    fm_devices.add_argument('instance', choices=['BWW', 'ARBYS', 'SONIC'], help='FortiManager instance')
    fm_devices.add_argument('--adom', default='root', help='Administrative domain (default: root)')
    
    # Investigate command (combines multiple tools)
    investigate_parser = subparsers.add_parser('investigate', help='Complete store investigation')
    investigate_parser.add_argument('brand', choices=['BWW', 'ARBYS', 'SONIC'], help='Brand code')
    investigate_parser.add_argument('store_id', help='Store ID')
    investigate_parser.add_argument('--period', default='24h', help='Analysis period (default: 24h)')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    # Initialize CLI client
    cli = MCPCommandLine()

    async def run_command():
        try:
            if args.command == 'brands':
                result = await cli.call_tool("list_supported_brands", {})
                
            elif args.command == 'brand':
                result = await cli.call_tool("get_brand_store_summary", {"brand": args.brand})
                
            elif args.command == 'security':
                result = await cli.call_tool("get_store_security_health", {
                    "brand": args.brand,
                    "store_id": args.store_id,
                    "include_recommendations": not args.no_recommendations
                })
                
            elif args.command == 'blocking':
                result = await cli.call_tool("analyze_url_blocking_patterns", {
                    "brand": args.brand,
                    "store_id": args.store_id,
                    "analysis_period": args.period,
                    "export_report": not args.no_export
                })
                
            elif args.command == 'events':
                result = await cli.call_tool("get_security_event_summary", {
                    "device_name": args.device_name,
                    "timeframe": args.timeframe,
                    "top_count": args.count
                })
                
            elif args.command == 'fortimanager':
                if args.fm_command == 'list':
                    result = await cli.call_tool("list_fortimanager_instances", {})
                elif args.fm_command == 'devices':
                    result = await cli.call_tool("get_fortimanager_devices", {
                        "fortimanager_name": args.instance,
                        "adom": args.adom
                    })
                else:
                    print("FortiManager subcommand required: list, devices")
                    return
                    
            elif args.command == 'investigate':
                print(f"🔍 Investigating {args.brand} Store {args.store_id}")
                print("=" * 50)
                
                # Security health
                print("\n📊 Security Health:")
                health = await cli.call_tool("get_store_security_health", {
                    "brand": args.brand,
                    "store_id": args.store_id
                })
                print(json.dumps(health, indent=2))
                
                # URL blocking
                print("\n🌐 URL Blocking Analysis:")
                blocking = await cli.call_tool("analyze_url_blocking_patterns", {
                    "brand": args.brand,
                    "store_id": args.store_id,
                    "analysis_period": args.period,
                    "export_report": True
                })
                print(json.dumps(blocking, indent=2))
                
                # Security events
                device_name = f"IBR-{args.brand}-{args.store_id.zfill(5)}"
                print(f"\n🚨 Security Events for {device_name}:")
                events = await cli.call_tool("get_security_event_summary", {
                    "device_name": device_name,
                    "timeframe": args.period
                })
                print(json.dumps(events, indent=2))
                return
            
            # Print result for single commands
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Run the async command
    asyncio.run(run_command())

if __name__ == '__main__':
    main()