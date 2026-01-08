# Organization-Specific Query Examples

When managing multiple Meraki organizations, use organization-specific MCP servers for faster, targeted queries.

## Buffalo Wild Wings Operations

```
@Meraki_BuffaloWildWings Show me clients connected to SSID V850_Guest_SSID
@Meraki_BuffaloWildWings List all networks and their device counts
@Meraki_BuffaloWildWings Show recent alerts in the past 24 hours
@Meraki_BuffaloWildWings Get wireless health metrics for all access points
```

## Baskin Robbins Store Management

```
@Meraki_BaskinRobbins list all networks
@Meraki_BaskinRobbins show offline devices at network "Store-Boston-01"
@Meraki_BaskinRobbins get wireless health metrics for all APs
@Meraki_BaskinRobbins show clients with connection issues
```

## Arby's Multi-Site Operations

```
@Meraki_Arbys show me device inventory across all locations
@Meraki_Arbys list clients with connection issues in the past hour
@Meraki_Arbys get SSID configuration for "Arbys_Guest_WiFi"
@Meraki_Arbys show network health summary across all stores
```

## Comcast Dunkin Operations

```
@Meraki_ComcastDunkin show clients on SSID "Guest_WiFi"
@Meraki_ComcastDunkin list switch port status at network "Dunkin-NYC-Central"
@Meraki_ComcastDunkin get traffic analytics for past 7 days
@Meraki_ComcastDunkin show firmware versions for all devices
```

## Comcast Dunkin Wireless

```
@Meraki_ComcastDunkinWireless list all SSIDs and their configurations
@Meraki_ComcastDunkinWireless show RF profile settings
@Meraki_ComcastDunkinWireless get wireless client connection history
```

## Comcast Baskin Robbins

```
@Meraki_ComcastBaskin show network topology
@Meraki_ComcastBaskin list all access points and their status
@Meraki_ComcastBaskin get device uptime statistics
```

## Inspire Brands Corporate

```
@Meraki_InspireBrands show network health across all brands
@Meraki_InspireBrands list firmware versions for all devices
@Meraki_InspireBrands get security appliance configurations
@Meraki_InspireBrands show VPN connectivity status
```

## Cross-Organization Discovery

```
@Meraki_All_Orgs list all organizations and their network counts
@Meraki_All_Orgs show me total client count across all brands
@Meraki_All_Orgs get inventory summary for all organizations
@Meraki_All_Orgs show licensing status across all orgs
```

## Tips for Organization-Specific Queries

1. **Use specific org servers for faster responses** - Targeting one org avoids discovery overhead
2. **Use @Meraki_All_Orgs for comparison queries** - Get data across all organizations at once
3. **Combine with network names** - "show clients at network 'Store-Boston-01' in @Meraki_BaskinRobbins"
4. **Cache benefits** - Repeated queries to the same org use cached data for speed

## See Also

- [SCENARIOS.md](SCENARIOS.md) - Detailed use case walkthroughs
- [README-DYNAMIC.md](README-DYNAMIC.md) - Dynamic MCP documentation with full API access
- [README.md](README.md) - Main project documentation
