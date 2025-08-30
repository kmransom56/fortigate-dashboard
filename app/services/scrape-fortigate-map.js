const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Replace with your FortiGate login URL
  await page.goto('http://10.208.103.1:2456');

  // Replace with actual selectors for username and password fields
  await page.fill('#username', 'YOUR_USERNAME');
  await page.fill('#password', 'YOUR_PASSWORD');
  await page.click('#login');

  // Wait for navigation to the map display page
  // Replace with actual navigation or selector for the map display
  await page.waitForSelector('#mapDisplay');

  // Scrape the map display HTML (adjust selector as needed)
  const mapHtml = await page.$eval('#mapDisplay', el => el.outerHTML);

  // Print to console
  console.log(mapHtml);

  // Save to file
  fs.writeFileSync('scraped_map.html', mapHtml);

  await browser.close();
})();
