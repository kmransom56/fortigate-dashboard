#!/usr/bin/env node

const { Command } = require('commander');
const inquirer = require('inquirer');
const chalk = require('chalk');
const ora = require('ora');
const fs = require('fs-extra');
const path = require('path');
const { chromium } = require('playwright');
const FortiGateAuth = require('./fortigate-auth');
const logger = require('../utils/logger');

const program = new Command();

program
  .name('fortigate-scraper')
  .description('FortiGate topology scraper CLI')
  .version('1.0.0');

program
  .command('scrape')
  .description('Scrape FortiGate topology styling and data')
  .option('-h, --host <host>', 'FortiGate host IP/domain')
  .option('-u, --username <username>', 'FortiGate username')
  .option('-p, --password <password>', 'FortiGate password')
  .option('--headless [headless]', 'Run in headless mode', true)
  .option('--output-dir <dir>', 'Output directory for scraped assets', './assets')
  .option('--view <view>', 'Topology view to scrape (physical|logical|both)', 'both')
  .action(async (options) => {
    const spinner = ora('Initializing scraper...').start();
    
    try {
      const config = await getScrapingConfig(options);
      await performScraping(config, spinner);
    } catch (error) {
      spinner.fail(chalk.red(`Scraping failed: ${error.message}`));
      logger.error('Scraping error:', error);
      process.exit(1);
    }
  });

program
  .command('daemon')
  .description('Run scraper as a daemon with scheduled intervals')
  .option('--interval <hours>', 'Scraping interval in hours', '6')
  .action(async (options) => {
    console.log(chalk.blue('🤖 Starting FortiGate scraper daemon...'));
    
    const intervalMs = parseInt(options.interval) * 60 * 60 * 1000;
    
    // Initial scrape
    await runScrapingCycle();
    
    // Set up recurring scrapes
    setInterval(async () => {
      await runScrapingCycle();
    }, intervalMs);
    
    console.log(chalk.green(`✅ Daemon running with ${options.interval}h intervals`));
  });

program
  .command('test-login')
  .description('Test FortiGate authentication')
  .option('-h, --host <host>', 'FortiGate host IP/domain')
  .option('-u, --username <username>', 'FortiGate username')
  .option('-p, --password <password>', 'FortiGate password')
  .action(async (options) => {
    const spinner = ora('Testing authentication...').start();
    
    try {
      const config = await getAuthConfig(options);
      const auth = new FortiGateAuth(config);
      const isValid = await auth.testConnection();
      
      if (isValid) {
        spinner.succeed(chalk.green('Authentication successful!'));
      } else {
        spinner.fail(chalk.red('Authentication failed!'));
      }
    } catch (error) {
      spinner.fail(chalk.red(`Authentication error: ${error.message}`));
    }
  });

async function getScrapingConfig(options) {
  const questions = [];
  
  if (!options.host) {
    questions.push({
      type: 'input',
      name: 'host',
      message: 'Enter FortiGate host IP or domain:',
      validate: (input) => input.length > 0 || 'Host is required'
    });
  }
  
  if (!options.username) {
    questions.push({
      type: 'input',
      name: 'username',
      message: 'Enter FortiGate username:',
      validate: (input) => input.length > 0 || 'Username is required'
    });
  }
  
  if (!options.password) {
    questions.push({
      type: 'password',
      name: 'password',
      message: 'Enter FortiGate password:',
      validate: (input) => input.length > 0 || 'Password is required'
    });
  }
  
  const answers = await inquirer.prompt(questions);
  
  return {
    host: options.host || answers.host,
    username: options.username || answers.username,
    password: options.password || answers.password,
    headless: options.headless !== 'false',
    outputDir: options.outputDir,
    view: options.view
  };
}

async function getAuthConfig(options) {
  const questions = [];
  
  if (!options.host) {
    questions.push({
      type: 'input',
      name: 'host',
      message: 'Enter FortiGate host IP or domain:',
      validate: (input) => input.length > 0 || 'Host is required'
    });
  }
  
  if (!options.username) {
    questions.push({
      type: 'input',
      name: 'username',
      message: 'Enter FortiGate username:',
      validate: (input) => input.length > 0 || 'Username is required'
    });
  }
  
  if (!options.password) {
    questions.push({
      type: 'password',
      name: 'password',
      message: 'Enter FortiGate password:',
      validate: (input) => input.length > 0 || 'Password is required'
    });
  }
  
  const answers = await inquirer.prompt(questions);
  
  return {
    host: options.host || answers.host,
    username: options.username || answers.username,
    password: options.password || answers.password
  };
}

async function performScraping(config, spinner) {
  spinner.text = 'Launching browser...';
  
  const browser = await chromium.launch({
    headless: config.headless,
    args: ['--no-sandbox', '--disable-web-security']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  });
  
  const page = await context.newPage();
  
  try {
    // Enable CSS coverage
    await page.coverage.startCSS();
    await page.coverage.startJS();
    
    spinner.text = 'Authenticating to FortiGate...';
    
    // Navigate to FortiGate login
    const loginUrl = `https://${config.host}/login`;
    await page.goto(loginUrl, { waitUntil: 'networkidle' });
    
    // Perform login
    await page.fill('input[name="username"]', config.username);
    await page.fill('input[name="secretkey"]', config.password);
    await page.click('input[type="submit"]');
    
    // Wait for dashboard
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 30000 });
    
    spinner.text = 'Navigating to topology view...';
    
    // Navigate to Security Fabric > Topology
    await page.goto(`https://${config.host}/ng/security-fabric/topology`, { 
      waitUntil: 'networkidle' 
    });
    
    // Wait for topology to load
    await page.waitForSelector('.topology-container', { timeout: 30000 });
    
    spinner.text = 'Capturing topology styling...';
    
    if (config.view === 'both' || config.view === 'physical') {
      await captureTopologyView(page, 'physical', config.outputDir);
    }
    
    if (config.view === 'both' || config.view === 'logical') {
      // Switch to logical view
      await page.click('[data-view="logical"]');
      await page.waitForTimeout(2000);
      await captureTopologyView(page, 'logical', config.outputDir);
    }
    
    // Capture CSS and JS coverage
    const cssCoverage = await page.coverage.stopCSS();
    const jsCoverage = await page.coverage.stopJS();
    
    spinner.text = 'Saving captured assets...';
    
    await saveAssets(cssCoverage, jsCoverage, config.outputDir);
    
    spinner.succeed(chalk.green('Scraping completed successfully!'));
    
  } finally {
    await browser.close();
  }
}

async function captureTopologyView(page, viewType, outputDir) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const viewDir = path.join(outputDir, viewType, timestamp);
  
  await fs.ensureDir(viewDir);
  
  // Capture screenshot
  await page.screenshot({ 
    path: path.join(viewDir, 'screenshot.png'),
    fullPage: true
  });
  
  // Capture DOM snapshot
  const html = await page.content();
  await fs.writeFile(path.join(viewDir, 'dom-snapshot.html'), html);
  
  // Capture computed styles for key elements
  const computedStyles = await page.evaluate(() => {
    const styles = {};
    
    // Topology container
    const container = document.querySelector('.topology-container');
    if (container) {
      styles.container = window.getComputedStyle(container);
    }
    
    // Nodes
    const nodes = document.querySelectorAll('.topology-node');
    styles.nodes = Array.from(nodes).map(node => ({
      selector: node.className,
      styles: window.getComputedStyle(node)
    }));
    
    // Links
    const links = document.querySelectorAll('.topology-link');
    styles.links = Array.from(links).map(link => ({
      selector: link.className,
      styles: window.getComputedStyle(link)
    }));
    
    return styles;
  });
  
  await fs.writeJson(path.join(viewDir, 'computed-styles.json'), computedStyles, { spaces: 2 });
  
  // Capture network requests
  const requests = [];
  page.on('request', request => {
    requests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers()
    });
  });
  
  await fs.writeJson(path.join(viewDir, 'network-requests.json'), requests, { spaces: 2 });
}

async function saveAssets(cssCoverage, jsCoverage, outputDir) {
  const assetsDir = path.join(outputDir, 'assets');
  await fs.ensureDir(assetsDir);
  
  // Save CSS files
  for (const entry of cssCoverage) {
    if (entry.url.includes('.css')) {
      const filename = path.basename(entry.url);
      const filepath = path.join(assetsDir, filename);
      await fs.writeFile(filepath, entry.text);
    }
  }
  
  // Save JS files  
  for (const entry of jsCoverage) {
    if (entry.url.includes('.js')) {
      const filename = path.basename(entry.url);
      const filepath = path.join(assetsDir, filename);
      await fs.writeFile(filepath, entry.text);
    }
  }
  
  // Save coverage reports
  await fs.writeJson(path.join(assetsDir, 'css-coverage.json'), cssCoverage, { spaces: 2 });
  await fs.writeJson(path.join(assetsDir, 'js-coverage.json'), jsCoverage, { spaces: 2 });
}

async function runScrapingCycle() {
  const spinner = ora('Starting scheduled scraping cycle...').start();
  
  try {
    const config = {
      host: process.env.FORTIGATE_HOST,
      username: process.env.FORTIGATE_USERNAME,
      password: process.env.FORTIGATE_PASSWORD,
      headless: true,
      outputDir: './assets',
      view: 'both'
    };
    
    await performScraping(config, spinner);
    logger.info('Scheduled scraping cycle completed successfully');
  } catch (error) {
    spinner.fail(chalk.red(`Scheduled scraping failed: ${error.message}`));
    logger.error('Scheduled scraping error:', error);
  }
}

if (require.main === module) {
  program.parse();
}

module.exports = { performScraping, captureTopologyView };