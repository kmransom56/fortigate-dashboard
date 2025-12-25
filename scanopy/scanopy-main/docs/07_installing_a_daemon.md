# Installing a Daemon

Daemons are lightweight agents that perform discovery scans on your networks. This guide provides installation instructions for various platforms.

> **Caution**
> Each daemon is tied to a specific network in Scanopy. When you create a new network, you will be provided with a unique installation command for that network’s daemon.

## Docker (Recommended)

This is the easiest way to run a daemon.

```bash
docker run -d \
  --name scanopy-daemon \
  --network=host \
  --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e SCANOPY_DAEMON_TOKEN="your-unique-token" \
  ghcr.io/scanopy/scanopy/daemon:latest
```

**Note for Docker Desktop (Mac/Windows) Users**: Docker Desktop does not support `--network=host`. You will need to use the binary installation instead.

## Docker Compose

If you are running the Scanopy server with Docker Compose, you can add a daemon service to your `docker-compose.yml` file:

```yaml
services:
  daemon:
    image: ghcr.io/scanopy/scanopy/daemon:latest
    container_name: scanopy-daemon
    network_mode: host
    privileged: true
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      SCANOPY_DAEMON_TOKEN: "your-unique-token"
```

## Unraid

A Scanopy Daemon template is available in the Unraid Community Apps store.

1.  Go to the **Apps** tab in your Unraid UI.
2.  Search for “Scanopy Daemon” and click **Install**.
3.  Enter your daemon token when prompted.

## Binary

You can also run the daemon as a binary on Linux or macOS.

1.  Download the latest release from the [GitHub Releases](https://github.com/scanopy/scanopy/releases) page.
2.  Make the binary executable:

    ```bash
    chmod +x scanopy-daemon
    ```

3.  Run the daemon with your token:

    ```bash
    SCANOPY_DAEMON_TOKEN="your-unique-token" ./scanopy-daemon
    ```

You may need to run the binary with `sudo` for it to have the necessary network permissions.

```