# Limitations

This page outlines the current limitations of Scanopy.

## Discovery

*   **UDP Port Scanning**: UDP scanning is significantly slower and less reliable than TCP scanning. Scanopy’s UDP scanning is limited to a small number of common ports.
*   **IPv6 Support**: Scanopy does not currently support IPv6 scanning.
*   **OS Detection**: Operating system detection is based on a limited set of fingerprints and may not always be accurate.

## Topology

*   **Layer 2 Topology**: Scanopy does not currently perform Layer 2 topology mapping (e.g., discovering which switch ports devices are connected to). The topology view is primarily a Layer 3 visualization.
*   **Large Networks**: The topology view may become slow or difficult to navigate with very large networks (thousands of hosts).

## Service Detection

*   **Encrypted Services**: Services running on TLS/SSL-encrypted ports are difficult to identify, as Scanopy cannot inspect the traffic. Detection is limited to matching the port number.
*   **Authentication**: Services that require authentication may not be detected if the authentication prompt prevents Scanopy from accessing service-identifying information.
