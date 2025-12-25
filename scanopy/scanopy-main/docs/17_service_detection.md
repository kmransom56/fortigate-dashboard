# Service Detection

Scanopy automatically identifies 200+ services during network discovery. This page explains how detection works and what to do when a service isn’t detected.

For the complete list of detectable services and their match patterns, see [scanopy.net/services](https://scanopy.net/services).

## Why Wasn’t My Service Detected?

**First**: Check if the service is in Scanopy’s detection list at [scanopy.net/services](https://scanopy.net/services). If it’s not listed, you can [request it](#requesting-new-service-detection).

**If the service is supported but wasn’t detected:**

**Service on non-standard port** — Grafana on port 8080 instead of 3000? Scanopy won’t probe port 8080 for Grafana’s endpoint pattern. Move to the default port or manually add the service.

**Service requires authentication** — If a service returns 401/403 before Scanopy can read the response body, endpoint matching fails. Some services (like Plex) have patterns that account for this, but many don’t.

**Docker container not exposed** — Containers on internal bridge networks aren’t reachable via network scan. Use Docker discovery instead, which inspects the Docker API directly.

**Firewall blocking the daemon** — The daemon must be able to connect to the service’s port. Check that firewall rules allow the daemon to probe the host.

## How Detection Works

Detection happens in phases:

1.  **Port scan** — Find open TCP and UDP ports
2.  **Endpoint probing** — Send HTTP requests to known paths
3.  **Pattern matching** — Compare results against service definitions

Each service has a **detection pattern** that specifies what to look for. Patterns can include:

| Check | What It Does |
| --- | --- |
| **Port** | Is a specific port open? |
| **Endpoint** | Does the HTTP response body contain a string? |
| **Header** | Does an HTTP header contain a value? |
| **MAC Vendor** | Does the device’s MAC address belong to a vendor? |
| **Gateway** | Is this IP in the daemon’s routing table? |

Patterns can be combined with **AllOf** (all must match) or **AnyOf** (any can match).

### Example: Pi-hole

Pi-hole’s pattern requires:

*   DNS port open (53/tcp OR 53/udp) **AND**
*   HTTP response from `/admin` contains “pi-hole”

Both conditions must be true for Pi-hole to be detected.

### Example: Plex

Plex’s pattern accepts either:

*   HTTP response from port 32400 `/web/index.html` contains “Plex” **OR**
*   HTTP response has `X-Plex-Protocol` header

Either condition is sufficient.

## Confidence Levels

Each detected service has a confidence level indicating match strength.

| Level | Meaning |
| --- | --- |
| **Certain** | System services only (Scanopy Daemon, Docker Daemon) |
| **High** | Strong match — endpoint content or header matched |
| **Medium** | Moderate match — MAC vendor or unique port |
| **Low** | Weak match — common port, could be multiple services |
| **N/A** | Generic service — definitional match (port 53 = DNS) |

### Generic Services

Some services are **generic** — they’re defined by their port alone:

*   Port 53 → DNS Server
*   Port 5432 → PostgreSQL
*   Port 22 → SSH

These show “N/A” confidence because there’s no uncertainty. Port 53 *is* DNS by definition. If you’re running a specific DNS server (Pi-hole, AdGuard), it will be detected separately with its own pattern.

## Improving Detection

**Use default ports** — Detection patterns are written for standard ports. Check [scanopy.net/services](https://scanopy.net/services) for which port each service expects.

**Use Docker discovery for containers** — Docker discovery inspects the Docker API directly, so it works for containers on internal networks without port exposure. It’s more reliable than network scanning for containerized services.

## Requesting New Service Detection

If a service isn’t detected:

1.  **Check existing definitions** at [scanopy.net/services](https://scanopy.net/services)
2.  **Report a detection issue** if Scanopy should have detected it but didn’t:

    [Service detection issue](https://github.com/scanopy/scanopy/issues/new?template=service-detection-issue.md)
3.  **Request a new service** if it’s not in the list:

    [Missing service request](https://github.com/scanopy/scanopy/issues/new?template=missing-service-detection.md)

When requesting, include:

*   Service name and what it does
*   Default port(s)
*   Any unique HTTP endpoints or headers
*   How you currently identify it
