#!/usr/bin/env python3
"""
Meraki Magic TUI - Interactive Dashboard with Chat
Browse organizations, networks, devices, and query via chat
"""
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

import meraki
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Static,
    DataTable,
    Button,
    Label,
    Input,
    Select,
    RichLog,
)
from textual.binding import Binding
from rich.text import Text
from rich.markdown import Markdown

# Import MCP client wrapper
from mcp_client import MerakiMCPWrapper

# Import reusable AI assistant framework
import sys
from pathlib import Path

reusable_path = Path(__file__).parent / "reusable"
if str(reusable_path) not in sys.path:
    sys.path.insert(0, str(reusable_path))

try:
    from reusable.simple_ai import (
        get_ai_assistant,
        audit_file,
        repair_code,
        optimize_code,
        learn_from_codebase,
    )
    from reusable.config import AIConfig
    from reusable.agent_framework_wrapper import AgentBackend

    AI_ASSISTANT_AVAILABLE = True
except ImportError as e:
    AI_ASSISTANT_AVAILABLE = False
    print(f"⚠️  AI Assistant not available: {e}")

# Load environment
load_dotenv()


class ChatPanel(VerticalScroll):
    """Chat interface for MCP server queries"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_log = []

    def compose(self) -> ComposeResult:
        yield RichLog(id="chat_messages", wrap=True, highlight=True)
        with Horizontal(id="chat_input_container"):
            yield Input(
                placeholder="Ask about your Meraki networks...", id="chat_input"
            )
            yield Button("Send", id="send_btn", variant="primary")

    def add_message(self, role: str, content: str):
        """Add message to chat log"""
        log = self.query_one("#chat_messages", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "user":
            log.write(Text(f"[{timestamp}] You: {content}", style="bold cyan"))
        elif role == "assistant":
            log.write(Text(f"[{timestamp}] Assistant:", style="bold green"))
            log.write(Markdown(content))
        elif role == "system":
            log.write(Text(f"[{timestamp}] System: {content}", style="yellow"))

        self.message_log.append(
            {"role": role, "content": content, "timestamp": timestamp}
        )


class MerakiDashboard(App):
    """Interactive Meraki Dashboard TUI with Chat"""

    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $primary;
        color: $text;
    }
    
    #org_selector {
        height: 4;
        background: $primary;
        padding: 1;
        border: solid $accent;
    }
    
    #org_selector Label {
        color: $text;
        text-style: bold;
        width: 15;
    }
    
    #org_select {
        width: 1fr;
        background: $surface;
    }
    
    #main_container {
        height: 1fr;
    }
    
    #sidebar {
        width: 30;
        background: $panel;
        padding: 1;
    }
    
    #content_area {
        width: 1fr;
    }
    
    #data_view {
        height: 60%;
        padding: 1;
    }
    
    #chat_panel {
        height: 40%;
        border-top: solid $primary;
        padding: 1;
    }
    
    #chat_messages {
        height: 1fr;
        background: $surface-darken-1;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    #chat_input_container {
        height: 3;
    }
    
    #chat_input {
        width: 1fr;
    }
    
    #send_btn {
        width: 10;
        margin-left: 1;
    }
    
    .button {
        margin: 1 0;
    }
    
    DataTable {
        height: 100%;
    }
    
    #status_bar {
        height: 3;
        background: $panel;
        padding: 1;
        color: $text-muted;
    }
    
    #org_info {
        margin-top: 2;
        padding: 1;
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("o", "focus_org_selector", "Org Selector"),
        Binding("1", "show_networks", "Networks"),
        Binding("2", "show_devices", "Devices"),
        Binding("3", "show_clients", "Clients"),
        Binding("4", "show_alerts", "Alerts"),
        Binding("ctrl+c", "focus_chat", "Chat"),
        Binding("escape", "focus_table", "Table"),
    ]

    TITLE = "Meraki Magic Dashboard + Chat"
    SUB_TITLE = "Multi-Organization Network Management with AI Assistant"

    def __init__(self, use_mcp: bool = True, use_ai: bool = True):
        super().__init__()
        # Use MCP wrapper instead of direct API
        # This allows TUI to use MCP tools and integrate with AI tools
        self.meraki_api = MerakiMCPWrapper(use_mcp=use_mcp)
        self.use_mcp = use_mcp

        # Initialize AI assistant if available
        self.use_ai = use_ai and AI_ASSISTANT_AVAILABLE
        self.ai_assistant = None
        if self.use_ai:
            try:
                self.ai_assistant = get_ai_assistant(
                    app_name="meraki_magic_mcp", auto_setup=False
                )
            except Exception as e:
                print(f"⚠️  Could not initialize AI assistant: {e}")
                self.use_ai = False

        self.organizations = []
        self.current_org = None
        self.current_view = "networks"
        self.cached_networks = {}
        self.cached_devices = {}
    
    def _extract_data_from_mcp_response(self, response_data: Any) -> List[Dict]:
        """
        Extract data from MCP response, handling both normal and truncated formats.
        
        Args:
            response_data: Response from MCP (can be str, dict, or list)
            
        Returns:
            List of data items
        """
        # Handle JSON string response from MCP
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError:
                return []
        
        # Handle truncated response format from MCP
        if isinstance(response_data, dict):
            if response_data.get("_response_truncated"):
                # Extract preview data or load from cache
                preview = response_data.get("_preview", [])
                if preview and isinstance(preview, list):
                    data = preview
                    # Try to load full data from cache file
                    cache_file = response_data.get("_full_response_cached")
                    if cache_file and os.path.exists(cache_file):
                        try:
                            with open(cache_file, 'r') as f:
                                cached = json.load(f)
                                full_data = cached.get('data', [])
                                if isinstance(full_data, list) and len(full_data) > 0:
                                    data = full_data
                        except Exception:
                            pass  # Use preview if cache load fails
                    return data
                else:
                    return []
            elif "error" in response_data:
                # Return empty list for errors - caller should handle status message
                return []
            else:
                return []
        elif isinstance(response_data, list):
            return response_data
        else:
            return []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        # Organization selector
        with Container(id="org_selector"):
            yield Label("Organization (Press 'o' to focus):")
            yield Select([("Loading...", "")], id="org_select")

        # Main container
        with Horizontal(id="main_container"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Button("📊 Networks", id="btn_networks", classes="button")
                yield Button("💻 Devices", id="btn_devices", classes="button")
                yield Button("👥 Clients", id="btn_clients", classes="button")
                yield Button("⚠️ Alerts", id="btn_alerts", classes="button")
                yield Button("💚 Health", id="btn_health", classes="button")
                yield Static("", id="org_info")

            # Content area (data + chat)
            with Vertical(id="content_area"):
                # Data view
                with Container(id="data_view"):
                    yield DataTable(id="data_table")

                # Chat panel
                yield ChatPanel(id="chat_panel")

        # Status bar
        with Container(id="status_bar"):
            yield Static("Loading organizations...", id="status_text")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize dashboard on startup"""
        chat = self.query_one("#chat_panel", ChatPanel)
        mcp_status = (
            "✅ MCP Integration Enabled" if self.use_mcp else "⚠️ Direct API Mode"
        )
        ai_status = (
            "✅ AI Assistant Available"
            if self.use_ai
            else "⚠️ AI Assistant Not Available"
        )
        chat.add_message(
            "system",
            f"🚀 Meraki Magic Dashboard initialized!\n"
            f"{mcp_status}\n"
            f"{ai_status}\n\n"
            f"Ask me anything about your networks, or use AI commands:\n"
            f"• 'audit [file]' - Audit code/configuration\n"
            f"• 'repair [issue]' - Get repair suggestions\n"
            f"• 'optimize [file]' - Get optimization suggestions\n"
            f"• 'learn [topic]' - Learn from codebase\n"
            f"Type 'help' for all commands.",
        )
        await self.load_organizations()

    async def load_organizations(self) -> None:
        """Load all accessible organizations"""
        try:
            # Use MCP wrapper instead of direct API
            orgs_data = self.meraki_api.get_organizations()
            # Handle JSON string response from MCP
            if isinstance(orgs_data, str):
                orgs_data = json.loads(orgs_data)
            self.organizations = orgs_data if isinstance(orgs_data, list) else []

            # Set default org
            default_org_id = os.getenv("MERAKI_ORG_ID")
            if default_org_id:
                self.current_org = next(
                    (o for o in self.organizations if o["id"] == default_org_id),
                    self.organizations[0],
                )
            else:
                self.current_org = self.organizations[0] if self.organizations else None

            # Update UI
            if self.current_org:
                await self.update_org_selector()
                await self.show_networks()
                self.update_org_info()

            org_count = len(self.organizations)
            self.update_status(
                f"✅ Loaded {org_count} organization{'s' if org_count != 1 else ''} - Press 'o' to switch"
            )

            chat = self.query_one("#chat_panel", ChatPanel)
            org_list = "\n".join(
                [
                    f"{i+1}. {org['name']} ({org['id']})"
                    for i, org in enumerate(self.organizations)
                ]
            )
            chat.add_message(
                "assistant",
                f"**Available Organizations ({org_count}):**\n{org_list}\n\n"
                f"Currently viewing: **{self.current_org['name']}**\n"
                f"💡 Press 'o' to focus organization selector, or use dropdown above",
            )

        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    def update_org_info(self) -> None:
        """Update organization info panel"""
        if not self.current_org:
            return

        # Find current org index
        org_index = next(
            (
                i
                for i, org in enumerate(self.organizations)
                if org["id"] == self.current_org["id"]
            ),
            -1,
        )
        org_number = org_index + 1 if org_index >= 0 else "?"
        total_orgs = len(self.organizations)

        info = self.query_one("#org_info", Static)
        info.update(
            f"""
[b]Current Organization:[/b]
{self.current_org['name']}

[b]Organization {org_number} of {total_orgs}[/b]
ID: {self.current_org['id']}

[b]Quick Commands:[/b]
• Press 'o' to switch orgs
• Press 1-4 for views
• Ctrl+C for chat
• Type 'switch to [name]'
        """
        )

    async def update_org_selector(self) -> None:
        """Update organization dropdown"""
        select = self.query_one("#org_select", Select)
        select.set_options(
            [(f"{org['name']}", org["id"]) for org in self.organizations]
        )
        if self.current_org:
            select.value = self.current_org["id"]

    def update_status(self, message: str, error: bool = False) -> None:
        """Update status bar"""
        status = self.query_one("#status_text", Static)
        timestamp = datetime.now().strftime("%H:%M:%S")
        status.update(f"[{timestamp}] {message}")
        if error:
            status.styles.color = "red"
        else:
            status.styles.color = "white"

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle organization selection change"""
        if event.select.id == "org_select":
            org_id = event.value
            self.current_org = next(
                (o for o in self.organizations if o["id"] == org_id), None
            )
            self.update_org_info()
            await self.refresh_current_view()

            chat = self.query_one("#chat_panel", ChatPanel)
            chat.add_message(
                "system", f"Switched to organization: {self.current_org['name']}"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "send_btn":
            await self.handle_chat_input()
            return

        button_actions = {
            "btn_networks": self.show_networks,
            "btn_devices": self.show_devices,
            "btn_clients": self.show_clients,
            "btn_alerts": self.show_alerts,
            "btn_health": self.show_health,
        }

        action = button_actions.get(event.button.id)
        if action:
            await action()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle chat input submission"""
        if event.input.id == "chat_input":
            await self.handle_chat_input()

    async def handle_chat_input(self) -> None:
        """Process chat input"""
        chat_input = self.query_one("#chat_input", Input)
        message = chat_input.value.strip()

        if not message:
            return

        # Clear input
        chat_input.value = ""

        # Add user message to chat
        chat = self.query_one("#chat_panel", ChatPanel)
        chat.add_message("user", message)

        # Process message
        await self.process_chat_message(message)

    async def process_chat_message(self, message: str) -> None:
        """Process and respond to chat message"""
        chat = self.query_one("#chat_panel", ChatPanel)
        message_lower = message.lower()

        try:
            # Command: show networks
            if "show networks" in message_lower or "list networks" in message_lower:
                await self.show_networks()
                networks = self.cached_networks.get(self.current_org["id"], [])
                response = f"**Showing {len(networks)} networks in {self.current_org['name']}:**\n\n"
                for net in networks[:10]:
                    response += f"- {net['name']} ({net['id']})\n"
                if len(networks) > 10:
                    response += f"\n_...and {len(networks) - 10} more_"
                chat.add_message("assistant", response)

            # Command: show devices
            elif "show devices" in message_lower or "list devices" in message_lower:
                await self.show_devices()
                devices = self.cached_devices.get(self.current_org["id"], [])
                online = sum(1 for d in devices if d.get("status") == "online")
                response = f"**Device Summary for {self.current_org['name']}:**\n\n"
                response += f"- Total: {len(devices)}\n"
                response += f"- Online: 🟢 {online}\n"
                response += f"- Offline: 🔴 {len(devices) - online}\n"
                chat.add_message("assistant", response)

            # Command: clients on SSID or count clients on SSID
            elif ("clients" in message_lower and "ssid" in message_lower) or \
                 ("how many" in message_lower and "clients" in message_lower and ("guest" in message_lower or "wifi" in message_lower or "wi-fi" in message_lower)):
                # Extract SSID name - try multiple patterns
                ssid_name = None
                
                # Pattern 1: Quoted SSID name
                if '"' in message:
                    parts = message.split('"')
                    if len(parts) >= 2:
                        ssid_name = parts[1]
                # Pattern 2: "Guest Wifi" or "Guest WiFi" or "Guest_WiFi"
                elif "guest" in message_lower:
                    # Look for common Guest SSID patterns
                    guest_patterns = ["guest wifi", "guest_wifi", "guest wi-fi", "guest-wifi", "guestwifi"]
                    for pattern in guest_patterns:
                        if pattern in message_lower:
                            # Try to extract the exact SSID name
                            idx = message_lower.find(pattern)
                            # Get surrounding text
                            words = message.split()
                            for i, word in enumerate(words):
                                if "guest" in word.lower():
                                    # Check if next word might be part of SSID
                                    if i + 1 < len(words):
                                        potential_ssid = f"{word}_{words[i+1]}"
                                    else:
                                        potential_ssid = word
                                    # Try common variations
                                    ssid_candidates = [
                                        "Guest_WiFi", "Guest WiFi", "Guest-WiFi", 
                                        "Guest_Wifi", "Guest Wifi", "Guest-Wifi",
                                        "guest_wifi", "guest wifi", "guest-wifi"
                                    ]
                                    # Use the first candidate for now, will search all networks
                                    ssid_name = "Guest"
                                    break
                            if ssid_name:
                                break
                
                # If still no SSID name, try to infer from context
                if not ssid_name and "guest" in message_lower:
                    ssid_name = "Guest"  # Will search for SSIDs containing "Guest"
                
                if ssid_name or "guest" in message_lower:
                    await self._handle_ssid_client_query(chat, ssid_name or "Guest", "how many" in message_lower)
                else:
                    chat.add_message(
                        "assistant",
                        "Please specify SSID name, e.g., \"How many clients on Guest WiFi\" or \"Show clients on SSID 'Guest_WiFi'\"",
                    )

            # Command: health
            elif "health" in message_lower or "status" in message_lower:
                await self.show_health()
                chat.add_message("assistant", "**Health metrics displayed above.** ✅")

            # Command: switch org
            elif "switch to" in message_lower or "change to" in message_lower:
                for org in self.organizations:
                    if org["name"].lower() in message_lower:
                        self.current_org = org
                        select = self.query_one("#org_select", Select)
                        select.value = org["id"]
                        self.update_org_info()
                        await self.refresh_current_view()
                        chat.add_message(
                            "assistant", f"✅ Switched to **{org['name']}**"
                        )
                        return
                chat.add_message(
                    "assistant",
                    "❌ Organization not found. Available orgs:\n"
                    + "\n".join([f"- {org['name']}" for org in self.organizations]),
                )

            # Command: help
            elif "help" in message_lower or message_lower == "?":
                help_text = """
**Available Commands:**

**Data Views:**
- `show networks` - Display all networks
- `show devices` - Display all devices
- `show clients` - Display connected clients
- `show health` - Display health metrics

**Meraki Queries:**
- `show clients on SSID "Guest_WiFi"` - Filter by SSID
- `switch to Buffalo Wild Wings` - Change organization

**AI Assistant Commands:**"""
                if self.use_ai:
                    help_text += """
- `audit [file]` - Audit code/configuration for issues
- `audit [file] security` - Security audit
- `repair [issue] [file]` - Get repair suggestions
- `optimize [file]` - Get optimization suggestions
- `learn [topic]` - Learn from codebase"""
                else:
                    help_text += (
                        "\n⚠️ AI Assistant not available (install reusable components)"
                    )

                help_text += """

**Keyboard Shortcuts:**
- `1-4` - Quick view switch
- `Ctrl+C` - Focus chat
- `Escape` - Focus table
- `R` - Refresh view

Try asking: "Show me devices in Buffalo Wild Wings" or "List all networks"
                """
                chat.add_message("assistant", help_text)

            # Try AI assistant commands
            elif self.use_ai and self.ai_assistant:
                # Check for AI commands
                if message_lower.startswith("audit "):
                    await self.handle_ai_audit(message, chat)
                elif message_lower.startswith("repair "):
                    await self.handle_ai_repair(message, chat)
                elif message_lower.startswith("optimize "):
                    await self.handle_ai_optimize(message, chat)
                elif message_lower.startswith("learn "):
                    await self.handle_ai_learn(message, chat)
                else:
                    # Try MCP generic API call or AI natural language query
                    await self.try_ai_or_mcp_query(message, chat)

            # Try MCP generic API caller for unknown commands
            else:
                # Attempt to parse as MCP API call
                await self.try_mcp_api_call(message, chat)

        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def handle_ai_audit(self, message: str, chat) -> None:
        """Handle AI audit command"""
        try:
            parts = message.split(" ", 2)
            if len(parts) < 2:
                chat.add_message(
                    "assistant",
                    "Usage: `audit [file] [type]`\nTypes: code, security, performance, config, dependencies",
                )
                return

            file_path = parts[1]
            audit_type = parts[2] if len(parts) > 2 else "code"

            chat.add_message("assistant", f"🔍 Auditing {file_path} ({audit_type})...")

            result = audit_file(file_path, audit_type)

            if "error" in result:
                chat.add_message("assistant", f"❌ Error: {result['error']}")
            else:
                findings = result.get("findings", "No findings")
                recommendations = result.get("recommendations", [])

                response = f"**Audit Results for {file_path}:**\n\n{findings}"
                if recommendations:
                    response += "\n\n**Recommendations:**\n"
                    for rec in recommendations[:5]:  # Limit to 5
                        response += f"- {rec}\n"

                chat.add_message("assistant", response)
        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def handle_ai_repair(self, message: str, chat) -> None:
        """Handle AI repair command"""
        try:
            parts = message.split(" ", 2)
            if len(parts) < 2:
                chat.add_message(
                    "assistant", "Usage: `repair [issue description] [file]`"
                )
                return

            issue = parts[1]
            file_path = parts[2] if len(parts) > 2 else None

            chat.add_message("assistant", f"🔧 Analyzing repair for: {issue}...")

            result = repair_code(issue, file_path)

            if "error" in result:
                chat.add_message("assistant", f"❌ Error: {result['error']}")
            else:
                fix = result.get("fix", "No fix provided")
                response = f"**Repair Analysis:**\n\n{fix}"

                if result.get("suggested_changes"):
                    response += "\n\n**Suggested Changes:**\n"
                    for lang, code in list(result["suggested_changes"].items())[
                        :2
                    ]:  # Limit
                        response += f"\n```{lang}\n{code[:300]}...\n```"

                chat.add_message("assistant", response)
        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def handle_ai_optimize(self, message: str, chat) -> None:
        """Handle AI optimize command"""
        try:
            parts = message.split(" ", 2)
            if len(parts) < 2:
                chat.add_message(
                    "assistant",
                    "Usage: `optimize [file] [type]`\nTypes: performance, memory, code_quality",
                )
                return

            file_path = parts[1]
            opt_type = parts[2] if len(parts) > 2 else "performance"

            chat.add_message("assistant", f"⚡ Optimizing {file_path} ({opt_type})...")

            result = optimize_code(file_path, opt_type)

            if "error" in result:
                chat.add_message("assistant", f"❌ Error: {result['error']}")
            else:
                recommendations = result.get("recommendations", "No recommendations")
                chat.add_message(
                    "assistant",
                    f"**Optimization Recommendations:**\n\n{recommendations}",
                )
        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def handle_ai_learn(self, message: str, chat) -> None:
        """Handle AI learn command"""
        try:
            parts = message.split(" ", 1)
            if len(parts) < 2:
                chat.add_message(
                    "assistant", "Usage: `learn [topic]` or `learn [source] [topic]`"
                )
                return

            source_or_topic = parts[1]
            # Simple: if it looks like a path, it's a source, otherwise it's a topic
            if "/" in source_or_topic or source_or_topic.startswith("."):
                source = source_or_topic
                topic = None
            else:
                source = "."
                topic = source_or_topic

            chat.add_message(
                "assistant", f"📚 Learning about: {topic or 'codebase'}..."
            )

            result = learn_from_codebase(source, topic)

            if "error" in result:
                chat.add_message("assistant", f"❌ Error: {result['error']}")
            else:
                summary = result.get("summary", "Learning completed")
                chat.add_message("assistant", f"**Learning Summary:**\n\n{summary}")
        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def try_ai_or_mcp_query(self, message: str, chat) -> None:
        """Try AI natural language query or MCP API call"""
        try:
            # First try AI assistant for natural language
            if self.use_ai and self.ai_assistant:
                try:
                    # Use AI to understand the query
                    response = self.ai_assistant.agent.chat(
                        f"User is asking about Meraki networks: {message}\n"
                        f"Current org: {self.current_org['name'] if self.current_org else 'None'}\n"
                        f"Available data: {len(self.organizations)} orgs, "
                        f"{len(self.cached_networks.get(self.current_org['id'], []))} networks cached.\n"
                        f"Provide a helpful response or suggest MCP commands.",
                        system_prompt="You are a Meraki network assistant. Help users understand their networks.",
                    )
                    chat.add_message("assistant", f"**AI Response:**\n\n{response}")
                    return
                except Exception as e:
                    # AI failed, try MCP
                    pass

            # Fallback to MCP API call
            await self.try_mcp_api_call(message, chat)
        except Exception as e:
            chat.add_message("assistant", f"❌ Error: {str(e)}")

    async def try_mcp_api_call(self, message: str, chat) -> None:
        """Try to interpret message as MCP API call"""
        try:
            # Simple pattern matching for common queries
            message_lower = message.lower()

            # Try to extract section and method from natural language
            if "firewall" in message_lower and "rule" in message_lower:
                # Try to get firewall rules
                if self.current_org and self.cached_networks.get(
                    self.current_org["id"]
                ):
                    networks = self.cached_networks[self.current_org["id"]]
                    if networks:
                        # Get firewall rules for first network
                        result = self.meraki_api.call_meraki_api(
                            section="appliance",
                            method="getNetworkApplianceFirewallL3FirewallRules",
                            parameters={"networkId": networks[0]["id"]},
                        )
                        if isinstance(result, str):
                            result = json.loads(result)
                        chat.add_message(
                            "assistant",
                            f"**Firewall Rules:**\n```json\n{json.dumps(result, indent=2)[:500]}...\n```",
                        )
                        return

            # Generic fallback - show help
            chat.add_message(
                "assistant",
                f"🤔 I'm not sure how to handle: _{message}_\n\n"
                "**Available Commands:**\n"
                "- `show networks` - Display all networks\n"
                "- `show devices` - Display all devices\n"
                "- `show clients` - Display connected clients\n"
                "- `show health` - Display health metrics\n"
                "- `switch to [org name]` - Change organization\n\n"
                "**MCP Integration:** The TUI can use MCP tools for advanced queries.\n"
                "Type **help** for more commands.",
            )
        except Exception as e:
            chat.add_message("assistant", f"❌ Error processing MCP call: {str(e)}")

    async def show_networks(self) -> None:
        """Display networks for current org"""
        if not self.current_org:
            self.update_status("❌ No organization selected", error=True)
            return

        self.current_view = "networks"
        self.update_status(f"📡 Loading networks for {self.current_org['name']}...")

        try:
            # Use MCP wrapper
            networks_data = self.meraki_api.get_organization_networks(
                self.current_org["id"]
            )
            # Handle JSON string response from MCP
            if isinstance(networks_data, str):
                networks_data = json.loads(networks_data)
            
            # Handle truncated response format from MCP
            if isinstance(networks_data, dict):
                if networks_data.get("_response_truncated"):
                    # Extract preview data or load from cache
                    preview = networks_data.get("_preview", [])
                    if preview and isinstance(preview, list):
                        networks = preview
                        # Try to load full data from cache file
                        cache_file = networks_data.get("_full_response_cached")
                        if cache_file and os.path.exists(cache_file):
                            try:
                                with open(cache_file, 'r') as f:
                                    cached = json.load(f)
                                    full_data = cached.get('data', [])
                                    if isinstance(full_data, list) and len(full_data) > 0:
                                        networks = full_data
                            except Exception:
                                pass  # Use preview if cache load fails
                    else:
                        networks = []
                elif "error" in networks_data:
                    self.update_status(f"❌ Error: {networks_data.get('error')}", error=True)
                    return
                else:
                    networks = []
            elif isinstance(networks_data, list):
                networks = networks_data
            else:
                networks = []
            
            self.cached_networks[self.current_org["id"]] = networks

            table = self.query_one("#data_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "ID", "Products", "Tags")

            for net in networks:
                table.add_row(
                    net.get("name", "N/A"),
                    net.get("id", "N/A")[:20] + "...",
                    ", ".join(net.get("productTypes", [])),
                    ", ".join(net.get("tags", [])) if net.get("tags") else "None",
                )

            self.update_status(f"✅ Showing {len(networks)} networks")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    async def show_devices(self) -> None:
        """Display devices for current org"""
        if not self.current_org:
            self.update_status("❌ No organization selected", error=True)
            return

        self.current_view = "devices"
        self.update_status(f"💻 Loading devices for {self.current_org['name']}...")

        try:
            # Use MCP wrapper
            devices_data = self.meraki_api.get_organization_devices(
                self.current_org["id"]
            )
            # Handle JSON string response from MCP
            if isinstance(devices_data, str):
                devices_data = json.loads(devices_data)
            
            # Handle truncated response format from MCP
            if isinstance(devices_data, dict):
                if devices_data.get("_response_truncated"):
                    # Extract preview data or load from cache
                    preview = devices_data.get("_preview", [])
                    if preview and isinstance(preview, list):
                        devices = preview
                        # Try to load full data from cache file
                        cache_file = devices_data.get("_full_response_cached")
                        if cache_file and os.path.exists(cache_file):
                            try:
                                with open(cache_file, 'r') as f:
                                    cached = json.load(f)
                                    full_data = cached.get('data', [])
                                    if isinstance(full_data, list) and len(full_data) > 0:
                                        devices = full_data
                            except Exception:
                                pass  # Use preview if cache load fails
                    else:
                        devices = []
                elif "error" in devices_data:
                    self.update_status(f"❌ Error: {devices_data.get('error')}", error=True)
                    return
                else:
                    devices = []
            elif isinstance(devices_data, list):
                devices = devices_data
            else:
                devices = []
            
            self.cached_devices[self.current_org["id"]] = devices

            table = self.query_one("#data_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "Model", "Serial", "Status", "Network")

            for device in devices:
                table.add_row(
                    device.get("name", "N/A"),
                    device.get("model", "N/A"),
                    device.get("serial", "N/A"),
                    "🟢 Online" if device.get("status") == "online" else "🔴 Offline",
                    (
                        (device.get("networkId", "N/A")[:15] + "...")
                        if device.get("networkId")
                        else "N/A"
                    ),
                )

            self.update_status(f"✅ Showing {len(devices)} devices")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    async def show_clients(self) -> None:
        """Display clients for current org"""
        if not self.current_org:
            self.update_status("❌ No organization selected", error=True)
            return

        self.current_view = "clients"
        self.update_status(f"👥 Loading clients...")

        try:
            networks = self.cached_networks.get(self.current_org["id"])
            if not networks:
                networks_data = self.meraki_api.get_organization_networks(
                    self.current_org["id"]
                )
                if isinstance(networks_data, str):
                    networks_data = json.loads(networks_data)
                
                # Handle truncated response format from MCP
                if isinstance(networks_data, dict):
                    if networks_data.get("_response_truncated"):
                        preview = networks_data.get("_preview", [])
                        if preview and isinstance(preview, list):
                            networks = preview
                            # Try to load full data from cache file
                            cache_file = networks_data.get("_full_response_cached")
                            if cache_file and os.path.exists(cache_file):
                                try:
                                    with open(cache_file, 'r') as f:
                                        cached = json.load(f)
                                        full_data = cached.get('data', [])
                                        if isinstance(full_data, list) and len(full_data) > 0:
                                            networks = full_data
                                except Exception:
                                    pass  # Use preview if cache load fails
                        else:
                            networks = []
                    else:
                        networks = []
                elif isinstance(networks_data, list):
                    networks = networks_data
                else:
                    networks = []

            table = self.query_one("#data_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Description", "MAC", "IP", "SSID", "Network")

            total_clients = 0
            for net in networks[:5]:
                try:
                    # Use MCP wrapper
                    clients_data = self.meraki_api.get_network_clients(
                        net["id"], timespan=3600
                    )
                    if isinstance(clients_data, str):
                        clients_data = json.loads(clients_data)
                    
                    # Handle truncated response format from MCP
                    if isinstance(clients_data, dict):
                        if clients_data.get("_response_truncated"):
                            preview = clients_data.get("_preview", [])
                            if preview and isinstance(preview, list):
                                clients = preview
                                # Try to load full data from cache file
                                cache_file = clients_data.get("_full_response_cached")
                                if cache_file and os.path.exists(cache_file):
                                    try:
                                        with open(cache_file, 'r') as f:
                                            cached = json.load(f)
                                            full_data = cached.get('data', [])
                                            if isinstance(full_data, list) and len(full_data) > 0:
                                                clients = full_data
                                    except Exception:
                                        pass  # Use preview if cache load fails
                            else:
                                clients = []
                        else:
                            clients = []
                    elif isinstance(clients_data, list):
                        clients = clients_data
                    else:
                        clients = []
                    for client in clients[:20]:
                        table.add_row(
                            client.get("description", "Unknown")[:30],
                            client.get("mac", "N/A"),
                            client.get("ip", "N/A"),
                            client.get("ssid", "N/A"),
                            net.get("name", "N/A")[:20],
                        )
                        total_clients += 1
                except Exception as e:
                    # Continue with next network if this one fails
                    continue

            self.update_status(f"✅ Showing {total_clients} recent clients")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    async def show_alerts(self) -> None:
        """Display alerts"""
        if not self.current_org:
            self.update_status("❌ No organization selected", error=True)
            return

        self.current_view = "alerts"
        self.update_status(f"⚠️ Loading alerts...")

        try:
            networks = self.cached_networks.get(self.current_org["id"])
            if not networks:
                networks_data = self.meraki_api.get_organization_networks(
                    self.current_org["id"]
                )
                if isinstance(networks_data, str):
                    networks_data = json.loads(networks_data)
                
                # Handle truncated response format from MCP
                if isinstance(networks_data, dict):
                    if networks_data.get("_response_truncated"):
                        preview = networks_data.get("_preview", [])
                        if preview and isinstance(preview, list):
                            networks = preview
                            # Try to load full data from cache file
                            cache_file = networks_data.get("_full_response_cached")
                            if cache_file and os.path.exists(cache_file):
                                try:
                                    with open(cache_file, 'r') as f:
                                        cached = json.load(f)
                                        full_data = cached.get('data', [])
                                        if isinstance(full_data, list) and len(full_data) > 0:
                                            networks = full_data
                                except Exception:
                                    pass  # Use preview if cache load fails
                        else:
                            networks = []
                    else:
                        networks = []
                elif isinstance(networks_data, list):
                    networks = networks_data
                else:
                    networks = []

            table = self.query_one("#data_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Type", "Description", "Network", "Time")

            for net in networks[:3]:
                try:
                    # Use MCP wrapper
                    events_data = self.meraki_api.get_network_events(
                        net["id"], per_page=10
                    )
                    if isinstance(events_data, str):
                        events_data = json.loads(events_data)
                    events = (
                        events_data.get("events", [])
                        if isinstance(events_data, dict)
                        else (events_data if isinstance(events_data, list) else [])
                    )
                    for event in events:
                        table.add_row(
                            event.get("eventType", "N/A")[:20],
                            event.get("description", "N/A")[:50],
                            net.get("name", "N/A")[:20],
                            event.get("occurredAt", "N/A")[-8:],
                        )
                except Exception as e:
                    # Continue with next network if this one fails
                    continue

            self.update_status("✅ Showing recent events")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    async def show_health(self) -> None:
        """Display health metrics"""
        if not self.current_org:
            self.update_status("❌ No organization selected", error=True)
            return

        self.current_view = "health"
        self.update_status("💚 Loading health metrics...")

        try:
            devices = self.cached_devices.get(self.current_org["id"])
            if not devices:
                devices_data = self.meraki_api.get_organization_devices(
                    self.current_org["id"]
                )
                if isinstance(devices_data, str):
                    devices_data = json.loads(devices_data)
                
                # Handle truncated response format from MCP
                if isinstance(devices_data, dict):
                    if devices_data.get("_response_truncated"):
                        preview = devices_data.get("_preview", [])
                        if preview and isinstance(preview, list):
                            devices = preview
                            # Try to load full data from cache file
                            cache_file = devices_data.get("_full_response_cached")
                            if cache_file and os.path.exists(cache_file):
                                try:
                                    with open(cache_file, 'r') as f:
                                        cached = json.load(f)
                                        full_data = cached.get('data', [])
                                        if isinstance(full_data, list) and len(full_data) > 0:
                                            devices = full_data
                                except Exception:
                                    pass  # Use preview if cache load fails
                        else:
                            devices = []
                    else:
                        devices = []
                elif isinstance(devices_data, list):
                    devices = devices_data
                else:
                    devices = []

            online = sum(1 for d in devices if d.get("status") == "online")
            offline = len(devices) - online

            table = self.query_one("#data_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Metric", "Value")

            table.add_row("Total Devices", str(len(devices)))
            table.add_row("Online", f"🟢 {online}")
            table.add_row("Offline", f"🔴 {offline}")
            table.add_row(
                "Uptime %", f"{(online/len(devices)*100):.1f}%" if devices else "N/A"
            )

            self.update_status("✅ Health summary")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", error=True)

    async def refresh_current_view(self) -> None:
        """Refresh current view"""
        view_actions = {
            "networks": self.show_networks,
            "devices": self.show_devices,
            "clients": self.show_clients,
            "alerts": self.show_alerts,
            "health": self.show_health,
        }

        action = view_actions.get(self.current_view)
        if action:
            await action()

    def action_refresh(self) -> None:
        """Refresh current view"""
        self.run_async(self.refresh_current_view())

    def action_show_networks(self) -> None:
        """Show networks view"""
        self.run_async(self.show_networks())

    def action_show_devices(self) -> None:
        """Show devices view"""
        self.run_async(self.show_devices())

    def action_show_clients(self) -> None:
        """Show clients view"""
        self.run_async(self.show_clients())

    def action_show_alerts(self) -> None:
        """Show alerts view"""
        self.run_async(self.show_alerts())

    def action_focus_chat(self) -> None:
        """Focus chat input"""
        chat_input = self.query_one("#chat_input", Input)
        chat_input.focus()

    def action_focus_table(self) -> None:
        """Focus data table"""
        table = self.query_one("#data_table", DataTable)
        table.focus()

    def action_focus_org_selector(self) -> None:
        """Focus organization selector"""
        select = self.query_one("#org_select", Select)
        select.focus()
        self.update_status(
            "💡 Use arrow keys to navigate, Enter to select organization"
        )
    
    async def _handle_ssid_client_query(self, chat, ssid_pattern: str, count_only: bool = False) -> None:
        """
        Handle queries about clients on a specific SSID.
        
        Args:
            chat: ChatPanel instance
            ssid_pattern: SSID name or pattern to search for
            count_only: If True, only return count; if False, show details
        """
        try:
            self.update_status(f"🔍 Searching for clients on SSID: {ssid_pattern}...")
            
            # Get networks for current org
            networks = self.cached_networks.get(self.current_org["id"])
            if not networks:
                networks_data = self.meraki_api.get_organization_networks(
                    self.current_org["id"]
                )
                networks = self._extract_data_from_mcp_response(networks_data)
                self.cached_networks[self.current_org["id"]] = networks
            
            if not networks:
                chat.add_message("assistant", "❌ No networks found in this organization.")
                return
            
            # Search for SSIDs matching the pattern (case-insensitive)
            matching_ssids = []
            total_clients = 0
            clients_by_network = {}
            
            # First, get SSIDs from networks
            for net in networks[:10]:  # Limit to first 10 networks for performance
                try:
                    # Get wireless SSIDs for this network
                    try:
                        ssids_data = self.meraki_api.call_meraki_api(
                            section="wireless",
                            method="getNetworkWirelessSsids",
                            parameters={"networkId": net["id"]}
                        )
                        ssids = self._extract_data_from_mcp_response(ssids_data)
                    except Exception:
                        # If wireless API fails, try to get SSIDs from clients
                        ssids = []
                    
                    # Find matching SSIDs
                    for ssid in ssids:
                        ssid_name = ssid.get("name", "")
                        if ssid_pattern.lower() in ssid_name.lower() or ssid_name.lower() in ssid_pattern.lower():
                            matching_ssids.append({
                                "network": net["name"],
                                "network_id": net["id"],
                                "ssid_name": ssid_name,
                                "ssid_number": ssid.get("number", 0)
                            })
                except Exception as e:
                    continue  # Skip networks that fail
            
            # If no SSIDs found via API, try searching clients directly
            if not matching_ssids:
                # Fallback: search all clients for matching SSID pattern
                for net in networks[:5]:  # Limit to 5 networks for performance
                    try:
                        clients_data = self.meraki_api.get_network_clients(
                            net["id"], timespan=3600
                        )
                        clients = self._extract_data_from_mcp_response(clients_data)
                        
                        # Filter clients by SSID containing the pattern
                        matching_clients = [
                            c for c in clients 
                            if ssid_pattern.lower() in c.get("ssid", "").lower()
                        ]
                        
                        if matching_clients:
                            client_count = len(matching_clients)
                            total_clients += client_count
                            # Get unique SSID names
                            ssid_names = list(set([c.get("ssid", "Unknown") for c in matching_clients if c.get("ssid")]))
                            clients_by_network[net["name"]] = {
                                "ssid": ", ".join(ssid_names) if ssid_names else "Unknown",
                                "count": client_count,
                                "clients": matching_clients
                            }
                    except Exception:
                        continue
                
                # If still no results, return error
                if not clients_by_network:
                    chat.add_message(
                        "assistant",
                        f"❌ No clients found on SSIDs matching '{ssid_pattern}'. Try checking the network names or use 'show networks' to see available networks."
                    )
                    return
            
            # Get clients for each matching SSID
            for ssid_info in matching_ssids:
                try:
                    clients_data = self.meraki_api.get_network_clients(
                        ssid_info["network_id"], timespan=3600
                    )
                    clients = self._extract_data_from_mcp_response(clients_data)
                    
                    # Filter clients by SSID (case-insensitive partial match)
                    ssid_clients = [
                        c for c in clients 
                        if ssid_info["ssid_name"].lower() in c.get("ssid", "").lower() or
                           c.get("ssid", "").lower() in ssid_info["ssid_name"].lower()
                    ]
                    
                    client_count = len(ssid_clients)
                    total_clients += client_count
                    clients_by_network[ssid_info["network"]] = {
                        "ssid": ssid_info["ssid_name"],
                        "count": client_count,
                        "clients": ssid_clients
                    }
                except Exception as e:
                    continue
            
            # Build response
            if count_only:
                response = f"**Clients on '{ssid_pattern}' SSID:**\n\n"
                response += f"**Total: {total_clients} clients**\n\n"
                if clients_by_network:
                    response += "**By Network:**\n"
                    for net_name, info in clients_by_network.items():
                        response += f"- {net_name} ({info['ssid']}): {info['count']} clients\n"
            else:
                response = f"**Clients on '{ssid_pattern}' SSID:**\n\n"
                response += f"**Total: {total_clients} clients** across {len(matching_ssids)} SSID(s)\n\n"
                
                if clients_by_network:
                    response += "**Details by Network:**\n"
                    for net_name, info in list(clients_by_network.items())[:5]:  # Limit to 5 networks
                        response += f"\n**{net_name}** ({info['ssid']}): {info['count']} clients\n"
                        if info['clients']:
                            for client in info['clients'][:5]:  # Show first 5 clients
                                response += f"  - {client.get('description', 'Unknown')} ({client.get('mac', 'N/A')})\n"
                            if len(info['clients']) > 5:
                                response += f"  ... and {len(info['clients']) - 5} more\n"
                
                # Also update the table view
                await self.show_clients()
            
            chat.add_message("assistant", response)
            self.update_status(f"✅ Found {total_clients} clients on '{ssid_pattern}' SSID")
            
        except Exception as e:
            import traceback
            chat.add_message("assistant", f"❌ Error searching for clients: {str(e)}")
            self.update_status(f"❌ Error: {str(e)}", error=True)


def main():
    """Run the TUI application"""
    import sys

    # Check if MCP should be disabled
    use_mcp = "--no-mcp" not in sys.argv
    # Check if AI should be disabled
    use_ai = "--no-ai" not in sys.argv
    app = MerakiDashboard(use_mcp=use_mcp, use_ai=use_ai)
    app.run()


if __name__ == "__main__":
    main()
