import requests
import json
import ipaddress

SERIALS = <Serial>

STORE_NUMBER = "<Store number>"
START_IP = ipaddress.IPv4Address("<Starting IP address>")
GATEWAY = format(START_IP)
ADDRESS = "<Address>"

count = 1

for SERIAL in SERIALS:

    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Cisco-Meraki-API-Key': '<API Key>'
    }

    url = f"https://api.meraki.com/api/v1/devices/{SERIAL}"
 
    payload = json.dumps({
    "name": STORE_NUMBER + "-" + "AP" + str(count).zfill(2),
    "address": str(ADDRESS)
    })
 
    response = requests.request("PUT", url, headers=headers, data=payload)

    payload = json.dumps({
    "wan1": {
    "usingStaticIp": "true",
    "staticIp": format(START_IP + count),
    "staticGatewayIp": str(GATEWAY),
    "staticSubnetMask": "255.255.255.0",
    "staticDns": [
      "10.244.89.15",
      "10.241.89.15"
    ]}
  })
 
    url = f"https://api.meraki.com/api/v1/devices/{SERIAL}/managementInterface"

    response = requests.request("PUT", url, headers=headers, data=payload)

    count += 1
    print(response.text)
-
