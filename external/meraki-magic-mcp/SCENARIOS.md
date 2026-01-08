# Meraki Magic MCP - Real-World Scenarios & Use Cases

This guide provides detailed walkthroughs of real-world scenarios showing when and how to use each MCP version.

## Organization-Specific Query Examples

When you have multiple Meraki organizations configured, target specific orgs for faster, focused queries:

**Buffalo Wild Wings Network Operations:**
```
@Meraki_BuffaloWildWings Show me clients connected to SSID V850_Guest_SSID
@Meraki_BuffaloWildWings List all networks and their device counts
@Meraki_BuffaloWildWings Show recent alerts in the past 24 hours
```

**Baskin Robbins Store Management:**
```
@Meraki_BaskinRobbins list all networks
@Meraki_BaskinRobbins show offline devices at network "Store-Boston-01"
@Meraki_BaskinRobbins get wireless health metrics for all APs
```

**Arby's Multi-Site Operations:**
```
@Meraki_Arbys show me device inventory across all locations
@Meraki_Arbys list clients with connection issues in the past hour
@Meraki_Arbys get SSID configuration for "Arbys_Guest_WiFi"
```

**Comcast Dunkin Operations:**
```
@Meraki_ComcastDunkin show clients on SSID "Guest_WiFi"
@Meraki_ComcastDunkin list switch port status at network "Dunkin-NYC-Central"
@Meraki_ComcastDunkin get traffic analytics for past 7 days
```

**Inspire Brands Corporate:**
```
@Meraki_InspireBrands show network health across all brands
@Meraki_InspireBrands list firmware versions for all devices
```

**Cross-Organization Discovery:**
```
@Meraki_All_Orgs list all organizations and their network counts
@Meraki_All_Orgs show me total client count across all brands
```

---

## Table of Contents

1. [Quick Decision Guide](#quick-decision-guide)
2. [Network Operations Scenarios](#network-operations-scenarios)
3. [Security & Compliance Scenarios](#security--compliance-scenarios)
4. [MSP & Multi-Tenant Scenarios](#msp--multi-tenant-scenarios)
5. [Troubleshooting Scenarios](#troubleshooting-scenarios)
6. [Automation & Integration Scenarios](#automation--integration-scenarios)
7. [Performance & Optimization Tips](#performance--optimization-tips)

---

## Quick Decision Guide

### Use Dynamic MCP When:

✅ You need to **explore** capabilities  
✅ You're **troubleshooting** unknown issues  
✅ You need **broad API coverage** (100+ endpoints)  
✅ You want **auto-updates** with SDK releases  
✅ You're doing **one-time analysis** or audits  
✅ You need to **discover** available methods  

### Use Manual MCP When:

✅ You have **repetitive workflows** (10-20 endpoints)  
✅ You need **type safety** and validation  
✅ You want **custom business logic**  
✅ You're building **production automation**  
✅ You need **detailed documentation**  
✅ You prefer a **curated toolset**  

### Use Both MCPs When:

✅ You want **flexibility** for different tasks  
✅ Your team has **varied skill levels**  
✅ You need **exploration + automation**  
✅ You want **maximum capability**  

---

## Network Operations Scenarios

### Scenario 1: Daily Health Check Dashboard

**Challenge:** NOC team needs to check health of 50+ networks every morning

**Solution:** Dynamic MCP (ad-hoc queries) + Manual MCP (standard checks)

**Workflow with Dynamic MCP:**
```
Morning Check Prompts:

1. "Show me all networks with critical alerts in the past 24 hours"

2. "For each network with alerts, get:
   - Current device statuses
   - Recent configuration changes
   - Top 5 clients by bandwidth"

3. "List any devices that have been offline >1 hour"

4. "Show wireless health: channel utilization and signal quality trends"
```

**Why Dynamic:** 
- Unpredictable alert types require flexible endpoint access
- Can pivot investigation based on findings
- Discovery tools help locate relevant methods

**Code Example:**
```python
# Using call_meraki_api for flexible queries
call_meraki_api(
    section="organizations",
    method="getOrganizationAlertsHistory",
    parameters={
        "organizationId": "123456",
        "startingAfter": "2026-01-05T00:00:00Z"
    }
)
```

---

### Scenario 2: Standardized Network Provisioning

**Challenge:** MSP needs to deploy 10 networks/week with identical config

**Solution:** Manual MCP (validated workflows)

**Workflow with Manual MCP:**
```
Provisioning Prompts:

1. "Create a new network named 'Customer-XYZ-HQ' using template settings"

2. "Configure SSIDs:
   - Corporate: WPA2-Enterprise with RADIUS
   - Guest: WPA2-PSK with splash page
   - IoT: WPA2-PSK on VLAN 100"

3. "Set up firewall rules:
   - Block inter-VLAN routing
   - Allow only ports 80,443 outbound for Guest
   - Enable content filtering on MX"

4. "Claim devices: [serial1, serial2, serial3]"
```

**Why Manual:**
- Repetitive workflow benefits from type validation
- Pydantic schemas prevent configuration errors
- Custom templates can be coded into tools
- Production-safe with error handling

**Validation Benefits:**
```python
# Manual MCP uses Pydantic for safety
class NetworkCreateSchema(BaseModel):
    name: str
    productTypes: List[str]
    tags: Optional[List[str]]
    # Validates before API call
```

---

## Security & Compliance Scenarios

### Scenario 3: Quarterly Security Audit

**Challenge:** Compliance team needs to audit all firewall rules quarterly

**Solution:** Dynamic MCP (one-time comprehensive analysis)

**Audit Workflow:**
```
Security Audit Prompts:

1. "Get all organizations I have access to"

2. "For each organization, list all networks"

3. "For each network, analyze:
   - L3 firewall rules (identify any rules with 0.0.0.0/0 source)
   - L7 firewall rules (check application blocking)
   - Content filtering status
   - Wireless SSID security (flag anything weaker than WPA2)
   - VPN configuration (site-to-site and client VPN)"

4. "Generate summary report:
   - Networks with open firewall rules
   - Wireless networks with weak security
   - MX appliances without content filtering"
```

**Why Dynamic:**
- Need access to 10+ endpoint types
- One-time analysis (not repeated daily)
- Requirements may change quarterly
- Discovery tools help find relevant methods

**Advanced Example:**
```
Prompt: "Use search_methods to find all security-related endpoints, then audit my network 'HQ' for:
- Any firewall rules allowing inbound from internet
- Wireless SSIDs without 802.1X
- Content filtering categories not blocked"
```

---

### Scenario 4: Real-Time Security Monitoring

**Challenge:** Security team needs instant alerts on suspicious activity

**Solution:** Dynamic MCP (flexible investigation) + webhooks

**Investigation Workflow:**
```
Alert Response Prompts:

Alert: "Suspicious traffic detected on network 'Branch-05'"

1. "Show me security events for network 'Branch-05' in past 30 minutes"

2. "Get firewall denials grouped by source IP"

3. "For top offending IPs, show:
   - Client details (hostname, MAC, user)
   - Recent network events
   - Device they're connected to"

4. "Check if these IPs appear in other networks"

5. "If malicious, block them:
   - Add to group policy 'Blocked-Devices'
   - Update firewall rules to deny"
```

**Why Dynamic:**
- Investigation path is unpredictable
- Need to pivot based on findings
- May need obscure endpoints (Air Marshal, IDS events)
- Speed matters in security incidents

---

## MSP & Multi-Tenant Scenarios

### Scenario 5: Multi-Org Management

**Challenge:** MSP manages 50 customer organizations

**Solution:** Dynamic MCP (discovery) + Manual MCP (standard ops)

**Cross-Org Operations:**
```
MSP Management Prompts:

1. "List all organizations I manage"

2. "For each organization, collect:
   - License expiration dates
   - Total device count by model
   - Networks with firmware alerts
   - API request usage (approaching limits?)"

3. "Identify customers needing license renewal in next 60 days"

4. "Generate executive summary for customer 'ABC Corp':
   - Network uptime (past 30 days)
   - Top 5 alerts
   - Bandwidth trends
   - Device health scores"
```

**Why Dynamic:**
- Varies by customer (different endpoint needs)
- Executive reports need flexibility
- License management uses rare endpoints

**MSP Automation Tip:**
```
Use Dynamic for discovery, then automate common tasks with Manual MCP:

Dynamic: "Which networks need VLAN reconfiguration?"
Manual: "Update VLAN 100 on switch XYZ to 192.168.1.0/24"
```

---

### Scenario 6: Customer Onboarding

**Challenge:** Onboard new MSP customer with 5 locations

**Solution:** Manual MCP (validated, repeatable process)

**Onboarding Workflow:**
```
Step-by-Step Prompts:

1. "Create organization 'Customer-ABC'"

2. "Create 5 networks:
   - ABC-HQ (combined MX/MS/MR)
   - ABC-Branch-1 (combined MX/MS/MR)
   - ABC-Branch-2 (combined MX/MS/MR)
   - ABC-Branch-3 (combined MS/MR)
   - ABC-Remote (combined MS/MR)"

3. "Apply standard configuration template to all networks:
   - SSIDs: Corporate, Guest
   - Firewall rules: Standard MSP policy
   - Content filtering: Standard categories
   - VLANs: Management, Data, Voice, Guest"

4. "Create admin accounts:
   - Customer IT lead (full access)
   - Customer help desk (read-only)"

5. "Claim devices to respective networks"

6. "Generate welcome document with network details"
```

**Why Manual:**
- Repeatable process (weekly onboarding)
- Type validation prevents errors
- Custom templates coded into tools
- Consistent results across customers

---

## Troubleshooting Scenarios

### Scenario 7: "Users Can't Connect" Emergency

**Challenge:** 2am phone call - users at branch office can't connect

**Solution:** Dynamic MCP (fast, flexible troubleshooting)

**Emergency Troubleshooting:**
```
Incident Response Prompts:

1. "Show me current status of all devices at network 'Branch-Office'"

2. "Are there any critical alerts? When did they start?"

3. "Check recent configuration changes (past 4 hours)"

4. "Get wireless health data:
   - Channel utilization
   - Connection failures
   - RF interference"

5. "Show clients attempting to connect (past 15 minutes)"

6. "For failed connections, show:
   - Authentication failures
   - DHCP issues
   - Wireless association problems"

7. "Compare current settings to yesterday's working config"
```

**Why Dynamic:**
- Time-sensitive (need any endpoint instantly)
- Investigation path unknown
- May need obscure diagnostics
- Helper tools aid discovery

**Live Diagnostics:**
```
Advanced Prompts:

"Run cable test on all switch ports at Branch-Office"
"Ping gateway from MX appliance"
"Show ARP table on distribution switch"
"Check if any ports are error-disabled"
```

---

### Scenario 8: Performance Degradation Analysis

**Challenge:** Network "feels slow" - need to find bottleneck

**Solution:** Dynamic MCP (comprehensive data collection)

**Performance Analysis:**
```
Investigation Prompts:

1. "Get traffic analysis for network 'HQ' over past 7 days"

2. "Identify top 10 bandwidth consumers:
   - By client
   - By application
   - By port"

3. "Check switch port utilization:
   - Any ports >80% utilization?
   - Error rates by port
   - Duplex mismatches?"

4. "Analyze wireless performance:
   - Channel congestion
   - Retransmission rates
   - Signal quality by AP"

5. "Check MX appliance:
   - WAN utilization
   - VPN throughput
   - CPU/memory usage"

6. "Review QoS configuration:
   - Are policies applied correctly?
   - Any unexpected traffic prioritization?"
```

**Why Dynamic:**
- Need many endpoint types
- Hypothesis-driven investigation
- May need custom data correlation

---

## Automation & Integration Scenarios

### Scenario 9: CI/CD Pipeline Integration

**Challenge:** Automate network changes via GitOps

**Solution:** Manual MCP (type-safe automation)

**Pipeline Example:**
```yaml
# .github/workflows/network-update.yml
name: Apply Network Configuration

on:
  push:
    paths:
      - 'networks/**.yaml'

jobs:
  apply-config:
    runs-on: ubuntu-latest
    steps:
      - name: Update Firewall Rules
        run: |
          claude-cli --mcp Meraki_Curated \
            "Update firewall rules on network {{ network_id }} 
             using rules from firewall-rules.yaml"
```

**Why Manual:**
- Type validation prevents pipeline failures
- Pydantic schemas validate YAML configs
- Predictable tool behavior for CI/CD
- Custom error handling

---

### Scenario 10: CMDB Synchronization

**Challenge:** Sync Meraki inventory to ServiceNow CMDB

**Solution:** Dynamic MCP (comprehensive data export)

**Sync Workflow:**
```
CMDB Sync Prompts:

1. "Export complete inventory:
   - All organizations
   - All networks per org
   - All devices per network (with full details)
   - All clients (past 24 hours)
   - License status"

2. "For each device, collect:
   - Model, serial, MAC
   - Firmware version
   - Last seen timestamp
   - Network assignment
   - Management IP
   - Tags"

3. "Export as JSON for CMDB import"

4. "Flag any discrepancies:
   - Devices in CMDB but not in Meraki
   - Devices in Meraki but not in CMDB"
```

**Why Dynamic:**
- Comprehensive data collection
- May need new fields as CMDB evolves
- One-way sync (read-only)

---

## Performance & Optimization Tips

### When Using Dynamic MCP

**Enable Caching:**
```env
# .env
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300
```
Reduces API calls by 50-90% for read operations

**Use Batch Operations:**
```
Instead of:
"Get network details for network 1"
"Get network details for network 2"
"Get network details for network 3"

Use:
"Get details for all networks in organization 123456"
```

**Leverage Discovery Tools:**
```
1. "List all methods in the 'wireless' section"
2. "Search for methods containing 'channel'"
3. "Get parameter info for getNetworkWirelessChannelUtilizationHistory"
4. Actually call the method
```

### When Using Manual MCP

**Use Schemas for Validation:**
```python
# Manual MCP validates inputs
update_wireless_ssid(
    network_id="L_123",
    ssid_number=0,
    ssid_settings={
        "name": "Corporate",
        "enabled": True,
        "authMode": "psk",
        "encryptionMode": "wpa",  # Wrong! Caught by schema
        "psk": "password123"
    }
)
# Error: encryptionMode must be 'wpa2' or stronger
```

**Create Custom Workflows:**
```python
# Manual MCP allows custom tools
@mcp.tool()
async def provision_standard_network(name: str, location: str):
    """Custom tool combining multiple operations"""
    # Create network
    # Configure SSIDs
    # Set firewall rules
    # Apply templates
    # Return summary
```

### Using Both Together

**Best Practice: Route by Task Type**
```
Exploration Tasks → Dynamic MCP
"What firewall methods are available?"
"Show me all security events"

Production Tasks → Manual MCP
"Create SSID 'Guest-WiFi' on network 'Branch-01'"
"Update port 12 to VLAN 100"
```

Claude automatically chooses the right MCP server based on your prompt!

---

## Prompt Templates by Role

### Network Administrator
```
Daily Check:
"Show me networks with alerts, offline devices, and high bandwidth users"

Provisioning:
"Create network 'Branch-06' and configure standard SSIDs and firewall rules"

Troubleshooting:
"Why can't client ABC123 connect to SSID 'Corporate'?"
```

### Security Analyst
```
Audit:
"Audit all firewall rules for networks allowing inbound from internet"

Investigation:
"Show security events for IP 192.168.1.100 in the past hour"

Response:
"Block client MAC ab:cd:ef:12:34:56 across all networks"
```

### MSP Engineer
```
Customer Check:
"Generate health report for customer 'ABC Corp' covering uptime, alerts, and device status"

Onboarding:
"Create organization 'New-Customer-XYZ' with 3 networks using standard template"

License Management:
"List all customers with licenses expiring in next 90 days"
```

### DevOps Engineer
```
Automation:
"Export all network configurations as JSON for version control"

Integration:
"Get all devices with their IPs and MACs for IPAM sync"

Validation:
"Verify all networks have required SSIDs and firewall rules"
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Too Many API Calls

**Problem:** Rate limiting errors

**Solution with Dynamic MCP:**
```env
ENABLE_CACHING=true  # Cache read operations
```

**Solution with Manual MCP:**
```python
# Use batch operations
get_organization_devices(org_id)  # Gets all devices at once
# Instead of:
# get_device_details(serial1)
# get_device_details(serial2)
# ...
```

### Pitfall 2: Unclear Prompts

**Problem:** Claude doesn't know which tool to use

**Bad Prompt:**
"Show me stuff about networks"

**Good Prompt:**
"Use get_networks to list all networks in organization 123456, then for each network, get device count and alert history"

### Pitfall 3: Missing Parameters

**Problem:** API calls fail due to missing required fields

**Solution with Manual MCP:**
- Pydantic schemas validate before calling API
- Clear error messages guide you

**Solution with Dynamic MCP:**
- Use `get_method_info` to see required parameters
- Check method documentation first

---

## Additional Resources

- **[README.md](README.md)** - Main documentation
- **[README-DYNAMIC.md](README-DYNAMIC.md)** - Dynamic MCP details
- **[INSTALL.md](INSTALL.md)** - Installation guide
- **[QUICKSTART.md](QUICKSTART.md)** - Getting started
- **[COMPARISON.md](COMPARISON.md)** - Feature comparison
- **[OPTIMIZATIONS.md](OPTIMIZATIONS.md)** - Performance tuning

---

## Contributing Your Scenarios

Have a scenario that helped you? Submit a PR with:
1. Scenario description
2. Which MCP version you used
3. Example prompts
4. Results/lessons learned

This helps the community learn from real-world usage!
