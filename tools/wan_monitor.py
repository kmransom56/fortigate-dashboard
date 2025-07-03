import time
import smtplib
import ssl
import requests

# FortiGate API details
FORTIGATE_HOST = 'https://your-fortigate-ip'
API_TOKEN = 'your-api-token'

# Email settings
SMTP_SERVER = 'smtp.yourprovider.com'
SMTP_PORT = 587
EMAIL_FROM = 'your-email@example.com'
EMAIL_TO = 'recipient@example.com'
EMAIL_PASSWORD = 'your-email-password'

def send_email_alert(subject, body):
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(EMAIL_FROM, EMAIL_TO, message)

def check_wan():
    headers = {
        'Authorization': f'Bearer {API_TOKEN}'
    }
    try:
        response = requests.get(f"{FORTIGATE_HOST}/api/v2/monitor/system/interface", headers=headers, verify=False)
        interfaces = response.json()['results']
        wan_links = [iface for iface in interfaces if iface['name'] in ['wan1', 'wan2']]

        for wan in wan_links:
            if not wan['link']:
                print(f"[ALERT] {wan['name']} is DOWN!")
                send_email_alert(
                    f"WAN DOWN ALERT: {wan['name']}",
                    f"The WAN interface {wan['name']} is DOWN at FortiGate."
                )
    except Exception as e:
        print(f"Error checking WAN links: {e}")

if __name__ == "__main__":
    while True:
        check_wan()
        time.sleep(60)  # Check every 60 seconds
