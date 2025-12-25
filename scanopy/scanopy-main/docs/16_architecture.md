# Architecture

Scanopy is composed of three main components that work together to discover and visualize your network.

![Scanopy Architecture Diagram](/docs/_astro/architecture.C-11111111.png)

## 1. Server

The server is the central component of Scanopy. It is responsible for:

*   Storing all network data in a PostgreSQL database
*   Serving the web UI
*   Providing an API for daemons and the UI
*   Managing user authentication and access control
*   Scheduling and coordinating discovery scans

The server is a Rust application built with the Axum framework.

## 2. Daemon

Daemons are lightweight agents that run on your networks and perform discovery scans. Their responsibilities include:

*   Scanning IP ranges to find live hosts
*   Port scanning hosts to identify open ports
*   Probing open ports to detect services
*   Querying the Docker socket to discover containers
*   Reporting all discovered data back to the server

Daemons are also Rust applications and are designed to be lightweight and run on a variety of platforms.

## 3. UI

The UI is a web-based interface that allows you to:

*   View your network topology
*   Manage hosts, subnets, and groups
*   Configure and run discovery scans
*   Manage users and organization settings

The UI is a single-page application built with Svelte and TypeScript.
