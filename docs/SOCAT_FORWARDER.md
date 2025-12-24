# FortiGate SOCAT Forwarder Service

## Overview

This systemd service provides a persistent TCP forwarder that bridges Docker Desktop's network limitation, allowing containers to access the FortiGate API at `192.168.0.254:443` through `host.docker.internal:8443`.

## Service Details

- **Service Name**: `fortigate-socat-forwarder.service`
- **Location**: `/etc/systemd/system/fortigate-socat-forwarder.service`
- **Source**: `scripts/fortigate-socat-forwarder.service`
- **Function**: Forwards TCP connections from `localhost:8443` to `192.168.0.254:443`

## Why This Is Needed

Docker Desktop on Linux runs containers in a VM that cannot directly access the host's physical network (192.168.0.0/24). The socat forwarder runs on the host and bridges this gap, allowing containers to reach the FortiGate through `host.docker.internal:8443`.

## Management Commands

### Check Status
```bash
sudo systemctl status fortigate-socat-forwarder.service
```

### Start Service
```bash
sudo systemctl start fortigate-socat-forwarder.service
```

### Stop Service
```bash
sudo systemctl stop fortigate-socat-forwarder.service
```

### Restart Service
```bash
sudo systemctl restart fortigate-socat-forwarder.service
```

### Enable Service (start on boot)
```bash
sudo systemctl enable fortigate-socat-forwarder.service
```

### Disable Service (don't start on boot)
```bash
sudo systemctl disable fortigate-socat-forwarder.service
```

### View Logs
```bash
sudo journalctl -u fortigate-socat-forwarder.service -f
```

## Configuration

The service is configured to:
- Listen on `localhost:8443` (all interfaces)
- Forward to `192.168.0.254:443` (FortiGate HTTPS)
- Auto-restart on failure (5 second delay)
- Run as user `keith` (update in service file if needed)
- Start after network is online

## Troubleshooting

### Service Won't Start
1. Check if port 8443 is already in use:
   ```bash
   sudo netstat -tuln | grep 8443
   sudo lsof -i :8443
   ```

2. Check service logs:
   ```bash
   sudo journalctl -u fortigate-socat-forwarder.service -n 50
   ```

3. Verify socat is installed:
   ```bash
   which socat
   ```

### Connection Issues
1. Test from host:
   ```bash
   curl -k https://localhost:8443/api/v2/monitor/system/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. Test from container:
   ```bash
   docker exec fortigate-dashboard curl -k \
     https://host.docker.internal:8443/api/v2/monitor/system/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. Verify FortiGate is reachable from host:
   ```bash
   ping -c 3 192.168.0.254
   curl -k https://192.168.0.254/api/v2/monitor/system/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Updating the Service

If you need to change the FortiGate IP or port:

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/fortigate-socat-forwarder.service
   ```

2. Update the `ExecStart` line with new IP/port

3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart fortigate-socat-forwarder.service
   ```

## Related Configuration

- **Docker Compose**: `docker-compose.yml` sets `FORTIGATE_HOST=https://host.docker.internal:8443`
- **Application Code**: `app/services/fortigate_redis_session.py` handles the hostname parsing
