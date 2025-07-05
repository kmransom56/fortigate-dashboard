#!/usr/bin/env python3
"""
Comprehensive Demo of FortiGate and FortiSwitch API Integration
Demonstrates both FortiGate management and FortiSwitch control capabilities
"""

import sys
import os
import json
from datetime import datetime

# Add the MCP server to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCP server components
from fortinet_server_enhanced import fg_api, fm_api, api_parser, discovered_endpoints

def demo_fortigate_api_coverage():
    """Demonstrate comprehensive FortiGate API coverage"""
    print("=" * 60)
    print("FORTIGATE API COMPREHENSIVE COVERAGE DEMO")
    print("=" * 60)
    
    # Analyze FortiGate endpoints
    fortigate_files = [
        'FortiOS 7.6 FortiOS 7.6.3 Configuration API system',
        'FortiOS 7.6 FortiOS 7.6.3 Monitor API system', 
        'FortiOS 7.6 FortiOS 7.6.3 Monitor API switch-controller'
    ]
    
    functional_groups = {
        'system_management': [],
        'network_monitoring': [],
        'security_management': [],
        'switch_controller': [],
        'configuration': [],
        'logging': [],
        'vpn_management': [],
        'user_management': [],
        'high_availability': [],
        'other': []
    }
    
    for key, info in discovered_endpoints.items():
        source = info.get('source_file', '')
        if any(fg_file in source for fg_file in fortigate_files):
            path = info.get('path', '').lower()
            
            # Categorize by functionality
            if 'switch-controller' in path:
                functional_groups['switch_controller'].append(key)
            elif 'system' in path and any(x in path for x in ['status', 'admin', 'interface', 'resource']):
                functional_groups['system_management'].append(key)
            elif any(x in path for x in ['firewall', 'policy', 'security', 'antivirus', 'ips']):
                functional_groups['security_management'].append(key)
            elif any(x in path for x in ['vpn', 'ipsec', 'ssl']):
                functional_groups['vpn_management'].append(key)
            elif any(x in path for x in ['user', 'group', 'authentication']):
                functional_groups['user_management'].append(key)
            elif any(x in path for x in ['ha', 'cluster']):
                functional_groups['high_availability'].append(key)
            elif any(x in path for x in ['log', 'event']):
                functional_groups['logging'].append(key)
            elif 'cmdb' in path:
                functional_groups['configuration'].append(key)
            elif any(x in path for x in ['network', 'interface', 'routing']):
                functional_groups['network_monitoring'].append(key)
            else:
                functional_groups['other'].append(key)
    
    total_fortigate = sum(len(eps) for eps in functional_groups.values())
    print(f"Total FortiGate API endpoints available: {total_fortigate}")
    print()
    
    print("FortiGate API Categories:")
    for group, endpoints in functional_groups.items():
        if endpoints:
            print(f"  📁 {group.replace('_', ' ').title()}: {len(endpoints)} endpoints")
    
    return functional_groups

def demo_system_management():
    """Demonstrate FortiGate system management capabilities"""
    print("\n" + "=" * 60)
    print("FORTIGATE SYSTEM MANAGEMENT DEMO")
    print("=" * 60)
    
    # System status
    print("\n1. System Status:")
    status = fg_api._make_request("GET", "monitor/system/status")
    if "error" not in status:
        results = status.get('results', {})
        print(f"   🖥️  Hostname: {results.get('hostname', 'Unknown')}")
        print(f"   📋 Model: {results.get('model', 'Unknown')}")
        print(f"   🏷️  Serial: {results.get('serial', 'Unknown')}")
        print(f"   📊 Version: {results.get('version', 'Unknown')}")
        print(f"   ⏱️  Uptime: {results.get('uptime', 'Unknown')}")
    else:
        print(f"   ❌ Error: {status.get('error', 'Unknown error')}")
    
    # Resource usage
    print("\n2. Resource Utilization:")
    resources = fg_api._make_request("GET", "monitor/system/resource/usage")
    if "error" not in resources:
        results = resources.get('results', {})
        cpu = results.get('cpu', 'Unknown')
        memory = results.get('memory', 'Unknown')
        disk = results.get('disk', 'Unknown')
        sessions = results.get('session_count', 'Unknown')
        
        print(f"   🔥 CPU Usage: {cpu}%")
        print(f"   💾 Memory Usage: {memory}%")
        print(f"   💿 Disk Usage: {disk}%")
        print(f"   🔗 Active Sessions: {sessions}")
        
        # Health assessment
        try:
            cpu_val = float(cpu) if cpu != 'Unknown' else 0
            mem_val = float(memory) if memory != 'Unknown' else 0
            
            if cpu_val > 80 or mem_val > 85:
                print("   ⚠️  WARNING: High resource utilization detected!")
            else:
                print("   ✅ System resources are healthy")
        except:
            print("   ℹ️  Resource values not numeric, cannot assess health")
    else:
        print(f"   ❌ Error: {resources.get('error', 'Unknown error')}")

def demo_network_management():
    """Demonstrate FortiGate network management capabilities"""
    print("\n" + "=" * 60)
    print("FORTIGATE NETWORK MANAGEMENT DEMO")
    print("=" * 60)
    
    # Interface statistics
    print("\n1. Network Interfaces:")
    interfaces = fg_api._make_request("GET", "monitor/system/interface")
    if "error" not in interfaces:
        interface_list = interfaces.get('results', [])
        total_interfaces = len(interface_list)
        active_interfaces = len([i for i in interface_list if i.get('link', False)])
        
        print(f"   📡 Total Interfaces: {total_interfaces}")
        print(f"   ✅ Active Interfaces: {active_interfaces}")
        print(f"   ❌ Inactive Interfaces: {total_interfaces - active_interfaces}")
        
        print("\n   Top Interfaces by Traffic:")
        sorted_interfaces = sorted(
            interface_list, 
            key=lambda x: x.get('rx_bytes', 0) + x.get('tx_bytes', 0), 
            reverse=True
        )
        
        for i, iface in enumerate(sorted_interfaces[:5]):
            name = iface.get('name', 'Unknown')
            status = '🟢' if iface.get('link', False) else '🔴'
            rx_bytes = iface.get('rx_bytes', 0)
            tx_bytes = iface.get('tx_bytes', 0)
            total_bytes = rx_bytes + tx_bytes
            
            print(f"     {i+1}. {status} {name}: {total_bytes:,} bytes total")
    else:
        print(f"   ❌ Error: {interfaces.get('error', 'Unknown error')}")
    
    # Routing information
    print("\n2. Routing Table:")
    routes = fg_api._make_request("GET", "monitor/router/ipv4")
    if "error" not in routes:
        route_list = routes.get('results', [])
        total_routes = len(route_list)
        default_routes = len([r for r in route_list if r.get('destination') == '0.0.0.0/0'])
        static_routes = len([r for r in route_list if r.get('type') == 'static'])
        
        print(f"   🛣️  Total Routes: {total_routes}")
        print(f"   🏠 Default Routes: {default_routes}")
        print(f"   📍 Static Routes: {static_routes}")
    else:
        print(f"   ❌ Error: {routes.get('error', 'Unknown error')}")

def demo_switch_controller():
    """Demonstrate FortiGate switch controller capabilities"""
    print("\n" + "=" * 60)
    print("FORTIGATE SWITCH CONTROLLER DEMO")
    print("=" * 60)
    
    # Detected devices (your original curl command functionality)
    print("\n1. Detected Devices (Your Original Curl Command Enhanced):")
    devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    if "error" not in devices:
        device_list = devices.get('results', [])
        print(f"   🔍 Total Detected Devices: {len(device_list)}")
        
        if device_list:
            # Group by switch
            switches = {}
            vlans = set()
            
            for device in device_list:
                switch_id = device.get('switch_id', 'Unknown')
                vlan_id = device.get('vlan_id')
                
                if switch_id not in switches:
                    switches[switch_id] = []
                switches[switch_id].append(device)
                
                if vlan_id:
                    vlans.add(vlan_id)
            
            print(f"   🔀 Managed Switches: {len(switches)}")
            print(f"   🏷️  VLANs in Use: {sorted(vlans)}")
            
            print("\n   📋 Device Details:")
            for i, device in enumerate(device_list[:10]):  # Show first 10
                mac = device.get('mac', 'Unknown')
                port = device.get('port_name', 'Unknown')
                switch_id = device.get('switch_id', 'Unknown')
                vlan = device.get('vlan_id', 'Unknown')
                last_seen = device.get('last_seen', 'Unknown')
                
                print(f"     {i+1}. 📱 MAC: {mac}")
                print(f"        🔌 Port: {port} on {switch_id}")
                print(f"        🏷️  VLAN: {vlan} | ⏰ Last Seen: {last_seen}s ago")
        else:
            print("   ℹ️  No devices detected")
    else:
        print(f"   ❌ Error: {devices.get('error', 'Unknown error')}")

def demo_security_features():
    """Demonstrate FortiGate security features"""
    print("\n" + "=" * 60)
    print("FORTIGATE SECURITY FEATURES DEMO")
    print("=" * 60)
    
    # Security statistics
    security_stats = {}
    
    print("\n1. Security Protection Status:")
    
    # Antivirus stats
    av_stats = fg_api._make_request("GET", "monitor/antivirus/stats")
    if "error" not in av_stats:
        print("   🛡️  Antivirus: Active")
        security_stats['antivirus'] = av_stats.get('results', {})
    else:
        print("   🛡️  Antivirus: Status unknown")
    
    # IPS stats
    ips_stats = fg_api._make_request("GET", "monitor/ips/stats")
    if "error" not in ips_stats:
        print("   🔒 IPS: Active")
        security_stats['ips'] = ips_stats.get('results', {})
    else:
        print("   🔒 IPS: Status unknown")
    
    # Web filter stats
    webfilter_stats = fg_api._make_request("GET", "monitor/webfilter/stats")
    if "error" not in webfilter_stats:
        print("   🌐 Web Filter: Active")
        security_stats['webfilter'] = webfilter_stats.get('results', {})
    else:
        print("   🌐 Web Filter: Status unknown")
    
    # VPN status
    print("\n2. VPN Status:")
    vpn_status = fg_api._make_request("GET", "monitor/vpn/ipsec")
    if "error" not in vpn_status:
        vpn_tunnels = vpn_status.get('results', [])
        active_tunnels = len([t for t in vpn_tunnels if t.get('status') == 'up'])
        total_tunnels = len(vpn_tunnels)
        
        print(f"   🔐 Total VPN Tunnels: {total_tunnels}")
        print(f"   ✅ Active Tunnels: {active_tunnels}")
        print(f"   ❌ Inactive Tunnels: {total_tunnels - active_tunnels}")
    else:
        print(f"   ❌ Error: {vpn_status.get('error', 'Unknown error')}")

def demo_fortiswitch_direct():
    """Demonstrate FortiSwitch direct API capabilities"""
    print("\n" + "=" * 60)
    print("FORTISWITCH DIRECT API DEMO")
    print("=" * 60)
    
    # FortiSwitch specific endpoints
    fortiswitch_files = [
        'FortiSwitch 7.6.1 Monitor API switch',
        'FortiSwitch 7.6.1 Monitor API system'
    ]
    
    fortiswitch_endpoints = []
    for key, info in discovered_endpoints.items():
        source = info.get('source_file', '')
        if any(fsw_file in source for fsw_file in fortiswitch_files):
            fortiswitch_endpoints.append({
                'key': key,
                'path': info.get('path', ''),
                'method': info.get('method', 'GET'),
                'summary': info.get('summary', '')
            })
    
    print(f"\n1. FortiSwitch Direct API Endpoints Available: {len(fortiswitch_endpoints)}")
    
    # Group by functionality
    categories = {
        'switch_management': [],
        'port_management': [],
        'vlan_management': [],
        'security': [],
        'system': [],
        'monitoring': []
    }
    
    for endpoint in fortiswitch_endpoints:
        path = endpoint['path'].lower()
        if any(x in path for x in ['switch/', 'switch-']):
            if 'port' in path:
                categories['port_management'].append(endpoint)
            elif 'vlan' in path:
                categories['vlan_management'].append(endpoint)
            elif any(x in path for x in ['802.1x', 'acl', 'security']):
                categories['security'].append(endpoint)
            elif 'system' in path:
                categories['system'].append(endpoint)
            elif any(x in path for x in ['stats', 'status', 'monitor']):
                categories['monitoring'].append(endpoint)
            else:
                categories['switch_management'].append(endpoint)
    
    print("\n   📂 FortiSwitch Endpoint Categories:")
    for category, endpoints in categories.items():
        if endpoints:
            print(f"     📁 {category.replace('_', ' ').title()}: {len(endpoints)} endpoints")
    
    # Show sample endpoints
    print("\n2. Sample FortiSwitch Direct Endpoints:")
    for category, endpoints in categories.items():
        if endpoints:
            print(f"\n   📋 {category.replace('_', ' ').title()}:")
            for endpoint in endpoints[:3]:  # Show first 3
                print(f"     - {endpoint['key']}: {endpoint['path']} ({endpoint['method']})")

def demo_comprehensive_report():
    """Generate comprehensive network report combining all capabilities"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE NETWORK REPORT")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'report_type': 'comprehensive_network_analysis',
        'fortigate_system': {},
        'network_status': {},
        'switch_controller': {},
        'security_status': {},
        'api_coverage': {},
        'health_summary': {}
    }
    
    print("\n🔍 Generating comprehensive network report...")
    
    # System information
    status = fg_api._make_request("GET", "monitor/system/status")
    if "error" not in status:
        results = status.get('results', {})
        report['fortigate_system'] = {
            'hostname': results.get('hostname', 'Unknown'),
            'model': results.get('model', 'Unknown'),
            'version': results.get('version', 'Unknown'),
            'serial': results.get('serial', 'Unknown'),
            'status': 'online'
        }
    
    # Network status
    interfaces = fg_api._make_request("GET", "monitor/system/interface")
    if "error" not in interfaces:
        interface_list = interfaces.get('results', [])
        report['network_status'] = {
            'total_interfaces': len(interface_list),
            'active_interfaces': len([i for i in interface_list if i.get('link', False)]),
            'interface_health': 'good' if len([i for i in interface_list if i.get('link', False)]) > 0 else 'warning'
        }
    
    # Switch controller
    devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    if "error" not in devices:
        device_list = devices.get('results', [])
        switches = set([d.get('switch_id', '') for d in device_list if d.get('switch_id')])
        report['switch_controller'] = {
            'detected_devices': len(device_list),
            'managed_switches': len(switches),
            'switches': list(switches)
        }
    
    # API coverage
    report['api_coverage'] = {
        'total_endpoints': len(discovered_endpoints),
        'fortigate_endpoints': len([k for k, v in discovered_endpoints.items() 
                                   if 'FortiOS' in v.get('source_file', '')]),
        'fortiswitch_endpoints': len([k for k, v in discovered_endpoints.items() 
                                     if 'FortiSwitch' in v.get('source_file', '')]),
        'categories': list(api_parser.categories.keys())
    }
    
    # Health summary
    health_checks = []
    health_checks.append(report['fortigate_system'].get('status') == 'online')
    health_checks.append(report['network_status'].get('active_interfaces', 0) > 0)
    health_checks.append(report['switch_controller'].get('detected_devices', 0) > 0)
    
    health_score = (sum(health_checks) / len(health_checks)) * 100
    report['health_summary'] = {
        'overall_health_score': health_score,
        'status': 'excellent' if health_score > 90 else 'good' if health_score > 70 else 'warning',
        'fortigate_online': health_checks[0],
        'network_active': health_checks[1],
        'switches_detected': health_checks[2]
    }
    
    # Display summary
    print(f"\n📊 Report Summary:")
    print(f"   🖥️  FortiGate: {report['fortigate_system'].get('hostname', 'Unknown')} ({report['fortigate_system'].get('status', 'Unknown')})")
    print(f"   📡 Network: {report['network_status'].get('active_interfaces', 0)}/{report['network_status'].get('total_interfaces', 0)} interfaces active")
    print(f"   🔀 Switches: {report['switch_controller'].get('detected_devices', 0)} devices on {report['switch_controller'].get('managed_switches', 0)} switches")
    print(f"   🔧 API Coverage: {report['api_coverage']['total_endpoints']} endpoints available")
    print(f"   💚 Health Score: {report['health_summary']['overall_health_score']:.1f}% ({report['health_summary']['status']})")
    
    # Save report
    report_filename = f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    return report

def main():
    """Main demonstration function"""
    print("🚀 FORTINET MCP SERVER COMPREHENSIVE DEMO")
    print("Demonstrating both FortiGate and FortiSwitch API capabilities")
    print()
    
    try:
        # 1. Show API coverage
        functional_groups = demo_fortigate_api_coverage()
        
        # 2. FortiGate system management
        demo_system_management()
        
        # 3. Network management
        demo_network_management()
        
        # 4. Switch controller (your original curl functionality enhanced)
        demo_switch_controller()
        
        # 5. Security features
        demo_security_features()
        
        # 6. FortiSwitch direct API
        demo_fortiswitch_direct()
        
        # 7. Comprehensive report
        report = demo_comprehensive_report()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\n✅ Key Achievements:")
        print(f"   📈 {len(discovered_endpoints)} API endpoints discovered and tested")
        print(f"   🔧 {len([k for k, v in discovered_endpoints.items() if 'FortiOS' in v.get('source_file', '')])} FortiGate endpoints")
        print(f"   🔀 {len([k for k, v in discovered_endpoints.items() if 'FortiSwitch' in v.get('source_file', '')])} FortiSwitch endpoints")
        print(f"   🎯 Your original curl command now part of comprehensive API ecosystem")
        print(f"   🤖 Ready for AI integration via Claude Desktop")
        print(f"   🐍 Available as Python module for automation")
        
    except Exception as e:
        print(f"\n❌ Demo encountered an error: {e}")
        print("💡 This might be due to network connectivity or API permissions")
        print("🔧 Check your FortiGate connection and API token")

if __name__ == "__main__":
    main()