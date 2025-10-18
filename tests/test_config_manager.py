"""Unit tests for config_manager module."""
import json
import os
import tempfile
import pytest
from config_manager import ConfigManager


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_load_empty_config(self):
        """Test loading configuration from non-existent file."""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            config_path = tmp.name + "_nonexistent.json"
            manager = ConfigManager(config_path)
            assert manager.config == {"universal_keywords": [], "companies": []}
    
    def test_load_existing_config(self):
        """Test loading valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            test_config = {
                "universal_keywords": ["python", "remote"],
                "companies": [
                    {"name": "Test Co", "job_board_url": "https://test.com", "keywords": ["senior"]}
                ]
            }
            json.dump(test_config, tmp)
            tmp_path = tmp.name
        
        try:
            manager = ConfigManager(tmp_path)
            assert manager.config["universal_keywords"] == ["python", "remote"]
            assert len(manager.config["companies"]) == 1
            assert manager.config["companies"][0]["name"] == "Test Co"
        finally:
            os.unlink(tmp_path)
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write("{invalid json")
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                ConfigManager(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            manager = ConfigManager(tmp_path)
            manager.config["universal_keywords"] = ["test"]
            manager.save_config()
            
            with open(tmp_path, 'r') as f:
                saved = json.load(f)
                assert saved["universal_keywords"] == ["test"]
        finally:
            os.unlink(tmp_path)
    
    def test_parse_keywords_single(self):
        """Test parsing single keyword."""
        manager = ConfigManager()
        result = manager.parse_keywords("python")
        assert result == ["python"]
    
    def test_parse_keywords_comma_separated(self):
        """Test parsing comma-separated keywords."""
        manager = ConfigManager()
        result = manager.parse_keywords("python, java, golang")
        assert result == ["python", "java", "golang"]
    
    def test_parse_keywords_with_whitespace(self):
        """Test parsing keywords with extra whitespace."""
        manager = ConfigManager()
        result = manager.parse_keywords("  python  ,  java  ,  golang  ")
        assert result == ["python", "java", "golang"]
    
    def test_parse_keywords_empty(self):
        """Test parsing empty string."""
        manager = ConfigManager()
        result = manager.parse_keywords("")
        assert result == []
    
    def test_add_universal_keywords(self):
        """Test adding universal keywords."""
        manager = ConfigManager()
        manager.add_universal_keywords(["python", "java"])
        assert "python" in manager.config["universal_keywords"]
        assert "java" in manager.config["universal_keywords"]
    
    def test_add_universal_keywords_no_duplicates(self):
        """Test that duplicate keywords are not added."""
        manager = ConfigManager()
        manager.add_universal_keywords(["python"])
        manager.add_universal_keywords(["python"])
        assert manager.config["universal_keywords"].count("python") == 1
    
    def test_add_company(self):
        """Test adding a company."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            manager = ConfigManager(tmp_path)
            manager.add_company("Test Co", "https://test.com/jobs", ["senior", "remote"])
            
            assert len(manager.config["companies"]) == 1
            company = manager.config["companies"][0]
            assert company["name"] == "Test Co"
            assert company["job_board_url"] == "https://test.com/jobs"
            assert company["keywords"] == ["senior", "remote"]
        finally:
            os.unlink(tmp_path)

