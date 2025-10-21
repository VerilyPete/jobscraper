"""Custom configuration-based job extractor."""
import logging
from typing import List, Dict, Optional
from playwright.async_api import Page
from bs4 import BeautifulSoup

from .base import BaseExtractor
from ..url_utils import make_absolute_url, is_same_url
from ..constants import MIN_TITLE_LENGTH

logger = logging.getLogger(__name__)


class CustomExtractor(BaseExtractor):
    """Extractor that uses custom scraping configuration."""
    
    async def extract(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        custom_config: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """Extract job listings using custom scraping configuration.
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Optional timeout override
            custom_config: Custom scraping configuration
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        found_jobs = set()
        
        if timeout is None:
            timeout = self.timeout
        
        if not custom_config:
            logger.warning("No custom config provided to CustomExtractor")
            return jobs
        
        # Wait for page to be ready
        await self._wait_for_page_ready(page, wait_state, timeout)
        
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
            try:
                containers = soup.select(selector)
                if containers:
                    job_containers = containers
                    logger.debug(f"Found {len(containers)} containers with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        # Process each container
        for container in job_containers:
            # Skip if in nav, header, or footer
            if self._should_exclude_by_parent(container):
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
            url = make_absolute_url(url, page.url)
            
            # Skip non-http URLs
            if not url.startswith('http'):
                continue
            
            # Check exclude URL patterns
            if self._should_exclude_by_url(url, exclude_urls):
                continue
            
            # Skip if it's the careers page itself
            if is_same_url(url, page.url):
                continue
            
            # Find title using custom selector
            title = self._extract_title_from_container(
                container,
                title_selector,
                link
            )
            
            # Skip if no meaningful title
            if not self._is_valid_title(title, MIN_TITLE_LENGTH):
                continue
            
            # Check exclude title patterns
            if self._should_exclude_by_title(title, exclude_titles):
                continue
            
            # Get description
            description = self._extract_description_from_container(
                container,
                description_selector
            )
            
            # Avoid duplicates
            if url not in found_jobs:
                found_jobs.add(url)
                jobs.append({
                    'title': title,
                    'url': url,
                    'description': description
                })
        
        logger.debug(f"CustomExtractor found {len(jobs)} jobs")
        return jobs

