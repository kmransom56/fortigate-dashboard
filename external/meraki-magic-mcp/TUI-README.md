# Meraki Magic TUI - Interactive Dashboard

Beautiful terminal-based dashboard for managing Meraki networks across multiple organizations.

## Features

- 🏢 **Multi-Organization Support** - Switch between all your Meraki organizations
- 📊 **Real-Time Views** - Networks, Devices, Clients, Alerts, Health metrics
- ⌨️ **Keyboard Shortcuts** - Fast navigation with hotkeys
- 🎨 **Rich Interface** - Modern TUI with colors and tables
- 🔄 **Live Refresh** - Update data on demand
- 📱 **Responsive Layout** - Adapts to terminal size

## Installation

```bash
# Install dependencies
uv pip install textual python-dotenv

# Or use the launcher (handles installation automatically)
.\launch-tui.bat
```

## Usage

### Quick Start

```bash
# Launch the TUI
python meraki_tui.py

# Or use the Windows launcher
.\launch-tui.bat

# Or use the installed command (after pip install -e .)
meraki-tui
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `r` | Refresh current view |
| `1` | Show Networks |
| `2` | Show Devices |
| `3` | Show Clients |
| `4` | Show Alerts |
| `↑↓` | Navigate tables |
| `Tab` | Switch between widgets |

### Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Meraki Magic Dashboard - Multi-Organization Management     │
├─────────────────────────────────────────────────────────────┤
│ Organization: [Buffalo Wild Wings ▼]                       │
├──────────────┬──────────────────────────────────────────────┤
│ [Networks]   │  Name         │ ID     │ Products │ Tags   │
│ [Devices]    │  Store-01     │ N_xxx  │ wireless │ retail │
│ [Clients]    │  Store-02     │ N_yyy  │ switch   │ store  │
│ [Alerts]     │  HQ-Office    │ N_zzz  │ appliance│ corp   │
│ [Health]     │                                             │
│              │                                             │
│ Org Info:    │                                             │
│ Networks: 42 │                                             │
│ Devices: 186 │                                             │
├──────────────┴──────────────────────────────────────────────┤
│ [12:34:56] Showing 42 networks                             │
└─────────────────────────────────────────────────────────────┘
```

## Views

### 1. Networks View
Displays all networks in the current organization:
- Network name
- Network ID
- Product types (wireless, switch, appliance)
- Tags

### 2. Devices View
Shows all devices across networks:
- Device name
- Model
- Serial number
- Online/Offline status
- Network assignment

### 3. Clients View
Recent connected clients (last hour):
- Client description
- MAC address
- IP address
- SSID
- Network name

### 4. Alerts View
Recent network events and alerts:
- Event type
- Description
- Network
- Timestamp

### 5. Health View
Organization health summary:
- Total devices
- Online count
- Offline count
- Uptime percentage

## Configuration

The TUI uses the same `.env` configuration as the MCP servers:

```env
MERAKI_API_KEY="your_api_key"
MERAKI_ORG_ID="default_org_id"  # Optional: sets default org
```

## Organization-Specific Usage

When managing multiple organizations:

1. **Use the dropdown** - Select organization from the top dropdown
2. **Auto-discovery** - All accessible orgs are loaded automatically
3. **Default org** - Set `MERAKI_ORG_ID` in `.env` for startup default

## Performance Tips

- **Client view** is limited to first 5 networks and 20 clients each for speed
- **Alerts view** shows events from 3 most recent networks
- **Press `r`** to refresh data when needed
- **Use keyboard shortcuts** (`1-4`) for fastest navigation

## Examples

### Monitor Buffalo Wild Wings Locations

1. Launch TUI: `.\launch-tui.bat`
2. Select "Buffalo Wild Wings" from dropdown
3. Press `1` to view all store networks
4. Press `3` to see active clients
5. Press `4` to check recent alerts

### Check Health Across Arby's Stores

1. Switch to "Arby's" organization
2. Press `2` to view all devices
3. Check online/offline status
4. Press `5` for health summary

### Investigate Connectivity Issues

1. Press `3` for client view
2. Look for clients with issues
3. Press `4` for recent alerts
4. Cross-reference SSID and network

## Troubleshooting

**TUI won't start:**
```bash
# Ensure dependencies are installed
uv pip install textual python-dotenv meraki

# Check API key is set
echo %MERAKI_API_KEY%
```

**No organizations showing:**
- Verify API key has correct permissions
- Check `.env` file exists and is loaded
- Ensure API key hasn't expired

**Slow performance:**
- Reduce number of networks being queried
- Use organization-specific views
- Check network connectivity

**Terminal display issues:**
- Use Windows Terminal or modern terminal emulator
- Ensure terminal supports Unicode
- Try resizing terminal window

## Advanced Features

### Custom Views (Coming Soon)
- Filter devices by model
- Search clients by MAC/IP
- Export data to CSV
- Historical trend charts

### Multi-Org Comparison
- Side-by-side org metrics
- Cross-org device inventory
- Aggregated health scores

## Integration with MCP Servers

The TUI complements the MCP servers:

- **TUI**: Visual browsing and monitoring
- **MCP**: AI-powered queries and automation
- **Both**: Use same `.env` configuration

Use together:
```bash
# Monitor in TUI
launch-tui.bat

# Query via Copilot Chat
@Meraki_BuffaloWildWings Show me clients connected to SSID V850_Guest_SSID
```

## Keyboard Reference Card

```
┌─────────────────────────────────────┐
│ Meraki Magic TUI - Shortcuts       │
├─────────────────────────────────────┤
│ Navigation                          │
│   ↑ ↓  Scroll table rows           │
│   Tab  Switch widgets               │
│                                     │
│ Views                               │
│   1    Networks                     │
│   2    Devices                      │
│   3    Clients                      │
│   4    Alerts                       │
│                                     │
│ Actions                             │
│   r    Refresh view                 │
│   q    Quit application             │
└─────────────────────────────────────┘
```

## See Also

- [README.md](README.md) - Main project documentation
- [SCENARIOS.md](SCENARIOS.md) - Use case examples
- [ORG-EXAMPLES.md](ORG-EXAMPLES.md) - Organization-specific queries
- [Textual Documentation](https://textual.textualize.io/) - TUI framework docs
