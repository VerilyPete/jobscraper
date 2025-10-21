"""Default job extractor with comprehensive patterns."""
import logging
from typing import List, Dict, Optional, Set
from playwright.async_api import Page
from bs4 import BeautifulSoup

from .base import BaseExtractor
from ..url_utils import make_absolute_url, is_same_url, is_job_url, get_domain
from ..constants import (
    DEFAULT_CONTAINER_KEYWORDS,
    RESULT_ITEM_PATTERNS,
    DATA_ATTR_EXCLUSIONS,
    JOB_LINK_SELECTORS,
    MIN_TITLE_LENGTH,
    MIN_ROW_TEXT_LENGTH,
    NON_JOB_KEYWORDS,
    JOB_URL_PATTERNS
)

logger = logging.getLogger(__name__)


class DefaultExtractor(BaseExtractor):
    """Default extractor using comprehensive pattern matching."""
    
    async def extract(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Extract job listings using default generic logic.
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Optional timeout override
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        if timeout is None:
            timeout = self.timeout
        
        # Wait for page to be ready
        await self._wait_for_page_ready(page, wait_state, timeout)
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for common job listing container patterns
        job_containers = self._find_job_containers(soup)
        
        found_jobs: Set[str] = set()
        
        # Process job containers
        for container in job_containers:
            job = self._extract_job_from_container(container, page.url, found_jobs)
            if job:
                jobs.append(job)
        
        # Also check direct job links (for sites that don't use container elements)
        direct_jobs = self._extract_direct_job_links(soup, page.url, found_jobs)
        jobs.extend(direct_jobs)
        
        logger.debug(f"DefaultExtractor found {len(jobs)} jobs")
        return jobs
    
    def _find_job_containers(self, soup: BeautifulSoup) -> List:
        """Find all potential job containers on the page.
        
        Args:
            soup: BeautifulSoup parsed page content
            
        Returns:
            List of potential job container elements
        """
        job_containers = []
        
        # Pattern 1: Look for elements with job-related classes or data attributes
        for container_selector in ['article', 'li', 'div']:
            for keyword in DEFAULT_CONTAINER_KEYWORDS:
                try:
                    # Match keyword in class or id
                    containers = soup.select(f'{container_selector}[class*="{keyword}"]')
                    containers += soup.select(f'{container_selector}[id*="{keyword}"]')
                    # Also match data attributes
                    containers += soup.select(f'{container_selector}[data-qa*="{keyword}"]')
                    containers += soup.select(f'{container_selector}[data-testid*="{keyword}"]')
                    job_containers.extend(containers)
                except Exception as e:
                    logger.debug(f"Error with container selector: {e}")
                    continue
        
        # Pattern 1b: Some sites use data attributes without job-related keywords
        for selector in RESULT_ITEM_PATTERNS:
            try:
                containers = soup.select(selector)
                for container in containers:
                    # Exclude non-job items
                    data_qa = container.get('data-qa', '')
                    if any(exclude in data_qa.lower() for exclude in DATA_ATTR_EXCLUSIONS):
                        continue
                    job_containers.append(container)
            except Exception as e:
                logger.debug(f"Error with result item pattern: {e}")
                continue
        
        # Pattern 1c: Look for table rows
        table_rows = soup.select('table tr')
        for row in table_rows:
            if self._is_valid_table_row(row):
                job_containers.append(row)
        
        return job_containers
    
    def _is_valid_table_row(self, row: BeautifulSoup) -> bool:
        """Check if table row is a valid job listing.
        
        Args:
            row: BeautifulSoup table row element
            
        Returns:
            True if row contains a job listing
        """
        # Skip if in nav, header, or footer
        if self._should_exclude_by_parent(row):
            return False
        
        # Check if row has links with actual href
        links = row.find_all('a', href=True)
        has_valid_link = False
        for link in links:
            href = link.get('href', '')
            if href and href.startswith(('http', '/')):
                has_valid_link = True
                break
        
        if not has_valid_link:
            return False
        
        # Check if row has substantial text
        row_text = row.get_text(separator=' ', strip=True)
        return len(row_text) > MIN_ROW_TEXT_LENGTH
    
    def _extract_job_from_container(
        self,
        container: BeautifulSoup,
        page_url: str,
        found_jobs: Set[str]
    ) -> Optional[Dict[str, str]]:
        """Extract job from a single container.
        
        Args:
            container: BeautifulSoup container element
            page_url: Current page URL
            found_jobs: Set of already found job URLs
            
        Returns:
            Job dictionary or None if invalid
        """
        # Skip if in nav, header, or footer
        if self._should_exclude_by_parent(container):
            return None
        
        # Find the main link within the container
        link = container.find('a', href=True)
        if not link:
            return None
        
        url = link.get('href', '')
        if not url:
            return None
        
        # Make URL absolute
        url = make_absolute_url(url, page_url)
        
        # Skip non-http URLs
        if not url.startswith('http'):
            return None
        
        # Skip if it's the careers page itself or search/filter pages
        if is_same_url(url, page_url) or '/search' in url or '/filter' in url:
            return None
        
        # Check if URL looks like a job page
        page_domain = get_domain(page_url)
        if not is_job_url(url, page_domain, JOB_URL_PATTERNS):
            return None
        
        # Get title
        title = self._extract_title_for_container_type(container, link)
        
        # Skip if no meaningful title
        if not self._is_valid_title(title, MIN_TITLE_LENGTH):
            return None
        
        # Skip non-job items by title content
        if self._should_exclude_by_title(title, NON_JOB_KEYWORDS):
            return None
        
        # Get description
        description = container.get_text(separator=' ', strip=True)
        
        # Avoid duplicates
        if url in found_jobs:
            return None
        
        found_jobs.add(url)
        return {
            'title': title,
            'url': url,
            'description': description
        }
    
    def _extract_title_for_container_type(
        self,
        container: BeautifulSoup,
        link: BeautifulSoup
    ) -> str:
        """Extract title based on container type.
        
        Args:
            container: BeautifulSoup container element
            link: Link element within container
            
        Returns:
            Extracted title
        """
        title = ''
        
        # For table rows, special handling
        if container.name == 'tr':
            title = self._extract_title_from_table_row(container, link)
        else:
            # For other containers, look for headings first
            heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                title = heading.get_text(separator=' ', strip=True)
            else:
                # Try link text
                title = link.get_text(separator=' ', strip=True)
                if not title:
                    # Look for common job title elements
                    title_elem = container.find(
                        ['span', 'div', 'p'],
                        class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower())
                    )
                    if title_elem:
                        title = title_elem.get_text(separator=' ', strip=True)
                    else:
                        # Use first substantial text
                        all_text = container.get_text(separator=' ', strip=True)
                        title = all_text.split('\n')[0][:100].strip()
        
        return title
    
    def _extract_title_from_table_row(
        self,
        row: BeautifulSoup,
        link: BeautifulSoup
    ) -> str:
        """Extract title from table row.
        
        Args:
            row: Table row element
            link: Link element within row
            
        Returns:
            Extracted title
        """
        title = ''
        
        # Find cell containing the link
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
        
        return title
    
    def _extract_direct_job_links(
        self,
        soup: BeautifulSoup,
        page_url: str,
        found_jobs: Set[str]
    ) -> List[Dict[str, str]]:
        """Extract jobs from direct job links (not in containers).
        
        Args:
            soup: BeautifulSoup parsed page content
            page_url: Current page URL
            found_jobs: Set of already found job URLs
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for selector in JOB_LINK_SELECTORS:
            try:
                links = soup.select(selector)
                for link in links:
                    # Skip if in nav, header, or footer
                    if link.find_parent(['nav', 'header', 'footer']):
                        continue
                    
                    url = link.get('href', '')
                    if not url:
                        continue
                    
                    # Make URL absolute
                    url = make_absolute_url(url, page_url)
                    
                    # Skip non-http URLs
                    if not url.startswith('http'):
                        continue
                    
                    # Skip if it's the careers page itself
                    if is_same_url(url, page_url):
                        continue
                    
                    title = link.get_text(separator=' ', strip=True)
                    
                    # Skip if no meaningful title
                    if not self._is_valid_title(title, MIN_TITLE_LENGTH):
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
            except Exception as e:
                logger.debug(f"Error extracting direct job links with selector '{selector}': {e}")
                continue
        
        return jobs

