# scraper.js

## Purpose
`scraper.js` is a powerful, command-line interface (CLI) tool built with Node.js. Its primary purpose is to automate the process of scraping detailed styling and structural data from a FortiGate's web UI, specifically the "Security Fabric > Topology" pages. It uses the Playwright library to perform sophisticated browser automation, capturing not just HTML, but also screenshots, computed CSS styles, and even the CSS/JS files themselves. It is designed to be run either as a one-time command or as a continuous daemon for periodic scraping.

## Dependencies
- **`commander`**: To create a professional, option-rich CLI structure.
- **`inquirer`**: To interactively prompt the user for credentials if they are not provided as command-line arguments.
- **`chalk`**: For adding color and styling to the console output, improving readability.
- **`ora`**: To display spinners in the terminal, providing feedback during long-running operations.
- **`fs-extra`**: An enhanced version of the Node.js file system module, used for creating directories and writing files.
- **`path`**: A built-in Node.js module for working with file and directory paths.
- **`playwright`**: The core library for browser automation.
- **`./fortigate-auth`**: A local module used by the `test-login` command to verify credentials.
- **`../utils/logger`**: A local utility for logging.

## API (CLI Commands)
This script is a CLI tool and is invoked from the terminal. It provides the following commands:

- **`scrape`**: This is the main command. It launches a headless browser, logs into the FortiGate UI, navigates to the topology page, and systematically captures assets for both the "physical" and "logical" views.
  - **Options**: `--host`, `--username`, `--password`, `--headless`, `--output-dir`, `--view`.

- **`daemon`**: This command runs the scraper in a continuous loop, performing a new scrape at a scheduled interval (e.g., every 6 hours). It is intended for automated, periodic data collection.
  - **Options**: `--interval`.

- **`test-login`**: A utility command that allows a user to quickly check if their FortiGate credentials are valid without performing a full scrape.

## Configuration
The tool can be configured in multiple ways:
1.  **Command-line options**: Passing arguments like `--host <ip>` directly when running the `scrape` command.
2.  **Interactive prompts**: If required options (like host or username) are omitted, the tool will use `inquirer` to prompt the user to enter them.
3.  **Environment variables**: The `daemon` command relies on environment variables (`FORTIGATE_HOST`, `FORTIGATE_USERNAME`, `FORTIGATE_PASSWORD`) for its configuration.

## Data Flow
The typical data flow for the `scrape` command is as follows:
1.  The script parses command-line arguments or prompts the user for configuration.
2.  It launches a Playwright-controlled Chromium browser.
3.  It navigates to the FortiGate login page and submits the credentials.
4.  After a successful login, it navigates directly to the "Security Fabric > Topology" page.
5.  It waits for the topology container element to be visible.
6.  It calls the `captureTopologyView` function for the "physical" view. This function:
    -   Takes a full-page screenshot (`screenshot.png`).
    -   Saves the complete DOM structure (`dom-snapshot.html`).
    -   Evaluates JavaScript in the browser to get the computed CSS styles for key elements (`computed-styles.json`).
    -   Captures a log of network requests (`network-requests.json`).
7.  It then programmatically clicks the button to switch to the "logical" view and repeats the capture process.
8.  Finally, it uses Playwright's coverage tools to save the relevant CSS and JavaScript files that were used to render the page.
9.  All captured assets are saved to a structured directory under the specified output directory.

## Error Handling
- The main scraping logic is wrapped in a `try...finally` block to ensure that the browser instance is always closed, even if an error occurs.
- It uses `ora` spinners to provide clear feedback to the user, indicating success or failure of the operation.
- The Playwright operations have timeouts, which prevent the script from hanging indefinitely if a page or element doesn't load.

## Testing
This file does not contain its own unit tests. Testing this CLI tool would be complex and would likely involve a combination of:
- Unit tests for individual helper functions.
- Integration tests that run the scraper against a mock HTTP server that simulates the FortiGate UI, or against a live, dedicated test device.
