"""Pytest configuration and fixtures for test suite."""
import pytest
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with asyncio marker."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(scope="function")
async def browser():
    """Create a browser instance for each test."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
    yield page
    await page.close()


def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class FixtureHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for serving test fixtures."""
    
    def __init__(self, *args, fixtures_dir=None, **kwargs):
        self.fixtures_dir = fixtures_dir
        super().__init__(*args, directory=fixtures_dir, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


@pytest.fixture(scope="session")
def http_server():
    """Start an HTTP server to serve test fixtures."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    port = find_free_port()
    
    def create_handler(*args, **kwargs):
        return FixtureHTTPRequestHandler(*args, fixtures_dir=fixtures_dir, **kwargs)
    
    server = HTTPServer(('localhost', port), create_handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    base_url = f"http://localhost:{port}"
    yield base_url
    
    server.shutdown()
    thread.join(timeout=1)


@pytest.fixture
def fixture_url(http_server):
    """Helper to generate fixture URLs."""
    def _fixture_url(filename):
        return f"{http_server}/{filename}"
    return _fixture_url


@pytest.fixture
def test_company_factory():
    """Factory for creating test company configurations."""
    def _create_company(
        name="Test Company",
        url="https://example.com/jobs",
        keywords=None,
        timeout=None,
        wait_for_load_state=None,
        use_iframe=False,
        pre_scrape_actions=None,
        scraping_config=None,
        location_filters=None
    ):
        company = {
            "name": name,
            "job_board_url": url,
            "keywords": keywords or []
        }
        
        if timeout is not None:
            company["timeout"] = timeout
        if wait_for_load_state is not None:
            company["wait_for_load_state"] = wait_for_load_state
        if use_iframe:
            company["use_iframe"] = use_iframe
        if pre_scrape_actions is not None:
            company["pre_scrape_actions"] = pre_scrape_actions
        if scraping_config is not None:
            company["scraping_config"] = scraping_config
        if location_filters is not None:
            company["location_filters"] = location_filters
        
        return company
    
    return _create_company


@pytest.fixture
def test_config_factory():
    """Factory for creating test scraper configurations."""
    def _create_config(universal_keywords=None, companies=None):
        return {
            "universal_keywords": universal_keywords or [],
            "companies": companies or []
        }
    return _create_config

