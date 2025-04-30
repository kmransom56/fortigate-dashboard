# FortiGate Dashboard - Fixed Version

This is a fixed version of the FortiGate Dashboard application that addresses the 401 Unauthorized error when accessing the FortiGate API.

## Issue Fixed

The original application was using the API token as a query parameter (`access_token=token`), but the FortiGate API requires the token to be sent in the Authorization header as a Bearer token.

## Changes Made

1. Fixed the authentication method in all API calls to use the Authorization header with Bearer token.
2. Updated the Docker configuration to include the fixed files.
3. Added documentation on the correct authentication method for FortiGate APIs.

## Files Added/Modified

- `curl_command.sh`: curl command that uses the Authorization header.
- `fortigate_api_authentication_guide.md`: A comprehensive guide on FortiGate API authentication.
- `Dockerfile`: Updated Dockerfile for the dashboard service.
- `Dockerfile.wan_monitor`: Updated Dockerfile for the WAN monitor service.
- `docker-compose.yml`: Updated docker-compose file that uses the fixed Dockerfiles.
- `wan_monitor.py`: Updated WAN monitor script with the correct authentication method.
- `build_and_run.sh`: Script to build and run the fixed Docker containers.

## How to Use

### Option 1: Using the build script

1. Make the build script executable:
   ```bash
   chmod +x build_and_run.sh
   ```

2. Run the build script:
   ```bash
   ./build_and_run.sh
   ```

### Option 2: Manual build and run

1. Build the Docker images:
   ```bash
   docker-compose -f docker-compose.fixed.yml build
   ```

2. Start the containers:
   ```bash
   docker-compose -f docker-compose.fixed.yml up -d
   ```

3. Check the container status:
   ```bash
   docker-compose -f docker-compose.fixed.yml ps
   ```

## Accessing the Dashboard

Once the containers are running, you can access the dashboard at:
- http://localhost:8001

## Viewing Logs

To view the logs of the running containers:

```bash
# Dashboard logs
docker-compose -f docker-compose.fixed.yml logs -f dashboard

# WAN monitor logs
docker-compose -f docker-compose.fixed.yml logs -f wan_monitor
```

## Stopping the Containers

To stop the containers:

```bash
docker-compose -f docker-compose.fixed.yml down
```

## FortiGate API Authentication Guide

For more information on the correct authentication method for FortiGate APIs, see the `fortigate_api_authentication_guide.md` file.