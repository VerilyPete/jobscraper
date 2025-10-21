"""Iframe-based job extractor."""
import logging
from typing import List, Dict, Optional
from playwright.async_api import Page
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .base import BaseExtractor
from ..url_utils import make_absolute_url
from ..constants import (
    IFRAME_JOB_SELECTORS,
    JOB_INDICATORS,
    EXCLUDE_URL_PATTERNS,
    EXCLUDE_TITLE_KEYWORDS,
    MIN_URL_DEPTH,
    MIN_TITLE_WORDS
)

logger = logging.getLogger(__name__)


class IframeExtractor(BaseExtractor):
    """Extractor for jobs embedded in iframes (Greenhouse, Breezy HR, etc.)."""
    
    async def extract(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Try to extract jobs from iframes on the page.
        
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
        
        try:
            # Get all frames (iframes)
            frames = page.frames
            
            for frame in frames:
                # Skip the main frame
                if frame == page.main_frame:
                    continue
                
                try:
                    # Wait for frame to load
                    await frame.wait_for_load_state(wait_state, timeout=timeout)
                    
                    # Get frame content
                    content = await frame.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Check if this looks like a job board (common indicators)
                    if not self._has_job_content(soup):
                        continue
                    
                    # Extract jobs from this iframe
                    frame_jobs = await self._extract_jobs_from_frame(soup, frame)
                    jobs.extend(frame_jobs)
                    
                    logger.info(f"Found {len(frame_jobs)} jobs in iframe")
                    
                except Exception as e:
                    # Frame might be inaccessible or errored, skip it
                    logger.debug(f"Error extracting from iframe: {e}")
                    continue
                    
        except Exception as e:
            # If iframe extraction fails entirely, return empty list
            logger.warning(f"Iframe extraction failed: {e}")
        
        logger.debug(f"IframeExtractor found {len(jobs)} total jobs")
        return jobs
    
    def _has_job_content(self, soup: BeautifulSoup) -> bool:
        """Check if iframe content looks like a job board.
        
        Args:
            soup: BeautifulSoup parsed frame content
            
        Returns:
            True if frame contains job-related content
        """
        frame_text = soup.get_text().lower()
        return any(indicator in frame_text for indicator in JOB_INDICATORS)
    
    async def _extract_jobs_from_frame(
        self,
        soup: BeautifulSoup,
        frame
    ) -> List[Dict[str, str]]:
        """Extract jobs from a single iframe.
        
        Args:
            soup: BeautifulSoup parsed frame content
            frame: Playwright frame object
            
        Returns:
            List of job dictionaries from this frame
        """
        jobs = []
        job_containers = []
        
        # Look for common job listing patterns (Greenhouse and similar ATS)
        for selector in IFRAME_JOB_SELECTORS:
            try:
                containers = soup.select(selector)
                job_containers.extend(containers)
            except Exception as e:
                logger.debug(f"Error with iframe selector '{selector}': {e}")
                continue
        
        # Deduplicate containers
        unique_containers = self._deduplicate_containers(job_containers)
        
        # Process containers
        for container in unique_containers:
            link = container.find('a', href=True)
            if not link:
                continue
            
            url = link.get('href', '')
            if not url or url.startswith('#'):
                continue
            
            # Filter out non-job URLs
            if self._should_exclude_by_url(url, EXCLUDE_URL_PATTERNS):
                continue
            
            # Job URLs should have some path beyond just the base
            if url.count('/') < MIN_URL_DEPTH:
                continue
            
            # Make URL absolute if needed
            url = self._make_frame_url_absolute(url, frame.url)
            
            # Extract title
            title = self._extract_title_from_container(container, link=link)
            
            if not title:
                continue
            
            # Filter out non-job titles
            if self._should_exclude_by_title(title, EXCLUDE_TITLE_KEYWORDS):
                continue
            
            # Title should have some substance
            if len(title.split()) < MIN_TITLE_WORDS:
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
        
        return jobs
    
    def _deduplicate_containers(self, containers: List) -> List:
        """Remove duplicate containers based on object identity.
        
        Args:
            containers: List of BeautifulSoup containers
            
        Returns:
            List of unique containers
        """
        seen_containers = set()
        unique_containers = []
        
        for container in containers:
            container_id = id(container)
            if container_id not in seen_containers:
                seen_containers.add(container_id)
                unique_containers.append(container)
        
        return unique_containers
    
    def _make_frame_url_absolute(self, url: str, frame_url: str) -> str:
        """Make URL absolute using frame URL as base.
        
        Args:
            url: Potentially relative URL
            frame_url: Frame URL to use as base
            
        Returns:
            Absolute URL
        """
        if url.startswith('http'):
            return url
        
        if url.startswith('/'):
            # Get base URL from frame
            parsed = urlparse(frame_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        else:
            return f"{frame_url.rsplit('/', 1)[0]}/{url}"

