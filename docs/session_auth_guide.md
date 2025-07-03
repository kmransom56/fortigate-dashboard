# FortiGate Session Key Authentication

This implementation adds session-based authentication to the FortiGate dashboard, providing a more secure and dynamic alternative to static API tokens.

## Overview

### Authentication Methods Supported

1. **Session-based Authentication** (Preferred)

   - Uses username/password to establish a session
   - Automatically handles session renewal
   - More secure than static tokens
   - Sessions typically last 30 minutes

2. **API Token Authentication** (Fallback)
   - Uses static API tokens
   - Falls back automatically if session auth fails
   - Maintains backward compatibility

## How It Works

### Session Management

The `FortiGateSessionManager` class handles:

- **Login Process**: Authenticates with FortiGate using `/logincheck` endpoint
- **Session Key Extraction**: Extracts session cookies from authentication response
- **Session Validation**: Checks if current session is still valid
- **Auto-renewal**: Automatically re-authenticates when sessions expire
- **Graceful Fallback**: Falls back to token authentication if session auth fails

### API Flow

1. **Initial Request**: Service tries session authentication first
2. **Session Check**: Validates if current session is still valid
3. **Auto-login**: If no valid session, automatically logs in
4. **API Call**: Makes authenticated API request using session cookies
5. **Error Handling**: If session expires mid-request, re-authenticates automatically
6. **Fallback**: If session auth fails completely, tries token authentication

## Configuration

### Environment Variables

```bash
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_USERNAME=admin
```

### Docker Secrets

The system supports loading credentials from Docker secrets:

```yaml
secrets:
  fortigate_password:
    file: ./secrets/fortigate_password.txt
```

### File Locations

Credentials are loaded from these locations in order:

1. `FORTIGATE_PASSWORD` environment variable
2. `/run/secrets/fortigate_password` (Docker secrets)
3. `/secrets/fortigate_password.txt` (Local development)
4. `./secrets/fortigate_password.txt` (Relative path)

## Setup Instructions

### Option 1: Interactive Setup

Run the configuration utility:

```bash
python tools/setup_auth.py
```

This will:

- Prompt for FortiGate IP address
- Ask for authentication method preference
- Collect credentials securely
- Create necessary configuration files

### Option 2: Manual Setup

1. **Create password file**:

   ```bash
   echo "your_admin_password" > secrets/fortigate_password.txt
   ```

2. **Update environment variables**:

   ```bash
   export FORTIGATE_HOST=https://192.168.0.254
   export FORTIGATE_USERNAME=admin
   ```

3. **Update Docker Compose** (already configured):
   ```yaml
   secrets:
     - fortigate_password
   environment:
     - FORTIGATE_USERNAME=admin
   ```

## Testing

### Test Session Authentication

```bash
python test_session_auth.py
```

This will:

- Test session manager initialization
- Attempt login with credentials
- Make test API calls
- Verify session functionality

### Expected Output

```
Testing FortiGate Session Authentication
==================================================
FortiGate IP: 192.168.0.254
Username: admin
Password loaded: Yes

Attempting to login...
✅ Login successful!
Session key: abcd1234efgh5678...
Session expires: 2024-01-01 15:30:00

Testing API call...
✅ API call successful! Retrieved 8 interfaces

Testing through service...
✅ Service returned 8 interfaces

✅ Logged out successfully
```

## Advantages of Session Authentication

### Security Benefits

1. **Dynamic Credentials**: Session keys change regularly
2. **Automatic Expiration**: Sessions expire after inactivity
3. **No Static Secrets**: No long-lived tokens in configuration
4. **Audit Trail**: Login/logout events are logged

### Operational Benefits

1. **Automatic Renewal**: No manual token rotation needed
2. **Graceful Degradation**: Falls back to token auth if needed
3. **Rate Limit Friendly**: Sessions are less likely to hit rate limits
4. **Standard Practice**: Uses FortiGate's standard web authentication

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Check username/password in secrets file
   - Verify FortiGate is accessible
   - Check firewall rules

2. **Session Expired Quickly**

   - FortiGate may have short session timeouts
   - Check FortiGate admin session settings
   - Monitor session renewal logs

3. **Fallback to Token Auth**
   - Session authentication not supported on this FortiGate
   - Network connectivity issues
   - Incorrect credentials

### Debug Logging

Enable debug logging to see detailed authentication flow:

```bash
export LOG_LEVEL=DEBUG
```

This will show:

- Login attempts and responses
- Session key extraction
- API call authentication methods
- Fallback decisions

## Migration from Token-only

The implementation is backward compatible. Existing token-based setups will continue working, with session auth attempted first as the preferred method.

### Gradual Migration

1. **Keep existing token setup**
2. **Add password configuration**
3. **Test session authentication**
4. **Monitor logs for successful session usage**
5. **Eventually remove token files if desired**

## Architecture

### Class Structure

```
FortiGateSessionManager
├── _load_credentials()     # Load username/password from various sources
├── login()                 # Authenticate and get session key
├── logout()                # Clean session termination
├── _is_session_valid()     # Check session expiration
├── get_session_key()       # Get valid session key (with auto-renewal)
└── make_api_request()      # Make authenticated API calls
```

### Integration Points

- `fortigate_service.py`: Updated to use session auth preferentially
- `deploy/compose.yml`: Added password secret mounting
- Environment variables: Added username configuration
- Error handling: Graceful fallback to token authentication

This implementation provides a robust, secure, and user-friendly authentication system for the FortiGate dashboard.
