<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I am looking for reusable code that when building web applications behind zscaler cert inspection, I can have my application not fail on ssl certificate errors. I am sure many others have faced and solved the issue

Based on my extensive research on Zscaler certificate inspection and SSL bypass solutions for web applications, I can provide you with comprehensive reusable code patterns and solutions that many developers have successfully implemented to handle SSL certificate errors in corporate environments.

# Reusable SSL Bypass Solutions for Web Applications Behind Zscaler

When developing web applications behind Zscaler certificate inspection, SSL verification failures are a common challenge. Here are proven, reusable code patterns organized by technology stack:

## Node.js/JavaScript Solutions

### Environment Variable Approach

```javascript
// Global SSL bypass - set at application startup
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
```


### Axios Configuration

```javascript
const https = require('https');
const axios = require('axios');

// Create reusable agent
const agent = new https.Agent({
  rejectUnauthorized: false
});

// At instance level (recommended for reusability)
const instance = axios.create({
  httpsAgent: agent
});

// At request level
axios.get('https://api.example.com', { httpsAgent: agent });
```


### Express.js Middleware Pattern

```javascript
const https = require('https');

// Reusable middleware for corporate environments
const corporateSSLConfig = (req, res, next) => {
  if (process.env.NODE_ENV === 'corporate' || process.env.ZSCALER_BYPASS === 'true') {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
  }
  next();
};

app.use(corporateSSLConfig);
```


## Python Solutions

### Requests Library Pattern

```python
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global session configuration
session = requests.Session()
session.verify = False

# Environment-based configuration
import os

class SSLConfig:
    @staticmethod
    def get_verify_setting():
        return os.getenv('CORPORATE_ENV', 'false').lower() != 'true'
    
    @staticmethod
    def make_request(url, **kwargs):
        kwargs['verify'] = SSLConfig.get_verify_setting()
        return requests.get(url, **kwargs)
```


### Certificate Path Solution

```python
import os
import requests

# Using corporate certificate
cert_path = os.getenv('ZSCALER_CERT_PATH', '/path/to/zscaler-root-ca.crt')

def corporate_request(url, **kwargs):
    try:
        # First try with corporate cert
        return requests.get(url, verify=cert_path, **kwargs)
    except requests.exceptions.SSLError:
        # Fallback to no verification in dev/test
        if os.getenv('ENV') in ['dev', 'test']:
            return requests.get(url, verify=False, **kwargs)
        raise
```


## Java Solutions

### Trust All Certificates Pattern

```java
import javax.net.ssl.*;
import java.security.cert.X509Certificate;

public class SSLConfig {
    
    public static void disableSSLVerification() {
        try {
            TrustManager[] trustAllCerts = new TrustManager[]{
                new X509TrustManager() {
                    public X509Certificate[] getAcceptedIssuers() { return null; }
                    public void checkClientTrusted(X509Certificate[] certs, String authType) {}
                    public void checkServerTrusted(X509Certificate[] certs, String authType) {}
                }
            };
            
            SSLContext sc = SSLContext.getInstance("SSL");
            sc.init(null, trustAllCerts, new java.security.SecureRandom());
            HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
            
            HostnameVerifier validHosts = (hostname, session) -> true;
            HttpsURLConnection.setDefaultHostnameVerifier(validHosts);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```


### Spring Boot Configuration

```java
@Configuration
@Profile("corporate")
public class CorporateSSLConfig {
    
    @Bean
    public RestTemplate restTemplate() throws Exception {
        TrustStrategy acceptingTrustStrategy = (X509Certificate[] chain, String authType) -> true;
        
        SSLContext sslContext = SSLContexts.custom()
                .loadTrustMaterial(null, acceptingTrustStrategy)
                .build();
                
        SSLConnectionSocketFactory csf = new SSLConnectionSocketFactory(sslContext);
        
        CloseableHttpClient httpClient = HttpClients.custom()
                .setSSLSocketFactory(csf)
                .build();
                
        HttpComponentsClientHttpRequestFactory requestFactory = 
                new HttpComponentsClientHttpRequestFactory();
        requestFactory.setHttpClient(httpClient);
        
        return new RestTemplate(requestFactory);
    }
}
```


## Universal Environment Variable Solutions

### Cross-Language Environment Variables

```bash
# Add to .env file or system environment
NODE_TLS_REJECT_UNAUTHORIZED=0
SSL_VERIFY=false
PYTHONHTTPSVERIFY=0
REQUESTS_CA_BUNDLE=/path/to/zscaler-root-ca.crt
```


### Docker Configuration

```dockerfile
# In Dockerfile for corporate deployments
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
ENV SSL_VERIFY=false
ENV PYTHONHTTPSVERIFY=0
COPY zscaler-root-ca.crt /usr/local/share/ca-certificates/
```


## Configuration Management Pattern

### Environment-Based Configuration Class

```javascript
class CorporateConfig {
  static isCorpEnvironment() {
    return process.env.CORPORATE_NETWORK === 'true' || 
           process.env.ZSCALER_ENABLED === 'true';
  }
  
  static getHttpsAgent() {
    if (this.isCorpEnvironment()) {
      const https = require('https');
      return new https.Agent({
        rejectUnauthorized: false
      });
    }
    return undefined; // Use default agent
  }
  
  static getRequestConfig() {
    return {
      httpsAgent: this.getHttpsAgent(),
      timeout: this.isCorpEnvironment() ? 30000 : 10000
    };
  }
}

// Usage
const config = CorporateConfig.getRequestConfig();
axios.get('https://api.example.com', config);
```


## Git and Package Manager Solutions

### Git Configuration

```bash
# Disable SSL verification for specific repos
git config http.sslVerify false

# For corporate environments
git config --global http.proxy http://proxy.company.com:8080
git config --global http.sslVerify false
git config --global http.sslBackend schannel  # Windows
```


### NPM Configuration

```bash
npm config set strict-ssl false
npm config set registry https://registry.npmjs.org/
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080
```


## Production-Ready Implementation

### Feature Flag Approach

```python
import os
from functools import wraps

def ssl_context_manager(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we're in corporate environment
        if os.getenv('DEPLOYMENT_ENV') == 'corporate':
            kwargs['verify'] = False
            # Suppress warnings in corporate env
            import urllib3
            urllib3.disable_warnings()
        return func(*args, **kwargs)
    return wrapper

@ssl_context_manager
def make_api_request(url, **kwargs):
    return requests.get(url, **kwargs)
```


## Key Recommendations

### Security Best Practices

1. **Environment-based configuration**: Only disable SSL verification in known corporate environments[^1_1][^1_2]
2. **Certificate installation**: Prefer installing Zscaler root certificates when possible[^1_3][^1_4]
3. **Logging**: Always log when SSL verification is bypassed[^1_5]
4. **Conditional application**: Use feature flags or environment variables to control SSL bypass[^1_6]

### Certificate Management Solution

```bash
# Set environment variable to point to corporate cert bundle
export SSL_CERT_FILE=/path/to/zscaler-root-ca.crt
export REQUESTS_CA_BUNDLE=/path/to/zscaler-root-ca.crt
```

These solutions have been successfully implemented by many development teams working behind Zscaler and similar corporate proxies. The key is to make SSL bypass conditional and environment-aware, ensuring security isn't compromised in production while enabling development productivity in corporate networks.[^1_7][^1_8]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_9]</span>

<div style="text-align: center">⁂</div>

[^1_1]: https://learn.microsoft.com/en-us/answers/questions/2278301/ssl-certificate-issue-while-using-azure-ai-search

[^1_2]: https://dev.to/elphynomenon/resolving-ssl-certificate-issues-with-zscaler-4hba

[^1_3]: https://stackoverflow.com/questions/10667960/python-requests-throwing-sslerror

[^1_4]: https://discuss.python.org/t/python-3-13-x-ssl-security-changes/91266

[^1_5]: https://scrapingant.com/blog/requests-ignore-ssl

[^1_6]: https://hayageek.com/disable-ssl-verification-in-node-js/

[^1_7]: https://www.zscaler.com/blogs/product-insights/ssl-inspection-developer-environments-unlock-advanced-threat-protection

[^1_8]: https://www.reddit.com/r/Zscaler/comments/1g6gl6l/zscaler_for_engineering_heavy_organisations/

[^1_9]: https://proxidize.com/blog/curl-ignore-ssl/

[^1_10]: https://www.reddit.com/r/Zscaler/comments/1d3kk1f/ssl_inspection_more_trouble_than_its_worth/

[^1_11]: https://github.com/orgs/community/discussions/8866

[^1_12]: https://www.namehero.com/blog/how-to-ignore-invalid-and-self-signed-ssl-errors-with-curl/

[^1_13]: https://help.zscaler.com/zia/certificate-pinning-and-ssl-inspection

[^1_14]: https://www.reddit.com/r/Zscaler/comments/1cm6p7t/executable_download_from_site_which_was_ssl/

[^1_15]: https://stackoverflow.com/questions/62723045/web-traffic-behind-corporate-firewall

[^1_16]: https://community.zscaler.com/s/question/0D54u0000ASQTuBCQX/failed-client-ssl-handshake

[^1_17]: https://stackoverflow.com/questions/63180813/curl-60-ssl-certificate-problem-when-uploading-behind-proxy

[^1_18]: https://stackoverflow.com/questions/54903199/how-to-ignore-ssl-certificate-validation-in-node-requests/54903835

[^1_19]: https://stackoverflow.com/questions/4663147/is-there-a-java-setting-for-disabling-certificate-validation

[^1_20]: https://dev.to/hardy_mervana/step-by-step-guide-to-fixing-nodejs-ssl-certificate-errors-2il2

[^1_21]: https://discuss.gradle.org/t/disable-ssl-cert-validation/24092

[^1_22]: https://stackoverflow.com/questions/10888610/ignore-invalid-self-signed-ssl-certificate-in-node-js-with-https-request

[^1_23]: https://www.geeksforgeeks.org/python/how-to-disable-security-certificate-checks-for-requests-in-python/

[^1_24]: https://www.digitalocean.com/community/tutorials/ssl-verification

[^1_25]: https://github.com/axios/axios/issues/535

[^1_26]: https://www.dsebastien.net/2020-06-06-how-to-access-the-web-from-tools-and-terminals-in-corporate-environments/

[^1_27]: https://www.cyberark.com/resources/threat-research-blog/how-to-bypass-golang-ssl-verification

[^1_28]: https://support.atlassian.com/jira/kb/bypass-a-proxy-or-ssl-to-test-network-connectivity-for-jira-server-and-data-center/

[^1_29]: https://support.atlassian.com/atlassian-knowledge-base/kb/data-center-how-to-bypass-a-reverse-proxy-or-ssl-in-application-links/

[^1_30]: https://docs.conda.io/projects/conda/en/stable/user-guide/configuration/disable-ssl-verification.html

[^1_31]: https://knowledge.broadcom.com/external/article/166297/how-to-bypass-ssl-based-on-server-certif.html

[^1_32]: https://en.wikipedia.org/wiki/Transport_Layer_Security

[^1_33]: https://lowendtalk.com/discussion/55755/ssl-injection-by-corporate-proxy

[^1_34]: https://stackoverflow.com/questions/36506539/how-do-i-get-visual-studio-code-to-trust-our-self-signed-proxy-certificate

[^1_35]: https://stackoverflow.com/questions/16538372/git-proxy-bypass

[^1_36]: https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-admin/certificate-management/set-up-verification-for-certificate-revocation-status/configure-revocation-status-verification-of-certificates-used-for-ssltls-decryption

[^1_37]: https://scrapingant.com/blog/curl-ignore-ssl

[^1_38]: https://github.com/rust-lang/cargo/issues/636

[^1_39]: https://www.reddit.com/r/msp/comments/14qb7ck/ssl_inspection_is_it_worth_it/

[^1_40]: https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/disable-universal-ssl/

[^1_41]: https://github.com/sonertari/SSLproxy

[^1_42]: https://stackoverflow.com/questions/57327608/ssl-certificate-problem-self-signed-certificate-in-certificate-chain

[^1_43]: https://support.hostinger.com/en/articles/6299503-troubleshooting-cloudflare-universal-ssl

[^1_44]: https://github.com/nodejs/corepack/issues/417

[^1_45]: https://docs.fortinet.com/document/fortigate/6.4.5/administration-guide/505842/certificate-inspection

