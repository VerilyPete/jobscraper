# Job Scraper CLI

A Python CLI application that scrapes company job boards for matching positions based on configurable keywords.

![Tests](https://github.com/VerilyPete/jobscraper/actions/workflows/tests.yml/badge.svg)

## Features

- 🔍 Scrapes multiple company job boards
- 🤖 Supports JavaScript-rendered pages using Playwright
- 🔑 Universal and company-specific keyword matching
- 📄 Handles pagination automatically
- 📊 Beautiful HTML output with styled tables
- 💬 Text output to stdout
- ⚙️ Interactive configuration mode
- 🆕 **Match history tracking** - Automatically detects new vs previously found jobs
- 🌎 **Location filtering** - Per-company include/exclude filters
- 🎯 **Site-specific scraping configuration** - Custom selectors per company
- 🖱️ **Pre-scrape actions** - Click filters, accept cookies, load more content
- 🔄 **Dynamic content loading** - Repeat-click buttons until all content loads
- 🖼️ **Iframe support** - Extract jobs from embedded job boards
- 🧪 **Single company testing** - Test configurations one company at a time

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

## Lazy Mode: Adding Companies with Playwright MCP

Too lazy to manually figure out selectors? Let your LLM do the work! If you have the [Playwright MCP](https://github.com/executeautomation/playwright-mcp-server) server configured, you can add companies with a single prompt:

**Example prompt:**
```
Add the company Philo (https://www.philo.com/jobs/job-board) to config.json. 
They have 5 jobs posted. Configure the scraping settings to return all 5 jobs.
```

**What the model will do:**
1. Navigate to the job board using Playwright
2. Inspect the HTML structure to find job containers
3. Identify the correct selectors for links, titles, and pagination
4. Test the configuration to verify it finds the expected number of jobs
5. Add the properly configured entry to your `config.json`

**Result:**
```json
{
  "name": "Philo",
  "job_board_url": "https://www.philo.com/jobs/job-board",
  "keywords": [],
  "scraping_config": {
    "container_selectors": ["main li"],
    "link_selector": "a",
    "title_selector": "h3",
    "pagination_selectors": []
  }
}
```

This is especially useful for job boards with unusual HTML structures that don't work with the default scraping logic. No more manual selector hunting!

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

**Note:** You can enter keywords as a comma-separated list for faster input!

---

## Pro Tips

### Bake Filters into the URL

Many job boards let you apply filters (location, department, job type) and the selections are reflected in the URL. **Save the filtered URL** as your `job_board_url` to avoid needing `pre_scrape_actions`:

**Example - Oracle with filters pre-applied:**
```json
{
  "name": "Oracle",
  "job_board_url": "https://careers.oracle.com/jobs/?keyword=Engineering&location=United%20States&locationId=300000000149325",
  "keywords": ["senior", "cloud"]
}
```

This URL already has "Engineering & Development" and "United States" selected, so the scraper immediately sees only relevant jobs.

**How to find the filtered URL:**
1. Go to the company's job board
2. Apply your desired filters (location, department, remote, etc.)
3. Copy the URL from your browser's address bar
4. Use that URL in your config

This is often simpler and more reliable than clicking filters with `pre_scrape_actions`!

---

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

# Scrape only a single company (useful for testing)
uv run python main.py --company "Company Name"

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

- **`pre_scrape_actions`** (array of objects, optional): Actions to perform before scraping (e.g., clicking filters, accepting cookies, loading more content). Useful for job boards that require interaction to show all positions. Each action supports:
  
  - **`type`** (required): Action type
    - `click` - Click an element
    - `fill` - Fill text into an input
    - `select` - Select an option from dropdown
    - `check` - Check a checkbox
    - `uncheck` - Uncheck a checkbox
    - `press` - Press a keyboard key
    - `hover` - Hover over an element
    - `wait` - Wait for an element to appear (no interaction)
  
  - **`selector`** (required): CSS selector or Playwright text selector (e.g., `"button:has-text('Accept')"`, `"text=Remote Only"`)
  
  - **`value`** (optional): Value to use for `fill`, `select`, or `press` actions
  
  - **`wait_after`** (optional): Milliseconds to wait after action completes (default: 500)
  
  - **`wait_for_network_idle`** (optional): Whether to wait for network to settle after the action (default: false)
  
  - **`timeout`** (optional): Element visibility timeout in milliseconds (default: 5000)
  
  - **`repeat_until_gone`** (optional, `click` only): Keep clicking until element disappears. Perfect for "Load More" or "Show More Results" buttons. Use with:
    - `max_repeats` (optional): Maximum number of clicks (default: 50)
  
  **Examples:**
  ```json
  // Accept cookie banner
  {
    "type": "click",
    "selector": "button:has-text('Accept all')",
    "wait_after": 1000
  }
  
  // Click "Show More" until all content loads
  {
    "type": "click",
    "selector": "button:has-text('Show More Results')",
    "wait_after": 2000,
    "repeat_until_gone": true,
    "max_repeats": 100
  }
  
  // Wait for dynamic content to load
  {
    "type": "wait",
    "selector": "[role='region']",
    "timeout": 10000
  }
  ```
  
  **Real-World Examples:**
  
  **IBM - Multiple filters with dynamic content:**
  ```json
  // IBM's job board requires accepting cookies, then clicking filters,
  // and waiting for the job list to dynamically populate
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "button:has-text('Accept all')",
      "wait_after": 1000
      // Dismiss cookie banner that blocks the page
    },
    {
      "type": "click",
      "selector": "text=Remote only",
      "wait_after": 1000
      // Click the "Remote only" filter to show only remote positions
    },
    {
      "type": "click",
      "selector": "button:has-text('Location')",
      "wait_after": 500
      // Open the location dropdown menu
    },
    {
      "type": "click",
      "selector": "text=United States",
      "wait_after": 1000
      // Select "United States" from the location dropdown
    },
    {
      "type": "wait",
      "selector": "[role='region']",
      "timeout": 10000
      // Wait for the filtered job results to load into the page
      // The jobs appear in elements with role="region"
    }
  ]
  ```
  
  **Twitch - Sequential clicks to reveal hidden options:**
  ```json
  // Twitch hides location options until you click "Offices" first,
  // then you can select specific remote locations
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "text=Offices",
      "wait_after": 500
      // Click "Offices" button to reveal the location filter list
      // Without this, "Remote (United States)" isn't visible
    },
    {
      "type": "click",
      "selector": "text=Remote (United States)",
      "wait_after": 1000
      // Now that the list is visible, select remote US positions
    }
  ]
  ```
  
  **Oracle - Load all pages of results:**
  ```json
  // Oracle uses a "Show More Results" button instead of pagination
  // If you're scraping for IC engineer roles, that could be as many as 1500 jobs
  // Need to click it repeatedly to load them all
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "button:has-text('Show More Results')",
      "wait_after": 2000,
      "repeat_until_gone": true,
      "max_repeats": 110
      // Clicks the button, waits 2s for jobs to load, then clicks again
      // Continues until button disappears or hits 110 clicks (safety limit)
      // Each click loads ~15 more jobs
    }
  ]
  ```

- **`timeout`** (integer, default: `30000`): Page load timeout in milliseconds. Override when a company's job board is particularly slow to load or faster than average.
  
  Example:
  ```json
  {
    "name": "Slow Company",
    "job_board_url": "https://example.com/careers",
    "keywords": ["engineer"],
    "timeout": 60000  // 60 seconds instead of default 30
  }
  ```

- **`wait_for_load_state`** (string, default: `"networkidle"`): Load state to wait for before scraping. Options:
  - `"networkidle"` (default): Wait until network activity settles (recommended for most sites)
  - `"load"`: Wait only for the page load event (faster, use for sites with continuous background activity)
  - `"domcontentloaded"`: Wait only for DOM to be ready (fastest, use with caution)
  
  Use `"load"` for sites that have ads, tracking, or analytics that prevent networkidle from being reached.

- **`scraping_config`** (object, optional): Override default scraping logic with custom selectors. Use when default logic finds wrong elements or misses jobs. All fields optional - only specify what needs customization:

  - **`container_selectors`** (array of strings): CSS selectors for job containers, tried in order until jobs found. Use specific selectors to avoid false matches.
    
    Example: `["div.job-listing", "article.position"]`
  
  - **`link_selector`** (string): CSS selector to find job link within container.
    
    Example: `"a[href*='/job/']"`
  
  - **`title_selector`** (string): CSS selector to find job title within container.
    
    Example: `"h3, h2, .job-title"`
  
  - **`description_selector`** (string, optional): CSS selector for job description. Defaults to container text.
  
  - **`exclude_patterns`** (object, optional): Patterns to filter out non-job matches:
    - `urls` (array): URL patterns to exclude (e.g., `["/careers/$", "/search"]`)
    - `titles` (array): Title keywords to exclude (e.g., `["talent network", "filter"]`)
  
  - **`pagination_selectors`** (array of strings): Conservative pagination selectors. Empty array `[]` disables pagination.
    
    Example: `["a.pagination-next", "button.load-more"]`

  **When to use**: If scraper finds 0 jobs, wrong elements, or scrapes phantom pages, add custom config with specific selectors found via Playwright MCP inspection.

- **`use_iframe`** (boolean, default: `false`): Extract jobs from iframes instead of main page. Some job boards (especially those using Greenhouse, Breezy HR, or similar platforms) embed their job listings in iframes. When enabled:
  - The scraper searches all iframes on the page
  - Looks for job-related content using specialized patterns
  - Extracts jobs with proper URL and title handling
  
  **When to use**: If you see an embedded job board on the page but the scraper returns 0 jobs, the jobs are likely in an iframe. Combine with `wait_for_load_state: "load"` and pre-scrape actions for cookie banners.
  
  Example:
  ```json
  {
    "name": "Company with Iframe Jobs",
    "job_board_url": "https://example.com/careers",
    "keywords": ["engineer"],
    "wait_for_load_state": "load",
    "use_iframe": true,
    "pre_scrape_actions": [
      {
        "type": "click",
        "selector": "button:has-text('Accept Cookies')",
        "wait_after": 2000
      }
    ]
  }
  ```

- **`max_pages`** (integer, default: `10`): Maximum number of pages to scrape before stopping. Override when a site legitimately has many pages of results. The default of 10 is a safety measure to prevent infinite pagination loops.
  
  **When to override:** If you know a site has more than 10 pages of results and you want to scrape them all. For example, large companies may have 50+ pages of engineering roles.
  
  **Important:** This only applies to traditional pagination (Next/Previous buttons, page numbers). Sites using "Load More" buttons with `repeat_until_gone` should disable pagination instead by setting `"pagination_selectors": []` in their `scraping_config`.
  
  Example:
  ```json
  {
    "name": "Large Company",
    "job_board_url": "https://example.com/careers",
    "keywords": ["engineer"],
    "max_pages": 50
  }
  ```
  
  **For sites with "Load More" buttons:** If you use `repeat_until_gone` to load all content, disable pagination to prevent false positive page detection:
  ```json
  {
    "name": "Oracle",
    "job_board_url": "https://oracle.com/careers",
    "keywords": [],
    "pre_scrape_actions": [
      {
        "type": "click",
        "selector": "button:has-text('Show More')",
        "repeat_until_gone": true,
        "max_repeats": 110
      }
    ],
    "scraping_config": {
      "pagination_selectors": []
    }
  }
  ```

## Common Configuration Patterns

### Pattern 1: Standard Job Board (Works Out of the Box)
Most job boards work with zero configuration:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"]
}
```

### Pattern 2: Job Board with Cookie Banner
Accept cookies before scraping:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"],
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "button:has-text('Accept')",
      "wait_after": 1000
    }
  ]
}
```

### Pattern 3: Job Board with "Load More" Button
Click "Show More" until all jobs load:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"],
  "wait_for_load_state": "load",
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "button:has-text('Show More')",
      "wait_after": 2000,
      "repeat_until_gone": true,
      "max_repeats": 100
    }
  ]
}
```

### Pattern 4: Jobs in an Iframe (Greenhouse, Breezy HR, etc.)
Extract jobs from embedded job boards:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"],
  "wait_for_load_state": "load",
  "use_iframe": true
}
```

### Pattern 5: Job Board with Filters
Click filters to show relevant jobs:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"],
  "wait_for_load_state": "load",
  "pre_scrape_actions": [
    {
      "type": "click",
      "selector": "text=Remote only",
      "wait_after": 1000
    },
    {
      "type": "click",
      "selector": "text=United States",
      "wait_after": 2000
    },
    {
      "type": "wait",
      "selector": "[role='region']",
      "timeout": 10000
    }
  ]
}
```

### Pattern 6: Custom Scraping for Unusual Structure
Override selectors when default logic fails:
```json
{
  "name": "Company Name",
  "job_board_url": "https://company.com/careers",
  "keywords": ["engineer"],
  "scraping_config": {
    "container_selectors": ["main li", "div.job-card"],
    "link_selector": "a",
    "title_selector": "h2, h3",
    "pagination_selectors": []
  }
}
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

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

### Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions. The workflow:
- Runs all 104 tests (unit + integration)
- Uses Python 3.12 on Ubuntu
- Installs Playwright Chromium browser
- Typically completes in 2-4 minutes

See `.github/workflows/tests.yml` for workflow configuration.

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
- **Check the URL**: Ensure the job board URL is correct and accessible
- **Try the `--company` flag**: Test one company at a time to isolate issues
- **Check for iframes**: If you see jobs on the page but scraper finds 0, try adding `"use_iframe": true`
- **Inspect with Playwright**: Use Playwright's browser tools to find the right selectors
- **Add custom scraping config**: Some job boards need specific `container_selectors`
- **Check for dynamic content**: Add `pre_scrape_actions` if jobs load after clicking "Show More"
- **Try broader keywords**: Make keywords less specific to catch more matches

**Timeout errors?**
- **Use `"wait_for_load_state": "load"`**: Many sites have background requests that prevent `networkidle`
- **Check pre-scrape action selectors**: If an action times out, the selector might be wrong
- **Increase action timeout**: Add `"timeout": 10000` to specific pre-scrape actions
- **Check for cookie banners**: Add a click action to dismiss them before other actions

**Wrong jobs or phantom pages scraped?**
- **Add custom `scraping_config`**: Use specific `container_selectors` to target only job listings
- **Add `exclude_patterns`**: Filter out non-job links and titles
- **Set `pagination_selectors: []`**: Disable pagination if it's clicking the wrong buttons

**Jobs appearing multiple times?**
- This should be automatically fixed by URL deduplication, but if it persists, check if the same job has multiple URLs

**Jobs from wrong locations?**
- **Use `location_filters`**: Add `exclude` patterns for unwanted locations or `include` patterns for desired ones

## License

MIT

