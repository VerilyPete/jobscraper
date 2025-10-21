# Code Review Report: Job Scraper Application

**Date:** October 21, 2025  
**Reviewer:** Senior Python Engineer  
**Codebase:** Job Scraper CLI Application

---

## Executive Summary

The application is **functionally sound with comprehensive test coverage**, but has significant **maintainability and architectural concerns**. The main issues center around the `scraper.py` file, which has grown to nearly 1000 lines with multiple responsibilities and code duplication.

---

## 🔴 **CRITICAL ISSUES** (Must Fix)

### 1. **Monolithic `scraper.py` Module** (Lines: 986, Cyclomatic Complexity: Very High)

**Location:** `/Users/pete/Documents/jobscraper/scraper.py`

**Problem:** Single file containing multiple distinct extraction strategies, URL manipulation, pagination, action execution, and coordination logic.

**Issues:**
- `extract_jobs_from_page()` method is 250+ lines (lines 458-703)
- Multiple extraction methods with duplicated logic
- Hard to test individual components
- Violates Single Responsibility Principle

**Impact:** High maintenance burden, difficult onboarding, error-prone modifications

**Recommendation:** Refactor into separate modules:
```
scraper/
  ├── __init__.py
  ├── core.py              # JobScraper, scrape_all
  ├── extractors/
  │   ├── __init__.py
  │   ├── base.py          # Base extraction interface
  │   ├── custom.py        # extract_jobs_with_custom_config
  │   ├── clicking.py      # extract_jobs_by_clicking
  │   ├── iframe.py        # extract_jobs_from_iframe
  │   └── default.py       # Default extraction logic
  ├── url_utils.py         # URL normalization, validation
  ├── pagination.py        # check_for_next_page
  └── actions.py           # execute_pre_scrape_actions
```

---

### 2. **Repeated URL Construction Logic**

**Location:** `scraper.py` lines 152, 572, 674 (and others)

**Problem:** Same URL normalization pattern repeated 5+ times:
```python
if url.startswith('/'):
    url = page.url.split('/')[0] + '//' + page.url.split('/')[2] + url
```

**Impact:** Bug-prone, inconsistent behavior if modified in one place but not others

**Recommendation:** Extract to utility function:
```python
def make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute using base URL."""
    from urllib.parse import urljoin
    return urljoin(base_url, url)
```

---

### 3. **Silent Exception Handling**

**Location:** `scraper.py` lines 236, 273, 287, 310, 316, 322, 448, 452

**Problem:** Multiple bare `except Exception:` blocks that silently swallow errors:
```python
except Exception:
    pass
```

**Impact:** Debugging nightmares, silent failures in production

**Recommendation:** At minimum, log warnings:
```python
except Exception as e:
    logger.warning(f"Failed to extract title: {e}")
```

---

## 🟡 **HIGH PRIORITY** (Should Fix Soon)

### 4. **Magic Numbers and Strings Throughout Code**

**Location:** Multiple locations in `scraper.py`

**Examples:**
- Line 30: `self.timeout = 30000` (no constant)
- Line 31: `self.max_pages = 10` (no constant)
- Line 177: `if not title or len(title) < 3:` (magic number 3)
- Line 233: `timeout=10000` (hardcoded)
- Line 397: `if url.count('/') < 4:` (magic number 4)
- Line 429: `if len(title.split()) < 2:` (magic number 2)
- Line 537: `if len(row_text) > 10:` (magic number 10)

**Recommendation:** Define constants:
```python
class ScraperConstants:
    DEFAULT_TIMEOUT_MS = 30000
    MAX_PAGINATION_PAGES = 10
    MIN_TITLE_LENGTH = 3
    MIN_URL_DEPTH = 4
    CONTAINER_WAIT_TIMEOUT_MS = 10000
```

---

### 5. **Code Duplication in Extraction Methods**

**Location:** `scraper.py` - title extraction duplicated across methods

**Problem:** Similar title extraction logic appears in:
- `extract_jobs_with_custom_config` (lines 167-174)
- `extract_jobs_by_clicking` (lines 267-279)
- `extract_jobs_from_iframe` (lines 412-420)
- `extract_jobs_from_page` (lines 595-633)

**Recommendation:** Extract to helper method:
```python
def _extract_title(
    self, 
    container: BeautifulSoup, 
    title_selector: str = None, 
    link: BeautifulSoup = None
) -> str:
    """Extract title from container using selector or fallback."""
    # Centralized title extraction logic
```

---

### 6. **Type Hints Missing or Incomplete**

**Location:** Throughout `scraper.py`, `main.py`, `config_manager.py`

**Examples:**
- `main.py` line 10: `def main():` (no return type)
- Many method parameters lack type hints
- `Dict` used without specifying key/value types

**Recommendation:** Add comprehensive type hints:
```python
from typing import Dict, List, Optional, Any

def main() -> int:
    """Main entry point for CLI."""
    ...

async def extract_jobs_from_page(
    self, 
    page: Page, 
    wait_state: str = 'networkidle', 
    timeout: Optional[int] = None,
    custom_config: Optional[Dict[str, Any]] = None,
    use_iframe: bool = False
) -> List[Dict[str, str]]:
```

---

### 7. **Inline HTML Generation in `output.py`**

**Location:** `output.py` lines 138-529

**Problem:** 400 lines of HTML as string literals mixed with Python logic

**Impact:** Hard to maintain, test, or modify styling

**Recommendation:** Use Jinja2 templating:
```python
from jinja2 import Template

def generate_html(matches: List[JobMatch], ...):
    template = Template(Path('templates/job_matches.html').read_text())
    return template.render(
        matches=matches,
        new_matches=new_matches,
        existing_matches=existing_matches,
        date=datetime.now()
    )
```

---

## 🟢 **MEDIUM PRIORITY** (Nice to Have)

### 8. **Inconsistent Error Messaging**

**Location:** Throughout `scraper.py`

**Problem:** Mix of emojis, symbols, and text formats:
- `⚠` vs `ℹ` vs `✓` vs plain text
- Inconsistent capitalization and punctuation

**Recommendation:** Standardize using Python's `logging` module with levels

---

### 9. **Long Parameter Lists**

**Location:** `scraper.py` line 855 (scrape_company method)

**Problem:** Method extracts 8+ configuration values individually:
```python
company_name = company.get('name', 'Unknown')
job_board_url = company.get('job_board_url', '')
company_keywords = [k.lower() for k in company.get('keywords', [])]
location_filters = company.get('location_filters', None)
timeout = company.get('timeout', self.timeout)
wait_for_load_state = company.get('wait_for_load_state', 'networkidle')
scraping_config = company.get('scraping_config', None)
use_iframe = company.get('use_iframe', False)
```

**Recommendation:** Create a `CompanyConfig` dataclass:
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class CompanyConfig:
    name: str
    job_board_url: str
    keywords: List[str] = field(default_factory=list)
    timeout: int = 30000
    wait_for_load_state: str = 'networkidle'
    scraping_config: Optional[Dict] = None
    use_iframe: bool = False
    location_filters: Optional[Dict] = None
    pre_scrape_actions: List[Dict] = field(default_factory=list)
    max_pages: int = 10
```

---

### 10. **No Logging Infrastructure**

**Location:** All files

**Problem:** Using `print()` statements instead of proper logging

**Impact:** 
- Can't control verbosity
- No log levels (debug, info, warning, error)
- No log file output option
- Hard to debug in production

**Recommendation:** Implement Python's `logging` module:
```python
import logging

logger = logging.getLogger(__name__)

# Instead of print(f"   ⚠ Timeout loading {company_name}")
logger.warning(f"Timeout loading {company_name}")
```

---

### 11. **Hardcoded Selector Lists**

**Location:** `scraper.py` lines 362-367, 492-500, 505-507, 542-551, 641-645, 716-749

**Problem:** Long lists of CSS selectors hardcoded in methods:
```python
for selector in [
    '.opening',
    'div.opening',
    'section.level-0',
    'div[id*="job"]',
]:
```

**Recommendation:** Move to configuration/constants files:
```python
# selectors.py
IFRAME_JOB_SELECTORS = [
    '.opening',
    'div.opening',
    'section.level-0',
    'div[id*="job"]',
]

NON_JOB_KEYWORDS = [
    'talent network',
    'join our',
    'talent community',
    ...
]
```

---

### 12. **No Retry Logic for Network Operations**

**Location:** `scraper.py` - page.goto, network operations

**Problem:** No retry mechanism for transient failures

**Recommendation:** Add retry decorator for resilience:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _goto_with_retry(page: Page, url: str, timeout: int):
    await page.goto(url, timeout=timeout)
```

---

### 13. **URL Construction Using String Splitting**

**Location:** Lines 152, 572, 674, 587-588

**Problem:** Using `url.split('/')[2]` instead of proper URL parsing

**Current:**
```python
url = page.url.split('/')[0] + '//' + page.url.split('/')[2] + url
```

**Better:**
```python
from urllib.parse import urlparse, urljoin

parsed = urlparse(page.url)
base_url = f"{parsed.scheme}://{parsed.netloc}"
url = urljoin(base_url, url)
```

---

## 🔵 **LOW PRIORITY** (Polish)

### 14. **Docstring Inconsistencies**

- Some methods have detailed docstrings, others minimal
- No consistent format (Google/NumPy/Sphinx style)

**Recommendation:** Standardize on Google-style docstrings

---

### 15. **Test Coverage Gaps**

While you have 110 tests, there's no coverage for:
- Error recovery paths in `extract_jobs_by_clicking`
- Timeout handling in various methods
- Edge cases in URL construction

**Recommendation:** Run coverage analysis:
```bash
uv run pytest --cov=. --cov-report=html
```

---

### 16. **No Input Validation**

**Location:** `config_manager.py`, `scraper.py`

**Problem:** No validation of configuration values (e.g., negative timeouts, invalid URLs)

**Recommendation:** Add Pydantic for validation:
```python
from pydantic import BaseModel, HttpUrl, Field

class CompanyConfig(BaseModel):
    name: str
    job_board_url: HttpUrl
    keywords: List[str] = Field(default_factory=list)
    timeout: int = Field(default=30000, gt=0)
```

---

### 17. **Comments Could Be Improved**

Many comments describe *what* the code does rather than *why*:
```python
# Get page content  ← States the obvious
content = await page.content()
```

Better:
```python
# Capture current DOM state for BeautifulSoup parsing since
# we can't use Playwright selectors for complex CSS queries
content = await page.content()
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Critical Issues | 3 |
| High Priority | 7 |
| Medium Priority | 7 |
| Low Priority | 3 |
| **Total Issues** | **20** |
| Lines of Code | ~2,200 |
| Test Coverage | 110 tests (good) |
| Largest File | scraper.py (986 lines) |

---

## Recommended Remediation Order

1. **Phase 1 (Critical):** Extract URL utilities, add logging, fix silent exceptions
2. **Phase 2 (High):** Refactor scraper.py into modules, add type hints
3. **Phase 3 (Medium):** Add constants, create config dataclasses, improve error handling
4. **Phase 4 (Low):** Polish docstrings, improve test coverage

---

## Positive Aspects ✅

1. **Excellent test coverage** (110 tests)
2. **Good separation between CLI, config, scraping, and output**
3. **Well-documented README** with comprehensive examples
4. **Async/await used correctly throughout**
5. **Thoughtful feature set** (pagination, iframes, pre-scrape actions, location filtering)
6. **Good use of BeautifulSoup + Playwright combination**

---

## Conclusion

The codebase is **production-ready** but would benefit significantly from the refactoring suggested above for long-term maintainability. The critical issues should be addressed to prevent technical debt accumulation.

