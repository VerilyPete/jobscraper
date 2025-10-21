"""Clicking-based job extractor for JavaScript navigation."""
import asyncio
import logging
from typing import List, Dict, Optional
from playwright.async_api import Page

from .base import BaseExtractor
from ..constants import CONTAINER_WAIT_TIMEOUT_MS, URL_NAVIGATION_TIMEOUT_MS, POST_NAVIGATION_DELAY_MS

logger = logging.getLogger(__name__)


class ClickingExtractor(BaseExtractor):
    """Extractor that clicks job containers to extract URLs via JavaScript navigation."""
    
    async def extract(
        self,
        page: Page,
        wait_state: str = 'networkidle',
        timeout: Optional[int] = None,
        custom_config: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """Extract job listings by clicking on each job container to get the URL.
        
        This method is used for job boards that use JavaScript-based navigation
        without traditional href links (e.g., Gem job boards).
        
        Args:
            page: Playwright page object
            wait_state: Load state to wait for
            timeout: Optional timeout override
            custom_config: Custom scraping configuration
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        if timeout is None:
            timeout = self.timeout
        
        if not custom_config:
            logger.warning("No custom config provided to ClickingExtractor")
            return jobs
        
        # Wait for page to be ready
        await self._wait_for_page_ready(page, wait_state, timeout)
        
        # Get custom selectors
        container_selectors = custom_config.get('container_selectors', [])
        title_selector = custom_config.get('title_selector')
        
        if not container_selectors:
            logger.warning("No container selectors specified for JavaScript navigation")
            return jobs
        
        # Store the initial URL
        initial_url = page.url
        
        # Wait for job containers to be present and use Playwright locators directly
        found_selector = None
        for selector in container_selectors:
            try:
                # Wait for at least one container to be visible
                await page.wait_for_selector(selector, state='visible', timeout=CONTAINER_WAIT_TIMEOUT_MS)
                found_selector = selector
                logger.debug(f"Found containers with selector: {selector}")
                break
            except Exception as e:
                logger.debug(f"Selector '{selector}' not found: {e}")
                continue
        
        if not found_selector:
            logger.info(f"No job containers found with selectors: {container_selectors}")
            return jobs
        
        # Get all matching containers using Playwright
        containers = await page.locator(found_selector).all()
        num_jobs = len(containers)
        
        if num_jobs == 0:
            logger.info(f"No job containers found with selector: {found_selector}")
            return jobs
        
        logger.info(f"Found {num_jobs} job containers, clicking each to extract URLs...")
        
        # Process each container by clicking it
        for index in range(num_jobs):
            try:
                # Re-fetch containers on each iteration (DOM might change after navigation)
                await self._wait_for_page_ready(page, wait_state, timeout)
                containers = await page.locator(found_selector).all()
                
                if index >= len(containers):
                    logger.warning(f"Job {index + 1} no longer exists after re-fetch")
                    continue
                
                container_elem = containers[index]
                
                # Extract title before clicking
                title = await self._extract_title_from_element(
                    container_elem,
                    title_selector
                )
                
                # Click the container and wait for navigation
                await container_elem.click()
                
                # Wait for navigation to complete
                try:
                    await page.wait_for_url(
                        lambda url: url != initial_url,
                        timeout=URL_NAVIGATION_TIMEOUT_MS
                    )
                except Exception as e:
                    # If URL didn't change, wait a bit and check again
                    logger.debug(f"URL navigation wait failed: {e}")
                    await asyncio.sleep(1)
                
                # Get the new URL
                job_url = page.url
                
                # Only add if we actually navigated to a new page
                if job_url != initial_url and not job_url.endswith('/'):
                    jobs.append({
                        'title': title,
                        'url': job_url,
                        'description': title  # We can't get description without loading the page
                    })
                    logger.info(f"Job {index + 1}/{num_jobs}: {title}")
                
                # Go back to the listing page
                await page.goto(initial_url, timeout=timeout)
                await self._wait_for_page_ready(page, wait_state, timeout)
                
                # Wait for the job containers to be visible again after navigation
                try:
                    await page.wait_for_selector(found_selector, state='visible', timeout=URL_NAVIGATION_TIMEOUT_MS)
                except Exception as e:
                    logger.debug(f"Container visibility wait failed: {e}")
                
                # Small delay to be respectful and let page stabilize
                await asyncio.sleep(POST_NAVIGATION_DELAY_MS / 1000)
                
            except Exception as e:
                logger.warning(f"Error clicking job {index + 1}: {str(e)}")
                # Try to recover by going back to initial page
                try:
                    await page.goto(initial_url, timeout=timeout)
                    await self._wait_for_page_ready(page, wait_state, timeout)
                except Exception as recovery_error:
                    logger.error(f"Failed to recover to initial page: {recovery_error}")
                continue
        
        logger.debug(f"ClickingExtractor found {len(jobs)} jobs")
        return jobs
    
    async def _extract_title_from_element(
        self,
        element,
        title_selector: Optional[str] = None
    ) -> str:
        """Extract title from Playwright element.
        
        Args:
            element: Playwright locator element
            title_selector: Optional CSS selector for title
            
        Returns:
            Extracted title string
        """
        title = ''
        
        if title_selector:
            try:
                title_elem = await element.locator(title_selector).first
                title = await title_elem.text_content()
                title = title.strip() if title else ''
            except Exception as e:
                logger.debug(f"Failed to extract title with selector '{title_selector}': {e}")
        
        if not title:
            # Try to get any text from the container
            try:
                title = await element.text_content()
                title = title.strip() if title else ''
            except Exception as e:
                logger.debug(f"Failed to extract title from element: {e}")
        
        return title

