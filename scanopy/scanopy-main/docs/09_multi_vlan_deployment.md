# Multi-VLAN Deployment

To scan multiple VLANs, you need to deploy a daemon in each VLAN. This guide explains how to set this up.

## Why a Daemon Per VLAN?

Scanopy’s discovery methods, such as ARP scans, are most effective when run from within the same Layer 2 network. Deploying a daemon in each VLAN ensures that all hosts are discovered accurately.

## Setup Overview

1.  **Create a Network in Scanopy for Each VLAN**: For each VLAN you want to scan, create a corresponding network in the Scanopy UI (**Settings > Networks**).
2.  **Deploy a Daemon in Each VLAN**: For each network you create, you will get a unique daemon token. Use this token to install a daemon in the corresponding VLAN.

## Example Scenario

You have three VLANs:

*   VLAN 10: Servers (192.168.10.0/24)
*   VLAN 20: Workstations (192.168.20.0/24)
*   VLAN 30: IoT Devices (192.168.30.0/24)

### Step 1: Create Networks in Scanopy

In the Scanopy UI, create three networks:

*   “Servers”
*   “Workstations”
*   “IoT”

You will get a unique daemon token for each of these networks.

### Step 2: Deploy Daemons

*   On a machine in VLAN 10, install a daemon using the token for the “Servers” network.
*   On a machine in VLAN 20, install a daemon using the token for the “Workstations” network.
*   On a machine in VLAN 30, install a daemon using the token for the “IoT” network.

Once all daemons are running, they will begin scanning their respective VLANs and sending data back to your Scanopy server.
