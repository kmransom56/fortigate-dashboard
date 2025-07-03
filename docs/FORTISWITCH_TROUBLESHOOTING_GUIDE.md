# FortiSwitch Device Detection Troubleshooting Guide

## Overview

This guide addresses common issues with obtaining connected device information on FortiSwitch ports via the FortiGate API. The improvements made to the FortiSwitch service resolve several key problems that prevent proper device detection.

## Key Issues Identified and Fixed

### 1. Rate Limiting Too Aggressive

**Problem**: The original service had a 10-second delay between API calls, making the application very slow.
**Solution**: Reduced rate limiting to 2 seconds between API calls for better responsiveness while still respecting FortiGate API limits.

### 2. MAC Address Normalization Issues

**Problem**: Inconsistent MAC address formats from different sources caused device matching failures.
**Solution**: Improved MAC normalization function that handles:

- Various separators (`:`, `-`, `.`, none)
- Missing leading zeros
- Mixed case
- Invalid formats with graceful fallback

### 3. Device Aggregation Logic Flaws

**Problem**: Devices detected by the switch controller weren't being properly matched with DHCP information.
**Solution**: Enhanced device aggregation with:

- Better error handling for invalid data
- Improved logging for debugging
- Robust MAC address matching between detected devices and DHCP leases

## Test Results

The improved service successfully detects and aggregates devices:

```
=== Test Results ===
- Detected devices: 6 (from switch controller)
- DHCP leases: 8 (from FortiGate DHCP server)
- Successfully matched: 5 devices with full information
- Ports with devices: 5 out of 6 active ports

Device Examples:
- Port port1: ne-atlanta-hq-c48ba34bdf5e (192.168.0.9) [C4:8B:A3:4B:DF:5F]
- Port port19: UbuntuAIServer (192.168.0.6) [10:7C:61:3F:2B:5D]
- Port port21: IB-3rdU6Gz3qRSm (192.168.0.7) [38:14:28:D5:ED:34]
- Port port22: unbound (192.168.0.3) [DC:A6:32:EB:46:F7]
```

## API Endpoints Used

The service queries multiple FortiGate API endpoints for comprehensive device detection:

1. **Switch Controller Detected Devices**: `/api/v2/monitor/switch-controller/detected-device`
2. **DHCP Leases**: `/api/v2/monitor/system/dhcp`
3. **Managed Switch Status**: `/api/v2/monitor/switch-controller/managed-switch/status`
4. **System ARP Table**: `/api/v2/monitor/system/arp` (for additional device discovery)

## Authentication Methods Supported

The service supports multiple authentication methods with automatic fallback:

1. **Session Authentication** (Preferred)

   - Uses username/password stored in `secrets/fortigate_password.txt`
   - Automatically manages session cookies
   - More secure than API tokens

2. **API Token Authentication** (Fallback)
   - Uses Bearer token from environment variables
   - Supports file-based token storage
   - Legacy compatibility

## Common Troubleshooting Steps

### 1. Check Authentication

```bash
# Verify session authentication
ls -la secrets/fortigate_password.txt

# Or verify API token
echo $FORTIGATE_API_TOKEN
```

### 2. Test API Connectivity

```bash
# Run the debug script
python test_improved_service.py

# Or test the main service
python app/services/fortiswitch_service.py
```

### 3. Check FortiGate Configuration

Ensure the following are configured on FortiGate:

- Switch controller is enabled
- FortiSwitch is properly managed
- DHCP server is running on the appropriate interface
- API user has sufficient permissions

### 4. Verify Network Topology

The service works best when:

- Devices are connected to FortiSwitch ports
- FortiSwitch is managed by FortiGate via FortiLink
- DHCP is served by FortiGate
- Switch controller can detect devices

## Debug Files Available

The following debug files contain sample API responses for testing:

- `debug_detected_devices.json` - Switch controller detected devices
- `debug_dhcp_info.json` - DHCP lease information
- `debug_switch_status.json` - Managed switch status and port information

## Logging Configuration

Set the log level for detailed debugging:

```bash
export LOG_LEVEL=DEBUG
python app/services/fortiswitch_service.py
```

## API Rate Limiting

The service implements intelligent rate limiting:

- Minimum 2 seconds between API calls
- Automatic retry on rate limit errors (429)
- Configurable via `min_api_interval` variable

## Error Handling Improvements

The improved service includes:

- Graceful handling of missing or invalid data
- Detailed error logging with context
- Fallback mechanisms for authentication
- Robust data validation

## Performance Optimizations

1. **Reduced API Call Frequency**: From 10s to 2s intervals
2. **Efficient Data Structures**: Using dictionaries for O(1) lookups
3. **Lazy Loading**: Only fetch additional data when needed
4. **Connection Reuse**: Session management for persistent connections

## Integration with Dashboard

The improved service integrates seamlessly with the existing dashboard:

- Same API interface (`get_fortiswitches()`)
- Enhanced data structure with device details
- Backward compatibility maintained
- Additional metadata for better visualization

## Future Enhancements

Potential improvements for even better device detection:

1. **Direct FortiSwitch API Integration**: Query switch directly for MAC tables
2. **SNMP Support**: Alternative discovery method for non-FortiLink scenarios
3. **Device Classification**: Automatic device type detection based on MAC OUI
4. **Historical Data**: Track device connection history
5. **Real-time Updates**: WebSocket-based live device status

## Conclusion

The improved FortiSwitch service resolves the primary issues with device detection on switch ports. The key improvements are:

1. **Faster Response Times**: 5x faster API calls
2. **Better Device Matching**: Improved MAC normalization and matching
3. **Enhanced Reliability**: Robust error handling and fallback mechanisms
4. **Comprehensive Logging**: Detailed debugging information
5. **Multiple Data Sources**: Combines switch controller, DHCP, and ARP data

The service now successfully detects and displays connected devices with their hostnames, IP addresses, and port associations, providing the visibility needed for network management and troubleshooting.
