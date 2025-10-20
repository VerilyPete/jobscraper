# Test Suite Documentation

This directory contains the comprehensive test suite for the job scraper application.

## Test Structure

### Unit Tests
Tests that verify individual functions and methods in isolation:

- **`test_scraper.py`** - Tests for scraper logic, keyword matching, location filtering, URL deduplication, and configuration validation
- **`test_config_manager.py`** - Tests for configuration management, loading, saving, and parsing
- **`test_output.py`** - Tests for output formatting (HTML and stdout) and match history tracking
- **`test_main.py`** - Tests for CLI argument parsing and main entry point logic

### Integration Tests
Tests that verify the complete workflow with real browser automation:

- **`test_scraper_async.py`** - Playwright integration tests for async scraping methods, pre-scrape actions, iframe extraction, and pagination
- **`test_integration.py`** - End-to-end pipeline tests from configuration to output

## Test Fixtures

The `fixtures/` directory contains HTML files that simulate various job board scenarios:

- **`basic_jobs.html`** - Simple job board with standard structure
- **`jobs_with_iframe.html`** - Page with embedded Greenhouse iframe
- **`greenhouse_jobs.html`** - Content inside the iframe
- **`jobs_with_load_more.html`** - Dynamic page with "Show More" button
- **`jobs_with_filters.html`** - Page with checkboxes and filters
- **`jobs_with_cookie_banner.html`** - Page with cookie consent banner
- **`jobs_custom_selectors.html`** - Non-standard HTML structure requiring custom selectors
- **`jobs_with_pagination.html`** - Multi-page job board with pagination
- **`jobs_with_pagination_page2.html`** - Second page of paginated results

## Running Tests

### Run All Tests
```bash
uv run pytest
```

### Run Specific Test File
```bash
uv run pytest tests/test_scraper.py -v
```

### Run Tests by Pattern
```bash
# Run only async tests
uv run pytest tests/test_scraper_async.py -v

# Run only tests with "location" in name
uv run pytest -k location -v

# Run only integration tests
uv run pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
uv run pytest --cov=. --cov-report=html
```

### Run Specific Test Class or Method
```bash
# Run a specific test class
uv run pytest tests/test_scraper.py::TestLocationFilter -v

# Run a specific test method
uv run pytest tests/test_scraper.py::TestLocationFilter::test_exclude_filter_matches -v
```

## Playwright Integration Tests

The async tests in `test_scraper_async.py` use real Playwright browser automation to verify:

- **Custom scraping configurations** - Container selectors, link selectors, title selectors, description selectors, exclude patterns
- **Iframe extraction** - Detecting and extracting jobs from embedded job boards (Greenhouse, Breezy HR, etc.)
- **Pre-scrape actions** - Click, fill, check, uncheck, press, hover, wait actions
- **Repeat-until-gone** - Dynamic "Load More" button clicking until all content loads
- **Pagination** - Detection and navigation of multi-page job boards
- **Real-world patterns** - Complex scenarios based on actual company configurations (Oracle, IBM, TVEyes, etc.)

### Playwright Setup

Tests use fixtures defined in `conftest.py`:

- **`playwright_instance`** - Session-scoped Playwright instance
- **`browser`** - Test-scoped Chromium browser (headless mode)
- **`page`** - Test-scoped browser page with 1920x1080 viewport
- **`http_server`** - Local HTTP server serving test fixtures
- **`fixture_url`** - Helper to generate URLs for fixture files

### Test Fixtures Configuration

The `conftest.py` file provides factory fixtures for creating test configurations:

- **`test_company_factory`** - Create company configurations with various options
- **`test_config_factory`** - Create scraper configurations

Example usage:
```python
def test_example(browser, fixture_url, test_company_factory):
    company = test_company_factory(
        name="Test Co",
        url=fixture_url("basic_jobs.html"),
        keywords=["python"],
        wait_for_load_state="load",
        pre_scrape_actions=[...]
    )
```

## Test Coverage Areas

### Core Functionality
- ✅ Keyword matching (case-insensitive, word boundaries)
- ✅ Location filtering (include/exclude patterns)
- ✅ URL deduplication
- ✅ Configuration loading and validation
- ✅ Output formatting (HTML and stdout)
- ✅ Match history tracking

### Per-Company Customizations
- ✅ `timeout` override
- ✅ `wait_for_load_state` options (networkidle, load, domcontentloaded)
- ✅ `use_iframe` flag
- ✅ `location_filters` (include/exclude)
- ✅ `pre_scrape_actions` (all action types)
- ✅ `scraping_config` (all selector options)

### Pre-Scrape Actions
- ✅ `click` - Click elements
- ✅ `fill` - Fill text inputs
- ✅ `select` - Select dropdown options
- ✅ `check` / `uncheck` - Toggle checkboxes
- ✅ `press` - Press keyboard keys
- ✅ `hover` - Hover over elements
- ✅ `wait` - Wait for elements to appear
- ✅ `repeat_until_gone` - Click until element disappears
- ✅ `max_repeats` - Safety limit for repeat actions
- ✅ `wait_after` - Delay between actions

### Scraping Configurations
- ✅ `container_selectors` - Multiple selectors with fallback
- ✅ `link_selector` - Custom link finding
- ✅ `title_selector` - Custom title extraction
- ✅ `description_selector` - Custom description extraction
- ✅ `exclude_patterns` - URL and title filtering
- ✅ `pagination_selectors` - Custom pagination detection

### CLI Features
- ✅ `--config` - Custom configuration file
- ✅ `--output` - Custom output file
- ✅ `--company` - Single company filtering
- ✅ `--configure` - Interactive configuration mode
- ✅ Error handling and exit codes

### Real-World Patterns
- ✅ Oracle - Repeat-click "Show More" button
- ✅ IBM - Cookie banner + filters + wait for dynamic content
- ✅ TVEyes/Philo - Custom selectors for non-standard HTML
- ✅ Greenhouse/Breezy - Iframe extraction
- ✅ Cookie banners - Pre-scrape actions to dismiss

## Debugging Tests

### Run with Verbose Output
```bash
uv run pytest -vv
```

### Run with Print Statements
```bash
uv run pytest -s
```

### Run Playwright in Headed Mode
For debugging Playwright tests, modify the `browser` fixture in `conftest.py` temporarily:
```python
browser = await playwright_instance.chromium.launch(headless=False, slow_mo=500)
```

### Inspect Failed Tests
```bash
# Stop on first failure
uv run pytest -x

# Drop into debugger on failure
uv run pytest --pdb
```

## Writing New Tests

### For Unit Tests
1. Add test to appropriate file (test_scraper.py, test_config_manager.py, etc.)
2. Use descriptive test names: `test_<what>_<expected_behavior>`
3. Follow AAA pattern: Arrange, Act, Assert
4. Keep tests focused on one behavior

### For Playwright Integration Tests
1. Add test to `test_scraper_async.py`
2. Mark with `@pytest.mark.asyncio`
3. Use provided fixtures: `browser`, `page`, `fixture_url`
4. Create new HTML fixtures in `fixtures/` if needed
5. Clean up any test state (fixtures auto-clean browsers)

Example:
```python
@pytest.mark.asyncio
async def test_new_feature(page, fixture_url):
    """Test description."""
    url = fixture_url("test_fixture.html")
    await page.goto(url)
    
    config = {"universal_keywords": [], "companies": []}
    scraper = JobScraper(config)
    
    result = await scraper.some_method(page)
    
    assert result == expected
```

## Continuous Integration

Tests are designed to run in CI environments:
- All tests use headless browser mode by default
- HTTP server finds free ports automatically
- No external dependencies (all fixtures are local)
- Tests clean up after themselves

## Performance Considerations

- **Fixtures** are cached at appropriate scopes (session, module, function)
- **Browser** is created per-test to ensure isolation
- **HTTP server** runs for the entire test session
- **Async tests** run efficiently with pytest-asyncio

## Test Maintenance

When adding new features:
1. Add corresponding tests before or alongside the feature
2. Update fixtures if new HTML structures are needed
3. Add integration tests for complex workflows
4. Document new test patterns in this README

When features change:
1. Update affected tests
2. Verify all related tests still pass
3. Add regression tests for bug fixes
4. Keep fixtures synchronized with real-world examples

