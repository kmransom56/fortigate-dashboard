# token-extractor.js

## Purpose
`token-extractor.js` is a Node.js command-line interface (CLI) tool designed to work with the assets produced by `scraper.js`. Its purpose is to parse the scraped CSS files and computed style JSON files to identify and extract fundamental design values, known as **design tokens**. These tokens represent reusable values for colors, typography, spacing, etc. By extracting these, a developer can create a systematic design system based on the FortiGate UI's actual styling, and output these tokens into various formats for use in other projects.

## Dependencies
- **`commander`**: For building the CLI commands and options.
- **`chalk`**: For colorizing console output.
- **`ora`**: For displaying progress spinners in the terminal.
- **`fs-extra`**: For file system operations like reading and writing files.
- **`path`**: A built-in Node.js module for handling file paths.
- **`css`**: A CSS parser that converts CSS code into an Abstract Syntax Tree (AST), which is essential for programmatically analyzing the styles.
- **`postcss`**: A tool for transforming CSS with JavaScript (listed as a dependency, but not actively used in the provided code).
- **`../utils/logger`**: A local utility for logging.

## API (CLI Commands)
This script provides two main commands to be run from the terminal:

- **`extract`**: This is the primary command. It recursively scans an input directory for CSS and `computed-styles.json` files, parses them, extracts the design tokens, and then generates output files in the specified format.
  - **Options**: `--input-dir`, `--output-dir`, `--format` (json, css, scss, js).

- **`validate`**: A utility command to perform basic checks on the extracted token files, ensuring they have the required categories and that color values are valid.

## Configuration
The tool is configured via command-line options when it is run.
- `--input-dir`: Specifies the directory where the scraped assets are located (defaults to `./assets`).
- `--output-dir`: Specifies where the generated token files should be saved (defaults to `./tokens`).
- `--format`: Defines the output format for the tokens.

## Data Flow
The `extract` command follows this workflow:
1.  It recursively scans the input directory to find all `.css` files and `computed-styles.json` files.
2.  It initializes an empty `tokens` object to hold the extracted data, categorized into sections like `colors`, `typography`, `spacing`, etc.
3.  **For each CSS file**:
    -   It reads the file content and uses the `css` library to parse it into an AST.
    -   It traverses the AST, examining each CSS rule and declaration.
    -   Helper functions (e.g., `isColorProperty`) determine if a declaration represents a design token.
    -   If it is a token, the value is extracted and stored in the appropriate category in the `tokens` object.
4.  **For each `computed-styles.json` file**:
    -   It reads and parses the JSON.
    -   It iterates through the computed styles for the container, nodes, and links, extracting token values in the same way.
5.  After processing all files, the script generates the output files based on the `--format` option (e.g., creating `tokens.json`, `tokens.css`, etc.).
6.  Finally, it generates a `README.md` file that documents all the extracted tokens.

## Error Handling
- The main command logic is wrapped in a `try...catch` block, which reports errors to the user via the `ora` spinner.
- It explicitly checks if any CSS files were found and throws an error if the input directory is empty.

## Testing
This file does not contain its own unit tests. Testing this tool would involve:
- Creating a temporary directory with sample scraped CSS and JSON files.
- Running the `extractTokens` function against this directory.
- Asserting that the generated output files (e.g., `tokens.json`) contain the correct, expected values based on the sample input files.
- Testing the helper functions (like `isColorProperty` and `extractColorValue`) in isolation.
