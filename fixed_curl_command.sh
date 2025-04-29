#!/bin/bash

# Fixed curl command using Authorization header instead of query parameter
curl --cacert app/certs/fortigate.pem \
  -X 'GET' \
  'https://192.168.0.254:443/api/v2/monitor/system/interface' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N'

# If you continue to have SSL certificate issues, you can use the -k flag to disable verification
# (not recommended for production use)
# curl -k -X 'GET' 'https://192.168.0.254:443/api/v2/monitor/system/interface' -H 'accept: application/json' -H 'Authorization: Bearer hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N'