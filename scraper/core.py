"""Core job scraper functionality."""
import asyncio
import re
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .extractors import CustomExtractor, ClickingExtractor, IframeExtractor, DefaultExtractor
from .constants import (
    DEFAULT_TIMEOUT_MS,
    MAX_PAGINATION_PAGES,
    DEFAULT_ACTION_WAIT_MS,
    RESPECTFUL_DELAY_MS,
    PAGINATION_KEYWORDS,
    DEFAULT_PAGINATION_SELECTORS
)

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((PlaywrightTimeout, Exception)),
    reraise=True
)
async def _goto_with_retry(page: Page, url: str, timeout: int) -> None:
    """Navigate to URL with automatic retry on failure.
    
    Retries up to 3 times with exponential backoff (4-10 seconds) on network failures.
    
    Args:
        page: Playwright page object
        url: URL to navigate to
        timeout: Timeout in milliseconds
    """
    logger.debug(f"Attempting to navigate to {url}")
    await page.goto(url, timeout=timeout, wait_until='commit')


class JobMatch:
    """Represents a matched job posting."""
    
    def __init__(self, title: str, url: str, company: str, matched_keywords: List[str]):
        self.title = title
        self.url = url
        self.company = company
        self.matched_keywords = matched_keywords
    
    def __repr__(self):
        return f"JobMatch(title={self.title}, company={self.company})"


class JobScraper:
    """Scrapes job boards for matching positions."""
    
    def __init__(self, config: Dict):
        """Initialize scraper with configuration.
        
        Args:
            config: Configuration dictionary with universal_keywords and companies
        """
        self.config = config
        self.universal_keywords = [k.lower() for k in config.get("universal_keywords", [])]
        self.companies = config.get("companies", [])
        self.timeout = DEFAULT_TIMEOUT_MS
        self.max_pages = MAX_PAGINATION_PAGES
        
        # Initialize extractors
        self.custom_extractor = CustomExtractor(timeout=self.timeout)
        self.clicking_extractor = ClickingExtractor(timeout=self.timeout)
        self.iframe_extractor = IframeExtractor(timeout=self.timeout)
        self.default_extractor = DefaultExtractor(timeout=self.timeout)
    
    # Backwards compatibility methods for tests
    async def extract_jobs_with_custom_config(self, page: Page, custom_config: Dict, wait_state: str = 'networkidle', timeout: Optional[int] = None) -> List[Dict[str, str]]:
        """Backwards compatibility wrapper for extract_jobs_with_custom_config."""
        return await self.custom_extractor.extract(page, wait_state, timeout, custom_config=custom_config)
    
    async def extract_jobs_by_clicking(self, page: Page, custom_config: Dict, wait_state: str = 'networkidle', timeout: Optional[int] = None) -> List[Dict[str, str]]:
        """Backwards compatibility wrapper for extract_jobs_by_clicking."""
        return await self.clicking_extractor.extract(page, wait_state, timeout, custom_config=custom_config)
    
    async def extract_jobs_from_iframe(self, page: Page, wait_state: str = 'networkidle', timeout: Optional[int] = None) -> List[Dict[str, str]]:
        """Backwards compatibility wrapper for extract_jobs_from_iframe."""
        return await self.iframe_extractor.extract(page, wait_state, timeout)
    
    def match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Check if any keywords match in the text (case-insensitive).
        
        Args:
            text: Text to search in
            keywords: List of keywords to match
            
        Returns:
            List of matched keywords
        """
        if not text or not keywords:
            return []
        
        text_lower = text.lower()
        matched = []
        
        for keyword in keywords:
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(keyword)
        
        return matched
    
    def matches_location_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches a location pattern (case-insensitive).
        
        Args:
            text: Text to check
            pattern: Location pattern to match
            
        Returns:
            True if pattern matches
        """
        if not text or not pattern:
            return False
        
        text_lower = text.lower()
        pattern_lower = pattern.lower()
        
        return pattern_lower in text_lower
    
    def should_filter_by_location(self, text: str, location_filters: Optional[Dict]) -> bool:
        """Check if job should be filtered based on location filters.
        
        Args:
            text: Job text (title + description)
            location_filters: Dict with 'include' and/or 'exclude' arrays
        
        Returns:
            True if job should be filtered out, False if it should be kept
        """
        if not location_filters:
            return False
        
        include_patterns = location_filters.get('include', [])
        exclude_patterns = location_filters.get('exclude', [])
        
        # If include patterns are specified, job must match at least one
        if include_patterns:
            matches_include = any(
                self.matches_location_pattern(text, pattern)
                for pattern in include_patterns
            )
            if not matches_include:
                return True  # Filter out
        
        # If exclude patterns are specified, job must not match any
        if exclude_patterns:
            matches_exclude = any(
                self.matches_location_pattern(text, pattern)
                for pattern in exclude_patterns
            )
            if matches_exclude:
                return True  # Filter out
        
        return False  # Keep the job
    
    async def extract_jobs_from_page(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        custom_config: Optional[Dict] = None,
        use_iframe: bool = False
    ) -> List[Dict[str, str]]:
        """Extract job listings from current page.
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Optional timeout override
            custom_config: Optional custom scraping configuration
            use_iframe: Whether to extract from iframes
            
        Returns:
            List of job dictionaries
        """
        # If custom config provided with JavaScript navigation, use clicking method
        if custom_config and custom_config.get('use_js_navigation', False):
            return await self.clicking_extractor.extract(
                page, wait_state, timeout, custom_config=custom_config
            )
        
        # If custom config provided, use custom extraction logic
        if custom_config:
            return await self.custom_extractor.extract(
                page, wait_state, timeout, custom_config=custom_config
            )
        
        # Only try iframe extraction if explicitly enabled
        if use_iframe:
            iframe_jobs = await self.iframe_extractor.extract(page, wait_state, timeout)
            if iframe_jobs:
                return iframe_jobs
        
        # Otherwise, use default generic logic
        return await self.default_extractor.extract(page, wait_state, timeout)
    
    async def check_for_next_page(
        self,
        page: Page,
        custom_pagination_selectors: Optional[List[str]] = None
    ) -> bool:
        """Check if there's a next page and navigate to it.
        
        Args:
            page: Playwright page object
            custom_pagination_selectors: Optional custom pagination selectors
            
        Returns:
            True if navigated to next page, False otherwise
        """
        # If custom pagination selectors provided, use only those
        if custom_pagination_selectors is not None:
            # Empty array means no pagination
            if not custom_pagination_selectors:
                return False
            next_selectors = custom_pagination_selectors
        else:
            next_selectors = DEFAULT_PAGINATION_SELECTORS
        
        for selector in next_selectors:
            try:
                next_button = page.locator(selector).first
                if await next_button.is_visible(timeout=1000):
                    # Double-check it's actually a next button by checking text
                    text = await next_button.text_content()
                    if text:
                        text_lower = text.lower().strip()
                        # Only click if it looks like a next/more button
                        if any(keyword in text_lower for keyword in PAGINATION_KEYWORDS) or \
                           any(symbol in text for symbol in ['>', '→', '»']):
                            await next_button.click()
                            await page.wait_for_load_state('networkidle', timeout=self.timeout)
                            return True
            except Exception as e:
                logger.debug(f"Pagination selector '{selector}' failed: {e}")
                continue
        
        return False
    
    async def execute_pre_scrape_actions(self, page: Page, actions: List[Dict]) -> None:
        """Execute pre-scrape actions before extracting jobs.
        
        Args:
            page: Playwright page object
            actions: List of action dictionaries
        """
        if not actions:
            return
        
        logger.info(f"Executing {len(actions)} pre-scrape action(s)...")
        
        for i, action in enumerate(actions):
            action_type = action.get('type')
            selector = action.get('selector')
            value = action.get('value')
            wait_for_network_idle = action.get('wait_for_network_idle', False)
            action_timeout = action.get('timeout', 5000)
            repeat_until_gone = action.get('repeat_until_gone', False)
            wait_after = action.get('wait_after', DEFAULT_ACTION_WAIT_MS)
            max_repeats = action.get('max_repeats', 50)
            
            try:
                if repeat_until_gone and action_type == 'click':
                    # Keep clicking until element is no longer visible
                    click_count = 0
                    while click_count < max_repeats:
                        try:
                            locator = page.locator(selector).first
                            await locator.wait_for(state='visible', timeout=2000)
                            await locator.click()
                            click_count += 1
                            logger.info(f"Action {i+1}: {action_type} on {selector[:50]}... (click {click_count})")
                            await asyncio.sleep(wait_after / 1000)
                        except Exception:
                            logger.info(f"Action {i+1} complete after {click_count} clicks (element gone)")
                            break
                    
                    if click_count >= max_repeats:
                        logger.warning(f"Action {i+1} stopped after {max_repeats} clicks (max limit)")
                else:
                    # Single execution
                    locator = page.locator(selector).first
                    await locator.wait_for(state='visible', timeout=action_timeout)
                    
                    # Perform action
                    if action_type == 'click':
                        await locator.click()
                    elif action_type == 'fill':
                        await locator.fill(value or '')
                    elif action_type == 'select':
                        await locator.select_option(value)
                    elif action_type == 'check':
                        await locator.check()
                    elif action_type == 'uncheck':
                        await locator.uncheck()
                    elif action_type == 'press':
                        await locator.press(value or 'Enter')
                    elif action_type == 'hover':
                        await locator.hover()
                    elif action_type == 'wait':
                        pass  # Just wait for element to be visible (already done)
                    else:
                        logger.warning(f"Unknown action type: {action_type}")
                        continue
                    
                    logger.info(f"Action {i+1}: {action_type} on {selector[:50]}...")
                    
                    # Wait for network to settle if requested
                    if wait_for_network_idle:
                        try:
                            await page.wait_for_load_state('networkidle', timeout=self.timeout)
                        except Exception:
                            logger.warning(f"Network idle timeout after action {i+1}, continuing...")
                    else:
                        await asyncio.sleep(wait_after / 1000)
                    
            except Exception as e:
                logger.warning(f"Failed action {i+1} ({action_type}): {str(e)[:100]}")
                continue
    
    async def scrape_company(self, browser, company: Dict) -> List[JobMatch]:
        """Scrape jobs from a single company.
        
        Args:
            browser: Playwright browser instance
            company: Company configuration dictionary
            
        Returns:
            List of JobMatch objects
        """
        company_name = company.get('name', 'Unknown')
        job_board_url = company.get('job_board_url', '')
        company_keywords = [k.lower() for k in company.get('keywords', [])]
        location_filters = company.get('location_filters', None)
        timeout = company.get('timeout', self.timeout)
        wait_for_load_state = company.get('wait_for_load_state', 'networkidle')
        scraping_config = company.get('scraping_config', None)
        use_iframe = company.get('use_iframe', False)
        
        # Combine universal and company-specific keywords
        all_keywords = list(set(self.universal_keywords + company_keywords))
        
        if not job_board_url:
            logger.warning(f"Skipping {company_name}: No job board URL")
            return []
        
        logger.info(f"\nScraping {company_name}...")
        logger.info(f"URL: {job_board_url}")
        logger.info(f"Keywords: {', '.join(all_keywords)}")
        
        matches = []
        
        try:
            # Create page with reasonable viewport size
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            await _goto_with_retry(page, job_board_url, timeout)
            
            # Execute pre-scrape actions if configured
            pre_scrape_actions = company.get('pre_scrape_actions', [])
            if pre_scrape_actions:
                await self.execute_pre_scrape_actions(page, pre_scrape_actions)
            
            page_count = 0
            all_jobs = []
            
            # Get max_pages override or use default
            company_max_pages = company.get('max_pages', self.max_pages)
            
            # Scrape first page and handle pagination
            while page_count < company_max_pages:
                page_count += 1
                logger.info(f"Scraping page {page_count}...")
                
                jobs = await self.extract_jobs_from_page(
                    page,
                    wait_state=wait_for_load_state,
                    timeout=timeout,
                    custom_config=scraping_config,
                    use_iframe=use_iframe
                )
                all_jobs.extend(jobs)
                
                # Check for next page
                custom_pagination = scraping_config.get('pagination_selectors') if scraping_config else None
                has_next = await self.check_for_next_page(page, custom_pagination_selectors=custom_pagination)
                if not has_next:
                    break
                
                # Small delay to be respectful
                await asyncio.sleep(RESPECTFUL_DELAY_MS / 1000)
            
            # Deduplicate jobs by URL
            unique_jobs = {}
            for job in all_jobs:
                unique_jobs[job['url']] = job
            all_jobs = list(unique_jobs.values())
            
            logger.info(f"Found {len(all_jobs)} job listings")
            
            # Match keywords and apply filters
            location_filtered = 0
            for job in all_jobs:
                combined_text = f"{job['title']} {job['description']}"
                
                # Apply location filters
                if self.should_filter_by_location(combined_text, location_filters):
                    location_filtered += 1
                    continue
                
                matched_keywords = self.match_keywords(combined_text, all_keywords)
                
                if matched_keywords:
                    matches.append(JobMatch(
                        title=job['title'],
                        url=job['url'],
                        company=company_name,
                        matched_keywords=matched_keywords
                    ))
            
            if location_filtered > 0:
                logger.info(f"Filtered out {location_filtered} job(s) by location")
            logger.info(f"Found {len(matches)} matching jobs")
            
            await page.close()
            
        except PlaywrightTimeout:
            logger.warning(f"Timeout loading {company_name}")
        except Exception as e:
            logger.error(f"Error scraping {company_name}: {str(e)}")
        
        return matches
    
    async def scrape_all(self) -> List[JobMatch]:
        """Scrape all companies and return matches.
        
        Returns:
            List of all JobMatch objects
        """
        if not self.companies:
            logger.warning("No companies configured. Use --configure to add companies.")
            return []
        
        logger.info("Starting job scraper...")
        logger.info(f"Universal keywords: {', '.join(self.universal_keywords) if self.universal_keywords else 'None'}")
        logger.info(f"Companies to scrape: {len(self.companies)}")
        
        all_matches = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for company in self.companies:
                matches = await self.scrape_company(browser, company)
                all_matches.extend(matches)
            
            await browser.close()
        
        return all_matches


def run_scraper(config: Dict) -> List[JobMatch]:
    """Synchronous wrapper for scraper.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of JobMatch objects
    """
    scraper = JobScraper(config)
    return asyncio.run(scraper.scrape_all())

