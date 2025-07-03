# SSL Certificate Verification Guide for FortiGate Dashboard

## Current Issue

The FortiGate Dashboard is currently experiencing SSL certificate verification errors when connecting to the FortiGate API. The error message indicates that the certificate verification is failing because the Python SSL library cannot verify the certificate chain:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)
```

This happens because the certificate file (`fortigate.pem`) contains only the server certificate, but not the complete certificate chain including the issuer certificates.

## Temporary Solution

Our current temporary solution is to disable SSL verification in the service files:

```python
# MODIFIED: Always disable SSL verification for testing
logger.warning("SSL verification disabled for testing")
response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
```

While this works, it's not recommended for production environments as it bypasses security checks and makes the application vulnerable to man-in-the-middle attacks.

## Permanent Solutions

Here are several options for a permanent solution to the SSL certificate verification issue:

### Option 1: Obtain a Complete Certificate Chain

The most secure option is to obtain a complete certificate chain that includes both the server certificate and all intermediate certificates up to the root CA.

1. **Export the complete certificate chain from the FortiGate device**:
   - Log in to the FortiGate web interface
   - Go to System > Certificates
   - Find your certificate and export it with the full chain

2. **Save the complete chain to `app/certs/fortigate.pem`**

3. **Verify the certificate chain**:
   ```bash
   openssl verify -CAfile app/certs/fortigate.pem app/certs/fortigate.pem
   ```

### Option 2: Add the FortiGate CA Certificate to the Trust Store

If you can't get the complete certificate chain, you can add the FortiGate's CA certificate to your system's trust store:

1. **Extract the CA certificate from the FortiGate**:
   ```bash
   openssl s_client -connect 192.168.0.254:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > ca.pem
   ```

2. **Add the CA certificate to the system's trust store**:
   - For Debian/Ubuntu:
     ```bash
     sudo cp ca.pem /usr/local/share/ca-certificates/fortigate-ca.crt
     sudo update-ca-certificates
     ```
   - For RHEL/CentOS:
     ```bash
     sudo cp ca.pem /etc/pki/ca-trust/source/anchors/fortigate-ca.crt
     sudo update-ca-trust
     ```

3. **Update the Docker image to use the system's trust store**:
   ```dockerfile
# In deploy/Dockerfile

### Option 3: Create a Custom Certificate Bundle

You can create a custom certificate bundle that includes both the FortiGate certificate and the CA certificates:

1. **Create a custom bundle**:
   ```bash
   cat app/certs/fortigate.pem /etc/ssl/certs/ca-certificates.crt > app/certs/custom-bundle.pem
   ```

2. **Update the code to use the custom bundle**:
   ```python
   CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH', '/app/certs/custom-bundle.pem')
   ```

### Option 4: Use certifi with Custom Certificates

The `certifi` package provides Mozilla's CA bundle, and you can extend it with your custom certificates:

1. **Install certifi**:
   ```bash
   pip install certifi
   ```

2. **Update the code to use certifi with your custom certificate**:
   ```python
   import certifi
   import os
   
   # Create a temporary file with both certifi's CA bundle and your certificate
   def get_cert_path():
       cafile = certifi.where()
       with open(cafile, 'rb') as certifi_file:
           certifi_content = certifi_file.read()
       
       with open('/app/certs/fortigate.pem', 'rb') as custom_cert_file:
           custom_cert_content = custom_cert_file.read()
       
       # Create a temporary file with both
       import tempfile
       temp_cert = tempfile.NamedTemporaryFile(delete=False)
       temp_cert.write(certifi_content + b'\n' + custom_cert_content)
       temp_cert.close()
       
       return temp_cert.name
   
   # Use the combined certificate file
   CERT_PATH = get_cert_path()
   ```

## Recommended Approach

For a production environment, I recommend **Option 1: Obtain a Complete Certificate Chain** as it's the most secure and straightforward approach. This ensures that your application can properly verify the FortiGate's certificate without compromising security.

If Option 1 is not feasible, **Option 2: Add the FortiGate CA Certificate to the Trust Store** is a good alternative, especially if you're managing the server where the application is running.

## Implementation Steps

1. **Obtain the complete certificate chain** from your FortiGate device or network administrator.

2. **Replace the current certificate file** at `app/certs/fortigate.pem` with the complete chain.

3. **Modify the service files** to re-enable SSL verification:
   ```python
   # Use the certificate for verification
   if CERT_PATH and os.path.exists(CERT_PATH):
       logger.info(f"Using certificate file for SSL verification: {CERT_PATH}")
       response = requests.get(url, headers=headers, params=params, verify=CERT_PATH, timeout=10)
       logger.info("Request with certificate verification successful")
   else:
       logger.warning(f"Certificate file not found at {CERT_PATH}, disabling SSL verification")
       response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
   ```

4. **Test the application** to ensure that SSL verification works correctly with the complete certificate chain.

By implementing one of these solutions, you'll have a secure and reliable way to connect to the FortiGate API without SSL certificate verification errors.