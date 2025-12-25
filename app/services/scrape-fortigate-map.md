# scrape-fortigate-map.js

## Purpose
`scrape-fortigate-map.js` is a simple, standalone Node.js script that uses the Playwright automation library to perform a specific web scraping task. Its goal is to programmatically log into a FortiGate's web UI, navigate to a page containing a network map, and extract the HTML content of that map. The scraped HTML is then saved to a local file. This script appears to be a prototype or a simple tool for capturing a specific piece of UI content.

## Dependencies
- **`playwright`**: The core browser automation library used to launch a browser, control the page, and interact with elements.
- **`fs`**: The built-in Node.js File System module, used here to write the scraped HTML content to a file.

## API
This script is not a module and does not export any functions. It is designed to be executed directly from the command line (e.g., `node app/services/scrape-fortigate-map.js`). It is wrapped in an Immediately Invoked Function Expression (IIFE) `(async () => { ... })();`, so it runs as soon as the file is executed.

## Configuration
All configuration for this script is **hardcoded** directly within the file:
- **Login URL**: `http://10.208.103.1:2456`
- **Username**: `'YOUR_USERNAME'` (placeholder)
- **Password**: `'YOUR_PASSWORD'` (placeholder)
- **Page Selectors**: `'#username'`, `'#password'`, `'#login'`, `'#mapDisplay'`
- **Output File**: `'scraped_map.html'`

To use this script, a developer would need to manually edit these values.

## Data Flow
The script executes the following steps in sequence:
1.  It launches a new Chromium browser instance using Playwright.
2.  It opens a new page and navigates to the hardcoded FortiGate login URL.
3.  It fills the username and password fields with the hardcoded credentials.
4.  It clicks the login button.
5.  It waits for an element with the ID `#mapDisplay` to become available on the page, which presumably contains the network map.
6.  It extracts the full `outerHTML` of the `#mapDisplay` element.
7.  The scraped HTML is printed to the console.
8.  The same HTML is written to a file named `scraped_map.html` in the current working directory.
9.  Finally, the browser is closed.

## Error Handling
The script lacks any explicit error handling. If the login fails, a selector is not found, or the page doesn't load, the Playwright functions will throw an error (usually after a timeout period), and the script will crash.

## Testing
This script does not contain any automated tests. It would be tested manually by running it against a live, accessible FortiGate device and verifying that the `scraped_map.html` file is created with the expected content.
