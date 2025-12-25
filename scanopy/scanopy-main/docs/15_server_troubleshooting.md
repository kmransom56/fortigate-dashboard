# Server Troubleshooting

Common issues and solutions for self-hosted Scanopy server deployments.
For daemon-related issues, see [Daemon Troubleshooting](/docs/daemons/troubleshooting/).

## Server Issues

### Port Already in Use

**Symptoms**: Server fails to start with “address already in use”

**Solution**: Change the port mapping in docker-compose.yml:

```yaml
ports:
  - '8080:60072' # Change 60072 to any available port
```

### Browser Shows “SSL Protocol Error”

**Symptoms**: Browser displays “ERR_SSL_PROTOCOL_ERROR” when accessing Scanopy

**Cause**: Using `https://` instead of `http://`. Scanopy doesn’t handle TLS directly.

```
http://your-server:60072
```

**Solution**: Use `http://` to access Scanopy directly. For HTTPS, put a reverse proxy (Traefik, Nginx, Caddy) in front to handle TLS termination.

### PostgreSQL “Could not create any Unix-domain sockets” (Proxmox)

**Symptoms**: PostgreSQL container fails to start on Proxmox host with socket creation error

**Cause**: AppArmor security policy blocking socket creation.

**Solution**: Add to both PostgreSQL and Scanopy services in docker-compose.yml:

```yaml
security_opt:
  - apparmor:unconfined
```

See [issue #87](https://github.com/scanopy/scanopy/issues/87) for details.

### Integrated Daemon Not Initializing

**Symptoms**: Integrated daemon shows in UI but doesn’t start discovery

**Diagnosis**:

> **Terminal window**
>
> ```
> # Check daemon logs
> docker logs scanopy-daemon
> # Check if daemon can reach server
> docker exec scanopy-daemon curl http://scanopy-server:60072/api/health
> ```

**Solutions**:

1.  **Verify bridge network**: Check your Docker bridge IP

    > **Terminal window**
    >
    > ```
    > docker network inspect bridge | grep Gateway
    > ```

2.  **Update compose file**: If gateway isn’t `172.17.0.1`, update `SCANOPY_INTEGRATED_DAEMON_URL`
3.  **Check API key**: Ensure the integrated daemon has a valid API key in the database

## Database Issues

### How to Backup Data

Scanopy stores all data in PostgreSQL. To backup:

**Docker setup**:

> **Terminal window**
>
> ```
> # Backup
> docker exec scanopy-db pg_dump -U postgres scanopy > scanopy_backup.sql
> # Restore
> docker exec -i scanopy-db psql -U postgres scanopy < scanopy_backup.sql
> ```

**Manual setup**: Use standard PostgreSQL backup tools (pg_dump, pg_restore).

### How to Reset Password

If SMTP is configured, use the “Forgot Password” link on the login page.

If SMTP is not configured:

1.  Generate a new password hash using bcrypt
2.  Update the `users` table with the new hash
3.  Or, ask another Owner to delete and re-invite you

### How to Delete All Data

To start fresh:

> **Terminal window**
>
> ```
> docker compose down -v # Removes all volumes including database
> docker compose up -d # Start fresh
> ```

## Reverse Proxy Setup

Configure your reverse proxy (Nginx, Traefik, Caddy) to forward traffic to port 60072.

For HTTPS, enable secure cookies in docker-compose.yml:

```yaml
environment:
  - SCANOPY_USE_SECURE_SESSION_COOKIES=true
```

See [Server Configuration](/docs/self-hosted/server-configuration/#session-security) for details.

## Getting Help

If your issue isn’t covered here:

*   **Discord**: Join our [Discord community](https://discord.gg/b7ffQr8AcZ)
*   **GitHub Issues**: [Open an issue](https://github.com/scanopy/scanopy/issues/new)
