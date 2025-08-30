# FortiGate Topology Clone

A comprehensive application that scrapes FortiGate topology styling and recreates the Security Fabric interface using modern web technologies.

## Features

- **Headless Scraping**: Automated extraction of FortiGate topology styles using Playwright
- **Design Token Generation**: Convert scraped styles into reusable design tokens
- **Interactive Topology**: D3.js-based network visualization with grouping modes
- **FortiGate API Integration**: Real-time data from FortiOS REST APIs
- **Docker Support**: Containerized development and production environments
- **CLI Tools**: Command-line interface for scraping and token extraction

## Architecture

```
├── src/
│   ├── backend/           # Express.js API server
│   │   ├── routes/        # API routes
│   │   ├── services/      # FortiGate authentication & data services
│   │   ├── middleware/    # Express middleware
│   │   └── utils/         # Utilities and logging
│   ├── frontend/          # Frontend application
│   │   ├── components/    # UI components
│   │   ├── services/      # API client services
│   │   ├── utils/         # Frontend utilities
│   │   └── styles/        # CSS styles and design tokens
│   └── cli/               # Command-line tools
├── assets/                # Scraped assets storage
├── tokens/                # Extracted design tokens
├── docker-compose.yml     # Docker orchestration
└── nginx/                 # Reverse proxy configuration
```

## Quick Start

### Prerequisites

- Node.js 18+
- Docker & Docker Compose (optional)
- Access to a FortiGate device

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd fortigate-topology-clone
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your FortiGate credentials
   ```

3. **Start development**:
   ```bash
   npm run dev
   ```

### Docker Deployment

```bash
npm run docker:build
npm run docker:up
```

## CLI Usage

### Scrape FortiGate Topology

```bash
# Interactive scraping
npm run scrape

# With parameters
npm run scrape -- --host 192.168.1.1 --username admin --password secret

# Run as daemon (scheduled scraping)
npm run scrape -- daemon --interval 6
```

### Extract Design Tokens

```bash
# Extract tokens from scraped assets
npm run extract-tokens

# Generate in different formats
npm run extract-tokens -- --format css
npm run extract-tokens -- --format scss
npm run extract-tokens -- --format js
```

### Test Authentication

```bash
npm run scrape -- test-login --host 192.168.1.1
```

## API Endpoints

- `GET /api/topology` - Get topology data
- `GET /api/topology/devices` - Get device status
- `GET /api/assets/tokens` - Get design tokens
- `POST /api/auth/test` - Test FortiGate authentication

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FORTIGATE_HOST` | FortiGate IP/domain | - |
| `FORTIGATE_USERNAME` | Username | admin |
| `FORTIGATE_PASSWORD` | Password | - |
| `PORT` | Server port | 3000 |
| `NODE_ENV` | Environment | development |
| `BROWSER_HEADLESS` | Headless browser | true |

### Design Tokens

The system extracts and categorizes design tokens:

- **Colors**: Severity states, vendors, device states
- **Typography**: Font families, sizes, weights
- **Spacing**: Margins, paddings, gaps
- **Borders**: Widths, radii, styles
- **Shadows**: Box shadows, elevations
- **Animations**: Transitions, durations

## Development

### Project Structure

```
src/
├── backend/
│   ├── server.js              # Express server
│   ├── routes/
│   │   ├── topology.js        # Topology API routes
│   │   ├── auth.js            # Authentication routes
│   │   └── assets.js          # Asset/token routes
│   ├── services/
│   │   └── fortigate-auth.js  # FortiGate API client
│   ├── middleware/
│   │   ├── errorHandler.js    # Error handling
│   │   └── rateLimiter.js     # Rate limiting
│   └── utils/
│       └── logger.js          # Winston logging
├── frontend/
│   ├── app.js                 # Main application
│   ├── components/
│   │   └── TopologyVisualization.js  # D3 topology component
│   ├── services/
│   │   └── apiService.js      # API client
│   ├── utils/
│   │   └── tokenManager.js    # Design token manager
│   └── styles/
│       └── main.css           # Main stylesheet
└── cli/
    ├── scraper.js             # Scraping CLI
    └── token-extractor.js     # Token extraction CLI
```

### Available Scripts

```bash
npm run dev              # Start development servers
npm run build            # Build for production
npm run start            # Start production server
npm run scrape           # Run scraper CLI
npm run extract-tokens   # Run token extractor
npm run test             # Run tests
npm run lint             # Lint code
npm run docker:build     # Build Docker images
npm run docker:up        # Start Docker stack
npm run docker:down      # Stop Docker stack
```

### Adding New Features

1. **Backend Routes**: Add to `src/backend/routes/`
2. **Frontend Components**: Add to `src/frontend/components/`
3. **Services**: Add to respective `services/` directories
4. **CLI Commands**: Extend `src/cli/scraper.js` or create new CLI tools

## Security Considerations

- FortiGate credentials are stored in environment variables
- HTTPS enforcement for FortiGate communication
- Rate limiting on API endpoints
- CSP headers and security middleware
- Session-based authentication for scraping

## Legal Compliance

- Extracted design tokens are reverse-engineered for interface recreation
- No proprietary Fortinet assets are redistributed
- CSS/JS bundles are analyzed but not copied verbatim
- Complies with fair use for interoperability purposes

## Troubleshooting

### Common Issues

1. **Authentication Fails**
   - Verify FortiGate credentials in `.env`
   - Check network connectivity
   - Ensure FortiGate API access is enabled

2. **Scraping Timeouts**
   - Increase `BROWSER_TIMEOUT` in `.env`
   - Check FortiGate performance
   - Verify topology page loads manually

3. **Missing Design Tokens**
   - Run `npm run extract-tokens -- validate`
   - Check scraped assets in `assets/` directory
   - Review extraction logs

4. **Development Server Issues**
   - Clear cache: `rm -rf cache/`
   - Reinstall dependencies: `rm -rf node_modules && npm install`
   - Check port availability

### Logging

Logs are stored in `logs/` directory:
- `error.log` - Error messages
- `combined.log` - All log levels
- Console output in development mode

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Submit an issue with reproduction steps
4. Include environment details and FortiGate version