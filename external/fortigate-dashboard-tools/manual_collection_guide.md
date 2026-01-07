# FortiGuard PSIRT Manual Collection Guide
## Efficient 3-Year Historical Data Collection

Since automated scraping is blocked by your corporate network, this guide provides the most efficient manual approach to collect comprehensive 3-year PSIRT data.

## Phase 1: Quick Sampling (30 minutes)
**Goal:** Determine which advisory ranges actually exist

### Step 1: Test Key Advisory URLs
Open your browser and test these URLs to find valid ranges:

**2022 Advisories:**
- https://fortiguard.fortinet.com/psirt/FG-IR-22-001
- https://fortiguard.fortinet.com/psirt/FG-IR-22-010
- https://fortiguard.fortinet.com/psirt/FG-IR-22-050
- https://fortiguard.fortinet.com/psirt/FG-IR-22-100
- https://fortiguard.fortinet.com/psirt/FG-IR-22-150

**2023 Advisories:**
- https://fortiguard.fortinet.com/psirt/FG-IR-23-001
- https://fortiguard.fortinet.com/psirt/FG-IR-23-010
- https://fortiguard.fortinet.com/psirt/FG-IR-23-050
- https://fortiguard.fortinet.com/psirt/FG-IR-23-100
- https://fortiguard.fortinet.com/psirt/FG-IR-23-150

**2024 Advisories:**
- https://fortiguard.fortinet.com/psirt/FG-IR-24-001
- https://fortiguard.fortinet.com/psirt/FG-IR-24-010
- https://fortiguard.fortinet.com/psirt/FG-IR-24-050
- https://fortiguard.fortinet.com/psirt/FG-IR-24-100
- https://fortiguard.fortinet.com/psirt/FG-IR-24-150

**2025 Advisories:**
- https://fortiguard.fortinet.com/psirt/FG-IR-25-001
- https://fortiguard.fortinet.com/psirt/FG-IR-25-010
- https://fortiguard.fortinet.com/psirt/FG-IR-25-020

### Step 2: Determine Valid Ranges
For each year, note:
- **Lowest valid number** (e.g., FG-IR-22-001 exists)
- **Highest valid number** (e.g., FG-IR-22-087 exists, but FG-IR-22-088 gives 404)
- **Any gaps** in the sequence

## Phase 2: Efficient Data Collection

### Method A: Spreadsheet Template
Create a spreadsheet with these columns:
- Advisory ID
- Title
- Published Date
- CVE ID(s)
- Affected Products
- Severity
- Summary (first 100 words)
- Environment Impact (High/Medium/Low)

### Method B: Browser Automation (if allowed)
If your IT policy allows browser extensions, consider:
- Web scraper browser extensions
- Copy-paste automation tools
- Bookmark management for batch processing

## Phase 3: Focus on High-Impact Advisories

### Priority 1: FortiGate Advisories
Since FortiGate appears to be your primary concern, focus on advisories that mention:
- "FortiGate"
- "FortiOS" 
- "Command injection"
- "Remote code execution"
- "Authentication bypass"

### Priority 2: Critical/High Severity
Look for advisories marked as:
- Critical severity
- High severity
- CVE scores 7.0+

### Priority 3: Recent Advisories
Start with 2024-2025 and work backwards, as recent advisories are most relevant.

## Optimized Collection Strategy

### Time-Efficient Approach:
1. **Start with 2024-2025** (most recent, highest priority)
2. **Sample every 5th advisory** in 2022-2023 to identify patterns
3. **Focus on FortiGate-specific advisories**
4. **Collect full details only for High/Critical severity**

### Data Points to Capture:
**Essential (always collect):**
- Advisory ID
- Title
- CVE ID(s)
- Affected products

**Important (collect if time allows):**
- Published date
- Severity rating
- Brief summary

**Optional (collect for critical advisories only):**
- Full technical details
- Workarounds
- Patch information

## Estimated Time Investment

| Scope | Time Required | Expected Results |
|-------|---------------|------------------|
| Quick sampling | 30 minutes | Valid ranges identified |
| High-priority advisories | 2 hours | 50-75 critical advisories |
| Comprehensive collection | 4-6 hours | 150-200 advisories |
| Full 3-year collection | 8-12 hours | 300+ advisories |

## Analysis Framework

Once you have the data, analyze by:

### By Year:
- 2022: Expected 50-100 advisories
- 2023: Expected 30-80 advisories  
- 2024: Expected 20-60 advisories
- 2025: Expected 5-20 advisories

### By Product Impact:
- FortiGate/FortiOS: Likely 80%+ of advisories
- FortiAnalyzer: Likely 20-30%
- FortiManager: Likely 15-25%
- Other products: Variable

### By Severity:
- Critical: Immediate attention required
- High: Plan remediation within 30 days
- Medium: Plan remediation within 90 days
- Low: Monitor and plan as resources allow

## Tools to Help

### Browser Tools:
- **Bookmark folders** for organizing advisory URLs
- **Browser notes/annotations** for quick data capture
- **Copy-paste managers** for efficient data transfer

### Spreadsheet Features:
- **Data validation** for consistent severity ratings
- **Conditional formatting** for priority highlighting
- **Pivot tables** for analysis by year/product/severity

## Expected Outcomes

Based on typical FortiGuard patterns, you should find:
- **100-200 total advisories** across 3 years
- **60-80% affecting FortiGate/FortiOS**
- **20-30% rated High or Critical severity**
- **Peak activity in 2022** (typical pattern)

This manual approach will give you the comprehensive 3-year PSIRT impact assessment you need for your environment, despite the corporate network restrictions on automated tools.
