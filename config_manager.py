"""Configuration management for job scraper."""
import json
import os
from typing import Dict, List


class ConfigManager:
    """Manages loading, saving, and interactive editing of configuration."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize config manager with path to config file."""
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            return {"universal_keywords": [], "companies": []}
        
        try:
            with open(self.config_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {"universal_keywords": [], "companies": []}
                config = json.loads(content)
                # Validate structure
                if "universal_keywords" not in config:
                    config["universal_keywords"] = []
                if "companies" not in config:
                    config["companies"] = []
                return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def parse_keywords(self, input_str: str) -> List[str]:
        """Parse keywords from input string (comma-separated or single)."""
        if ',' in input_str:
            # Split by comma and strip whitespace
            keywords = [k.strip() for k in input_str.split(',')]
            # Filter out empty strings
            return [k for k in keywords if k]
        else:
            # Single keyword
            return [input_str.strip()] if input_str.strip() else []
    
    def add_universal_keywords(self, keywords: List[str]) -> None:
        """Add keywords to universal keyword list."""
        for keyword in keywords:
            if keyword not in self.config["universal_keywords"]:
                self.config["universal_keywords"].append(keyword)
    
    def add_company(self, name: str, url: str, keywords: List[str]) -> None:
        """Add a new company to the configuration."""
        company = {
            "name": name,
            "job_board_url": url,
            "keywords": keywords
        }
        self.config["companies"].append(company)
    
    def interactive_configure(self) -> None:
        """Run interactive configuration mode."""
        print("=== Job Scraper Configuration ===\n")
        
        # Universal keywords
        print("Add universal keywords (one per line, or comma-separated)")
        print("Press Enter without input or type 'next' to continue\n")
        
        while True:
            keyword_input = input("Universal keyword(s): ").strip()
            if not keyword_input or keyword_input.lower() == 'next':
                break
            
            keywords = self.parse_keywords(keyword_input)
            self.add_universal_keywords(keywords)
            if len(keywords) == 1:
                print(f"  Added: {keywords[0]}")
            else:
                print(f"  Added {len(keywords)} keywords: {', '.join(keywords)}")
        
        print(f"\nCurrent universal keywords: {', '.join(self.config['universal_keywords']) if self.config['universal_keywords'] else 'None'}\n")
        
        # Companies
        print("Add companies (press Enter without input when done adding companies)\n")
        
        while True:
            company_name = input("Company name (or press Enter to finish): ").strip()
            if not company_name:
                break
            
            company_url = input("Job board URL: ").strip()
            if not company_url:
                print("  URL is required. Skipping company.\n")
                continue
            
            print(f"Add company-specific keywords for {company_name}")
            print("(one per line, or comma-separated. Press Enter or 'next' to finish)")
            
            company_keywords = []
            while True:
                keyword_input = input("  Keyword(s): ").strip()
                if not keyword_input or keyword_input.lower() == 'next':
                    break
                
                keywords = self.parse_keywords(keyword_input)
                company_keywords.extend(keywords)
                if len(keywords) == 1:
                    print(f"    Added: {keywords[0]}")
                else:
                    print(f"    Added {len(keywords)} keywords")
            
            self.add_company(company_name, company_url, company_keywords)
            print(f"  Added {company_name} with {len(company_keywords)} specific keywords\n")
        
        # Save configuration
        self.save_config()
        print(f"\nConfiguration saved to {self.config_path}")
        print(f"Total companies: {len(self.config['companies'])}")
        print(f"Universal keywords: {len(self.config['universal_keywords'])}")

