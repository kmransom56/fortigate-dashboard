# Fortigate Dashboard Application

A dashboard application for monitoring FortiGate interfaces and network status.

## Building the Application

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)
- A FortiGate device with API access configured
- API token for the FortiGate device

### Step 1: Clone the Repository
```bash
git clone https://github.com/kmransom56/fortigate-dashboard.git
cd fortigate-dashboard
```

### Step 2: Configure Environment Variables
Create or modify the `.env` file in the root directory with your FortiGate configuration:

```
# FortiGate API Configuration
FORTIGATE_HOST=https://your-fortigate-ip
FORTIGATE_API_TOKEN=your-api-token

# Path to FortiGate SSL Certificate
FORTIGATE_CERT_PATH=/app/certs/fortigate.pem

# Logging Configuration
LOG_LEVEL=DEBUG
```

### Step 3: Configure API Token Secret
Create or update the API token in the secrets file:

```bash
mkdir -p secrets
echo "your-api-token" > secrets/fortigate_api_token.txt
```

### Step 4: SSL Certificate (Optional)
If you have a FortiGate SSL certificate, place it in the `app/certs` directory:

```bash
mkdir -p app/certs
# Copy your certificate to the certs directory
cp your-fortigate-cert.pem app/certs/fortigate.pem
```

### Step 5: Build and Start the Application
Use Docker Compose to build and start the application:

```bash
docker-compose build
docker-compose up -d
```

This will:
1. Build the Docker images for the dashboard and WAN monitor
2. Start the containers in detached mode
3. The dashboard will be available at http://localhost:8001

### Step 6: Verify the Application is Running
Check the logs to ensure the application started correctly:

```bash
docker-compose logs dashboard
```

You should see output indicating the application has started and is connecting to the FortiGate API.

## Using the Application

### Accessing the Dashboard
Open your web browser and navigate to:
```
http://localhost:8001/dashboard
```

### Dashboard Features

1. **Interface Overview**: The dashboard displays all FortiGate interfaces with their status, IP addresses, and link speeds.

2. **WAN Status Monitoring**: The dashboard highlights WAN interfaces and shows alerts if any WAN links are down.

3. **Traffic Statistics**: View traffic statistics for each interface, including transmitted and received bytes.

4. **Network Map**: A visual representation of your network interfaces and their connections.

5. **Auto-Refresh**: The dashboard automatically refreshes every 10 seconds to show the latest data.

### API Endpoints

The application provides the following API endpoints:

1. **Interface Information**:
   ```
   GET /fortigate/api/interfaces
   ```
   Returns JSON data with information about all FortiGate interfaces.

2. **Dashboard Page**:
   ```
   GET /dashboard
   ```
   Renders the HTML dashboard with interface information.

3. **Home Page**:
   ```
   GET /
   ```
   Renders the application home page.

### Troubleshooting

1. **API Connection Issues**:
   - Check your API token in the `.env` file and `secrets/fortigate_api_token.txt`
   - Ensure your FortiGate device is reachable from the Docker container
   - Verify the IP restrictions in your FortiGate API user configuration

2. **SSL Certificate Issues**:
   - The application is configured to disable SSL verification if certificate issues occur
   - For production use, it's recommended to use a valid certificate

3. **Container Issues**:
   - If you make changes to the configuration, restart the containers:
     ```bash
     docker-compose down
     docker-compose up -d
     ```

4. **Viewing Logs**:
   - To view application logs:
     ```bash
     docker-compose logs -f dashboard
     ```
   - To view WAN monitor logs:
     ```bash
     docker-compose logs -f wan_monitor
     ```

## Security Considerations

1. **API Token**: Keep your API token secure and don't commit it to public repositories.

2. **SSL Verification**: For production environments, use proper SSL certificates instead of disabling verification.

3. **Network Access**: Restrict access to the dashboard to trusted networks.

4. **FortiGate API User**: Configure the FortiGate API user with the minimum required permissions.

## Authentication Notes

The FortiGate API requires the following authentication method:
- Use the `Authorization: Bearer <token>` header (not query parameters)
- Disable SSL verification or provide a valid certificate
- Ensure your client IP is allowed in the FortiGate API user's trusthost configuration

## License

[MIT License](LICENSE)