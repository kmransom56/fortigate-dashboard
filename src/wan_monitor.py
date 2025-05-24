import time
import smtplib
import ssl
import requests
import os
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# FortiGate API details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')
API_TOKEN = os.environ.get('API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

# Email settings
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.yourprovider.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'your-email@example.com')
EMAIL_TO = os.environ.get('EMAIL_TO', 'recipient@example.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-email-password')

def send_email_alert(subject, body):
    """Send an email alert when a WAN link goes down."""
    print(f"Sending email alert: {subject}")
    
    # Only send email if SMTP settings are configured
    if SMTP_SERVER != 'smtp.yourprovider.com':
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(EMAIL_FROM, EMAIL_TO, message)
            print("Email sent successfully")
    else:
        print("Email not sent - using default SMTP settings")

def check_wan():
    """Check the status of WAN interfaces and send alerts if they're down."""
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {API_TOKEN}'
    }
    
    print(f"Checking WAN links at {FORTIGATE_HOST}")
    
    try:
        # Use the correct authentication method (Authorization header with Bearer token)
        response = requests.get(
            f"{FORTIGATE_HOST}/api/v2/monitor/system/interface", 
            headers=headers, 
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'results' in data:
                interfaces = data['results']
                wan_links = [iface for name, iface in interfaces.items() if name.startswith('wan')]
                
                print(f"Found {len(wan_links)} WAN interfaces")
                
                for wan in wan_links:
                    status = "UP" if wan.get('link', False) else "DOWN"
                    print(f"WAN interface {wan.get('name', 'unknown')}: {status}")
                    
                    if not wan.get('link', False):
                        print(f"[ALERT] {wan.get('name', 'unknown')} is DOWN!")
                        send_email_alert(
                            f"WAN DOWN ALERT: {wan.get('name', 'unknown')}",
                            f"The WAN interface {wan.get('name', 'unknown')} is DOWN at FortiGate."
                        )
            else:
                print(f"Unexpected response format: {data}")
        else:
            print(f"Error checking WAN links: HTTP {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error checking WAN links: {e}")

if __name__ == "__main__":
    print("Starting FortiGate WAN Monitor")
    print(f"FortiGate Host: {FORTIGATE_HOST}")
    print(f"API Token: {API_TOKEN[:5]}...{API_TOKEN[-5:]}")
    
    # Initial check
    check_wan()
    
    # Continuous monitoring
    while True:
        time.sleep(60)  # Check every 60 seconds
        check_wan()