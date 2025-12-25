# Organization & Access

This guide explains how to manage organizations, networks, and user access in Scanopy.

## Organizations

An organization is the top-level container in Scanopy. It holds all your networks, hosts, and other data. When you first sign up, an organization is created for you.

*   **Cloud users** have one organization per account.
*   **Self-hosted users** can create multiple organizations to manage different environments (e.g., “Production” and “Staging”).

### Creating Organizations (Self-Hosted)

1.  Navigate to **Settings > Organizations**
2.  Click **Create Organization**
3.  Enter a name and click **Create**

## Networks

A network represents a distinct network segment, like a VLAN, a physical location, or a cloud environment. Each network is assigned a daemon to perform discovery scans.

### Creating Networks

1.  Navigate to **Settings > Networks**
2.  Click **Create Network**
3.  Enter a name and (optionally) select a parent network if it’s a sub-network of an existing one.
4.  Click **Create**

Once created, you’ll be prompted to create a daemon for the network. See [Installing a Daemon](/docs/daemons/installing-daemon/).

## User Access Management

Scanopy provides role-based access control (RBAC) to manage user permissions. You can invite users to your organization and assign them roles with specific privileges.

### Roles

*   **Admin**: Full access to all networks and settings within the organization. Can manage users, billing, and organization settings.
*   **User**: Can view network topology and host data for all networks. Cannot make changes to settings or run discoveries.
*   **Network Admin** (Self-Hosted Only): Full access to assigned networks. Can manage discoveries and settings for their assigned networks only.
*   **Network Viewer** (Self-Hosted Only): Read-only access to assigned networks.

### Inviting Users

1.  Navigate to **Settings > Users**
2.  Click **Invite User**
3.  Enter the user’s email address and select a role
4.  (Self-Hosted Only) If assigning a network-specific role, select the networks the user can access.
5.  Click **Send Invite**

The user will receive an email invitation to join your organization.

## Single Sign-On (SSO)

Scanopy supports SSO via OpenID Connect (OIDC), allowing users to authenticate with your identity provider (e.g., Google Workspace, Microsoft Entra ID, Okta).

See [OIDC Setup](/docs/self-hosted/oidc/) for configuration instructions.
