# Quick Start

This guide walks you through your first network discovery with Scanopy.

## Cloud Users

### Step 1: Start Onboarding

Go to [scanopy.net](https://scanopy.net) and click **Get Started**.

1.  Select your use case (Homelab, Company, or MSP)
2.  Enter your organization name and first network name

### Step 2: Set Up Your Daemon

Before creating your account, you’ll configure a daemon for your network.

Choose **Install Now** to get installation commands, or **Install Later** to skip. See [Installing a Daemon](/docs/daemons/installing-daemon/) for detailed platform-specific instructions.

### Step 3: Create Your Account

Complete registration with your email and password. Your daemon will automatically connect and begin scanning once your account is created.

### Step 4: View Your Network

Once discovery completes (typically 5-10 minutes per /24 subnet):

1.  **Topology** — See your network diagram
2.  **Manage > Hosts** — View discovered devices
3.  **Manage > Services** — See detected services

---

## Self-Hosted Users

### Prerequisites

A running Scanopy server. See [Server Installation](/docs/self-hosted/server-installation/).

### Step 1: Complete Onboarding

Access your server URL and complete the onboarding wizard:

1.  Select your use case
2.  Enter your organization name and first network name
3.  Create your account

### Step 2: Run Discovery

If you deployed with Docker Compose, the **integrated daemon** is already running and connected to your first network.

1.  Navigate to **Discover > Scheduled**
2.  Find the Network Scan discovery for your network
3.  Click **Run** to start your first scan

Discovery typically takes 5-10 minutes per /24 subnet (256 IP addresses).

### Step 3: View Your Network

Once discovery completes:

1.  **Topology** — See your network diagram
2.  **Manage > Hosts** — View discovered devices
3.  **Manage > Services** — See detected services

### Adding More Daemons

To scan additional networks or VLANs, deploy additional daemons. See [Multi-VLAN Deployment](/docs/daemons/multi-vlan/).

---

## Next Steps

*   [Discovery](/docs/using-scanopy/discovery/) — Configure scheduled scans
*   [Topology](/docs/using-scanopy/topology/) — Customize your network visualization
*   [Hosts, Subnets & Groups](/docs/using-scanopy/network-data/) — Organize your network data
