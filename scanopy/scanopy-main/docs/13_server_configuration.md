# Server Configuration

Configuration reference for self-hosted Scanopy server deployments.

## Configuration Methods

**Environment variables in docker-compose**:

```
environment:
  - SCANOPY_SERVER_PORT=60072
  - DATABASE_URL=postgresql://postgres:password@db:5432/scanopy
```

**Command-line** (for binary builds):

```
./scanopy-server --port 60072 --database-url postgresql://...
```

## Parameter Reference

| Parameter | CLI Flag | Environment Variable | Default | Description |
| --- | --- | --- | --- | --- |
| **Server Public URL** | `--public-url` | `SCANOPY_PUBLIC_URL` | `http://localhost:60072` | Public URL for webhooks, email links, etc |
| **Server Port** | `--server-port` | `SCANOPY_SERVER_PORT` | `60072` | Port for server to listen on |
| **Database URL** | `--database-url` | `SCANOPY_DATABASE_URL` | *Required* | PostgreSQL connection string |
| **Log Level** | `--log-level` | `SCANOPY_LOG_LEVEL` | `info` | Logging verbosity: `trace`, `debug`, `info`, `warn`, `error` |
| **Secure Cookies** | `--use-secure-session-cookies` | `SCANOPY_USE_SECURE_SESSION_COOKIES` | `false` | Enable HTTPS-only cookies |
| **Integrated Daemon URL** | `--integrated-daemon-url` | `SCANOPY_INTEGRATED_DAEMON_URL` | `http://172.17.0.1:60073` | URL to reach daemon in default docker compose |
| **Disable Registration** | `--disable-registration` | `SCANOPY_DISABLE_REGISTRATION` | `false` | Disable new user registration |
| **SMTP Username** | `--smtp-username` | `SCANOPY_SMTP_USERNAME` | - | SMTP username for email features |
| **SMTP Password** | `--smtp-password` | `SCANOPY_SMTP_PASSWORD` | - | SMTP password for email authentication |
| **SMTP Relay** | `--smtp-relay` | `SCANOPY_SMTP_RELAY` | - | SMTP server address (e.g., `smtp.gmail.com`) |
| **SMTP Email** | `--smtp-email` | `SCANOPY_SMTP_EMAIL` | - | Sender email address for outgoing emails |
| **Client IP Source** | `--client-ip-source` | `SCANOPY_CLIENT_IP_SOURCE` | - | Source of IP address from request headers for reverse proxy setups |

## Integrated Daemon URL

The integrated daemon runs in a separate container and needs to reach the server. The default assumes Docker’s bridge network gateway is `172.17.0.1`.

**Check your bridge gateway**:

```
docker network inspect bridge | grep Gateway
```

**If different**, update in docker-compose.yml:

```
environment:
  - SCANOPY_INTEGRATED_DAEMON_URL=http://YOUR_GATEWAY_IP:60073
```

## SMTP Configuration

SMTP settings enable email-based features such as password reset.

**All SMTP parameters are optional.** If not configured, email features will be disabled.

**Configuration**:

```
environment:
  - SCANOPY_SMTP_RELAY=smtp.gmail.com:587
  - SCANOPY_SMTP_USERNAME=[email protected]
  - SCANOPY_SMTP_PASSWORD=your-app-password
  - SCANOPY_SMTP_EMAIL=[email protected]
```

## UI Configuration

The UI automatically uses the hostname and port from your browser’s address bar to reach the API.

**No configuration needed** for standard deployments where UI and API are on the same domain.

### Advanced: API on Different Domain

If your API server is on a different hostname than where the UI is served (uncommon):

Rebuild the Docker image with build arguments:

```
docker build \
  --build-arg PUBLIC_SERVER_HOSTNAME=api.example.com \
  --build-arg PUBLIC_SERVER_PORT=8080 \
  -f backend/Dockerfile \
  -t scanopy-server:custom \
  .
```

Then use your custom image in docker-compose:

```
scanopy-server:
  image: scanopy-server:custom
  # ... rest of config
```

## Session Security

### Secure Cookies

**Important**: Enable secure cookies when running Scanopy behind HTTPS.

```
environment:
  - SCANOPY_USE_SECURE_SESSION_COOKIES=true
```

**When to enable**:

*   Behind a reverse proxy with TLS (Nginx, Traefik, Caddy)
*   Using a domain with HTTPS
*   Production deployments

**When to disable** (default):

*   Internal networks without HTTPS
*   Development environments
*   Accessing via IP address without TLS

**Effect**:

*   `true`: Cookies marked as Secure, only sent over HTTPS
*   `false`: Cookies sent over HTTP and HTTPS

## Environment Files

For easier management, use `.env` files:

**Create `.env`**:

```
# Database
SCANOPY_DATABASE_URL=postgresql://postgres:password@db:5432/scanopy
# Server
SCANOPY_SERVER_PORT=60072
SCANOPY_SERVER_PUBLIC_URL=http://your-domain.com:60072
SCANOPY_LOG_LEVEL=info
SCANOPY_USE_SECURE_SESSION_COOKIES=false
# SMTP (optional - for password reset and notifications)
SCANOPY_SMTP_RELAY=smtp.gmail.com:587
SCANOPY_SMTP_USERNAME=[email protected]
SCANOPY_SMTP_PASSWORD=your-app-password
SCANOPY_SMTP_EMAIL=[email protected]
# Daemon
SCANOPY_INTEGRATED_DAEMON_URL=http://172.17.0.1:60073
```

**Reference in docker-compose.yml**:

```
services:
  scanopy-server:
    image: ghcr.io/scanopy/scanopy/server:latest
    env_file:
      - .env
    # ... rest of config
```
