#!/usr/bin/env python3

import sys
import asyncio
sys.path.append('.')

from app.services.fortiswitch_service import get_fortiswitches as get_regular
from app.services.fortiswitch_service_optimized import get_fortiswitches_optimized

async def compare_services():
    """Compare data structure between regular and optimized services."""
    print('=== Comparing Service Data Structures ===')
    
    try:
        print('Fetching data from regular service...')
        regular_switches = get_regular()
        
        print('Fetching data from optimized service...')
        optimized_switches = await get_fortiswitches_optimized()
        
        print(f'Regular service: {len(regular_switches)} switches')
        print(f'Optimized service: {len(optimized_switches)} switches')
        
        if regular_switches and optimized_switches:
            reg_keys = set(regular_switches[0].keys())
            opt_keys = set(optimized_switches[0].keys())
            
            print(f'Regular keys: {sorted(reg_keys)}')
            print(f'Optimized keys: {sorted(opt_keys)}')
            print(f'Keys match: {reg_keys == opt_keys}')
            
            reg_enhanced = False
            opt_enhanced = False
            
            for switch in regular_switches:
                for port in switch.get('ports', []):
                    for device in port.get('connected_devices', []):
                        if 'restaurant_device_type' in device:
                            reg_enhanced = True
                            break
                    if reg_enhanced:
                        break
                if reg_enhanced:
                    break
            
            for switch in optimized_switches:
                for port in switch.get('ports', []):
                    for device in port.get('connected_devices', []):
                        if 'restaurant_device_type' in device:
                            opt_enhanced = True
                            break
                    if opt_enhanced:
                        break
                if opt_enhanced:
                    break
            
            print(f'Regular service has enhanced devices: {reg_enhanced}')
            print(f'Optimized service has enhanced devices: {opt_enhanced}')
            print(f'Enhancement consistency: {reg_enhanced == opt_enhanced}')
        
        return True
        
    except Exception as e:
        print(f'Error comparing services: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(compare_services())
