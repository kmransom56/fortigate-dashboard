# Hosts, Subnets & Groups

This guide covers how Scanopy handles network data, including hosts, subnets, and groups.

## Hosts

A host represents any device with an IP address on your network, such as servers, workstations, printers, and IoT devices. Hosts are discovered automatically during network scans.

### Host Details

Click on any host in the topology or host list (**Manage > Hosts**) to view its details, including:

*   **IP and MAC Addresses**
*   **Open Ports** and detected services
*   **Device Type**: The model or OS, if identified
*   **Subnet** and network location
*   **Discovery History**: When the host was first seen and last seen

### Editing Hosts

You can manually edit host information:

1.  Go to the host’s detail page
2.  Click the **Edit** button
3.  Change the name, device type, or assign it to a group

Manually assigned information is preserved and will not be overwritten by subsequent scans.

## Subnets

Scanopy automatically groups hosts into subnets based on their IP addresses. Subnets are used to organize the network topology and can be assigned friendly names for easier identification.

### Subnet Types

Scanopy assigns a type to each subnet based on its name or the name of the VLAN it belongs to. This helps categorize subnets and apply appropriate discovery settings. For example, a subnet named “Guest” will be treated as a guest network.

## Groups

Groups are custom collections of hosts that you can use to organize your network. For example, you could create groups for:

*   “Production Servers”
*   “IoT Devices”
*   “Marketing Department Workstations”

### Creating Groups

1.  Navigate to **Manage > Groups**
2.  Click **Create Group**
3.  Enter a name and click **Create**

### Assigning Hosts to Groups

You can assign a host to a group from the host’s detail page.
