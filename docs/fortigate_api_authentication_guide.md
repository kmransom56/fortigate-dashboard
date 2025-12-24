# FortiGate API Authentication Guide

## Issue Identified

The 401 Unauthorized error occurred because the FortiGate API requires authentication via the `Authorization` header with a Bearer token, but the curl command was using the token as a query parameter (`access_token=`).

## Correct Authentication Methods

### 1. Using curl

**Incorrect Method (Query Parameter):**
```bash
curl --cacert app/certs/fortigate.pem -X 'GET' \
  'https://192.168.0.254:443/api/v2/monitor/system/interface?access_token=w5r656wzh5QH7t808fgbdch109kbnk' \
  -H 'accept: application/json'
```

**Correct Method (Authorization Header):**
```bash
curl --cacert app/certs/fortigate.pem -X 'GET' \
  'https://192.168.0.254:443/api/v2/monitor/system/interface' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer fw5r656wzh5QH7t808fgbdch109kbnk'
```

### 2. Using Python Requests

**Incorrect Method (Query Parameter):**
```python
url = "https://192.168.0.254/api/v2/monitor/system/interface"
params = {"access_token": API_TOKEN}
headers = {"Accept": "application/json"}
response = requests.get(url, headers=headers, params=params, verify=CERT_PATH)
```

**Correct Method (Authorization Header):**
```python
url = "https://192.168.0.254/api/v2/monitor/system/interface"
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}
response = requests.get(url, headers=headers, verify=CERT_PATH)
```

## Files That Need Updating

Most of your application code already uses the correct authentication method. The following test files are using the query parameter approach and should be updated if you plan to continue using them:

1. test_api_variations.py
2. test_with_dotenv.py
3. test_fortigate_api.py
4. test_api_with_ip_check.py
5. test_api_auth.py
6. test_with_dotenv_no_ssl.py
7. test_endpoints.py
8. test_fortigate_api_no_ssl.py
9. test_token_formats.py

## Why Bearer Token Authentication is Preferred

1. **Security**: Query parameters can be logged in server logs, browser history, and proxy servers, potentially exposing the token.

2. **Standard Compliance**: Bearer token authentication in the Authorization header is the standard method defined in OAuth 2.0 and is widely adopted.

3. **URL Length Limitations**: Some servers and proxies have limitations on URL length, which can be an issue with long tokens in query parameters.

4. **Caching**: URLs with query parameters might be cached, potentially exposing sensitive tokens.

## FortiGate API Best Practices

1. **Always use HTTPS**: Ensure all API calls use HTTPS to encrypt the communication.

2. **Use Bearer Token Authentication**: Always use the Authorization header with Bearer token.

3. **Implement Token Rotation**: Regularly rotate API tokens to minimize the impact of token leakage.

4. **Restrict Token Permissions**: Create tokens with the minimum required permissions.

5. **IP Restrictions**: Use the FortiGate's trusthost settings to restrict API access to specific IP addresses.

6. **Certificate Verification**: In production environments, always verify SSL certificates. Only disable verification in development or testing environments.

## Troubleshooting Authentication Issues

If you encounter authentication issues with the FortiGate API:

1. **Check Token Validity**: Ensure the token is valid and has not expired.

2. **Verify IP Restrictions**: Check if your client IP is allowed in the FortiGate's trusthost settings.

3. **Check Authentication Method**: Ensure you're using the Authorization header with Bearer token.

4. **Inspect SSL Certificate**: If you're getting SSL certificate errors, ensure the certificate is valid and properly configured.

5. **Check API User Permissions**: Ensure the API user has the necessary permissions for the requested endpoint.
