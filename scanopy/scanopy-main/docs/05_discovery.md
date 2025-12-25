# Discovery

This guide explains how network discovery works in Scanopy and how to configure it.

## How Discovery Works

Scanopy uses daemons to perform network scans. Each daemon runs on a machine within a network and executes a series of discovery methods to identify hosts and services.

### Discovery Methods

*   **Ping Scan**: Sends ICMP echo requests to find live hosts.
*   **ARP Scan**: Scans the ARP table to find hosts on the local subnet.
*   **Port Scan**: Scans for open TCP ports to identify services running on hosts.
*   **Service Detection**: Probes open ports to identify the specific services running (e.g., distinguishing between a web server and a database).
*   **Docker Scan**: If a Docker socket is available, the daemon will query it to discover containerized services.

## Discovery Configuration

You can configure discovery settings for each network to control how scans are performed.

1.  Navigate to **Discover > Configuration**
2.  Select the network you want to configure

### Scan Targets

Specify the IP ranges you want to scan. You can enter:

*   Individual IP addresses (e.g., `192.168.1.1`)
*   CIDR ranges (e.g., `192.168.1.0/24`)
*   IP ranges (e.g., `192.168.1.100-200`)

### Port Scanning

*   **Top Ports**: Scans the most common 1,000 TCP ports. This is the default and recommended for most use cases.
*   **Full Scan**: Scans all 65,535 TCP ports. This is slower and more intensive.
*   **Custom**: Specify a custom list of ports to scan.

## Scheduled Discovery

Scanopy can run discovery scans on a schedule to keep your network documentation up-to-date.

1.  Navigate to **Discover > Scheduled**
2.  Find the Network Scan for your network and click **Edit**
3.  Enable the schedule and choose a frequency (e.g., daily, weekly).

## Running Scans Manually

You can trigger a scan at any time:

1.  Navigate to **Discover > Scheduled**
2.  Find the Network Scan for your network
3.  Click **Run**
