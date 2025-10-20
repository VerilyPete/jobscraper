"""Web scraping functionality for job boards."""
import asyncio
import re
from typing import List, Dict, Set
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup


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
        """Initialize scraper with configuration."""
        self.config = config
        self.universal_keywords = [k.lower() for k in config.get("universal_keywords", [])]
        self.companies = config.get("companies", [])
        self.timeout = 30000  # 30 seconds
        self.max_pages = 10  # Safety limit for pagination
    
    def match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Check if any keywords match in the text (case-insensitive)."""
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
        
        Supports simple substring matching and basic wildcards.
        """
        if not text or not pattern:
            return False
        
        text_lower = text.lower()
        pattern_lower = pattern.lower()
        
        # Simple substring match
        return pattern_lower in text_lower
    
    def should_filter_by_location(self, text: str, location_filters: Dict) -> bool:
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
                return True  # Filter out (doesn't match any include pattern)
        
        # If exclude patterns are specified, job must not match any
        if exclude_patterns:
            matches_exclude = any(
                self.matches_location_pattern(text, pattern)
                for pattern in exclude_patterns
            )
            if matches_exclude:
                return True  # Filter out (matches an exclude pattern)
        
        return False  # Keep the job
    
    async def extract_jobs_with_custom_config(self, page: Page, custom_config: Dict, wait_state: str = 'networkidle', timeout: int = None) -> List[Dict[str, str]]:
        """Extract job listings using custom scraping configuration."""
        jobs = []
        found_jobs = set()
        
        if timeout is None:
            timeout = self.timeout
        
        # Wait for page to be ready
        await page.wait_for_load_state(wait_state, timeout=timeout)
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get custom selectors
        container_selectors = custom_config.get('container_selectors', [])
        link_selector = custom_config.get('link_selector')
        title_selector = custom_config.get('title_selector')
        description_selector = custom_config.get('description_selector')
        exclude_patterns = custom_config.get('exclude_patterns', {})
        exclude_urls = exclude_patterns.get('urls', [])
        exclude_titles = exclude_patterns.get('titles', [])
        
        # Try each container selector in order
        job_containers = []
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                job_containers = containers
                break
        
        # Process each container
        for container in job_containers:
            # Skip if in nav, header, or footer
            if container.find_parent(['nav', 'header', 'footer']):
                continue
            
            # Find link using custom selector or default
            if link_selector:
                link = container.select_one(link_selector)
            else:
                link = container.find('a', href=True)
            
            if not link:
                continue
            
            url = link.get('href', '')
            if not url:
                continue
            
            # Make URL absolute if needed
            if url.startswith('/'):
                url = page.url.split('/')[0] + '//' + page.url.split('/')[2] + url
            elif not url.startswith('http'):
                continue
            
            # Check exclude URL patterns
            if any(pattern in url for pattern in exclude_urls):
                continue
            
            # Skip if it's the careers page itself
            base_url = url.split('?')[0].rstrip('/')
            base_page_url = page.url.split('?')[0].rstrip('/')
            if base_url == base_page_url:
                continue
            
            # Find title using custom selector
            title = ''
            if title_selector:
                title_elem = container.select_one(title_selector)
                if title_elem:
                    title = title_elem.get_text(separator=' ', strip=True)
            else:
                # Fallback to link text
                title = link.get_text(separator=' ', strip=True)
            
            # Skip if no meaningful title
            if not title or len(title) < 3:
                continue
            
            # Check exclude title patterns
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in exclude_titles):
                continue
            
            # Get description
            if description_selector:
                desc_elem = container.select_one(description_selector)
                description = desc_elem.get_text(separator=' ', strip=True) if desc_elem else ''
            else:
                description = container.get_text(separator=' ', strip=True)
            
            # Avoid duplicates
            if url not in found_jobs:
                found_jobs.add(url)
                jobs.append({
                    'title': title,
                    'url': url,
                    'description': description
                })
        
        return jobs
    
    async def extract_jobs_from_iframe(self, page: Page, wait_state: str = 'networkidle', timeout: int = None) -> List[Dict[str, str]]:
        """Try to extract jobs from iframes on the page."""
        jobs = []
        
        try:
            # Get all frames (iframes)
            frames = page.frames
            
            for frame in frames:
                # Skip the main frame
                if frame == page.main_frame:
                    continue
                
                try:
                    # Wait for frame to load
                    await frame.wait_for_load_state(wait_state, timeout=timeout or self.timeout)
                    
                    # Get frame content
                    content = await frame.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Check if this looks like a job board (common indicators)
                    frame_text = soup.get_text().lower()
                    job_indicators = ['job', 'position', 'career', 'opening', 'apply', 'role']
                    has_job_content = any(indicator in frame_text for indicator in job_indicators)
                    
                    if not has_job_content:
                        continue
                    
                    # Try to extract jobs using similar logic to main extraction
                    job_containers = []
                    
                    # Look for common job listing patterns (Greenhouse and similar ATS)
                    # Be specific to avoid picking up navigation/header elements
                    for selector in [
                        '.opening',  # Greenhouse uses this
                        'div.opening',
                        'section.level-0',  # Some Greenhouse boards
                        'div[id*="job"]',  # Jobs with IDs
                    ]:
                        containers = soup.select(selector)
                        job_containers.extend(containers)
                    
                    # Deduplicate containers
                    seen_containers = set()
                    unique_containers = []
                    for container in job_containers:
                        container_id = id(container)
                        if container_id not in seen_containers:
                            seen_containers.add(container_id)
                            unique_containers.append(container)
                    
                    # Process containers
                    for container in unique_containers:
                        link = container.find('a', href=True)
                        if not link:
                            continue
                        
                        url = link.get('href', '')
                        if not url or url.startswith('#'):
                            continue
                        
                        # Filter out non-job URLs (navigation, etc.)
                        url_lower = url.lower()
                        exclude_patterns = ['/embed/', '/careers$', '/careers/$', '/careers#', '#', 'javascript:', 'mailto:']
                        if any(pattern in url_lower for pattern in exclude_patterns):
                            continue
                        
                        # Job URLs should have some path beyond just the base
                        if url.count('/') < 4:  # e.g., https://domain.com/job/123 has 4 slashes
                            continue
                        
                        # Make URL absolute if needed
                        if not url.startswith('http'):
                            frame_url = frame.url
                            if url.startswith('/'):
                                # Get base URL from frame
                                from urllib.parse import urlparse
                                parsed = urlparse(frame_url)
                                url = f"{parsed.scheme}://{parsed.netloc}{url}"
                            else:
                                url = f"{frame_url.rsplit('/', 1)[0]}/{url}"
                        
                        # Extract title
                        title = ''
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                        if title_elem:
                            title = title_elem.get_text(separator=' ', strip=True)
                        elif link.get_text(strip=True):
                            title = link.get_text(separator=' ', strip=True)
                        
                        if not title:
                            continue
                        
                        # Filter out non-job titles
                        title_lower = title.lower()
                        exclude_titles = ['view all', 'see all', 'back to', 'home', 'careers', 'about', 'apply']
                        if any(exclude in title_lower for exclude in exclude_titles):
                            continue
                        
                        # Title should have some substance (more than just a location or department)
                        if len(title.split()) < 2:
                            continue
                        
                        # Extract description
                        description = ''
                        desc_elem = container.find(['p', 'div'])
                        if desc_elem:
                            description = desc_elem.get_text(separator=' ', strip=True)
                        
                        job_key = (url, title)
                        if job_key not in [(j['url'], j['title']) for j in jobs]:
                            jobs.append({
                                'url': url,
                                'title': title,
                                'description': description
                            })
                    
                    print(f"   ℹ Found {len(jobs)} jobs in iframe")
                    
                except Exception:
                    # Frame might be inaccessible or errored, skip it
                    continue
                    
        except Exception:
            # If iframe extraction fails entirely, return empty list
            pass
        
        return jobs
    
    async def extract_jobs_from_page(self, page: Page, wait_state: str = 'networkidle', timeout: int = None, custom_config: Dict = None, use_iframe: bool = False) -> List[Dict[str, str]]:
        """Extract job listings from current page."""
        # If custom config provided, use custom extraction logic
        if custom_config:
            return await self.extract_jobs_with_custom_config(page, custom_config, wait_state, timeout)
        
        # Only try iframe extraction if explicitly enabled
        if use_iframe:
            iframe_jobs = await self.extract_jobs_from_iframe(page, wait_state, timeout)
            if iframe_jobs:
                return iframe_jobs
        
        # Otherwise, use default generic logic on main page
        jobs = []
        
        if timeout is None:
            timeout = self.timeout
        
        # Wait for page to be ready
        await page.wait_for_load_state(wait_state, timeout=timeout)
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for common job listing container patterns first
        # These are more specific patterns for actual job listings
        job_containers = []
        
        # Pattern 1: Look for article, li, or div elements that contain job-related classes or data attributes
        for container_selector in ['article', 'li', 'div']:
            for keyword in ['job', 'position', 'role', 'opening', 'listing', 'vacancy', 'post-card', 'posting', 'opportunity']:
                # Match keyword in class or id (with or without hyphens)
                containers = soup.select(f'{container_selector}[class*="{keyword}"]')
                containers += soup.select(f'{container_selector}[id*="{keyword}"]')
                # Also match data attributes (e.g., data-qa="searchResultItem")
                containers += soup.select(f'{container_selector}[data-qa*="{keyword}"]')
                containers += soup.select(f'{container_selector}[data-testid*="{keyword}"]')
                job_containers.extend(containers)
        
        # Pattern 1b: Some sites use data attributes without job-related keywords (e.g., Oracle)
        # Look for common patterns like data-qa="searchResultItem" or similar
        # But exclude talent community / non-job items
        for selector in ['li[data-qa*="ResultItem"]', 'li[data-qa*="resultItem"]', 
                        'div[data-qa*="ResultItem"]', 'div[data-qa*="resultItem"]',
                        'li[data-qa="searchResultItem"]', 'div[data-qa="searchResultItem"]']:
            containers = soup.select(selector)
            for container in containers:
                # Exclude talent community, events, and other non-job items
                data_qa = container.get('data-qa', '')
                if any(exclude in data_qa.lower() for exclude in ['talent', 'community', 'event', 'tcjoin']):
                    continue
                job_containers.append(container)
        
        # Pattern 1c: Look for table rows that might contain job listings
        # Some sites (like Mux) display jobs in tables
        table_rows = soup.select('table tr')
        for row in table_rows:
            # Skip if in nav, header, or footer
            if row.find_parent(['nav', 'header', 'footer']):
                continue
            
            # Check if row has links with actual href (potential job links)
            links = row.find_all('a', href=True)
            has_valid_link = False
            for link in links:
                href = link.get('href', '')
                # Check if it's an actual URL (not just # or empty)
                if href and href.startswith(('http', '/')):
                    has_valid_link = True
                    break
            
            if has_valid_link:
                # Check if row has substantial text (not just navigation)
                row_text = row.get_text(separator=' ', strip=True)
                if len(row_text) > 10:  # Has meaningful content
                    job_containers.append(row)
        
        # Pattern 2: Look for links with job-specific patterns in href
        # But exclude navigation/footer links by checking they're not in nav/footer/header
        job_link_selectors = [
            'a[href*="/job/"]',
            'a[href*="/jobs/"]',
            'a[href*="/position/"]',
            'a[href*="/positions/"]',
            'a[href*="/opening/"]',
            'a[href*="/openings/"]',
            'a[href*="/role/"]',
            'a[href*="/roles/"]',
        ]
        
        found_jobs = set()
        
        # Process job containers
        for container in job_containers:
            # Skip if container is within nav, header, or footer
            if container.find_parent(['nav', 'header', 'footer']):
                continue
            
            # Find the main link within the container
            link = container.find('a', href=True)
            if not link:
                continue
            
            url = link.get('href', '')
            if not url:
                continue
            
            # Make URL absolute if needed
            if url.startswith('/'):
                url = page.url.split('/')[0] + '//' + page.url.split('/')[2] + url
            elif not url.startswith('http'):
                continue
            
            # Skip if it's a navigation link (points back to careers page itself)
            # Also skip if it's pointing to search/filter pages
            base_url = url.split('?')[0].rstrip('/')
            base_page_url = page.url.split('?')[0].rstrip('/')
            if base_url == base_page_url or '/search' in base_url or '/filter' in base_url:
                continue
            
            # Skip URLs that don't look like individual job pages
            # Job pages typically have patterns like /job/, /jobs/, /position/, /career/, etc.
            # But allow external job boards (different domain than the careers page)
            job_url_patterns = ['/job/', '/jobs/', '/position/', '/positions/', '/career/', '/careers/', '/opening/', '/openings/']
            page_domain = page.url.split('/')[2]
            link_domain = url.split('/')[2] if url.startswith('http') else page_domain
            
            # If it's on the same domain, require job-related URL patterns
            # If it's an external domain (like ashbyhq.com, greenhouse.io, etc.), allow it
            if link_domain == page_domain and not any(pattern in url.lower() for pattern in job_url_patterns):
                continue
            
            # Get title from the link or a heading in the container
            title = ''
            
            # For table rows, get title from headings within cells or link text
            if container.name == 'tr':
                # First check if there's a heading within the row (more reliable)
                cell_with_link = link.find_parent(['td', 'th'])
                if cell_with_link:
                    # Look for heading within this cell
                    heading_in_cell = cell_with_link.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if heading_in_cell:
                        title = heading_in_cell.get_text(separator=' ', strip=True)
                    else:
                        # Fall back to link text
                        title = link.get_text(separator=' ', strip=True)
                        if not title:
                            # Use cell text as last resort
                            title = cell_with_link.get_text(separator=' ', strip=True)
                else:
                    # No cell found, use link text
                    title = link.get_text(separator=' ', strip=True)
            else:
                # For other containers, look for headings first
                heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    title = heading.get_text(separator=' ', strip=True)
                else:
                    # For links without text, try to find a title element or use the container's first text
                    title = link.get_text(separator=' ', strip=True)
                    if not title:
                        # Look for common job title elements
                        title_elem = container.find(['span', 'div', 'p'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                        if title_elem:
                            title = title_elem.get_text(separator=' ', strip=True)
                        else:
                            # Use the first substantial text in the container
                            all_text = container.get_text(separator=' ', strip=True)
                            # Take first line/chunk (up to first newline or 100 chars)
                            title = all_text.split('\n')[0][:100].strip()
            
            # Skip if no meaningful title
            if not title or len(title) < 3:
                continue
            
            # Skip non-job items by title content
            title_lower = title.lower()
            non_job_keywords = ['talent network', 'join our', 'join the', 'talent community', 
                               'sign up', 'career alert', 'job alert', 'newsletter', 
                               'filter', 'sort by', 'results', 'open positions', 'our values',
                               'company values', 'benefits', 'perks']
            if any(keyword in title_lower for keyword in non_job_keywords):
                continue
            
            # Get description
            description = container.get_text(separator=' ', strip=True)
            
            # Avoid duplicates
            if url not in found_jobs:
                found_jobs.add(url)
                jobs.append({
                    'title': title,
                    'url': url,
                    'description': description
                })
        
        # Also check direct job links (for sites that don't use container elements)
        for selector in job_link_selectors:
            links = soup.select(selector)
            for link in links:
                # Skip if in nav, header, or footer
                if link.find_parent(['nav', 'header', 'footer']):
                    continue
                
                url = link.get('href', '')
                if not url:
                    continue
                
                # Make URL absolute if needed
                if url.startswith('/'):
                    url = page.url.split('/')[0] + '//' + page.url.split('/')[2] + url
                elif not url.startswith('http'):
                    continue
                
                # Skip if it's a navigation link
                if url == page.url or url.rstrip('/') == page.url.rstrip('/'):
                    continue
                
                title = link.get_text(separator=' ', strip=True)
                
                # Skip if no meaningful title
                if not title or len(title) < 3:
                    continue
                
                # Get description from parent
                description = ''
                parent = link.parent
                if parent:
                    description = parent.get_text(separator=' ', strip=True)
                
                # Avoid duplicates
                if url not in found_jobs:
                    found_jobs.add(url)
                    jobs.append({
                        'title': title,
                        'url': url,
                        'description': description
                    })
        
        return jobs
    
    async def check_for_next_page(self, page: Page, custom_pagination_selectors: List[str] = None) -> bool:
        """Check if there's a next page and navigate to it."""
        # If custom pagination selectors provided, use only those
        if custom_pagination_selectors is not None:
            # Empty array means no pagination
            if not custom_pagination_selectors:
                return False
            next_selectors = custom_pagination_selectors
        else:
            # Conservative pagination patterns - only match actual pagination controls
            # Be very specific to avoid false positives
            next_selectors = [
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
        
        for selector in next_selectors:
            try:
                next_button = page.locator(selector).first
                if await next_button.is_visible(timeout=1000):
                    # Double-check it's actually a next button by checking text
                    text = await next_button.text_content()
                    if text:
                        text_lower = text.lower().strip()
                        # Only click if it looks like a next/more button
                        pagination_keywords = ['next', 'more', '>', '→', '»', 'load more', 'show more']
                        if any(keyword in text_lower for keyword in pagination_keywords) or any(symbol in text for symbol in ['>', '→', '»']):
                            await next_button.click()
                            await page.wait_for_load_state('networkidle', timeout=self.timeout)
                            return True
            except:
                continue
        
        return False
    
    async def execute_pre_scrape_actions(self, page: Page, actions: List[Dict]) -> None:
        """Execute pre-scrape actions before extracting jobs."""
        if not actions:
            return
        
        print(f"   Executing {len(actions)} pre-scrape action(s)...")
        
        for i, action in enumerate(actions):
            action_type = action.get('type')
            selector = action.get('selector')
            value = action.get('value')
            wait_for_network_idle = action.get('wait_for_network_idle', False)
            action_timeout = action.get('timeout', 5000)
            repeat_until_gone = action.get('repeat_until_gone', False)
            wait_after = action.get('wait_after', 500)  # ms to wait after each action
            max_repeats = action.get('max_repeats', 50)  # Safety limit for repeating actions
            
            try:
                if repeat_until_gone and action_type == 'click':
                    # Keep clicking until element is no longer visible
                    click_count = 0
                    while click_count < max_repeats:
                        try:
                            locator = page.locator(selector).first
                            # Check if element is visible with a short timeout
                            await locator.wait_for(state='visible', timeout=2000)
                            await locator.click()
                            click_count += 1
                            print(f"   ✓ Action {i+1}: {action_type} on {selector[:50]}... (click {click_count})")
                            # Wait after click
                            await asyncio.sleep(wait_after / 1000)
                        except Exception:
                            # Element no longer visible or clickable
                            print(f"   ✓ Action {i+1} complete after {click_count} clicks (element gone)")
                            break
                    
                    if click_count >= max_repeats:
                        print(f"   ⚠ Action {i+1} stopped after {max_repeats} clicks (max limit)")
                else:
                    # Single execution
                    locator = page.locator(selector).first
                    
                    # Wait for element to be visible
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
                        # Just wait for element to be visible (already done above)
                        pass
                    else:
                        print(f"   ⚠ Unknown action type: {action_type}")
                        continue
                    
                    print(f"   ✓ Action {i+1}: {action_type} on {selector[:50]}...")
                    
                    # Wait for network to settle if requested
                    if wait_for_network_idle:
                        try:
                            await page.wait_for_load_state('networkidle', timeout=self.timeout)
                        except:
                            # If networkidle times out, continue anyway
                            print(f"   ⚠ Network idle timeout after action {i+1}, continuing...")
                    else:
                        # Small delay to let UI update
                        await asyncio.sleep(wait_after / 1000)
                    
            except Exception as e:
                print(f"   ⚠ Failed action {i+1} ({action_type}): {str(e)[:100]}")
                # Continue with remaining actions
                continue
    
    async def scrape_company(self, browser, company: Dict) -> List[JobMatch]:
        """Scrape jobs from a single company."""
        company_name = company.get('name', 'Unknown')
        job_board_url = company.get('job_board_url', '')
        company_keywords = [k.lower() for k in company.get('keywords', [])]
        location_filters = company.get('location_filters', None)
        # Allow per-company timeout override (in milliseconds)
        timeout = company.get('timeout', self.timeout)
        # Allow per-company wait state override ('networkidle', 'load', 'domcontentloaded')
        wait_for_load_state = company.get('wait_for_load_state', 'networkidle')
        # Allow per-company custom scraping configuration
        scraping_config = company.get('scraping_config', None)
        # Allow per-company iframe extraction
        use_iframe = company.get('use_iframe', False)
        
        # Combine universal and company-specific keywords
        all_keywords = list(set(self.universal_keywords + company_keywords))
        
        if not job_board_url:
            print(f"⚠ Skipping {company_name}: No job board URL")
            return []
        
        print(f"\n🔍 Scraping {company_name}...")
        print(f"   URL: {job_board_url}")
        print(f"   Keywords: {', '.join(all_keywords)}")
        
        matches = []
        
        try:
            # Create page with reasonable viewport size to ensure filters/controls are visible
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            await page.goto(job_board_url, timeout=timeout)
            
            # Execute pre-scrape actions if configured
            pre_scrape_actions = company.get('pre_scrape_actions', [])
            if pre_scrape_actions:
                await self.execute_pre_scrape_actions(page, pre_scrape_actions)
            
            page_count = 0
            all_jobs = []
            
            # Scrape first page and handle pagination
            while page_count < self.max_pages:
                page_count += 1
                print(f"   Scraping page {page_count}...")
                
                jobs = await self.extract_jobs_from_page(page, wait_state=wait_for_load_state, timeout=timeout, custom_config=scraping_config, use_iframe=use_iframe)
                all_jobs.extend(jobs)
                
                # Check for next page
                custom_pagination = scraping_config.get('pagination_selectors') if scraping_config else None
                has_next = await self.check_for_next_page(page, custom_pagination_selectors=custom_pagination)
                if not has_next:
                    break
                
                # Small delay to be respectful
                await asyncio.sleep(1)
            
            # Deduplicate jobs by URL (in case DOM contains duplicates after dynamic loading)
            unique_jobs = {}
            for job in all_jobs:
                unique_jobs[job['url']] = job
            all_jobs = list(unique_jobs.values())
            
            print(f"   Found {len(all_jobs)} job listings")
            
            # Match keywords and apply filters
            location_filtered = 0
            for job in all_jobs:
                combined_text = f"{job['title']} {job['description']}"
                
                # Apply location filters if configured for this company
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
                print(f"   ℹ Filtered out {location_filtered} job(s) by location")
            print(f"   ✓ Found {len(matches)} matching jobs")
            
            await page.close()
            
        except PlaywrightTimeout:
            print(f"   ⚠ Timeout loading {company_name}")
        except Exception as e:
            print(f"   ⚠ Error scraping {company_name}: {str(e)}")
        
        return matches
    
    async def scrape_all(self) -> List[JobMatch]:
        """Scrape all companies and return matches."""
        if not self.companies:
            print("No companies configured. Use --configure to add companies.")
            return []
        
        print(f"Starting job scraper...")
        print(f"Universal keywords: {', '.join(self.universal_keywords) if self.universal_keywords else 'None'}")
        print(f"Companies to scrape: {len(self.companies)}")
        
        all_matches = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for company in self.companies:
                matches = await self.scrape_company(browser, company)
                all_matches.extend(matches)
            
            await browser.close()
        
        return all_matches


def run_scraper(config: Dict) -> List[JobMatch]:
    """Synchronous wrapper for scraper."""
    scraper = JobScraper(config)
    return asyncio.run(scraper.scrape_all())

