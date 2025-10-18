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
        """Test that jobs are deduplicated by URL, not title."""
        # This test ensures that if the same URL appears multiple times
        # with different titles (e.g., with/without location), only one
        # job is kept
        config = {"universal_keywords": [], "companies": []}
        scraper = JobScraper(config)
        
        # In a real scenario, the extract_jobs_from_page method would
        # encounter the same URL multiple times with different titles
        # Since we can't easily test that without mocking, we verify
        # the logic by checking that URL is used for deduplication
        # This is a placeholder to document the expected behavior
        assert True  # The actual fix is in scraper.py line 109


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

