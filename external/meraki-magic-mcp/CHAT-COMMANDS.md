# Meraki Magic TUI - Chat Commands Reference

## Quick Start

```bash
# Launch the dashboard
.\launch-tui.bat

# Or run directly
python meraki_tui.py
```

## Chat Interface Features

The integrated chat allows natural language queries about your Meraki networks:

### Navigation Commands

**Focus Controls:**
- `Ctrl+C` - Focus chat input (type your question)
- `Escape` - Focus data table (navigate with arrows)
- `1-4` - Quick view shortcuts
- `R` - Refresh current view

### Chat Commands

**View Data:**
```
show networks
list networks
show devices
list devices
show clients
show health
status
```

**Query Specific Data:**
```
show clients on SSID "Guest_WiFi"
show clients on SSID "V850_Guest_SSID"
clients connected to "Corporate_WiFi"
```

**Switch Organizations:**
```
switch to Buffalo Wild Wings
change to Baskin Robbins
switch to Arby's
```

**Get Help:**
```
help
?
```

## Example Chat Session

```
You: show networks
Assistant: **Showing 42 networks in Buffalo Wild Wings:**
- Store-01 (N_xxxxx)
- Store-02 (N_yyyyy)
...and 32 more

You: show clients on SSID "V850_Guest_SSID"
Assistant: 🔍 Searching for clients connected to SSID: V850_Guest_SSID
Check the table above for results.

You: switch to Baskin Robbins
Assistant: ✅ Switched to Baskin Robbins

You: show health
Assistant: **Health metrics displayed above.** ✅
```

## Interface Layout

```
┌─ Meraki Magic Dashboard + Chat ─────────────────────────────┐
│ Organization: [Buffalo Wild Wings ▼]                        │
├────────────┬─────────────────────────────────────────────────┤
│ 📊 Networks│  DATA TABLE (60%)                              │
│ 💻 Devices │  ┌─────────────────────────────────────────┐  │
│ 👥 Clients │  │ Network Name │ ID    │ Products │ Tags │  │
│ ⚠️ Alerts  │  │ Store-01     │ N_xxx │ wireless │      │  │
│ 💚 Health  │  │ Store-02     │ N_yyy │ switch   │      │  │
│            │  └─────────────────────────────────────────┘  │
│ Org Info   │                                                │
│            │  CHAT PANEL (40%)                              │
│            │  ┌─────────────────────────────────────────┐  │
│            │  │ [12:45] You: show networks              │  │
│            │  │ [12:45] Assistant: Showing 42 networks  │  │
│            │  │                                         │  │
│            │  └─────────────────────────────────────────┘  │
│            │  [Ask about your networks...] [Send]          │
├────────────┴─────────────────────────────────────────────────┤
│ [12:45:30] ✅ Showing 42 networks                           │
└──────────────────────────────────────────────────────────────┘
```

## Chat Features

### Smart Context Awareness
- Chat knows which organization you're viewing
- Results update the data table automatically
- Message history persists during session

### Natural Language Processing
The chat understands various phrasings:
- "show me the networks"
- "list all devices"
- "what clients are connected?"
- "switch to BWW"
- "give me health status"

### Visual Feedback
- ✅ Success messages
- ❌ Error messages
- 🔍 Search indicators
- 🟢 Online status
- 🔴 Offline status
- ⚠️ Alert indicators

## Advanced Usage

### Combining Chat + Keyboard

1. Press `1` to show networks (keyboard shortcut)
2. Press `Ctrl+C` to focus chat
3. Type: "show clients on SSID 'Guest_WiFi'"
4. Press `Enter` to execute
5. View results in table above
6. Press `Escape` to navigate table with arrows

### Multi-Step Queries

```bash
# Step 1: Switch organization
You: switch to Buffalo Wild Wings

# Step 2: View devices
You: show devices

# Step 3: Check health
You: show health

# Step 4: View specific clients
You: show clients on SSID "V850_Guest_SSID"
```

## Tips & Tricks

### Performance
- Use chat commands for quick queries
- Use keyboard shortcuts (1-4) for instant view switching
- Chat caches data for faster responses
- Press `R` to force refresh

### Navigation
- `Tab` cycles through widgets
- Arrow keys navigate tables
- `Ctrl+C` jumps to chat anytime
- `Escape` returns to table

### Organization Switching
```bash
# Full names work:
switch to Buffalo Wild Wings

# Partial names work:
switch to BWW
change to Baskin

# Case insensitive:
SWITCH TO ARBYS
```

## Troubleshooting

**Chat not responding:**
- Ensure you pressed `Ctrl+C` to focus chat
- Check input field is highlighted
- Press `Enter` or click `Send` button

**Commands not working:**
- Type `help` for available commands
- Check organization is selected
- Verify API key in `.env` file

**Display issues:**
- Resize terminal window (minimum 120x40)
- Use Windows Terminal for best experience
- Try `Ctrl+L` to refresh screen

## Coming Soon

- Voice commands
- Export chat history
- Save favorite queries
- AI-powered insights
- Real-time notifications
- Multi-org comparison mode

## Keyboard Reference

| Key | Action |
|-----|--------|
| `Ctrl+C` | Focus chat |
| `Escape` | Focus table |
| `Enter` | Send chat message |
| `1` | Show networks |
| `2` | Show devices |
| `3` | Show clients |
| `4` | Show alerts |
| `R` | Refresh view |
| `Q` | Quit app |
| `Tab` | Next widget |
| `↑↓` | Navigate table |

## See Also

- [TUI-README.md](TUI-README.md) - Full TUI documentation
- [ORG-EXAMPLES.md](ORG-EXAMPLES.md) - Organization queries
- [SCENARIOS.md](SCENARIOS.md) - Use case examples
