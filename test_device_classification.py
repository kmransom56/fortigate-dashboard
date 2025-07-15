#!/usr/bin/env python3

from app.utils.restaurant_device_classifier import classify_restaurant_device, enhance_device_info, get_device_icon

def test_enterprise_classification():
    """Test enterprise device classification"""
    test_devices = [
        {'hostname': 'cisco-router-01', 'manufacturer': 'Cisco', 'mac': '00:1B:21:AA:BB:CC'},
        {'hostname': 'hp-printer-02', 'manufacturer': 'HP', 'mac': '00:0C:29:DD:EE:FF'},
        {'hostname': 'server-01', 'manufacturer': 'Dell', 'mac': '00:15:5D:11:22:33'},
        {'hostname': 'firewall-main', 'manufacturer': 'Fortinet', 'mac': '00:1E:C9:44:55:66'},
        {'hostname': 'switch-core-01', 'manufacturer': 'Cisco', 'mac': '00:2A:3B:CC:DD:EE'},
        {'hostname': 'ap-lobby', 'manufacturer': 'Ubiquiti', 'mac': '00:3C:4D:EE:FF:AA'}
    ]

    print('Testing enhanced device classification:')
    print('=' * 60)
    
    for device in test_devices:
        device_type, category, confidence = classify_restaurant_device(
            device['hostname'], device['manufacturer'], device['mac']
        )
        icon_config = get_device_icon(category, device_type)
        
        print(f'Device: {device["hostname"]}')
        print(f'  Manufacturer: {device["manufacturer"]}')
        print(f'  Type: {device_type}')
        print(f'  Category: {category}')
        print(f'  Confidence: {confidence:.2f}')
        print(f'  Icon: {icon_config["code"]} (color: {icon_config["color"]}, size: {icon_config["size"]})')
        print()

def test_enhanced_device_info():
    """Test the enhanced device info function"""
    test_device = {
        'device_name': 'cisco-switch-01',
        'manufacturer': 'Cisco',
        'device_mac': '00:1B:21:AA:BB:CC',
        'device_ip': '192.168.1.10'
    }
    
    enhanced = enhance_device_info(test_device)
    
    print('Testing enhance_device_info function:')
    print('=' * 60)
    print(f'Original device: {test_device}')
    print()
    print('Enhanced device info:')
    for key, value in enhanced.items():
        if key not in test_device:
            print(f'  {key}: {value}')

if __name__ == "__main__":
    test_enterprise_classification()
    print()
    test_enhanced_device_info()
