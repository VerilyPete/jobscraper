"""Output formatting for job matches."""
import os
from typing import List, Set, Tuple
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from scraper.core import JobMatch


def parse_previous_matches(html_file: str) -> Set[str]:
    """Parse existing HTML file and extract job URLs."""
    if not os.path.exists(html_file):
        return set()
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all job links
        urls = set()
        for link in soup.find_all('a', class_='job-link'):
            href = link.get('href')
            if href:
                urls.add(href)
        
        return urls
    except Exception as e:
        print(f"Warning: Could not parse previous matches: {e}")
        return set()


def split_matches(matches: List[JobMatch], previous_urls: Set[str]) -> Tuple[List[JobMatch], List[JobMatch]]:
    """Split matches into new and existing based on previous URLs."""
    new_matches = []
    existing_matches = []
    
    for match in matches:
        if match.url in previous_urls:
            existing_matches.append(match)
        else:
            new_matches.append(match)
    
    return new_matches, existing_matches


def format_stdout(matches: List[JobMatch], new_matches: List[JobMatch] = None, existing_matches: List[JobMatch] = None) -> str:
    """Format matches for stdout output."""
    if not matches:
        return "No matching jobs found."
    
    output = []
    output.append(f"\n{'='*80}")
    
    # If we have split matches, show new and existing separately
    if new_matches is not None and existing_matches is not None:
        output.append(f"Found {len(matches)} total matching job(s)")
        output.append(f"  🆕 {len(new_matches)} new, 📋 {len(existing_matches)} previously found")
        output.append(f"{'='*80}\n")
        
        # Show new matches first
        if new_matches:
            output.append("\n🆕 NEW MATCHES")
            output.append("=" * 80)
            by_company = {}
            for match in new_matches:
                if match.company not in by_company:
                    by_company[match.company] = []
                by_company[match.company].append(match)
            
            for company in sorted(by_company.keys()):
                jobs = by_company[company]
                output.append(f"\n{company} ({len(jobs)} match{'es' if len(jobs) != 1 else ''})")
                output.append("-" * 80)
                
                for job in jobs:
                    output.append(f"\n  Title: {job.title}")
                    output.append(f"  URL: {job.url}")
                    output.append(f"  Keywords: {', '.join(job.matched_keywords)}")
        
        # Show existing matches
        if existing_matches:
            output.append("\n\n📋 PREVIOUSLY FOUND MATCHES")
            output.append("=" * 80)
            by_company = {}
            for match in existing_matches:
                if match.company not in by_company:
                    by_company[match.company] = []
                by_company[match.company].append(match)
            
            for company in sorted(by_company.keys()):
                jobs = by_company[company]
                output.append(f"\n{company} ({len(jobs)} match{'es' if len(jobs) != 1 else ''})")
                output.append("-" * 80)
                
                for job in jobs:
                    output.append(f"\n  Title: {job.title}")
                    output.append(f"  URL: {job.url}")
                    output.append(f"  Keywords: {', '.join(job.matched_keywords)}")
    else:
        # Original behavior if not split
        by_company = {}
        for match in matches:
            if match.company not in by_company:
                by_company[match.company] = []
            by_company[match.company].append(match)
        
        output.append(f"Found {len(matches)} matching job(s) across {len(by_company)} company(ies)")
        output.append(f"{'='*80}\n")
        
        for company in sorted(by_company.keys()):
            jobs = by_company[company]
            output.append(f"\n{company} ({len(jobs)} match{'es' if len(jobs) != 1 else ''})")
            output.append("-" * 80)
            
            for job in jobs:
                output.append(f"\n  Title: {job.title}")
                output.append(f"  URL: {job.url}")
                output.append(f"  Keywords: {', '.join(job.matched_keywords)}")
    
    output.append(f"\n{'='*80}\n")
    
    return "\n".join(output)


def generate_html(matches: List[JobMatch], output_file: str = "job_matches.html", new_matches: List[JobMatch] = None, existing_matches: List[JobMatch] = None) -> None:
    """Generate HTML output file with styled table using Jinja2 template."""
    
    # Group by company
    by_company = {}
    for match in matches:
        if match.company not in by_company:
            by_company[match.company] = []
        by_company[match.company].append(match)
    
    # Prepare context for template
    context = {
        'matches': matches,
        'by_company': by_company,
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'generation_time': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'has_split_matches': new_matches is not None and existing_matches is not None,
    }
    
    # Add split matches data if provided
    if new_matches is not None and existing_matches is not None:
        context['new_matches'] = new_matches
        context['existing_matches'] = existing_matches
        
        # Group new matches by company
        new_by_company = {}
        for match in new_matches:
            if match.company not in new_by_company:
                new_by_company[match.company] = []
            new_by_company[match.company].append(match)
        context['new_by_company'] = new_by_company
        
        # Group existing matches by company
        existing_by_company = {}
        for match in existing_matches:
            if match.company not in existing_by_company:
                existing_by_company[match.company] = []
            existing_by_company[match.company].append(match)
        context['existing_by_company'] = existing_by_company
    
    # Setup Jinja2 environment
    template_dir = Path(__file__).parent / 'templates'
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('job_matches.html')
    
    # Render template
    html_content = template.render(**context)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def output_results(matches: List[JobMatch], html_file: str = "job_matches.html") -> None:
    """Output results to both stdout and HTML file."""
    # Parse previous matches from existing HTML
    previous_urls = parse_previous_matches(html_file)
    
    # Split matches into new and existing
    new_matches, existing_matches = split_matches(matches, previous_urls)
    
    # Print to stdout
    print(format_stdout(matches, new_matches, existing_matches))
    
    # Generate HTML
    generate_html(matches, html_file, new_matches, existing_matches)
    print(f"Results saved to {html_file}")
    
    if new_matches:
        print(f"🆕 {len(new_matches)} new match{'es' if len(new_matches) != 1 else ''} found!")
    if existing_matches:
        print(f"📋 {len(existing_matches)} previously found match{'es' if len(existing_matches) != 1 else ''}")

