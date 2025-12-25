# Server Installation

This guide covers installing the Scanopy server on your own infrastructure.

## Requirements

**Docker Installation (Recommended)**

*   Docker Engine 20.10 or later
*   Docker Compose V2

**Building from Source**

*   Rust 1.90 or later
*   Node.js 20 or later
*   PostgreSQL 17
*   4GB RAM minimum
*   20GB disk space

## Docker Installation (Recommended)

This is the easiest way to get started with self-hosted Scanopy.

### 1. Download the Docker Compose File

```
curl -O https://raw.githubusercontent.com/scanopy/scanopy/refs/heads/main/docker-compose.yml
```

### 2. Review Configuration

The default `docker-compose.yml` includes:

*   Scanopy server on port 60072
*   PostgreSQL database
*   Integrated daemon for immediate network scanning

**Important**: The integrated daemon assumes your Docker bridge network is `172.17.0.1`. If your Docker bridge uses a different address, edit the `SCANOPY_INTEGRATED_DAEMON_URL` environment variable in the compose file.

### 3. Start Scanopy

```
docker compose up -d
```

### 4. Verify Installation

Check that services are running:

```
docker compose ps
```

All three services should show as running: `scanopy-server`, `scanopy-postgres`, and `scanopy-daemon`.

If any service fails to start, check its logs with `docker compose logs <service-name>` and [open an issue](https://github.com/scanopy/scanopy/issues) with the output.

### 5. Access the UI

Navigate to `http://<your-server-ip>:60072`

You’ll see the registration page on first load.

## Platform-Specific Instructions

### Proxmox LXC Container

You can use this [helper script](https://community-scripts.github.io/ProxmoxVE/scripts?id=netvisor) to create a Scanopy LXC on your Proxmox host.

### Unraid

Scanopy is available as an Unraid community app.

**Common Issues:**

If running Scanopy directly on a Proxmox host and encountering `could not create any Unix-domain sockets`, add this to both the PostgreSQL and Scanopy services in your docker-compose:

```
security_opt:
  - apparmor:unconfined
```

If running in an LXC, you may need to change `SCANOPY_INTEGRATED_DAEMON_URL` to `172.31.0.1`.

See [issue #87](https://github.com/scanopy/scanopy/issues/87) for more details.

## Building from Source

Refer to [contributing](https://github.com/scanopy/scanopy/blob/main/CONTRIBUTING.md) for details on getting your dev environment set up to build from source.

## Uninstalling

### Docker Installation

```
# Stop and remove containers
docker compose down
# Remove volumes (deletes all data)
docker compose down -v
# Remove images
docker rmi ghcr.io/scanopy/scanopy/server:latest
docker rmi ghcr.io/scanopy/scanopy/daemon:latest
```

## Next Steps

*   [Server Configuration](/docs/self-hosted/server-configuration/) — Configure server settings
*   [OIDC Setup](/docs/self-hosted/oidc/) — Set up enterprise authentication
*   [Quick Start](/docs/getting-started/quick-start/) — Deploy your first daemon
