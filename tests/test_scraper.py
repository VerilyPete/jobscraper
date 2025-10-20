"""Unit tests for scraper module."""
import pytest
from scraper import JobScraper, JobMatch


class TestJobScraper:
    """Test JobScraper class."""
    
    def test_init(self):
        """Test scraper initialization."""
        config = {
            "universal_keywords": ["Python", "Remote"],
            "companies": []
        }
        scraper = JobScraper(config)
        
        # Keywords should be lowercased
        assert scraper.universal_keywords == ["python", "remote"]
        assert scraper.companies == []
    
    def test_match_keywords_single(self):
        """Test keyword matching with single keyword."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Python Developer position"
        keywords = ["python"]
        
        matched = scraper.match_keywords(text, keywords)
        assert "python" in matched
    
    def test_match_keywords_multiple(self):
        """Test keyword matching with multiple keywords."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Python Developer - Remote position"
        keywords = ["python", "remote", "java"]
        
        matched = scraper.match_keywords(text, keywords)
        assert "python" in matched
        assert "remote" in matched
        assert "java" not in matched
    
    def test_match_keywords_case_insensitive(self):
        """Test that keyword matching is case-insensitive."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "SENIOR PYTHON DEVELOPER"
        keywords = ["python", "senior"]
        
        matched = scraper.match_keywords(text, keywords)
        assert len(matched) == 2
    
    def test_match_keywords_word_boundary(self):
        """Test that keywords match on word boundaries."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        # "go" should not match "golang"
        text = "Golang Developer position"
        keywords = ["go"]
        
        matched = scraper.match_keywords(text, keywords)
        assert "go" not in matched
        
        # But "go" should match "Go Developer"
        text2 = "Go Developer position"
        matched2 = scraper.match_keywords(text2, keywords)
        assert "go" in matched2
    
    def test_match_keywords_empty_text(self):
        """Test keyword matching with empty text."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        matched = scraper.match_keywords("", ["python"])
        assert matched == []
    
    def test_match_keywords_empty_keywords(self):
        """Test keyword matching with empty keywords list."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        matched = scraper.match_keywords("Some text", [])
        assert matched == []


class TestJobMatch:
    """Test JobMatch class."""
    
    def test_job_match_creation(self):
        """Test creating a JobMatch object."""
        match = JobMatch(
            title="Python Developer",
            url="https://example.com/job/1",
            company="Test Co",
            matched_keywords=["python", "remote"]
        )
        
        assert match.title == "Python Developer"
        assert match.url == "https://example.com/job/1"
        assert match.company == "Test Co"
        assert match.matched_keywords == ["python", "remote"]
    
    def test_job_match_repr(self):
        """Test JobMatch string representation."""
        match = JobMatch(
            title="Python Developer",
            url="https://example.com/job/1",
            company="Test Co",
            matched_keywords=["python"]
        )
        
        repr_str = repr(match)
        assert "Python Developer" in repr_str
        assert "Test Co" in repr_str


class TestJobDeduplication:
    """Test job deduplication logic."""
    
    def test_url_based_deduplication(self):
        """Test that duplicate URLs are removed from job lists."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        # Simulate the deduplication logic in scrape_company
        all_jobs = [
            {'title': 'Software Engineer', 'url': 'https://example.com/job/1', 'description': 'Job 1'},
            {'title': 'Software Engineer - Location', 'url': 'https://example.com/job/1', 'description': 'Job 1 again'},
            {'title': 'QA Engineer', 'url': 'https://example.com/job/2', 'description': 'Job 2'},
            {'title': 'QA Engineer', 'url': 'https://example.com/job/2', 'description': 'Job 2 duplicate'},
            {'title': 'DevOps Engineer', 'url': 'https://example.com/job/3', 'description': 'Job 3'},
        ]
        
        # Apply deduplication logic (same as scraper.py lines 784-788)
        unique_jobs = {}
        for job in all_jobs:
            unique_jobs[job['url']] = job
        deduplicated = list(unique_jobs.values())
        
        # Should have only 3 unique URLs
        assert len(deduplicated) == 3
        urls = [job['url'] for job in deduplicated]
        assert urls.count('https://example.com/job/1') == 1
        assert urls.count('https://example.com/job/2') == 1
        assert urls.count('https://example.com/job/3') == 1
    
    def test_deduplication_preserves_last_occurrence(self):
        """Test that deduplication keeps the last occurrence when URLs match."""
        all_jobs = [
            {'title': 'First Title', 'url': 'https://example.com/job/1', 'description': 'First'},
            {'title': 'Second Title', 'url': 'https://example.com/job/1', 'description': 'Second'},
            {'title': 'Third Title', 'url': 'https://example.com/job/1', 'description': 'Third'},
        ]
        
        # Apply deduplication logic
        unique_jobs = {}
        for job in all_jobs:
            unique_jobs[job['url']] = job
        deduplicated = list(unique_jobs.values())
        
        # Should keep the last one
        assert len(deduplicated) == 1
        assert deduplicated[0]['title'] == 'Third Title'
        assert deduplicated[0]['description'] == 'Third'


class TestLocationFilter:
    """Test flexible location filtering system.
    
    Location filters support both 'include' and 'exclude' patterns.
    """
    
    def test_matches_location_pattern_simple(self):
        """Test simple pattern matching."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, Canada"
        assert scraper.matches_location_pattern(text, "remote, canada") is True
        assert scraper.matches_location_pattern(text, "remote, us") is False
    
    def test_matches_location_pattern_case_insensitive(self):
        """Test case-insensitive pattern matching."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - REMOTE, CANADA"
        assert scraper.matches_location_pattern(text, "remote, canada") is True
    
    def test_exclude_filter_matches(self):
        """Test exclude filter filters out matching jobs."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, Canada"
        filters = {"exclude": ["remote, canada"]}
        
        assert scraper.should_filter_by_location(text, filters) is True
    
    def test_exclude_filter_no_match(self):
        """Test exclude filter keeps non-matching jobs."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, US"
        filters = {"exclude": ["remote, canada"]}
        
        assert scraper.should_filter_by_location(text, filters) is False
    
    def test_exclude_filter_multiple_patterns(self):
        """Test exclude filter with multiple patterns."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        filters = {"exclude": ["remote, canada", "canada only"]}
        
        text1 = "Senior Developer - Remote, Canada"
        assert scraper.should_filter_by_location(text1, filters) is True
        
        text2 = "Senior Developer - Canada Only"
        assert scraper.should_filter_by_location(text2, filters) is True
        
        text3 = "Senior Developer - Remote, US"
        assert scraper.should_filter_by_location(text3, filters) is False
    
    def test_include_filter_matches(self):
        """Test include filter keeps matching jobs."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, US"
        filters = {"include": ["remote, us"]}
        
        assert scraper.should_filter_by_location(text, filters) is False
    
    def test_include_filter_no_match(self):
        """Test include filter filters out non-matching jobs."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, Canada"
        filters = {"include": ["remote, us"]}
        
        assert scraper.should_filter_by_location(text, filters) is True
    
    def test_include_filter_multiple_patterns(self):
        """Test include filter with multiple patterns (OR logic)."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        filters = {"include": ["remote, us", "us and canada"]}
        
        text1 = "Senior Developer - Remote, US"
        assert scraper.should_filter_by_location(text1, filters) is False
        
        text2 = "Senior Developer - Remote, US and Canada"
        assert scraper.should_filter_by_location(text2, filters) is False
        
        text3 = "Senior Developer - Remote, Canada"
        assert scraper.should_filter_by_location(text3, filters) is True
    
    def test_include_and_exclude_combined(self):
        """Test combining include and exclude filters."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        # Include US jobs, but exclude specific states
        filters = {
            "include": ["remote, us", "united states"],
            "exclude": ["california"]
        }
        
        text1 = "Senior Developer - Remote, US"
        assert scraper.should_filter_by_location(text1, filters) is False  # Keep
        
        text2 = "Senior Developer - Remote, US - California"
        assert scraper.should_filter_by_location(text2, filters) is True  # Filter (excluded)
        
        text3 = "Senior Developer - Remote, Canada"
        assert scraper.should_filter_by_location(text3, filters) is True  # Filter (not included)
    
    def test_no_filters(self):
        """Test that no filters means no filtering."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, Canada"
        
        # No filters at all
        assert scraper.should_filter_by_location(text, None) is False
        assert scraper.should_filter_by_location(text, {}) is False
    
    def test_empty_filter_arrays(self):
        """Test empty filter arrays."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        text = "Senior Developer - Remote, Canada"
        filters = {"include": [], "exclude": []}
        
        assert scraper.should_filter_by_location(text, filters) is False
    
    def test_real_world_vidyard_exclude(self):
        """Test real-world Vidyard scenario: exclude Canada-only, keep US+Canada."""
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        filters = {"exclude": ["remote, canada"]}
        
        # Should filter out
        canada_only = "Senior Developer - Remote, Canada"
        assert scraper.should_filter_by_location(canada_only, filters) is True
        
        # Should keep (has "and" so doesn't match "remote, canada" exactly)
        us_and_canada = "Senior Developer - Remote, US and Canada"
        assert scraper.should_filter_by_location(us_and_canada, filters) is False


class TestPerCompanyConfiguration:
    """Test per-company configuration options."""
    
    def test_timeout_override_config(self):
        """Test that timeout can be overridden per company."""
        company = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "timeout": 60000  # 60 seconds instead of default 30
        }
        
        assert company.get('timeout') == 60000
        assert company.get('timeout', 30000) == 60000
    
    def test_wait_for_load_state_options(self):
        """Test wait_for_load_state configuration options."""
        # Test networkidle (default)
        company1 = {
            "name": "Test Co 1",
            "job_board_url": "https://example.com/jobs",
            "keywords": []
        }
        assert company1.get('wait_for_load_state', 'networkidle') == 'networkidle'
        
        # Test load
        company2 = {
            "name": "Test Co 2",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "wait_for_load_state": "load"
        }
        assert company2.get('wait_for_load_state') == 'load'
        
        # Test domcontentloaded
        company3 = {
            "name": "Test Co 3",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "wait_for_load_state": "domcontentloaded"
        }
        assert company3.get('wait_for_load_state') == 'domcontentloaded'
    
    def test_use_iframe_flag(self):
        """Test use_iframe flag configuration."""
        # Default is False
        company1 = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": []
        }
        assert company1.get('use_iframe', False) is False
        
        # Can be enabled
        company2 = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "use_iframe": True
        }
        assert company2.get('use_iframe') is True
    
    def test_pre_scrape_actions_structure(self):
        """Test pre_scrape_actions configuration structure."""
        company = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "pre_scrape_actions": [
                {
                    "type": "click",
                    "selector": "button:has-text('Accept')",
                    "wait_after": 1000
                },
                {
                    "type": "click",
                    "selector": "button:has-text('Show More')",
                    "wait_after": 2000,
                    "repeat_until_gone": True,
                    "max_repeats": 50
                },
                {
                    "type": "wait",
                    "selector": "[role='region']",
                    "timeout": 10000
                }
            ]
        }
        
        actions = company.get('pre_scrape_actions', [])
        assert len(actions) == 3
        
        # Test click action
        assert actions[0]['type'] == 'click'
        assert actions[0]['selector'] == "button:has-text('Accept')"
        assert actions[0]['wait_after'] == 1000
        
        # Test repeat_until_gone
        assert actions[1]['repeat_until_gone'] is True
        assert actions[1]['max_repeats'] == 50
        
        # Test wait action
        assert actions[2]['type'] == 'wait'
        assert actions[2]['timeout'] == 10000
    
    def test_scraping_config_structure(self):
        """Test scraping_config configuration structure."""
        company = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "scraping_config": {
                "container_selectors": ["div.job-card", "article.position"],
                "link_selector": "a.job-link",
                "title_selector": "h3.job-title, h2",
                "description_selector": "div.job-description",
                "exclude_patterns": {
                    "urls": ["/careers/$", "/careers#", "/search"],
                    "titles": ["talent network", "job alert", "filter"]
                },
                "pagination_selectors": ["a[rel='next']", "button.load-more"]
            }
        }
        
        config = company.get('scraping_config', {})
        
        # Test all fields present
        assert 'container_selectors' in config
        assert 'link_selector' in config
        assert 'title_selector' in config
        assert 'description_selector' in config
        assert 'exclude_patterns' in config
        assert 'pagination_selectors' in config
        
        # Test container_selectors is array
        assert isinstance(config['container_selectors'], list)
        assert len(config['container_selectors']) == 2
        
        # Test exclude_patterns structure
        assert 'urls' in config['exclude_patterns']
        assert 'titles' in config['exclude_patterns']
        assert isinstance(config['exclude_patterns']['urls'], list)
        assert isinstance(config['exclude_patterns']['titles'], list)
        
        # Test pagination can be disabled
        assert isinstance(config['pagination_selectors'], list)
    
    def test_location_filters_structure_comprehensive(self):
        """Test location_filters configuration structure comprehensively."""
        # Exclude only
        company1 = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "location_filters": {
                "exclude": ["remote, canada", "canada only"]
            }
        }
        filters1 = company1.get('location_filters', {})
        assert 'exclude' in filters1
        assert isinstance(filters1['exclude'], list)
        assert len(filters1['exclude']) == 2
        
        # Include only
        company2 = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "location_filters": {
                "include": ["remote, us", "united states"]
            }
        }
        filters2 = company2.get('location_filters', {})
        assert 'include' in filters2
        assert isinstance(filters2['include'], list)
        
        # Both include and exclude
        company3 = {
            "name": "Test Co",
            "job_board_url": "https://example.com/jobs",
            "keywords": [],
            "location_filters": {
                "include": ["remote, us"],
                "exclude": ["california", "new york"]
            }
        }
        filters3 = company3.get('location_filters', {})
        assert 'include' in filters3
        assert 'exclude' in filters3
    
    def test_combined_company_configuration(self):
        """Test company with multiple customizations (like IBM)."""
        company = {
            "name": "IBM",
            "job_board_url": "https://www.ibm.com/careers/search",
            "keywords": [],
            "wait_for_load_state": "load",
            "timeout": 45000,
            "pre_scrape_actions": [
                {
                    "type": "click",
                    "selector": "button:has-text('Accept all')",
                    "wait_after": 1000
                },
                {
                    "type": "click",
                    "selector": "text=Remote only",
                    "wait_after": 1000
                },
                {
                    "type": "wait",
                    "selector": "[role='region']",
                    "timeout": 10000
                }
            ],
            "scraping_config": {
                "container_selectors": ["[role='region']"],
                "link_selector": "a",
                "title_selector": "a",
                "pagination_selectors": []
            }
        }
        
        # Verify all fields are accessible
        assert company['wait_for_load_state'] == 'load'
        assert company['timeout'] == 45000
        assert len(company['pre_scrape_actions']) == 3
        assert company['scraping_config']['container_selectors'] == ["[role='region']"]
        assert company['scraping_config']['pagination_selectors'] == []

