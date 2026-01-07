# Use Copilot CLI with MCP

**User:**   
**Created:**   
**Updated:**   
**Exported:** 10/31/2025 18:21:30  
**Link:** [https://chatgpt.com/share/6905361b-c674-800e-bc34-342ef3389b34](https://chatgpt.com/share/6905361b-c674-800e-bc34-342ef3389b34)  

## Prompt:
How to use copilot cli with mcp servers

## Response:
Casual answer 👇

You can use **Copilot CLI (`gh copilot`)** with **MCP (Model Context Protocol) servers** by registering your MCP servers in your local config, then running Copilot commands that can call those tools automatically.

* * *

✅ **1) Install the Copilot CLI**
--------------------------------

```bash
gh extension install github/gh-copilot
```

Test:

```bash
gh copilot
```

* * *

✅ **2) MCP config file**
------------------------

Copilot loads MCP servers from:

**Linux/Mac**

```
~/.config/mcp/servers.json
```

**Windows**

```
%APPDATA%\mcp\servers.json
```

Example:

```json
{
  "servers": {
    "example-mcp": {
      "command": "example-mcp-server",
      "args": []
    }
  }
}
```

You can define multiple servers.

* * *

✅ **3) Use an MCP server**
--------------------------

If your MCP server is local, you just point to its command.

Example MCP server:

```bash
npx @modelcontextprotocol/server-filesystem
```

Config:

```json
{
  "servers": {
    "fs": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"]
    }
  }
}
```

* * *

✅ **4) Run Copilot CLI using MCP**
----------------------------------

In a directory with MCP servers configured:

Ask Copilot to use tools:

```bash
gh copilot ask "List files in this folder"
```

If `server-filesystem` is registered, Copilot can call that tool to read directory listings.

If multiple MCP endpoints have tools, Copilot will pick from all.

* * *

✅ **5) Debug which MCP servers are loaded**
-------------------------------------------

```bash
gh copilot config view
```

* * *

✅ **6) Test MCP server alone (optional)**
-----------------------------------------

Useful to confirm your server speaks MCP:

```bash
npx @modelcontextprotocol/cli --server "your_mcp server command" ask "hello"
```

* * *

✅ Example: Python MCP server
----------------------------

`my_server.py`

```python
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("test-server")

@tool()
def say_hello(name: str):
    return f"Hello {name}"

mcp.run()
```

Add config:

```json
{
  "servers": {
    "test": {
      "command": "python",
      "args": ["my_server.py"]
    }
  }
}
```

Use:

```bash
gh copilot ask "Call say_hello('Keith')"
```

* * *

✅ Notes
-------

✔ Copilot shell only discovers tools defined in the MCP server  
✔ You can register multiple servers  
✔ Copilot _automatically_ surfaces MCP tools to the LLM  
✔ No need to call tools manually — the LLM chooses

* * *

Quick mental model
------------------

| Item | Meaning |
| --- | --- |
| MCP server | Provides tools/actions |
| Copilot CLI | Sends prompts & calls MCP tools |
| servers.json | Registers MCP servers |
| LLM | Decides when to call which tool |

So basically:

> You register MCP → Copilot discovers tools → You prompt → LLM optionally uses tools.

* * *

If you want, I can send:  
✅ Full example with filesystem + http + db tools  
✅ Starter `servers.json` template  
✅ Debug troubleshooting steps

Just say the word 👌

## Prompt:
Yes send full example. I use github, sequential thinking playwright deepview filesystem  mcp servers

## Response:
Thought for 26s

Awesome — here’s a **copy-paste full example** wiring Copilot CLI to these MCP servers: **GitHub**, **Sequential Thinking**, **Playwright**, **DeepView**, and **Filesystem**.

* * *

0) Prereqs
==========

```bash
# Copilot CLI
gh extension install github/gh-copilot

# Login (if needed)
gh auth login
```

Copilot CLI already ships with the **GitHub MCP server** enabled. [docs.github.com+1](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli?utm_source=chatgpt.com)

* * *

1) Install the MCP servers
==========================

> You can run these locally via `npx` so Copilot invokes them by command.

```bash
# Filesystem
npm i -g @modelcontextprotocol/server-filesystem
# Playwright (official)
npm i -g @playwright/mcp
# OR an alt Playwright MCP if you prefer:
# npm i -g @executeautomation/playwright-mcp-server

# Sequential Thinking
npm i -g @modelcontextprotocol/server-sequential-thinking

# DeepView (from source)
git clone https://github.com/ai-1st/deepview-mcp.git
cd deepview-mcp && npm i && npm run build
# (keep repo path handy for config)
```

Refs: filesystem, playwright, sequential thinking, deepview. [Glama – MCP Hosting Platform+5npm+5npm+5](https://www.npmjs.com/package/%40modelcontextprotocol/server-filesystem/v/2025.1.14?utm_source=chatgpt.com)

* * *

2) Register servers with Copilot CLI
====================================

In **Copilot CLI**, run the slash command and fill prompts:

```text
gh copilot
/mcp add
```

Then add each server:

**Filesystem**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@modelcontextprotocol/server-filesystem`
*   Env (optional): `ROOT={/path/you/want}`

**Playwright**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@playwright/mcp`

**Sequential Thinking**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@modelcontextprotocol/server-sequential-thinking`

**DeepView**

*   Type: `stdio`
*   Command: `node`
*   Args: `/abs/path/to/deepview-mcp/dist/index.js`
*   Env (example): `GOOGLE_API_KEY=...` (DeepView commonly uses Gemini)

Copilot CLI supports adding servers via `/mcp add`. [docs.github.com](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli?utm_source=chatgpt.com)

* * *

3) Alternative: workspace JSON (check into repo)
================================================

If you prefer file-based config (works nicely across VS Code/JetBrains too), create **`.vscode/mcp.json`** in your repo:

```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp"
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "env": { "ROOT": "." }
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp"]
    },
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sequential-thinking"]
    },
    "deepview": {
      "type": "stdio",
      "command": "node",
      "args": ["/ABS/PATH/deepview-mcp/dist/index.js"],
      "env": {
        "GOOGLE_API_KEY": "${env:GOOGLE_API_KEY}"
      }
    }
  }
}
```

*   VS Code and Copilot clients recognize `mcp.json`/`.vscode/mcp.json`; enterprises can also govern access via policy. [Visual Studio Code+1](https://code.visualstudio.com/docs/copilot/customization/mcp-servers?utm_source=chatgpt.com)

* * *

4) Quick tests you can run
==========================

```bash
# List what Copilot CLI sees
gh copilot /mcp list

# GitHub repo ops (uses built-in GitHub MCP)
gh copilot ask "List my open PRs in this repo and summarize risks"
# Filesystem
gh copilot ask "Enumerate ./scripts and read the first 40 lines of each file"
# Sequential Thinking
gh copilot ask "Create a step-by-step plan to migrate FortiManager exports to a PyQt6 GUI tool"
# Playwright (headless browser tasks)
gh copilot ask "Open https://docs.fortinet.com and screenshot the landing page"
# DeepView (codebase analysis)
gh copilot ask "Given this repo, produce a dependency map and identify hotspots to refactor"
```

* * *

5) Troubleshooting tips
=======================

*   **Not loading?** Re-run `/mcp add` and confirm each server **starts via stdio** without extra prompts. [docs.github.com](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli?utm_source=chatgpt.com)
*   **Where to configure by file?** Use workspace `.vscode/mcp.json` or user settings; VS Code docs show both patterns (the CLI honors the standard MCP config). [Visual Studio Code+1](https://code.visualstudio.com/docs/copilot/customization/mcp-servers?utm_source=chatgpt.com)
*   **Playwright errors?** Ensure Playwright browsers are installed: `npx playwright install`.
*   **Security**: Only install **trusted** MCP servers; there have been real-world malicious MCPs on npm. Pin versions, review source, and rotate tokens if you ever suspect compromise. [IT Pro](https://www.itpro.com/security/a-malicious-mcp-server-is-silently-stealing-user-emails?utm_source=chatgpt.com)

* * *

6) Minimal env template
=======================

```bash
# ~/.bashrc (example)
export GOOGLE_API_KEY="YOUR_GEMINI_KEY"
# anything else DeepView or other servers require
```

* * *

If you want, I’ll tailor commands to your repos (Arby’s/BWW/Sonic) and add **ready-made prompts** for:

*   Sequential Thinking → migration runbooks
*   Playwright → FortiGate/portal checks & screenshots
*   Filesystem → export/ingest workflows
*   GitHub → PR autoplan + labeler via MCP tools

Just say “generate the repo-specific prompts.”

## Prompt:
generate the repo-specific prompts

## Response:
Thought for 10s

Got you. Here are **ready-to-paste Copilot CLI prompts** for your three brand repos using **GitHub + Sequential Thinking + Playwright + DeepView + Filesystem** MCP. Replace `<owner>/<repo>` and paths as needed.

* * *

Arby’s — `Arbys-Stores` (FMG: `10.128.144.132`)
-----------------------------------------------

```bash
# GitHub – PR autoplan & risk
gh copilot ask -R <owner>/<arbys-repo> "Scan open PRs. For each: summarize scope, risky files, missing tests, and breaking changes. Propose labels & merge checklist. Output a table."

# DeepView – dependency & hotspot map
gh copilot ask -R <owner>/<arbys-repo> "Build a dependency graph (modules → imports). Flag top 10 hotspots by churn/complexity. Suggest refactors with effort estimates."

# Sequential Thinking – release plan
gh copilot ask -R <owner>/<arbys-repo> "Create a step-by-step release runbook for Arbys-Stores (ADOM='Arbys-Stores'). Include: config export, policy diff, URL-filter audit, rollback plan, and validation tests."

# Filesystem – exports inventory
gh copilot ask "List ./exports/arbys/**/*.json and summarize counts per type (policies, addrs, services). If missing, create a TODO.md with exact export commands."

# Playwright – portal smoke (ignore cert)
gh copilot ask "Use Playwright to open https://10.128.144.132, ignore TLS errors, wait for login form, screenshot to ./screens/arbys/login.png, then capture console errors to ./screens/arbys/console.txt."
```

* * *

Buffalo Wild Wings — `BWW_Stores` (FMG: `10.128.145.4`)
-------------------------------------------------------

```bash
# GitHub – PR review focus on FortiManager APIs
gh copilot ask -R <owner>/<bww-repo> "Review PRs touching FortiManager API calls. Verify pagination, timeouts, auth, and ADOM selection (BWW_Stores). List fixes & code snippets."

# DeepView – coupling report
gh copilot ask -R <owner>/<bww-repo> "Report modules with high bidirectional coupling. Suggest boundary seams and interface adapters for API clients & UI."

# Sequential Thinking – migration checklist
gh copilot ask -R <owner>/<bww-repo> "Produce a pre-flight migration checklist for BWW_Stores: backups, ADOM lock strategy, change window, smoke tests, and rollback triggers."

# Filesystem – artifact QC
gh copilot ask "Audit ./exports/bww/ for stale files (>14d). Output a CSV with path,size,mtime,sha256 to ./reports/bww_export_inventory.csv."

# Playwright – docs capture
gh copilot ask "Use Playwright to visit https://docs.fortinet.com (public), search 'FortiManager automation API', open first result, PDF it to ./screens/bww/fmg_api_overview.pdf."
```

* * *

Sonic — `SonicStores` (FMG: `10.128.156.36`)
--------------------------------------------

```bash
# GitHub – changelog & version bump
gh copilot ask -R <owner>/<sonic-repo> "Generate a Keep-a-Changelog entry since last tag. Propose next semver, PR titles to squash, and release notes."

# DeepView – test coverage targets
gh copilot ask -R <owner>/<sonic-repo> "Identify low-coverage modules that guard policy edits or device inventory. Propose 5 high-value tests with example cases."

# Sequential Thinking – PyQt6 GUI plan
gh copilot ask -R <owner>/<sonic-repo> "Draft a stepwise plan to ship the PyQt6 GUI (dark theme) with tabs: Services, URL Filters, Interfaces, Connected Devices, and 'Run All Brands'. Include packaging (.exe/.app)."

# Filesystem – brand merge prep
gh copilot ask "Compare ./exports/sonic vs ./exports/arbys and ./exports/bww. Produce a diff summary (adds/changes/deletes) and write ./reports/sonic_merge_plan.md."

# Playwright – internal portal shots
gh copilot ask "With Playwright, open https://10.128.156.36 (ignore TLS), take full-page screenshots of dashboard, policy, and objects pages to ./screens/sonic/{dashboard,policy,objects}.png."
```

* * *

Cross-brand (Run-All)
---------------------

```bash
# Sequential Thinking – orchestration
gh copilot ask "Plan a Run-All pipeline: for brands [Arbys-Stores,BWW_Stores,SonicStores] → export configs, validate schemas, run diffs, generate PDFs, and bundle artifacts per brand."

# Filesystem – bundle artifacts
gh copilot ask "Create ./dist/{arbys,bww,sonic} and move {screens,reports,exports} per brand into each folder. Then zip to ./dist/{arbys,bww,sonic}.zip with manifest.json."

# GitHub – multi-repo status
gh copilot ask "Across repos <owner>/{<arbys-repo>,<bww-repo>,<sonic-repo>}, list blockers for next release, owners, and ETA. Output a single Markdown dashboard."
```

* * *

Optional guardrails
-------------------

```bash
# Security sweep (any repo)
gh copilot ask -R <owner>/<repo> "Scan for hardcoded tokens, insecure HTTP, weak TLS flags, and broad firewall rules. Open issues with titles, severity, and fix PR stubs."
```

Want me to **fill in your actual repo names** and drop these into a `prompts.md` in each repo?

## Prompt:
you had given commands and install for gh copilot cli but I want to install https://github.com/github/copilot-cli?locale=en-US/

## Response:
Great — here’s how to install **GitHub Copilot CLI** (the official one at github.com/github/copilot-cli):

* * *

### ✅ Prerequisites

*   You must have a valid GitHub CLI (`gh`) installed. [docs.github.com+3thelazyadministrator.com+3docs.github.com+3](https://www.thelazyadministrator.com/2024/03/22/getting-started-with-github-copilot-in-the-cli/?utm_source=chatgpt.com)
*   You must have a subscription to GitHub Copilot (Individual / Business / Enterprise) and your organization must permit CLI usage. [docs.github.com+1](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli?utm_source=chatgpt.com)
*   Node.js v22+ (because some features rely on Node) and npm v10+. [docs.github.com](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli?utm_source=chatgpt.com)

* * *

### 🛠 Installation Steps

1.  **Install GitHub CLI** (if not already):
    *   On macOS: `brew install gh`
    *   On Ubuntu/Debian: follow instructions at GitHub CLI site. [thelazyadministrator.com+1](https://www.thelazyadministrator.com/2024/03/22/getting-started-with-github-copilot-in-the-cli/?utm_source=chatgpt.com)
2.  **Authenticate with GitHub**:
    ```bash
    gh auth login
    ```
    Follow browser/device code flow. [thelazyadministrator.com](https://www.thelazyadministrator.com/2024/03/22/getting-started-with-github-copilot-in-the-cli/?utm_source=chatgpt.com)
3.  **Install the Copilot CLI**:
    ```bash
    npm install -g @github/copilot
    ```
    (This is the official package as per GitHub docs.) [docs.github.com+1](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli?utm_source=chatgpt.com)
    Alternatively (older/preview version) you might see:
    ```bash
    gh extension install github/gh-copilot
    ```
    [DEV Community+1](https://dev.to/github/stop-struggling-with-terminal-commands-github-copilot-in-the-cli-is-here-to-help-4pnb?utm_source=chatgpt.com)
4.  **Verify installation**:
    ```bash
    gh copilot --help
    ```
    You should see commands like `suggest`, `explain`, `config`. [thelazyadministrator.com+1](https://www.thelazyadministrator.com/2024/03/22/getting-started-with-github-copilot-in-the-cli/?utm_source=chatgpt.com)

* * *

### 🔧 Set up aliases (optional but useful)

So you can type shorter commands like `ghcs` or `gce`:

If you’re using `bash` or `zsh`, add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias gce='gh copilot explain'
alias gcs='gh copilot suggest'
```

Then `source ~/.zshrc` (or your shell file). [DEV Community+1](https://dev.to/github/stop-struggling-with-terminal-commands-github-copilot-in-the-cli-is-here-to-help-4pnb?utm_source=chatgpt.com)

* * *

### ✅ Quick usage examples

```bash
gh copilot suggest "list all files >100MB in current folder" -t shell
gh copilot explain "what does git rebase --onto do?"
```

[DEV Community](https://dev.to/github/stop-struggling-with-terminal-commands-github-copilot-in-the-cli-is-here-to-help-4pnb?utm_source=chatgpt.com)

* * *

If you like, I can tailor **installation steps for Ubuntu (your environment)** including Node setup, environment variables, and alias config for your shell.

## Prompt:
tailor installation steps for Ubuntu (your environment) including Node setup, environment variables, and alias config for your shell to include copy-paste full example wiring Copilot CLI to these MCP servers: GitHub, Sequential Thinking, Playwright, DeepView, and Filesystem

## Response:
Thought for 15s

Got it. Here’s a tight, copy-paste Ubuntu setup that installs the **official GitHub Copilot CLI**, sets up **Node**, adds handy **aliases/env**, and wires **MCP servers**: GitHub (built-in), Sequential Thinking, Playwright, DeepView, and Filesystem.

* * *

1) System prep (Ubuntu)
=======================

```bash
# Update base
sudo apt update && sudo apt install -y build-essential curl git ca-certificates

# Install GitHub CLI
type -p gh >/dev/null || (type -p apt-add-repository >/dev/null || sudo apt install -y software-properties-common; \
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
  sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
  https://cli.github.com/packages stable main" | \
  sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
  sudo apt update && sudo apt install -y gh)

# Login to GitHub
gh auth login
```

Docs: Copilot CLI overview & install. [GitHub Docs+1](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli?utm_source=chatgpt.com)

* * *

2) Node.js (via nvm) + Copilot CLI
==================================

```bash
# Install nvm
export NVM_DIR="$HOME/.nvm"
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
. "$NVM_DIR/nvm.sh"

# Install LTS Node and use it
nvm install --lts
nvm use --lts

# Install Copilot CLI (official)
npm i -g @github/copilot

# Sanity check
gh copilot --help
```

Copilot CLI npm package (official). [npm](https://npmjs.com/package/%40github/copilot?utm_source=chatgpt.com)

* * *

3) Shell aliases + env (bash/zsh)
=================================

```bash
# Append to ~/.bashrc (or ~/.zshrc) — then: source ~/.bashrc
cat <<'EOF' >> ~/.bashrc
# --- GitHub Copilot CLI quality-of-life ---
alias gce='gh copilot explain'
alias gcs='gh copilot suggest'
alias gca='gh copilot ask'

# MCP-related env (examples; set your real values)
export GOOGLE_API_KEY=""     # used by some analysis servers (e.g., DeepView variants)
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright
EOF
source ~/.bashrc
```

* * *

4) Install MCP servers
======================

> Copilot CLI already has the **GitHub MCP** configured; we’ll add the rest. Use `npm -g` so the commands are on PATH. Then install Playwright browsers. [GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli?utm_source=chatgpt.com)

```bash
# Filesystem (official)
npm i -g @modelcontextprotocol/server-filesystem

# Sequential Thinking (official)
npm i -g @modelcontextprotocol/server-sequential-thinking

# Playwright MCP (official)
npm i -g @playwright/mcp
npx playwright install  # installs browser binaries

# DeepView (example: from source—adjust path if you use a different repo)
git clone https://github.com/ai-1st/deepview-mcp.git ~/deepview-mcp
cd ~/deepview-mcp && npm i && npm run build && cd -
```

Packages & references. [npm+2npm+2](https://www.npmjs.com/package/%40modelcontextprotocol/server-filesystem?activeTab=dependencies&utm_source=chatgpt.com)

* * *

5) Register MCP servers in Copilot CLI
======================================

> Use the **built-in slash flow** to add each server (transport stdio). [GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli?utm_source=chatgpt.com)

```bash
gh copilot
# then type:
# /mcp add
```

Add these entries (repeat `/mcp add` per server):

**Filesystem**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@modelcontextprotocol/server-filesystem`

**Sequential Thinking**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@modelcontextprotocol/server-sequential-thinking`

**Playwright**

*   Type: `stdio`
*   Command: `npx`
*   Args: `@playwright/mcp`

**DeepView**

*   Type: `stdio`
*   Command: `node`
*   Args: `/home/$USER/deepview-mcp/dist/index.js`
*   Env (optional): `GOOGLE_API_KEY=<your-key>`

(You can also use a JSON config if you prefer—see GitHub docs on MCP config.) [GitHub Docs](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-mcp?utm_source=chatgpt.com)

* * *

6) Quick smoke tests (copy-paste)
=================================

```bash
# List which MCP servers Copilot CLI sees
gh copilot /mcp list

# GitHub MCP (built-in): repo PR summary
gca -R <owner>/<repo> "List open PRs with risk, missing tests, and a merge checklist."

# Filesystem: enumerate & read
gca "List *.py in ./scripts and show first 30 lines of each."

# Sequential Thinking: plan
gca "Create a step-by-step runbook to export FortiManager configs for Arbys-Stores, BWW_Stores, SonicStores; then diff and package."

# Playwright: screenshot site (ignoring TLS for intranet)
gca "Use Playwright to open https://10.128.144.132, ignore TLS errors, screenshot to ./screens/arbys/login.png."

# DeepView: dependency map (run in a repo dir)
gca "Build a dependency graph for this repo and highlight top 10 refactor hotspots."
```

* * *

7) Optional workspace config (checked into repo)
================================================

If you’d rather keep MCP wiring in-repo (handy for team consistency), create `.vscode/mcp.json` like:

```json
{
  "servers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"]
    },
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sequential-thinking"]
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp"]
    },
    "deepview": {
      "type": "stdio",
      "command": "node",
      "args": ["/home/youruser/deepview-mcp/dist/index.js"],
      "env": { "GOOGLE_API_KEY": "${env:GOOGLE_API_KEY}" }
    }
  }
}
```

(General MCP config format + VS Code guidance.) [GitHub Docs+1](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-mcp?utm_source=chatgpt.com)

* * *

That’s it
---------

Want me to drop a **ready-made `bootstrap.sh`** that does all of this in one go (with idempotent checks) and a `prompts.md` for your Arby’s/BWW/Sonic repos?



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)