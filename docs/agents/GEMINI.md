# FortiGate Enterprise Dashboard

## Project Overview

This project is a comprehensive, enterprise-grade dashboard for visualizing and managing network infrastructure, primarily centered around Fortinet products (FortiGate, FortiSwitch, FortiAP). It is designed for a large-scale, multi-tenant environment, specifically for managing the network infrastructure of multiple restaurant brands (Sonic, Buffalo Wild Wings, Arby's), totaling nearly 6,000 locations and over 375,000 managed devices.

The application features a Python **FastAPI** backend that serves a rich REST API and a web frontend built with **Jinja2 templates** and **Bootstrap 5**. The architecture is containerized using **Docker** and orchestrated with **Docker Compose**. It employs a polyglot persistence model, using **PostgreSQL** for primary data, **Redis** for caching and session management, and **Neo4j** for graph-based network topology storage.

A key feature is its ability to handle hybrid network environments, integrating with both **FortiSwitch** and **Cisco Meraki** switches. The project also includes a suite of Node.js-based CLI tools for scraping UI styles and extracting design tokens from the FortiGate web interface to ensure visual consistency.

## Building and Running

The project is designed to be run using Docker and Docker Compose.

### Prerequisites

-   Docker and Docker Compose installed.
-   A `.env` file or environment variables set for credentials (see `docker-compose.yml`).
-   Secrets populated in the `./secrets` directory as per the `README.md`.

### Key Commands

-   **Build and Run All Services:**
    ```bash
    docker compose up --build -d
    ```

-   **View Application Logs:**
    ```bash
    docker compose logs -f fortigate-dashboard
    ```

-   **Stop All Services:**
    ```bash
    docker compose down
    ```

-   **Run Local Development Server (without Docker):**
    1.  Install Python dependencies: `pip install -r requirements.txt`
    2.  Run the server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

### Accessing the Application

-   **Main Dashboard:** [http://localhost:8000](http://localhost:8000) (or the NGINX port if using the full stack)
-   **Grafana:** [http://localhost:3000](http://localhost:3000)
-   **Prometheus:** [http://localhost:9090](http://localhost:9090)
-   **Neo4j Browser:** [http://localhost:7474](http://localhost:7474)

## Development Conventions

### Project Structure

-   **`app/`**: Contains the main FastAPI application.
    -   **`main.py`**: The main application entry point, defining routes and middleware.
    -   **`api/`**: Contains API router modules (e.g., `fortigate.py`).
    -   **`services/`**: The core business logic is encapsulated here. Each file represents a micro-service or a client for an external API (e.g., `fortigate_service.py`, `meraki_service.py`, `organization_service.py`).
    -   **`utils/`**: Holds helper functions and utilities (e.g., `icon_db.py`, `oui_lookup.py`).
    -   **`static/`**: For static assets like CSS, JavaScript, and images.
    -   **`templates/`**: Contains Jinja2 HTML templates for the frontend.
-   **`scripts/`**: Shell scripts for deployment and management tasks.
-   **`monitoring/`**: Configuration for Prometheus and Grafana.
-   **`secrets/`**: Holds sensitive information like API tokens and passwords (mounted into containers).
-   **`*.js` services**: The root of `app/services` also contains several Node.js-based CLI tools (`scraper.js`, `token-extractor.js`) for asset scraping and design token generation.

### Coding Style

-   **Python**: The backend follows a service-oriented architecture. Logic is separated into service modules that are imported into the `main.py` to serve API endpoints. It uses type hints extensively and follows modern FastAPI patterns.
-   **JavaScript**: The JavaScript tools are built as command-line applications using `commander` for the interface.

### Key Architectural Patterns

-   **Multi-Tenant Design**: The application is built from the ground up to support multiple organizations, with API endpoints often prefixed with an organization ID (e.g., `/api/v1/{organization_id}/...`).
-   **Hybrid Infrastructure Support**: The `hybrid_topology_service.py` and the presence of both `fortiswitch_service.py` and `meraki_service.py` indicate a key design goal is to abstract away the underlying switch vendor to present a unified topology.
-   **Data-Driven Device Identification**: The `restaurant_device_service.py` uses internal databases (OUI prefixes, hostname patterns) to intelligently classify devices, which is crucial for a restaurant environment with specialized hardware (POS, KDS, etc.).
-   **Containerization**: The entire stack, from the application to the databases and monitoring tools, is defined in `docker-compose.yml`, making it portable and easy to deploy.
