# Introduction to Scanopy

Scanopy is a network discovery and visualization tool that automatically discovers hosts, services, and network topology across your infrastructure.

## Key Features

*   **Network Discovery**: Automatically finds hosts and services on your network.
*   **Service Detection**: Identifies over 200 services, such as databases, web servers, and home automation systems.
*   **Topology Visualization**: Provides interactive network maps with filtering and grouping capabilities.
*   **Distributed Scanning**: Allows deployment of daemons across multiple networks.
*   **Docker Integration**: Discovers containers via Docker socket.

## Deployment Models

Scanopy is available in two deployment models:

*   **Scanopy Cloud**: A managed service where Scanopy handles the server infrastructure, offering quick setup and automatic updates. Users only need to deploy daemons to their networks.
*   **Self-Hosted**: Provides full control, data sovereignty, and customization options by running everything on your own infrastructure. Self-hosted users need to install the Scanopy server before deploying daemons.

## How Scanopy Works

1.  **Daemons** run on your networks and perform discovery scans.
2.  The **Server** stores data and serves the web UI.
3.  The **UI** provides visualization, management, and configuration.

## Next Steps

*   **Cloud users**: Continue to the Quick Start guide.
*   **Self-hosted users**: Start with Server Installation, then return to the Quick Start guide.
