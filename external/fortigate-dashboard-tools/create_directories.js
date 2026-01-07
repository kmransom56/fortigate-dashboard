#!/usr/bin/env node
/**
 * Create directory structure from markdown file
 * TypeScript/Node.js version
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { program } from 'commander';

interface ParsedStructure {
  directories: string[];
  files: string[];
}

async function parseTreeStructure(content: string): Promise<ParsedStructure> {
  const directories: string[] = [];
  const files: string[] = [];
  const lines = content.split('\n');
  const pathStack: string[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    // Remove tree characters and get the item name
    const cleaned = line.replace(/^[│├└─\s]*/, '').trim();
    if (!cleaned) continue;

    // Count indentation level
    const indentMatch = line.match(/^(\s*[│├└─\s]*)/);
    const indentLevel = indentMatch 
      ? Math.floor(indentMatch[1].replace(/[│├└─]/g, '').length / 4)
      : 0;

    // Adjust path stack to current level
    pathStack.splice(indentLevel);

    // Build full path
    const fullPath = pathStack.length > 0 
      ? [...pathStack, cleaned].join('/')
      : cleaned;

    // Determine if it's a file or directory
    if (cleaned.includes('.') && !cleaned.startsWith('.')) {
      files.push(fullPath);
    } else {
      directories.push(fullPath);
      pathStack.push(cleaned);
    }
  }

  return { directories, files };
}

async function parseListStructure(content: string): Promise<ParsedStructure> {
  const directories: Set<string> = new Set();
  const files: string[] = [];
  const lines = content.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.match(/^[-*+]\s/)) continue;

    // Remove list marker and clean path
    const itemPath = trimmed.replace(/^[-*+]\s*/, '').trim().replace(/^\/+/, '');
    if (!itemPath) continue;

    // Determine if it's a file or directory
    const basename = path.basename(itemPath);
    if (basename.includes('.') && !itemPath.endsWith('/')) {
      files.push(itemPath);
      // Add parent directories
      const parentDir = path.dirname(itemPath);
      if (parentDir && parentDir !== '.') {
        directories.add(parentDir);
      }
    } else {
      const cleanPath = itemPath.replace(/\/$/, '');
      if (cleanPath) {
        directories.add(cleanPath);
      }
    }
  }

  return { directories: Array.from(directories), files };
}

async function createStructure(
  basePath: string, 
  directories: string[], 
  files: string[], 
  dryRun: boolean = false
): Promise<void> {
  if (dryRun) {
    console.log(`DRY RUN - Would create structure in: ${path.resolve(basePath)}`);
    console.log('\nDirectories:');
    directories.sort().forEach(dir => console.log(`  📁 ${dir}`));
    console.log('\nFiles:');
    files.sort().forEach(file => console.log(`  📄 ${file}`));
    return;
  }

  // Create base directory
  await fs.mkdir(basePath, { recursive: true });

  // Create directories
  for (const directory of directories) {
    const dirPath = path.join(basePath, directory);
    await fs.mkdir(dirPath, { recursive: true });
    console.log(`Created directory: ${dirPath}`);
  }

  // Create files
  for (const file of files) {
    const filePath = path.join(basePath, file);
    // Ensure parent directory exists
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    // Create empty file if it doesn't exist
    try {
      await fs.access(filePath);
    } catch {
      await fs.writeFile(filePath, '');
      console.log(`Created file: ${filePath}`);
    }
  }
}

async function main() {
  program
    .argument('<markdown-file>', 'Path to markdown file containing structure')
    .option('-o, --output <path>', 'Output directory', '.')
    .option('-d, --dry-run', 'Show what would be created without creating')
    .option('-f, --format <type>', 'Format: auto, tree, or list', 'auto')
    .parse();

  const [markdownFile] = program.args;
  const options = program.opts();

  try {
    // Read markdown file
    const content = await fs.readFile(markdownFile, 'utf-8');

    // Parse structure based on format
    let parsed: ParsedStructure;
    if (options.format === 'auto') {
      // Auto-detect format
      if (content.includes('├──') || content.includes('└──')) {
        parsed = await parseTreeStructure(content);
      } else {
        parsed = await parseListStructure(content);
      }
    } else if (options.format === 'tree') {
      parsed = await parseTreeStructure(content);
    } else {
      parsed = await parseListStructure(content);
    }

    if (parsed.directories.length === 0 && parsed.files.length === 0) {
      console.log('No directory structure found in markdown file');
      process.exit(1);
    }

    // Create structure
    await createStructure(options.output, parsed.directories, parsed.files, options.dryRun);

    if (!options.dryRun) {
      console.log(`\nDirectory structure created successfully in: ${path.resolve(options.output)}`);
    }

  } catch (error) {
    console.error(`Error: ${error instanceof Error ? error.message : error}`);
    process.exit(1);
  }
}

main().catch(console.error);