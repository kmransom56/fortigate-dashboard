# Daemon Configuration

Daemons are configured using environment variables. This guide covers the available options.

## Required Configuration

### `SCANOPY_DAEMON_TOKEN`

**Required**. This token associates the daemon with a specific network in your Scanopy organization. You will get this token when you create a new network.

## Optional Configuration

### `SCANOPY_LOG_LEVEL`

Set the log level for the daemon.

*   **Default**: `info`
*   **Options**: `error`, `warn`, `info`, `debug`, `trace`

### `SCANOPY_PORT`

The port the daemon listens on for API requests.

*   **Default**: `60073`

### `SCANOPY_BIND_ADDRESS`

The IP address the daemon binds to.

*   **Default**: `0.0.0.0`

### `SCANOPY_NAME`

A custom name for the daemon, which will be displayed in the Scanopy UI.

*   **Default**: The machine’s hostname.

### `SCANOPY_SERVER_URL`

The URL of your Scanopy server. Only needed if the daemon cannot automatically discover the server (e.g., in a different network).

*   **Default**: Automatically discovered via DNS-SD.
