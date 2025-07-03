# certgen.ps1
$certDir = ".\app\certs"
New-Item -ItemType Directory -Force -Path $certDir | Out-Null

# Generate cert and key
openssl req -x509 -newkey rsa:4096 -keyout "$certDir\key.pem" -out "$certDir\cert.pem" -days 365 -nodes -subj "/CN=aicodestudio.netintegrate.net/O=Net Integrate"

# Create SAN config
$sanConfig = @"
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = aicodestudio.netintegrate.net
O = Net Integrate

[v3_req]
subjectAltName = @alt_names

[alt_names]
IP.1 = 192.168.0.2
DNS.1 = aicodestudio.netintegrate.net
"@
$sanConfigPath = "$certDir\openssl-san.cnf"
$sanConfig | Set-Content -Path $sanConfigPath

# Regenerate cert with SAN
openssl req -x509 -newkey rsa:4096 -keyout "$certDir\key.pem" -out "$certDir\cert.pem" -days 365 -nodes -config $sanConfigPath -extensions v3_req

# Convert to PFX
openssl pkcs12 -export -out "$certDir\cert.pfx" -inkey "$certDir\key.pem" -in "$certDir\cert.pem" -name "NetIntegrateCert"