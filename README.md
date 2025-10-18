# Job Scraper CLI

A Python CLI application that scrapes company job boards for matching positions based on configurable keywords.

## Features

- 🔍 Scrapes multiple company job boards
- 🤖 Supports JavaScript-rendered pages using Playwright
- 🔑 Universal and company-specific keyword matching
- 📄 Handles pagination automatically
- 📊 Beautiful HTML output with styled tables
- 💬 Text output to stdout
- ⚙️ Interactive configuration mode
- 🆕 **Match history tracking** - Automatically detects new vs previously found jobs
- 🌎 **Location filtering** - Per-company filters (e.g., exclude Canada-only positions)

## Quick Start

1. **Install dependencies:**
   ```bash
   cd jobscraper
   uv sync
   uv run playwright install chromium
   ```

2. **Configure your search:**
   ```bash
   uv run python main.py --configure
   ```
   
   Follow the prompts to add:
   - Universal keywords (e.g., "python, remote, senior")
   - Company job boards and their specific keywords

3. **Run the scraper:**
   ```bash
   uv run python main.py
   ```

4. **View results:**
   - Check the console output
   - Open `job_matches.html` in your browser

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Usage

### First-time Setup (Interactive Configuration)

Run the interactive configuration to add keywords and companies:

```bash
uv run python main.py --configure
```

This will prompt you to:
1. Add universal keywords (searched across all companies)
2. Add companies with their job board URLs
3. Add company-specific keywords for each company

**Pro tip:** You can enter keywords as a comma-separated list for faster input!

### Running the Scraper

Once configured, run the scraper:

```bash
uv run python main.py
```

This will:
- Scrape all configured company job boards
- Match jobs against your keywords (case-insensitive, in title and description)
- Output results to stdout
- Generate a beautiful HTML file (`job_matches.html`)

### Options

```bash
# Use custom config file
uv run python main.py --config my_config.json

# Specify custom HTML output file
uv run python main.py --output results.html

# Enter configuration mode
uv run python main.py --configure

# Show help
uv run python main.py --help
```

## Configuration File Format

The configuration is stored in `config.json`:

```json
{
  "universal_keywords": ["python", "remote", "senior"],
  "companies": [
    {
      "name": "Company Name",
      "job_board_url": "https://company.com/careers",
      "keywords": ["backend", "frontend"]
    },
    {
      "name": "Company With Exclude Filter",
      "job_board_url": "https://company.com/careers",
      "keywords": ["engineer"],
      "location_filters": {
        "exclude": ["remote, canada"]
      }
    },
    {
      "name": "Company With Include Filter",
      "job_board_url": "https://company.com/careers",
      "keywords": ["engineer"],
      "location_filters": {
        "include": ["remote, us", "us and canada"]
      }
    }
  ]
}
```

### Optional Company Configuration Fields

- **`keywords`** (array of strings, default: `[]`): Company-specific keywords to search for in addition to universal keywords.

- **`location_filters`** (object, optional): Filter jobs by location patterns. Supports both `include` and `exclude` strategies:
  - **`include`** (array of strings): Only include jobs matching at least one of these patterns (whitelist approach)
  - **`exclude`** (array of strings): Exclude jobs matching any of these patterns (blacklist approach)
  - Both can be used together: include filters are checked first, then exclude filters
  - Patterns are case-insensitive substring matches
  
  **Examples:**
  ```json
  // Exclude Canada-only positions (but keep "US and Canada")
  "location_filters": {
    "exclude": ["remote, canada"]
  }
  
  // Only include US positions
  "location_filters": {
    "include": ["remote, us", "remote - united states", "us and canada"]
  }
  
  // Include US positions but exclude specific states
  "location_filters": {
    "include": ["remote, us"],
    "exclude": ["california", "new york"]
  }
  ```

- **`pre_scrape_actions`** (array of objects, optional): Actions to perform before scraping (e.g., clicking filters, selecting options). Useful for job boards that require interaction to show all positions. Each action has:
  - `type`: Action type (`click`, `fill`, `select`, `check`, `uncheck`, `press`, `hover`)
  - `selector`: CSS selector or text selector for the element
  - `value`: Value to use (for `fill`, `select`, `press` actions)
  - `wait_for_network_idle`: Whether to wait for network to settle after the action
  - `timeout`: Timeout in milliseconds (default: 5000)
  
  Example:
  ```json
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "text=Remote (United States)",
      "wait_for_network_idle": true,
      "timeout": 10000
    }
  ]
  ```

## Keyword Matching

- **Case-insensitive**: "Python" matches "python", "PYTHON", etc.
- **Word boundaries**: "python" matches "Python Developer" but not "micropython"
- **Searches in**: Job title and description
- **Combined keywords**: Universal keywords + company-specific keywords

## Match History Tracking

The scraper automatically tracks which jobs you've seen before:

- **First run**: All matches are considered "new" 🆕
- **Subsequent runs**: The scraper reads the existing `job_matches.html` file and compares URLs
  - Jobs with URLs not in the previous HTML → **New Matches** (shown first)
  - Jobs with URLs already in the previous HTML → **Previously Found Matches** (shown after)
- **No separate file needed**: The HTML file itself serves as the history
- **How it works**: Each job URL is unique, so the scraper uses URL comparison to detect matches

This is perfect for daily runs - you'll immediately see which opportunities are new!

## HTML Output

The generated HTML file features:
- 🎨 Modern, responsive design
- 📊 Stats dashboard showing total, new, and previously found matches
- 🆕 Separate "New Matches" section (shown first)
- 📋 Separate "Previously Found Matches" section
- 📊 Grouped by company
- 🔗 Clickable job links (open in new tab)
- 🏷️ Color-coded keyword tags
- 📅 Timestamp of when the search was run

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_scraper.py -v
```

### Project Structure

```
jobscraper/
├── main.py              # CLI entry point
├── config_manager.py    # Configuration management
├── scraper.py          # Web scraping logic
├── output.py           # Output formatting
├── config.json         # Configuration file
├── tests/              # Test suite
│   ├── test_config_manager.py
│   ├── test_scraper.py
│   ├── test_output.py
│   └── test_integration.py
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # This file
```

## How It Works

1. **Configuration**: Load keywords and company URLs from `config.json`
2. **Scraping**: Use Playwright to navigate to each job board (supports JS-rendered pages)
3. **Pagination**: Automatically detect and navigate through multiple pages
4. **Matching**: Extract job listings and match against keywords
5. **Output**: Format results and save to HTML + stdout

## Limitations & Notes

- **Pagination**: Automatically handles common pagination patterns (Next buttons, page numbers)
- **Max pages**: Limited to 10 pages per company as a safety measure
- **Timeout**: 30-second timeout per page load
- **Selectors**: Uses common patterns to detect job listings; may need customization for unusual job boards
- **Rate limiting**: Includes 1-second delay between pages to be respectful

## Troubleshooting

**No jobs found?**
- Check that the job board URL is correct
- Try broader keywords
- Some job boards may have unusual structures (check the HTML)

**Timeout errors?**
- Some job boards may be slow to load
- The scraper waits up to 30 seconds per page

**Missing jobs?**
- The scraper looks for common patterns in job listings
- Some custom job boards may need selector adjustments in `scraper.py`

## License

MIT

