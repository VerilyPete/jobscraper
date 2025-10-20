# GitHub Actions Workflows

This directory contains CI/CD workflows for the job scraper project.

## Workflows

### `tests.yml` - Automated Testing

Runs the complete test suite on every push and pull request.

**Triggers:**
- Push to `main` or `master` branches
- Pull requests targeting `main` or `master`

**What it does:**
1. Checks out the code
2. Sets up Python 3.12
3. Installs `uv` package manager
4. Installs project dependencies via `uv sync`
5. Installs Playwright Chromium browser with system dependencies
6. Runs all 104 tests with pytest in verbose mode
7. Uploads test artifacts if tests fail (for debugging)

**Runs:**
- Operating System: Ubuntu Latest
- Python Version: 3.12
- Browser: Chromium (headless)
- Test Count: 104 tests (unit + integration)

**Duration:** Typically 2-4 minutes

**Badge:**
Add this to your README.md to show test status:
```markdown
![Tests](https://github.com/YOUR_USERNAME/jobscraper/actions/workflows/tests.yml/badge.svg)
```

## Local Testing

To ensure tests will pass in CI before pushing:

```bash
# Run all tests
uv run pytest -v

# Run with same options as CI
uv run pytest -v --tb=short
```

## Debugging Failed CI Tests

If tests fail in CI but pass locally:

1. Check the Actions tab in GitHub for detailed logs
2. Download test artifacts (available for 7 days after failure)
3. Look for environment differences (Ubuntu vs your OS)
4. Ensure Playwright browsers are properly installed locally: `uv run playwright install --with-deps chromium`

## Adding New Workflows

To add new workflows:

1. Create a new `.yml` file in `.github/workflows/`
2. Define triggers (on push, on schedule, manual, etc.)
3. Define jobs and steps
4. Test locally with [act](https://github.com/nektos/act) if possible

