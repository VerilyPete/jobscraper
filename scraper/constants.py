"""Constants for job scraper."""
from typing import List

# Timeouts (in milliseconds)
DEFAULT_TIMEOUT_MS = 30000  # 30 seconds
CONTAINER_WAIT_TIMEOUT_MS = 10000  # 10 seconds
URL_NAVIGATION_TIMEOUT_MS = 5000  # 5 seconds
ELEMENT_VISIBILITY_TIMEOUT_MS = 2000  # 2 seconds

# Pagination
MAX_PAGINATION_PAGES = 10  # Safety limit for pagination
MAX_REPEAT_CLICKS = 50  # Maximum number of times to repeat a click action

# Validation thresholds
MIN_TITLE_LENGTH = 3  # Minimum characters in a job title
MIN_TITLE_WORDS = 2  # Minimum words in a job title
MIN_ROW_TEXT_LENGTH = 10  # Minimum text length for table rows
MIN_URL_DEPTH = 4  # Minimum URL depth for job pages (e.g., https://domain.com/job/123)

# Wait times (in milliseconds)
DEFAULT_ACTION_WAIT_MS = 500  # Default wait after actions
RESPECTFUL_DELAY_MS = 1000  # Delay between pages to be respectful
POST_NAVIGATION_DELAY_MS = 1000  # Delay after navigating back to listing

# Iframe job selectors (Greenhouse and similar ATS)
IFRAME_JOB_SELECTORS: List[str] = [
    '.opening',  # Greenhouse uses this
    'div.opening',
    'section.level-0',  # Some Greenhouse boards
    'div[id*="job"]',  # Jobs with IDs
]

# Job indicators for iframe content detection
JOB_INDICATORS: List[str] = [
    'job',
    'position',
    'career',
    'opening',
    'apply',
    'role'
]

# Job URL patterns
JOB_URL_PATTERNS: List[str] = [
    '/job/',
    '/jobs/',
    '/position/',
    '/positions/',
    '/career/',
    '/careers/',
    '/opening/',
    '/openings/',
    '/role/',
    '/roles/',
]

# Exclude patterns for job URLs
EXCLUDE_URL_PATTERNS: List[str] = [
    '/embed/',
    '/careers$',
    '/careers/$',
    '/careers#',
    '#',
    'javascript:',
    'mailto:',
    '/search',
    '/filter'
]

# Exclude patterns for job titles
EXCLUDE_TITLE_KEYWORDS: List[str] = [
    'view all',
    'see all',
    'back to',
    'home',
    'careers',
    'about',
    'apply'
]

# Non-job keywords (for filtering out navigation/informational content)
NON_JOB_KEYWORDS: List[str] = [
    'talent network',
    'join our',
    'join the',
    'talent community',
    'sign up',
    'career alert',
    'job alert',
    'newsletter',
    'filter',
    'sort by',
    'results',
    'open positions',
    'our values',
    'company values',
    'benefits',
    'perks'
]

# Data attribute exclusions
DATA_ATTR_EXCLUSIONS: List[str] = [
    'talent',
    'community',
    'event',
    'tcjoin'
]

# Default pagination selectors (conservative patterns)
DEFAULT_PAGINATION_SELECTORS: List[str] = [
    # Aria label patterns
    'a[aria-label="Next"]',
    'a[aria-label="Next page"]',
    'button[aria-label="Next"]',
    'button[aria-label="Next page"]',
    
    # Rel attribute (standard HTML pagination)
    'a[rel="next"]',
    
    # Specific class names (common job board patterns)
    'a.next-page',
    'a.pagination-next',
    'button.next-page',
    'button.pagination-next',
    
    # Text content patterns (with Playwright :has-text)
    'nav a:has-text("Next")',
    'nav button:has-text("Next")',
    'div[role="navigation"] a:has-text("Next")',
    'div[role="navigation"] button:has-text("Next")',
    
    # "Load More" / "Show More" patterns
    'button:has-text("Show More")',
    'button:has-text("Load More")',
    'a:has-text("Show More")',
    'a:has-text("Load More")',
    
    # Strict pagination container patterns
    'nav.pagination a.next',
    'ul.pagination a.next',
    'div.pagination a.next',
    'nav[aria-label*="pagination" i] a:last-child',
]

# Pagination keywords for text content validation
PAGINATION_KEYWORDS: List[str] = [
    'next',
    'more',
    '>',
    '→',
    '»',
    'load more',
    'show more'
]

# Container selectors for default extraction
DEFAULT_CONTAINER_KEYWORDS: List[str] = [
    'job',
    'position',
    'role',
    'opening',
    'listing',
    'vacancy',
    'post-card',
    'posting',
    'opportunity'
]

# Result item data attribute patterns
RESULT_ITEM_PATTERNS: List[str] = [
    'li[data-qa*="ResultItem"]',
    'li[data-qa*="resultItem"]',
    'div[data-qa*="ResultItem"]',
    'div[data-qa*="resultItem"]',
    'li[data-qa="searchResultItem"]',
    'div[data-qa="searchResultItem"]'
]

# Job link href patterns
JOB_LINK_SELECTORS: List[str] = [
    'a[href*="/job/"]',
    'a[href*="/jobs/"]',
    'a[href*="/position/"]',
    'a[href*="/positions/"]',
    'a[href*="/opening/"]',
    'a[href*="/openings/"]',
    'a[href*="/role/"]',
    'a[href*="/roles/"]',
]

