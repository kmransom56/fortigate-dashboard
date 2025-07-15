#!/usr/bin/env python3

import sys
import asyncio
sys.path.append('.')

from app.services.fortiswitch_service_optimized import get_fortiswitches_optimized
from app.utils.restaurant_device_classifier import enhance_device_info

async def test_optimized_integration():
    """Test that optimized service properly integrates with enhanced device classification."""
    print('=== Testing Optimized Service Integration ===')
    
    test_device = {
        'device_name': 'cisco-switch-01',
        'manufacturer': 'Cisco',
        'device_mac': '00:1B:21:AA:BB:CC',
        'device_ip': '192.168.1.10'
    }
    
    enhanced = enhance_device_info(test_device)
    print('Enhanced device info keys:', sorted(enhanced.keys()))
    print('Classification result:', enhanced.get('restaurant_device_type'))
    print('Icon info:', enhanced.get('icon_code'), enhanced.get('icon_color'), enhanced.get('icon_size'))
    print()
    
    try:
        switches = await get_fortiswitches_optimized()
        print(f'Optimized service returned {len(switches)} switches')
        
        if switches:
            sample_switch = switches[0]
            expected_keys = ['name', 'serial', 'model', 'status', 'ports', 'connected_devices_count']
            for key in expected_keys:
                assert key in sample_switch, f"Missing key: {key}"
            print('✅ Switch data structure is correct')
            
            enhanced_found = False
            for port in sample_switch.get('ports', []):
                for device in port.get('connected_devices', []):
                    enhanced_fields = ['restaurant_device_type', 'icon_code', 'icon_color', 'classification_confidence']
                    for field in enhanced_fields:
                        if field in device:
                            enhanced_found = True
                            print(f'✅ Enhanced device fields present: {field} = {device[field]}')
                            break
                    if enhanced_found:
                        break
                if enhanced_found:
                    break
            
            if not enhanced_found:
                print('ℹ️ No enhanced devices found (expected in test environment without real FortiGate)')
        
        return True
            
    except Exception as e:
        print(f'❌ Error testing optimized service: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_integration())
    print(f'Integration test {"PASSED" if success else "FAILED"}')
