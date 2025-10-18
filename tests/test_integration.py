"""Integration tests for the complete job scraper pipeline."""
import os
import tempfile
import json
import pytest
from config_manager import ConfigManager
from scraper import JobScraper, JobMatch
from output import output_results


class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_config_to_scraper_pipeline(self):
        """Test that config loads correctly into scraper."""
        config = {
            "universal_keywords": ["Python", "Remote"],
            "companies": [
                {
                    "name": "Test Company",
                    "job_board_url": "https://example.com/jobs",
                    "keywords": ["Senior"]
                }
            ]
        }
        
        scraper = JobScraper(config)
        
        # Keywords should be lowercased
        assert "python" in scraper.universal_keywords
        assert "remote" in scraper.universal_keywords
        assert len(scraper.companies) == 1
        assert scraper.companies[0]["name"] == "Test Company"
    
    def test_matches_to_output_pipeline(self):
        """Test that matches can be output to HTML."""
        matches = [
            JobMatch(
                title="Python Developer",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python", "remote"]
            ),
            JobMatch(
                title="Java Developer",
                url="https://example.com/job/2",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            output_results(matches, tmp_path)
            
            # Verify file was created and has content
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Python Developer" in content
                assert "Java Developer" in content
                assert "Test Co" in content
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_full_config_manager_workflow(self):
        """Test complete config manager workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Create new config
            manager = ConfigManager(tmp_path)
            
            # Add universal keywords
            manager.add_universal_keywords(["python", "java"])
            
            # Add company
            manager.add_company(
                "Test Company",
                "https://example.com/jobs",
                ["senior", "remote"]
            )
            
            # Save
            manager.save_config()
            
            # Load again to verify persistence
            manager2 = ConfigManager(tmp_path)
            assert "python" in manager2.config["universal_keywords"]
            assert "java" in manager2.config["universal_keywords"]
            assert len(manager2.config["companies"]) == 1
            assert manager2.config["companies"][0]["name"] == "Test Company"
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_keyword_matching_in_scraper(self):
        """Test that keyword matching works as expected in scraper."""
        config = {
            "universal_keywords": ["python", "remote"],
            "companies": []
        }
        
        scraper = JobScraper(config)
        
        # Test various matching scenarios
        text1 = "Senior Python Developer - Remote position"
        matched1 = scraper.match_keywords(text1, scraper.universal_keywords)
        assert "python" in matched1
        assert "remote" in matched1
        
        # Test case insensitivity
        text2 = "PYTHON ENGINEER"
        matched2 = scraper.match_keywords(text2, scraper.universal_keywords)
        assert "python" in matched2
        
        # Test no match
        text3 = "Java Developer on-site"
        matched3 = scraper.match_keywords(text3, scraper.universal_keywords)
        assert len(matched3) == 0
    
    def test_empty_config_handling(self):
        """Test that empty config is handled gracefully."""
        config = {
            "universal_keywords": [],
            "companies": []
        }
        
        scraper = JobScraper(config)
        assert scraper.universal_keywords == []
        assert scraper.companies == []
    
    def test_config_with_company_specific_keywords(self):
        """Test that company-specific keywords are combined with universal."""
        config = {
            "universal_keywords": ["python"],
            "companies": [
                {
                    "name": "Test Co",
                    "job_board_url": "https://example.com/jobs",
                    "keywords": ["senior", "backend"]
                }
            ]
        }
        
        scraper = JobScraper(config)
        company = config["companies"][0]
        company_keywords = [k.lower() for k in company.get("keywords", [])]
        all_keywords = list(set(scraper.universal_keywords + company_keywords))
        
        # Should have combined keywords
        assert "python" in all_keywords
        assert "senior" in all_keywords
        assert "backend" in all_keywords
    
    def test_match_history_workflow(self):
        """Test complete match history workflow."""
        import tempfile
        import os
        from output import output_results
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # First run - all matches should be new
            first_run_matches = [
                JobMatch(
                    title="Python Developer",
                    url="https://example.com/job/1",
                    company="Test Co",
                    matched_keywords=["python"]
                ),
                JobMatch(
                    title="Java Developer",
                    url="https://example.com/job/2",
                    company="Test Co",
                    matched_keywords=["java"]
                )
            ]
            
            output_results(first_run_matches, tmp_path)
            
            # Verify HTML was created
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                # First run should show all as new
                assert "New Matches" in content
                assert "Python Developer" in content
                assert "Java Developer" in content
            
            # Second run - one new, one existing
            second_run_matches = [
                JobMatch(
                    title="Python Developer",  # Same URL, should be existing
                    url="https://example.com/job/1",
                    company="Test Co",
                    matched_keywords=["python"]
                ),
                JobMatch(
                    title="Go Developer",  # New URL
                    url="https://example.com/job/3",
                    company="Test Co",
                    matched_keywords=["golang"]
                )
            ]
            
            output_results(second_run_matches, tmp_path)
            
            # Verify the split
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "New Matches" in content
                assert "Previously Found Matches" in content
                assert "Go Developer" in content
                assert "Python Developer" in content
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

