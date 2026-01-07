network-device-mcp-server/
├── .github/
│   └── workflows/
│       └── deploy-mcp-server.yml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py (GitHub secrets integrated)
│   └── platforms/
│       ├── __init__.py
│       ├── fortigate.py
│       ├── fortimanager.py
│       └── meraki.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
└── scripts/
    ├── setup-secrets.py
    └── validate-config.py