"""Base extractor class with common functionality."""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from playwright.async_api import Page
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for job extractors."""
    
    def __init__(self, timeout: int = 30000):
        """Initialize base extractor.
        
        Args:
            timeout: Default timeout in milliseconds
        """
        self.timeout = timeout
    
    @abstractmethod
    async def extract(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Extract jobs from the page.
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Optional timeout override
            **kwargs: Additional extractor-specific parameters
            
        Returns:
            List of job dictionaries with 'title', 'url', 'description'
        """
        pass
    
    async def _wait_for_page_ready(
        self,
        page: Page,
        wait_state: str,
        timeout: int
    ) -> None:
        """Wait for page to be ready for scraping.
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Timeout in milliseconds
        """
        try:
            await page.wait_for_load_state(wait_state, timeout=timeout)
        except Exception as e:
            logger.debug(f"Wait for load state '{wait_state}' timed out: {e}")
    
    def _extract_title_from_container(
        self,
        container: BeautifulSoup,
        title_selector: Optional[str] = None,
        link: Optional[BeautifulSoup] = None
    ) -> str:
        """Extract title from container using selector or fallback.
        
        Args:
            container: BeautifulSoup container element
            title_selector: Optional CSS selector for title
            link: Optional link element to extract text from
            
        Returns:
            Extracted title string
        """
        title = ''
        
        # Try custom title selector first
        if title_selector:
            title_elem = container.select_one(title_selector)
            if title_elem:
                title = title_elem.get_text(separator=' ', strip=True)
        
        # Fall back to link text if available
        if not title and link:
            title = link.get_text(separator=' ', strip=True)
        
        # Last resort: search for headings
        if not title:
            heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                title = heading.get_text(separator=' ', strip=True)
        
        return title
    
    def _extract_description_from_container(
        self,
        container: BeautifulSoup,
        description_selector: Optional[str] = None
    ) -> str:
        """Extract description from container.
        
        Args:
            container: BeautifulSoup container element
            description_selector: Optional CSS selector for description
            
        Returns:
            Extracted description string
        """
        if description_selector:
            desc_elem = container.select_one(description_selector)
            if desc_elem:
                return desc_elem.get_text(separator=' ', strip=True)
        
        # Fall back to all container text
        return container.get_text(separator=' ', strip=True)
    
    def _is_valid_title(self, title: str, min_length: int = 3) -> bool:
        """Check if title is valid (not empty and meets minimum length).
        
        Args:
            title: Title to validate
            min_length: Minimum required length
            
        Returns:
            True if title is valid
        """
        return bool(title) and len(title) >= min_length
    
    def _should_exclude_by_parent(self, element: BeautifulSoup) -> bool:
        """Check if element is in nav, header, or footer.
        
        Args:
            element: BeautifulSoup element to check
            
        Returns:
            True if element should be excluded
        """
        return bool(element.find_parent(['nav', 'header', 'footer']))
    
    def _should_exclude_by_title(
        self,
        title: str,
        exclude_keywords: List[str]
    ) -> bool:
        """Check if title contains excluded keywords.
        
        Args:
            title: Job title
            exclude_keywords: List of keywords to exclude
            
        Returns:
            True if title should be excluded
        """
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in exclude_keywords)
    
    def _should_exclude_by_url(
        self,
        url: str,
        exclude_patterns: List[str]
    ) -> bool:
        """Check if URL contains excluded patterns.
        
        Args:
            url: URL to check
            exclude_patterns: List of patterns to exclude
            
        Returns:
            True if URL should be excluded
        """
        return any(pattern in url for pattern in exclude_patterns)

