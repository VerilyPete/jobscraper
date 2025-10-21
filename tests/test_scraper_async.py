"""Integration tests for async scraper methods with Playwright."""
import pytest
from scraper import JobScraper, JobMatch


class TestExtractJobsWithCustomConfig:
    """Test extract_jobs_with_custom_config method."""
    
    @pytest.mark.asyncio
    async def test_custom_container_selectors(self, page, fixture_url):
        """Test extraction with custom container selectors."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.position-item"],
            "link_selector": "a",
            "title_selector": "h2.position-title"
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 3
        assert any("Software Engineer" in job['title'] for job in jobs)
        assert any("QA Engineer" in job['title'] for job in jobs)
        assert any("Engineering Manager" in job['title'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_custom_link_and_title_selectors(self, page, fixture_url):
        """Test custom link_selector and title_selector."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.position-item"],
            "link_selector": ".position-title a",
            "title_selector": ".position-title"
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 3
        # Verify URLs are properly extracted
        assert all('href' in str(job['url']) or '/careers/' in job['url'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_custom_description_selector(self, page, fixture_url):
        """Test custom description_selector."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.position-item"],
            "link_selector": "a",
            "title_selector": "h2",
            "description_selector": ".position-details"
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 3
        # Verify descriptions are extracted
        assert any("Remote, US" in job['description'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_exclude_patterns_urls(self, page, fixture_url):
        """Test exclude_patterns for URLs."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["h2", "h3"],
            "link_selector": "a",
            "title_selector": "a",
            "exclude_patterns": {
                "urls": ["/careers/alerts"]
            }
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        # Should not include the "job alerts" link
        assert not any("alerts" in job['url'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_exclude_patterns_titles(self, page, fixture_url):
        """Test exclude_patterns for titles."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["h2", "h3"],
            "link_selector": "a",
            "title_selector": "a",
            "exclude_patterns": {
                "titles": ["job alerts", "sign up"]
            }
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        # Should not include titles with excluded keywords
        assert not any("alert" in job['title'].lower() for job in jobs)
    
    @pytest.mark.asyncio
    async def test_fallback_selectors(self, page, fixture_url):
        """Test that scraper tries multiple selectors in order."""
        url = fixture_url("jobs_custom_selectors.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": [
                "div.nonexistent-selector",  # This won't match
                "li.position-item"  # This should work
            ],
            "link_selector": "a",
            "title_selector": "h2"
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        # Should fall back to second selector and find jobs
        assert len(jobs) == 3
    
    @pytest.mark.asyncio
    async def test_no_selectors_match(self, page, fixture_url):
        """Test empty results when no selectors match."""
        url = fixture_url("basic_jobs.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": [
                "div.completely-nonexistent",
                "article.also-nonexistent"
            ],
            "link_selector": "a",
            "title_selector": "h2"
        }
        
        jobs = await scraper.extract_jobs_with_custom_config(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 0


class TestExtractJobsFromIframe:
    """Test extract_jobs_from_iframe method."""
    
    @pytest.mark.asyncio
    async def test_iframe_detection_and_extraction(self, page, fixture_url):
        """Test that jobs are extracted from iframes."""
        url = fixture_url("jobs_with_iframe.html")
        await page.goto(url, wait_until='load')
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        jobs = await scraper.extract_jobs_from_iframe(page, wait_state='load')
        
        # Should find jobs from the Greenhouse iframe
        assert len(jobs) >= 2
        assert any("Engineer" in job['title'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_greenhouse_style_iframe(self, page, fixture_url):
        """Test extraction from Greenhouse-style iframes."""
        url = fixture_url("jobs_with_iframe.html")
        await page.goto(url, wait_until='load')
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        jobs = await scraper.extract_jobs_from_iframe(page, wait_state='load')
        
        # Verify Greenhouse-specific structure is handled
        assert any("greenhouse" in job['url'].lower() for job in jobs if job['url'])
    
    @pytest.mark.asyncio
    async def test_no_iframes_present(self, page, fixture_url):
        """Test that empty list is returned when no iframes present."""
        url = fixture_url("basic_jobs.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        jobs = await scraper.extract_jobs_from_iframe(page, wait_state='load')
        
        assert len(jobs) == 0


class TestExecutePreScrapeActions:
    """Test execute_pre_scrape_actions method."""
    
    @pytest.mark.asyncio
    async def test_click_action(self, page, fixture_url):
        """Test click action on button."""
        url = fixture_url("jobs_with_cookie_banner.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        # Cookie banner should be visible initially
        banner = await page.query_selector("#cookie-banner")
        assert await banner.is_visible()
        
        actions = [
            {
                "type": "click",
                "selector": "#accept-cookies",
                "wait_after": 100
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Jobs should now be visible
        jobs_visible = await page.is_visible("#job-content")
        assert jobs_visible
    
    @pytest.mark.asyncio
    async def test_check_action(self, page, fixture_url):
        """Test check action on checkbox."""
        url = fixture_url("jobs_with_filters.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        actions = [
            {
                "type": "check",
                "selector": "#remote-only",
                "wait_after": 100
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Checkbox should be checked
        is_checked = await page.is_checked("#remote-only")
        assert is_checked
    
    @pytest.mark.asyncio
    async def test_uncheck_action(self, page, fixture_url):
        """Test uncheck action on checkbox."""
        url = fixture_url("jobs_with_filters.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        # First check it
        await page.check("#remote-only")
        assert await page.is_checked("#remote-only")
        
        # Now uncheck it
        actions = [
            {
                "type": "uncheck",
                "selector": "#remote-only",
                "wait_after": 100
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        is_checked = await page.is_checked("#remote-only")
        assert not is_checked
    
    @pytest.mark.asyncio
    async def test_fill_action(self, page, fixture_url):
        """Test fill action in text input."""
        # Create a simple page with an input
        html = """
        <html>
            <body>
                <input type="text" id="search" placeholder="Search">
                <div id="results"></div>
            </body>
        </html>
        """
        await page.set_content(html)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        actions = [
            {
                "type": "fill",
                "selector": "#search",
                "value": "python developer",
                "wait_after": 100
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Verify the input has the value
        value = await page.input_value("#search")
        assert value == "python developer"
    
    @pytest.mark.asyncio
    async def test_wait_action(self, page, fixture_url):
        """Test wait action for element to appear."""
        url = fixture_url("jobs_with_cookie_banner.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        actions = [
            {
                "type": "wait",
                "selector": "#cookie-banner",
                "timeout": 5000
            }
        ]
        
        # Should wait for element without interacting
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Element should be visible
        is_visible = await page.is_visible("#cookie-banner")
        assert is_visible
    
    @pytest.mark.asyncio
    async def test_repeat_until_gone(self, page, fixture_url):
        """Test repeat_until_gone on 'Show More' button."""
        url = fixture_url("jobs_with_load_more.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        # Initially should have 2 jobs
        initial_count = await page.locator(".job-item").count()
        assert initial_count == 2
        
        actions = [
            {
                "type": "click",
                "selector": "#load-more-btn",
                "wait_after": 100,
                "repeat_until_gone": True,
                "max_repeats": 10
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Should have more jobs now
        final_count = await page.locator(".job-item").count()
        assert final_count > initial_count
        
        # Button should be gone
        button_visible = await page.is_visible("#load-more-btn")
        assert not button_visible
    
    @pytest.mark.asyncio
    async def test_max_repeats_limit(self, page, fixture_url):
        """Test max_repeats safety limit."""
        url = fixture_url("jobs_with_load_more.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        actions = [
            {
                "type": "click",
                "selector": "#load-more-btn",
                "wait_after": 50,
                "repeat_until_gone": True,
                "max_repeats": 2  # Limit to 2 clicks
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Should have clicked exactly 2 times (adding 4 jobs)
        final_count = await page.locator(".job-item").count()
        assert final_count == 6  # 2 initial + 2*2 added
    
    @pytest.mark.asyncio
    async def test_wait_after_delay(self, page, fixture_url):
        """Test wait_after delay between actions."""
        url = fixture_url("jobs_with_filters.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        import time
        start_time = time.time()
        
        actions = [
            {
                "type": "check",
                "selector": "#remote-only",
                "wait_after": 500  # 500ms delay
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        elapsed = (time.time() - start_time) * 1000
        # Should have waited at least 500ms
        assert elapsed >= 400  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_multiple_actions_sequence(self, page, fixture_url):
        """Test sequence of multiple actions (cookie banner + filters)."""
        url = fixture_url("jobs_with_cookie_banner.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        actions = [
            {
                "type": "click",
                "selector": "#accept-cookies",
                "wait_after": 200
            },
            {
                "type": "wait",
                "selector": "#job-content",
                "timeout": 2000
            }
        ]
        
        await scraper.execute_pre_scrape_actions(page, actions)
        
        # Jobs should be visible after both actions
        jobs_visible = await page.is_visible("#job-content")
        assert jobs_visible


class TestCheckForNextPage:
    """Test check_for_next_page method."""
    
    @pytest.mark.asyncio
    async def test_pagination_detection_default(self, page, fixture_url):
        """Test pagination detection with default selectors."""
        url = fixture_url("jobs_with_pagination.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        has_next = await scraper.check_for_next_page(page)
        
        assert has_next is True
    
    @pytest.mark.asyncio
    async def test_custom_pagination_selectors(self, page, fixture_url):
        """Test custom pagination_selectors from scraping_config."""
        url = fixture_url("jobs_with_pagination.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_selectors = ["a.next-link"]
        has_next = await scraper.check_for_next_page(page, custom_pagination_selectors=custom_selectors)
        
        assert has_next is True
    
    @pytest.mark.asyncio
    async def test_empty_pagination_selectors_disables_pagination(self, page, fixture_url):
        """Test empty pagination_selectors array disables pagination."""
        url = fixture_url("jobs_with_pagination.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        # Empty array should disable pagination
        has_next = await scraper.check_for_next_page(page, custom_pagination_selectors=[])
        
        assert has_next is False
    
    @pytest.mark.asyncio
    async def test_no_pagination_present(self, page, fixture_url):
        """Test no pagination returns False."""
        url = fixture_url("basic_jobs.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        has_next = await scraper.check_for_next_page(page)
        
        assert has_next is False


class TestScrapeCompanyIntegration:
    """Test scrape_company with various configurations."""
    
    @pytest.mark.asyncio
    async def test_basic_company_scrape(self, browser, fixture_url, test_company_factory):
        """Test basic company scrape with no customizations."""
        company = test_company_factory(
            name="Test Company",
            url=fixture_url("basic_jobs.html"),
            keywords=["python", "qa"]
        )
        
        config = {
            "universal_keywords": ["engineer"],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        # Should find matching jobs
        assert len(matches) >= 2
        assert any("Python" in match.title for match in matches)
        assert any("QA" in match.title for match in matches)
    
    @pytest.mark.asyncio
    async def test_company_with_wait_for_load_state(self, browser, fixture_url, test_company_factory):
        """Test company with wait_for_load_state: 'load'."""
        company = test_company_factory(
            name="Test Company",
            url=fixture_url("basic_jobs.html"),
            keywords=["engineer"],
            wait_for_load_state="load"
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        assert len(matches) >= 1
    
    @pytest.mark.asyncio
    async def test_company_with_pre_scrape_actions(self, browser, fixture_url, test_company_factory):
        """Test company with pre_scrape_actions."""
        company = test_company_factory(
            name="Test Company",
            url=fixture_url("jobs_with_cookie_banner.html"),
            keywords=["engineer", "manager"],
            wait_for_load_state="load",
            pre_scrape_actions=[
                {
                    "type": "click",
                    "selector": "#accept-cookies",
                    "wait_after": 500
                }
            ]
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        # Should find jobs after accepting cookies
        assert len(matches) >= 2
    
    @pytest.mark.asyncio
    async def test_company_with_custom_scraping_config(self, browser, fixture_url, test_company_factory):
        """Test company with custom scraping_config."""
        company = test_company_factory(
            name="Test Company",
            url=fixture_url("jobs_custom_selectors.html"),
            keywords=["engineer"],
            wait_for_load_state="load",
            scraping_config={
                "container_selectors": ["li.position-item"],
                "link_selector": "a",
                "title_selector": "h2",
                "pagination_selectors": []
            }
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        assert len(matches) >= 2
    
    @pytest.mark.asyncio
    async def test_company_with_location_filters(self, browser, fixture_url, test_company_factory):
        """Test company with location_filters."""
        company = test_company_factory(
            name="Test Company",
            url=fixture_url("basic_jobs.html"),
            keywords=["engineer"],
            location_filters={
                "exclude": ["canada"]
            }
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        # Should exclude Canada-only jobs
        for match in matches:
            assert "remote, canada" not in match.title.lower()
    
    @pytest.mark.asyncio
    async def test_company_combining_multiple_customizations(self, browser, fixture_url, test_company_factory):
        """Test company combining multiple customizations (like IBM config)."""
        company = test_company_factory(
            name="IBM Style Company",
            url=fixture_url("jobs_with_cookie_banner.html"),
            keywords=["engineer", "quality"],
            wait_for_load_state="load",
            timeout=45000,
            pre_scrape_actions=[
                {
                    "type": "click",
                    "selector": "#accept-cookies",
                    "wait_after": 500
                },
                {
                    "type": "wait",
                    "selector": "#job-content",
                    "timeout": 5000
                }
            ],
            scraping_config={
                "container_selectors": [".job"],
                "link_selector": "a",
                "title_selector": "h2",
                "pagination_selectors": []
            }
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        assert len(matches) >= 1


class TestRealWorldPatterns:
    """Test complex real-world scraping patterns."""
    
    @pytest.mark.asyncio
    async def test_oracle_pattern_repeat_click(self, browser, fixture_url, test_company_factory):
        """Test Oracle pattern: Repeat-click 'Show More' until all jobs loaded."""
        company = test_company_factory(
            name="Oracle Style",
            url=fixture_url("jobs_with_load_more.html"),
            keywords=["job"],
            wait_for_load_state="load",
            pre_scrape_actions=[
                {
                    "type": "click",
                    "selector": "#load-more-btn",
                    "wait_after": 100,
                    "repeat_until_gone": True,
                    "max_repeats": 5
                }
            ]
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        # Should have loaded all jobs
        assert len(matches) >= 6  # Initial 2 + 3 clicks * 2 jobs
    
    @pytest.mark.asyncio
    async def test_custom_selector_pattern(self, browser, fixture_url, test_company_factory):
        """Test custom selector pattern (TVEyes/Philo style)."""
        company = test_company_factory(
            name="Custom Selector Company",
            url=fixture_url("jobs_custom_selectors.html"),
            keywords=["engineer"],
            scraping_config={
                "container_selectors": ["main li"],
                "link_selector": "a",
                "title_selector": "h2",
                "pagination_selectors": []
            }
        )
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        matches = await scraper.scrape_company(browser, company)
        
        assert len(matches) >= 2


class TestExtractJobsByClicking:
    """Test extract_jobs_by_clicking method for JavaScript navigation."""
    
    @pytest.mark.asyncio
    async def test_basic_js_navigation(self, page, fixture_url):
        """Test basic JavaScript navigation extraction."""
        url = fixture_url("jobs_with_js_navigation.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.job-posting"],
            "title_selector": ".job-title"
        }
        
        jobs = await scraper.extract_jobs_by_clicking(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 3
        assert any("QA Analyst" in job['title'] for job in jobs)
        assert any("Software Developer" in job['title'] for job in jobs)
        assert any("Engineering Manager" in job['title'] for job in jobs)
        
        # Check that URLs were captured
        assert all(job['url'] for job in jobs)
        assert any("/jobs/qa-analyst" in job['url'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_js_navigation_with_title_selector(self, page, fixture_url):
        """Test JavaScript navigation with custom title selector."""
        url = fixture_url("jobs_with_js_navigation.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.job-posting"],
            "title_selector": "div.job-title"
        }
        
        jobs = await scraper.extract_jobs_by_clicking(
            page, custom_config, wait_state='load'
        )
        
        # Verify titles are properly extracted and jobs found
        assert len(jobs) == 3
        assert all(job['title'] for job in jobs)
        # Verify we got actual job titles
        assert any("QA Analyst" in job['title'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_js_navigation_no_containers(self, page, fixture_url):
        """Test JavaScript navigation when no containers found."""
        url = fixture_url("basic_jobs.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.nonexistent-class"]
        }
        
        jobs = await scraper.extract_jobs_by_clicking(
            page, custom_config, wait_state='load'
        )
        
        assert len(jobs) == 0
    
    @pytest.mark.asyncio
    async def test_js_navigation_integration_with_extract_jobs_from_page(self, page, fixture_url):
        """Test that extract_jobs_from_page uses clicking method when use_js_navigation is true."""
        url = fixture_url("jobs_with_js_navigation.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "use_js_navigation": True,
            "container_selectors": ["li.job-posting"],
            "title_selector": ".job-title"
        }
        
        jobs = await scraper.extract_jobs_from_page(
            page, wait_state='load', custom_config=custom_config
        )
        
        assert len(jobs) == 3
        assert all(job['url'] for job in jobs)
    
    @pytest.mark.asyncio
    async def test_js_navigation_without_title_selector(self, page, fixture_url):
        """Test JavaScript navigation falls back to container text when no title selector."""
        url = fixture_url("jobs_with_js_navigation.html")
        await page.goto(url)
        
        config = {
            "universal_keywords": [],
            "companies": []
        }
        scraper = JobScraper(config)
        
        custom_config = {
            "container_selectors": ["li.job-posting"]
        }
        
        jobs = await scraper.extract_jobs_by_clicking(
            page, custom_config, wait_state='load'
        )
        
        # Should still extract titles from container text
        assert len(jobs) == 3
        assert all(job['title'] for job in jobs)
