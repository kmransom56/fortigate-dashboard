# Daemon Troubleshooting

Common issues and solutions for Scanopy daemons.

## Daemon Issues

### Daemon Not Connecting to Server

**Symptoms**: Daemon shows as offline in the UI, or logs show connection errors

**Diagnosis**:

```
# Check daemon logs
docker logs scanopy-daemon
# Test connectivity to server
curl https://your-server-url/api/health
```

**Solutions**:

1.  **Verify server URL**: Ensure `SCANOPY_SERVER_URL` is correct and reachable from the daemon host
2.  **Check API key**: Verify the API key is valid and not expired in **Manage > API Keys**
3.  **Firewall rules**: Ensure outbound HTTPS (port 443) is allowed from the daemon host

### Discovery Fails with “CONCURRENT_SCANS too high”

**Symptoms**: Daemon crashes or runs out of memory during scans

**Solution**: Reduce concurrent scans in daemon configuration:

**Docker:**

```
environment:
  - SCANOPY_CONCURRENT_SCANS=10 # Reduce from default
```

**Binary:**

```
scanopy-daemon --concurrent-scANS 10 ...
```

See [Daemon Configuration](/docs/daemons/daemon-configuration/#concurrent-scans) for recommended values.

### ”Too Many Open Files” Error

**Symptoms**: `Critical error scanning: Too many open files (os error 24)` in daemon logs

**Causes**: System file descriptor limit is too low for the configured concurrent scans.

**Solutions**:

1.  **Reduce concurrent scans** (easiest):

    ```
    environment:
      - SCANOPY_CONCURRENT_SCANS=10
    ```

2.  **Increase system file descriptor limit**:

    ```
    # Check current limit
    ulimit -n
    # Increase temporarily
    ulimit -n 65535
    # Increase permanently (add to /etc/security/limits.conf)
    * soft nofile 65535
    * hard nofile 65535
    ```

3.  **For Docker**: Add to your daemon container:

    ```
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
    ```

### Permission Denied Errors (Linux)

**Symptoms**: “Permission denied” when accessing Docker socket

**Solution**: Add user to docker group:

```
sudo usermod -aG docker $USER
newgrp docker
```

Log out and back in for changes to take effect.

If you’re using a Docker socket proxy and getting permission errors, see [Docker Socket Proxy troubleshooting](/docs/daemons/docker-proxy/#troubleshooting).

### Daemon Stops When Terminal Closes

**Symptoms**: Daemon runs in foreground and stops when SSH session ends

**Solution**: Install as a systemd service (see [Installing a Daemon](/docs/daemons/installing-daemon/#systemd-service-linux)), or run with a process manager like `screen` or `tmux`.

## Discovery Issues

### Discovery Takes Hours

**Symptoms**: Network discovery takes 10+ hours to complete

**Most likely cause**: You’re scanning a Docker bridge network. The default 172.17.0.0/16 is 65,536 IPs.

**Solutions**:

1.  **Remove large subnets**: In your Network Scan discovery, remove any Docker bridge networks (172.17.0.0/16, etc.)
2.  **Use Docker discovery instead**: It queries the Docker API directly and takes seconds
3.  **Check your subnet list**: Only scan subnets that actually contain hosts

### Topology Empty After Discovery

**Symptoms**: Discovery completes but topology shows nothing

**Check these**:

1.  **Discovery errors**: Check **Discover > Sessions** for failures
2.  **Network filter**: Check topology options panel — wrong network may be selected
3.  **Service filters**: Category filters may be hiding everything
4.  **Reachability**: Verify daemon can actually reach the target network

## Getting Help

If your issue isn’t covered here:

*   **Discord**: Join our [Discord community](https://discord.gg/b7ffQr8AcZ)
*   **GitHub Issues**: [Open an issue](https://github.com/scanopy/scanopy/issues/new)
