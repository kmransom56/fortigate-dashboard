#!/usr/bin/env node

const { Command } = require('commander');
const chalk = require('chalk');
const ora = require('ora');
const fs = require('fs-extra');
const path = require('path');
const css = require('css');
const postcss = require('postcss');
const logger = require('../utils/logger');

const program = new Command();

program
  .name('token-extractor')
  .description('Extract design tokens from scraped FortiGate assets')
  .version('1.0.0');

program
  .command('extract')
  .description('Extract design tokens from CSS assets')
  .option('-i, --input-dir <dir>', 'Input directory with scraped assets', './assets')
  .option('-o, --output-dir <dir>', 'Output directory for design tokens', './tokens')
  .option('--format <format>', 'Output format (json|css|scss|js)', 'json')
  .action(async (options) => {
    const spinner = ora('Extracting design tokens...').start();
    
    try {
      await extractTokens(options, spinner);
      spinner.succeed(chalk.green('Token extraction completed!'));
    } catch (error) {
      spinner.fail(chalk.red(`Token extraction failed: ${error.message}`));
      logger.error('Token extraction error:', error);
      process.exit(1);
    }
  });

program
  .command('validate')
  .description('Validate extracted design tokens')
  .option('-i, --input-dir <dir>', 'Directory with design tokens', './tokens')
  .action(async (options) => {
    const spinner = ora('Validating design tokens...').start();
    
    try {
      await validateTokens(options.inputDir, spinner);
      spinner.succeed(chalk.green('Token validation completed!'));
    } catch (error) {
      spinner.fail(chalk.red(`Token validation failed: ${error.message}`));
      process.exit(1);
    }
  });

async function extractTokens(options, spinner) {
  const inputDir = options.inputDir;
  const outputDir = options.outputDir;
  const format = options.format;
  
  await fs.ensureDir(outputDir);
  
  spinner.text = 'Scanning for CSS assets...';
  
  // Find all CSS files in assets directory
  const cssFiles = await findCssFiles(inputDir);
  
  if (cssFiles.length === 0) {
    throw new Error('No CSS files found in assets directory');
  }
  
  spinner.text = `Processing ${cssFiles.length} CSS files...`;
  
  const tokens = {
    colors: {},
    typography: {},
    spacing: {},
    borders: {},
    shadows: {},
    animations: {},
    breakpoints: {},
    components: {}
  };
  
  // Process each CSS file
  for (const cssFile of cssFiles) {
    const cssContent = await fs.readFile(cssFile, 'utf-8');
    const parsedCss = css.parse(cssContent);
    
    await extractFromCss(parsedCss, tokens);
  }
  
  // Process computed styles JSON files
  const computedStylesFiles = await findComputedStylesFiles(inputDir);
  
  for (const styleFile of computedStylesFiles) {
    const styles = await fs.readJson(styleFile);
    await extractFromComputedStyles(styles, tokens);
  }
  
  spinner.text = 'Generating token files...';
  
  // Generate output in requested format
  switch (format) {
    case 'json':
      await generateJsonTokens(tokens, outputDir);
      break;
    case 'css':
      await generateCssTokens(tokens, outputDir);
      break;
    case 'scss':
      await generateScssTokens(tokens, outputDir);
      break;
    case 'js':
      await generateJsTokens(tokens, outputDir);
      break;
    default:
      throw new Error(`Unsupported format: ${format}`);
  }
  
  // Generate token documentation
  await generateTokenDocs(tokens, outputDir);
}

async function findCssFiles(dir) {
  const files = [];
  const items = await fs.readdir(dir);
  
  for (const item of items) {
    const itemPath = path.join(dir, item);
    const stat = await fs.stat(itemPath);
    
    if (stat.isDirectory()) {
      const subFiles = await findCssFiles(itemPath);
      files.push(...subFiles);
    } else if (item.endsWith('.css')) {
      files.push(itemPath);
    }
  }
  
  return files;
}

async function findComputedStylesFiles(dir) {
  const files = [];
  const items = await fs.readdir(dir);
  
  for (const item of items) {
    const itemPath = path.join(dir, item);
    const stat = await fs.stat(itemPath);
    
    if (stat.isDirectory()) {
      const subFiles = await findComputedStylesFiles(itemPath);
      files.push(...subFiles);
    } else if (item === 'computed-styles.json') {
      files.push(itemPath);
    }
  }
  
  return files;
}

async function extractFromCss(parsedCss, tokens) {
  for (const rule of parsedCss.stylesheet.rules) {
    if (rule.type === 'rule') {
      for (const declaration of rule.declarations || []) {
        if (declaration.type === 'declaration') {
          await extractDeclaration(declaration, rule.selectors, tokens);
        }
      }
    } else if (rule.type === 'media') {
      // Extract breakpoints
      const media = rule.media;
      tokens.breakpoints[media] = media;
    }
  }
}

async function extractDeclaration(declaration, selectors, tokens) {
  const { property, value } = declaration;
  
  // Extract colors
  if (isColorProperty(property)) {
    const colorValue = extractColorValue(value);
    if (colorValue) {
      const colorName = generateColorName(property, selectors);
      tokens.colors[colorName] = colorValue;
    }
  }
  
  // Extract typography
  if (isTypographyProperty(property)) {
    const typographyName = generateTypographyName(property, selectors);
    tokens.typography[typographyName] = value;
  }
  
  // Extract spacing
  if (isSpacingProperty(property)) {
    const spacingName = generateSpacingName(property, selectors);
    tokens.spacing[spacingName] = value;
  }
  
  // Extract borders
  if (isBorderProperty(property)) {
    const borderName = generateBorderName(property, selectors);
    tokens.borders[borderName] = value;
  }
  
  // Extract shadows
  if (isShadowProperty(property)) {
    const shadowName = generateShadowName(property, selectors);
    tokens.shadows[shadowName] = value;
  }
  
  // Extract animations
  if (isAnimationProperty(property)) {
    const animationName = generateAnimationName(property, selectors);
    tokens.animations[animationName] = value;
  }
}

async function extractFromComputedStyles(styles, tokens) {
  // Extract from container styles
  if (styles.container) {
    extractComputedStyleObject(styles.container, 'container', tokens);
  }
  
  // Extract from node styles
  if (styles.nodes) {
    for (let i = 0; i < styles.nodes.length; i++) {
      const node = styles.nodes[i];
      extractComputedStyleObject(node.styles, `node-${i}`, tokens);
    }
  }
  
  // Extract from link styles
  if (styles.links) {
    for (let i = 0; i < styles.links.length; i++) {
      const link = styles.links[i];
      extractComputedStyleObject(link.styles, `link-${i}`, tokens);
    }
  }
}

function extractComputedStyleObject(styleObj, prefix, tokens) {
  for (const [property, value] of Object.entries(styleObj)) {
    if (isColorProperty(property)) {
      const colorValue = extractColorValue(value);
      if (colorValue) {
        tokens.colors[`${prefix}-${property}`] = colorValue;
      }
    }
    
    if (isTypographyProperty(property)) {
      tokens.typography[`${prefix}-${property}`] = value;
    }
    
    if (isSpacingProperty(property)) {
      tokens.spacing[`${prefix}-${property}`] = value;
    }
  }
}

function isColorProperty(property) {
  return ['color', 'background-color', 'border-color', 'fill', 'stroke'].includes(property);
}

function isTypographyProperty(property) {
  return ['font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing'].includes(property);
}

function isSpacingProperty(property) {
  return ['margin', 'padding', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
          'padding-top', 'padding-right', 'padding-bottom', 'padding-left'].includes(property);
}

function isBorderProperty(property) {
  return property.startsWith('border');
}

function isShadowProperty(property) {
  return ['box-shadow', 'text-shadow'].includes(property);
}

function isAnimationProperty(property) {
  return property.startsWith('animation') || property.startsWith('transition');
}

function extractColorValue(value) {
  // Extract hex, rgb, rgba, hsl values
  const colorRegex = /(#[0-9a-f]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|hsla\([^)]+\))/gi;
  const match = value.match(colorRegex);
  return match ? match[0] : null;
}

function generateColorName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

function generateTypographyName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

function generateSpacingName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

function generateBorderName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

function generateShadowName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

function generateAnimationName(property, selectors) {
  const selector = selectors[0] || 'unknown';
  const className = selector.replace(/[^a-zA-Z0-9]/g, '-');
  return `${className}-${property}`.replace(/--+/g, '-');
}

async function generateJsonTokens(tokens, outputDir) {
  await fs.writeJson(path.join(outputDir, 'tokens.json'), tokens, { spaces: 2 });
  
  // Generate separate files for each category
  for (const [category, values] of Object.entries(tokens)) {
    if (Object.keys(values).length > 0) {
      await fs.writeJson(path.join(outputDir, `${category}.json`), values, { spaces: 2 });
    }
  }
}

async function generateCssTokens(tokens, outputDir) {
  let cssContent = ':root {\n';
  
  for (const [category, values] of Object.entries(tokens)) {
    cssContent += `  /* ${category} */\n`;
    for (const [name, value] of Object.entries(values)) {
      cssContent += `  --${category}-${name}: ${value};\n`;
    }
    cssContent += '\n';
  }
  
  cssContent += '}\n';
  
  await fs.writeFile(path.join(outputDir, 'tokens.css'), cssContent);
}

async function generateScssTokens(tokens, outputDir) {
  let scssContent = '';
  
  for (const [category, values] of Object.entries(tokens)) {
    scssContent += `// ${category}\n`;
    for (const [name, value] of Object.entries(values)) {
      scssContent += `$${category}-${name}: ${value};\n`;
    }
    scssContent += '\n';
  }
  
  await fs.writeFile(path.join(outputDir, 'tokens.scss'), scssContent);
}

async function generateJsTokens(tokens, outputDir) {
  const jsContent = `export const tokens = ${JSON.stringify(tokens, null, 2)};

export default tokens;`;
  
  await fs.writeFile(path.join(outputDir, 'tokens.js'), jsContent);
}

async function generateTokenDocs(tokens, outputDir) {
  let markdownContent = '# FortiGate Design Tokens\n\n';
  markdownContent += 'Generated design tokens extracted from FortiGate topology interface.\n\n';
  
  for (const [category, values] of Object.entries(tokens)) {
    if (Object.keys(values).length > 0) {
      markdownContent += `## ${category.charAt(0).toUpperCase() + category.slice(1)}\n\n`;
      
      for (const [name, value] of Object.entries(values)) {
        markdownContent += `- **${name}**: \`${value}\`\n`;
      }
      
      markdownContent += '\n';
    }
  }
  
  await fs.writeFile(path.join(outputDir, 'README.md'), markdownContent);
}

async function validateTokens(inputDir, spinner) {
  spinner.text = 'Loading token files...';
  
  const tokenFiles = await fs.readdir(inputDir);
  const jsonFiles = tokenFiles.filter(file => file.endsWith('.json'));
  
  if (jsonFiles.length === 0) {
    throw new Error('No token files found');
  }
  
  spinner.text = 'Validating token structure...';
  
  for (const file of jsonFiles) {
    const filePath = path.join(inputDir, file);
    const tokens = await fs.readJson(filePath);
    
    // Validate structure
    validateTokenStructure(tokens, file);
  }
  
  spinner.text = 'Validation completed';
}

function validateTokenStructure(tokens, filename) {
  const requiredCategories = ['colors', 'typography', 'spacing'];
  
  for (const category of requiredCategories) {
    if (!tokens[category]) {
      console.warn(chalk.yellow(`Warning: ${filename} missing ${category} tokens`));
    }
  }
  
  // Validate color values
  if (tokens.colors) {
    for (const [name, value] of Object.entries(tokens.colors)) {
      if (!isValidColor(value)) {
        console.warn(chalk.yellow(`Warning: Invalid color value "${value}" for ${name}`));
      }
    }
  }
}

function isValidColor(value) {
  const colorRegex = /^(#[0-9a-f]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|hsla\([^)]+\))$/i;
  return colorRegex.test(value);
}

if (require.main === module) {
  program.parse();
}

module.exports = { extractTokens, validateTokens };