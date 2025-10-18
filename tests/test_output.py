"""Unit tests for output module."""
import os
import tempfile
from scraper import JobMatch
from output import format_stdout, generate_html, parse_previous_matches, split_matches


class TestOutput:
    """Test output formatting functions."""
    
    def test_format_stdout_no_matches(self):
        """Test stdout formatting with no matches."""
        output = format_stdout([])
        assert "No matching jobs found" in output
    
    def test_format_stdout_single_match(self):
        """Test stdout formatting with single match."""
        matches = [
            JobMatch(
                title="Python Developer",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python"]
            )
        ]
        
        output = format_stdout(matches)
        assert "Test Co" in output
        assert "Python Developer" in output
        assert "https://example.com/job/1" in output
        assert "python" in output
    
    def test_format_stdout_multiple_matches(self):
        """Test stdout formatting with multiple matches."""
        matches = [
            JobMatch(
                title="Python Developer",
                url="https://example.com/job/1",
                company="Company A",
                matched_keywords=["python", "remote"]
            ),
            JobMatch(
                title="Java Developer",
                url="https://example.com/job/2",
                company="Company B",
                matched_keywords=["java"]
            )
        ]
        
        output = format_stdout(matches)
        assert "Company A" in output
        assert "Company B" in output
        assert "Python Developer" in output
        assert "Java Developer" in output
        assert "2 match" in output
    
    def test_format_stdout_groups_by_company(self):
        """Test that stdout groups jobs by company."""
        matches = [
            JobMatch(
                title="Job 1",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Job 2",
                url="https://example.com/job/2",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        output = format_stdout(matches)
        assert "Test Co (2 matches)" in output
    
    def test_generate_html_no_matches(self):
        """Test HTML generation with no matches."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generate_html([], tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "No matching jobs found" in content
        finally:
            os.unlink(tmp_path)
    
    def test_generate_html_with_matches(self):
        """Test HTML generation with matches."""
        matches = [
            JobMatch(
                title="Python Developer",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python", "remote"]
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generate_html(matches, tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "Test Co" in content
                assert "Python Developer" in content
                assert "https://example.com/job/1" in content
                assert "python" in content
                assert "remote" in content
                assert "<table>" in content
        finally:
            os.unlink(tmp_path)
    
    def test_generate_html_multiple_companies(self):
        """Test HTML generation with multiple companies."""
        matches = [
            JobMatch(
                title="Job 1",
                url="https://example.com/job/1",
                company="Company A",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Job 2",
                url="https://example.com/job/2",
                company="Company B",
                matched_keywords=["java"]
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generate_html(matches, tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Company A" in content
                assert "Company B" in content
                # Should have stats showing 2 companies
                assert content.count('<div class="company-section">') == 2
        finally:
            os.unlink(tmp_path)
    
    def test_generate_html_creates_valid_links(self):
        """Test that HTML contains valid anchor tags."""
        matches = [
            JobMatch(
                title="Test Job",
                url="https://example.com/job/123",
                company="Test Co",
                matched_keywords=["test"]
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generate_html(matches, tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert '<a href="https://example.com/job/123"' in content
                assert 'target="_blank"' in content
        finally:
            os.unlink(tmp_path)
    
    def test_parse_previous_matches_no_file(self):
        """Test parsing previous matches when file doesn't exist."""
        urls = parse_previous_matches("nonexistent_file.html")
        assert urls == set()
    
    def test_parse_previous_matches_with_urls(self):
        """Test parsing previous matches from existing HTML."""
        html_content = """
        <html>
        <body>
            <a href="https://example.com/job/1" class="job-link">Job 1</a>
            <a href="https://example.com/job/2" class="job-link">Job 2</a>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name
        
        try:
            urls = parse_previous_matches(tmp_path)
            assert "https://example.com/job/1" in urls
            assert "https://example.com/job/2" in urls
            assert len(urls) == 2
        finally:
            os.unlink(tmp_path)
    
    def test_split_matches_all_new(self):
        """Test splitting matches when all are new."""
        matches = [
            JobMatch(
                title="Job 1",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Job 2",
                url="https://example.com/job/2",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        previous_urls = set()
        new_matches, existing_matches = split_matches(matches, previous_urls)
        
        assert len(new_matches) == 2
        assert len(existing_matches) == 0
    
    def test_split_matches_all_existing(self):
        """Test splitting matches when all are existing."""
        matches = [
            JobMatch(
                title="Job 1",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Job 2",
                url="https://example.com/job/2",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        previous_urls = {"https://example.com/job/1", "https://example.com/job/2"}
        new_matches, existing_matches = split_matches(matches, previous_urls)
        
        assert len(new_matches) == 0
        assert len(existing_matches) == 2
    
    def test_split_matches_mixed(self):
        """Test splitting matches with mix of new and existing."""
        matches = [
            JobMatch(
                title="Job 1",
                url="https://example.com/job/1",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Job 2",
                url="https://example.com/job/2",
                company="Test Co",
                matched_keywords=["java"]
            ),
            JobMatch(
                title="Job 3",
                url="https://example.com/job/3",
                company="Test Co",
                matched_keywords=["golang"]
            )
        ]
        
        previous_urls = {"https://example.com/job/1"}
        new_matches, existing_matches = split_matches(matches, previous_urls)
        
        assert len(new_matches) == 2
        assert len(existing_matches) == 1
        assert existing_matches[0].url == "https://example.com/job/1"
    
    def test_generate_html_with_history_split(self):
        """Test HTML generation with new/existing split."""
        all_matches = [
            JobMatch(
                title="New Job",
                url="https://example.com/job/new",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Old Job",
                url="https://example.com/job/old",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        new_matches = [all_matches[0]]
        existing_matches = [all_matches[1]]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generate_html(all_matches, tmp_path, new_matches, existing_matches)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "New Matches" in content
                assert "Previously Found Matches" in content
                assert "New Job" in content
                assert "Old Job" in content
                assert "🆕" in content
                assert "📋" in content
        finally:
            os.unlink(tmp_path)
    
    def test_format_stdout_with_history_split(self):
        """Test stdout formatting with new/existing split."""
        all_matches = [
            JobMatch(
                title="New Job",
                url="https://example.com/job/new",
                company="Test Co",
                matched_keywords=["python"]
            ),
            JobMatch(
                title="Old Job",
                url="https://example.com/job/old",
                company="Test Co",
                matched_keywords=["java"]
            )
        ]
        
        new_matches = [all_matches[0]]
        existing_matches = [all_matches[1]]
        
        output = format_stdout(all_matches, new_matches, existing_matches)
        
        assert "NEW MATCHES" in output
        assert "PREVIOUSLY FOUND MATCHES" in output
        assert "New Job" in output
        assert "Old Job" in output

