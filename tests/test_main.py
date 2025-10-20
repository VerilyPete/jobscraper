"""Unit tests for main CLI module."""
import pytest
import sys
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from main import main


class TestCLIArguments:
    """Test CLI argument parsing and handling."""
    
    def test_company_flag_filters_to_single_company(self):
        """Test --company flag filters to single company."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Company A", "job_board_url": "https://a.com/jobs", "keywords": []},
                    {"name": "Company B", "job_board_url": "https://b.com/jobs", "keywords": []},
                    {"name": "IBM", "job_board_url": "https://ibm.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path, '--company', 'IBM']):
                with patch('main.run_scraper', return_value=[]) as mock_scraper:
                    with patch('main.output_results'):
                        main()
                    
                    # Verify scraper was called with filtered config
                    called_config = mock_scraper.call_args[0][0]
                    assert len(called_config['companies']) == 1
                    assert called_config['companies'][0]['name'] == 'IBM'
        finally:
            os.unlink(tmp_path)
    
    def test_company_flag_case_insensitive(self):
        """Test --company flag is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "IBM", "job_board_url": "https://ibm.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path, '--company', 'ibm']):
                with patch('main.run_scraper', return_value=[]) as mock_scraper:
                    with patch('main.output_results'):
                        main()
                    
                    called_config = mock_scraper.call_args[0][0]
                    assert called_config['companies'][0]['name'] == 'IBM'
        finally:
            os.unlink(tmp_path)
    
    def test_company_not_found_returns_error(self):
        """Test error when --company specifies non-existent company."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Company A", "job_board_url": "https://a.com/jobs", "keywords": []},
                    {"name": "Company B", "job_board_url": "https://b.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path, '--company', 'NonExistent']):
                with patch('builtins.print') as mock_print:
                    result = main()
                    
                    assert result == 1
                    # Verify error message was printed
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any('not found' in str(call).lower() for call in print_calls)
                    assert any('Company A' in str(call) for call in print_calls)
        finally:
            os.unlink(tmp_path)
    
    def test_no_company_flag_scrapes_all(self):
        """Test that without --company flag, all companies are scraped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Company A", "job_board_url": "https://a.com/jobs", "keywords": []},
                    {"name": "Company B", "job_board_url": "https://b.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path]):
                with patch('main.run_scraper', return_value=[]) as mock_scraper:
                    with patch('main.output_results'):
                        main()
                    
                    called_config = mock_scraper.call_args[0][0]
                    assert len(called_config['companies']) == 2
        finally:
            os.unlink(tmp_path)
    
    def test_config_argument(self):
        """Test --config argument specifies config file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Test Co", "job_board_url": "https://test.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path]):
                with patch('main.run_scraper', return_value=[]):
                    with patch('main.output_results'):
                        result = main()
                        assert result == 0
        finally:
            os.unlink(tmp_path)
    
    def test_output_argument(self):
        """Test --output argument specifies output file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Test Co", "job_board_url": "https://test.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, config_tmp)
            config_path = config_tmp.name
        
        output_path = tempfile.mktemp(suffix='.html')
        
        try:
            with patch('sys.argv', ['main.py', '--config', config_path, '--output', output_path]):
                with patch('main.run_scraper', return_value=[]):
                    with patch('main.output_results') as mock_output:
                        main()
                        
                        # Verify output_results was called with correct path
                        assert mock_output.call_args[0][1] == output_path
        finally:
            os.unlink(config_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_configure_flag_enters_interactive_mode(self):
        """Test --configure flag enters interactive configuration mode."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path, '--configure']):
                with patch('config_manager.ConfigManager.interactive_configure') as mock_configure:
                    result = main()
                    
                    assert result == 0
                    mock_configure.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_no_companies_configured_error(self):
        """Test error when no companies are configured."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": []
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path]):
                with patch('builtins.print') as mock_print:
                    result = main()
                    
                    assert result == 1
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any('no companies configured' in str(call).lower() for call in print_calls)
        finally:
            os.unlink(tmp_path)
    
    def test_keyboard_interrupt_handling(self):
        """Test that keyboard interrupt is handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Test Co", "job_board_url": "https://test.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path]):
                with patch('main.run_scraper', side_effect=KeyboardInterrupt()):
                    with patch('builtins.print'):
                        result = main()
                        assert result == 130
        finally:
            os.unlink(tmp_path)
    
    def test_exception_handling(self):
        """Test that exceptions are handled and return error code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            config = {
                "universal_keywords": ["python"],
                "companies": [
                    {"name": "Test Co", "job_board_url": "https://test.com/jobs", "keywords": []}
                ]
            }
            json.dump(config, tmp)
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['main.py', '--config', tmp_path]):
                with patch('main.run_scraper', side_effect=Exception("Test error")):
                    with patch('builtins.print'):
                        result = main()
                        assert result == 1
        finally:
            os.unlink(tmp_path)

