#!/usr/bin/env python3
"""Job scraper CLI application."""
import argparse
import sys
from config_manager import ConfigManager
from scraper import run_scraper
from output import output_results


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Scrape job boards for matching positions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Run scraper with existing configuration
  %(prog)s --configure         # Enter interactive configuration mode
  %(prog)s --output results.html  # Specify custom output file
        """
    )
    
    parser.add_argument(
        '--configure',
        action='store_true',
        help='Enter interactive configuration mode to add keywords and companies'
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--output',
        default='job_matches.html',
        help='Path to HTML output file (default: job_matches.html)'
    )
    
    args = parser.parse_args()
    
    # Initialize config manager
    config_manager = ConfigManager(args.config)
    
    # Handle configure mode
    if args.configure:
        config_manager.interactive_configure()
        return 0
    
    # Validate configuration
    if not config_manager.config.get('companies'):
        print("Error: No companies configured.")
        print("Run with --configure to add companies and keywords.")
        return 1
    
    # Run scraper
    try:
        matches = run_scraper(config_manager.config)
        
        # Output results
        output_results(matches, args.output)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        return 130
    
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


