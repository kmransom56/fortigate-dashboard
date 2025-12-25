# Docker Socket Proxy

If you have containers running on a different machine than your Scanopy daemon, you can use a Docker socket proxy to allow the daemon to discover them.

> **Caution**
> Exposing the Docker socket over the network can be a security risk. Only do this on a trusted network.

## Setup Overview

1.  On the machine running your containers, run a Docker socket proxy.
2.  Configure your Scanopy daemon to connect to the proxy.

## Step 1: Run the Proxy

We recommend using [Tecnativa’s Docker Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy).

```bash
docker run -d -p 2375:2375 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  tecnativa/docker-socket-proxy
```

This will expose the Docker socket on port 2375.

## Step 2: Configure the Daemon

On your Scanopy daemon, set the `DOCKER_HOST` environment variable to the IP address and port of the machine running the proxy.

```bash
docker run -d \
  --name scanopy-daemon \
  --network=host \
  --privileged \
  -e SCANOPY_DAEMON_TOKEN="your-unique-token" \
  -e DOCKER_HOST="tcp://<ip-of-proxy-machine>:2375" \
  ghcr.io/scanopy/scanopy/daemon:latest
```

The daemon will now be able to discover containers running on the remote machine.

```