"""URL manipulation utilities for job scraper."""
from urllib.parse import urljoin, urlparse
from typing import List


def make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute using base URL.
    
    Args:
        url: Potentially relative URL
        base_url: Base URL to use for relative resolution
        
    Returns:
        Absolute URL
        
    Examples:
        >>> make_absolute_url('/jobs/123', 'https://example.com/careers')
        'https://example.com/jobs/123'
    """
    if not url:
        return url
    return urljoin(base_url, url)


def get_base_url(url: str) -> str:
    """Extract base URL (scheme + netloc) from full URL.
    
    Args:
        url: Full URL
        
    Returns:
        Base URL like "https://example.com"
        
    Examples:
        >>> get_base_url('https://example.com/jobs/123?id=1')
        'https://example.com'
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_url(url: str) -> str:
    """Normalize URL for comparison (remove trailing slash, query params).
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
        
    Examples:
        >>> normalize_url('https://example.com/jobs/?page=1')
        'https://example.com/jobs'
    """
    return url.split('?')[0].rstrip('/')


def is_same_url(url1: str, url2: str) -> bool:
    """Check if two URLs are the same after normalization.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if URLs are the same after normalization
    """
    return normalize_url(url1) == normalize_url(url2)


def is_job_url(url: str, page_domain: str, job_url_patterns: List[str]) -> bool:
    """Check if URL looks like a job posting URL.
    
    Args:
        url: URL to check
        page_domain: Domain of the current page
        job_url_patterns: List of patterns that indicate a job URL (e.g., '/job/', '/jobs/')
        
    Returns:
        True if URL appears to be a job posting
    """
    if not url or not url.startswith('http'):
        return False
    
    # Extract domain from URL
    url_domain = urlparse(url).netloc
    
    # If external domain, allow it (might be external job board)
    if url_domain != page_domain:
        return True
    
    # If same domain, check for job-related patterns
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in job_url_patterns)


def get_domain(url: str) -> str:
    """Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain (netloc) from URL
        
    Examples:
        >>> get_domain('https://example.com/jobs/123')
        'example.com'
    """
    return urlparse(url).netloc

