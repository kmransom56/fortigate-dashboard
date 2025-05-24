# FortiGate Dashboard and Troubleshooter

This project contains two applications for managing and troubleshooting FortiGate devices:

1. **FortiGate Dashboard** - A FastAPI web application for monitoring FortiGate interfaces and FortiSwitches
2. **FortiGate Troubleshooter** - A Flask application for diagnosing and troubleshooting FortiGate devices

## Project Structure

- `app/` - FastAPI dashboard application
- `src/` - Flask troubleshooter application
- `app/certs/` - SSL certificates for secure connections
- `logs/` - Application logs

## Features

### FortiGate Dashboard

- Monitor FortiGate interfaces and traffic statistics
- View connected FortiSwitches and their status
- Manage FortiSwitch IP addresses
- RESTful API endpoints for integration

### FortiGate Troubleshooter

- Run diagnostics on FortiGate devices
- Troubleshoot network connectivity issues
- Session table and flow debugging
- UTM and web filtering diagnostics
- VPN and authentication troubleshooting
- Hardware and high availability checks

## Prerequisites

- Python 3.8 or higher
- FortiGate device with API access
- API token for FortiGate authentication

## Installation and Setup

### Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/kmransom56/fortigate-dashboard.git
   cd fortigate-dashboard
   ```

### Option 1: Easy Docker Installation (Recommended)

1. Make the installation script executable:

   ```bash
   chmod +x install.sh
   ```

2. Run the installation script:

   ```bash
   ./install.sh
   ```

   The script will:
   - Check for Docker and Docker Compose
   - Create a configuration file (.env) if it doesn't exist
   - Generate self-signed SSL certificates if needed
   - Build and start the Docker containers
   - Display access URLs for the applications

### Option 2: Manual Docker Setup

1. Create a `.env` file with your FortiGate configuration:

   ```env
   FORTIGATE_HOST=https://192.168.0.254
   FORTIGATE_API_TOKEN=your_api_token_here
   ```

2. Build and start the Docker containers:

   ```bash
   docker-compose up -d --build
   ```

3. Access your applications at:
   - Dashboard: `http://localhost:8001`
   - Troubleshooter: `https://localhost:5002`

### Option 3: Using the startserver.sh script (Local Development)

1. Make the script executable:

   ```bash
   chmod +x startserver.sh
   ```

2. Run the script to start both applications:

   ```bash
   ./startserver.sh --all
   ```

   The script uses `uv` for faster package installation and virtual environment management.

## Accessing the Applications

- **FortiGate Dashboard**: `http://localhost:8001`
- **FortiGate Troubleshooter**: `https://localhost:5002` (uses SSL)

## Using the startserver.sh Script

The `startserver.sh` script provides several options for running the applications:

```bash
# Show help and available options
./startserver.sh --help

# Start just the dashboard (default)
./startserver.sh

# Start just the troubleshooter
./startserver.sh --troubleshooter

# Start both applications
./startserver.sh --all

# Start both with custom ports
./startserver.sh --all --dashboard-port 8080 --troubleshooter-port 5003

# Start without killing existing processes
./startserver.sh --all --no-kill
```

## Authentication

This project uses Bearer token authentication for the FortiGate API. For more information, see the `fortigate_api_authentication_guide.md` file.

## SSL Certificate Verification

For information on SSL certificate verification and troubleshooting, see the `ssl_certificate_verification_guide.md` file.

## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs/` directory
2. Verify your FortiGate API token is valid
3. Ensure the FortiGate device is accessible from your network
4. Check SSL certificate configuration if you're having connection issues

## License

This project is licensed under the MIT License. See the LICENSE file for details.