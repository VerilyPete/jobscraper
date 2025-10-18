"""Output formatting for job matches."""
import os
from typing import List, Set, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from scraper import JobMatch


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
    """Generate HTML output file with styled table."""
    
    # Group by company - determine which grouping to use
    by_company = {}
    for match in matches:
        if match.company not in by_company:
            by_company[match.company] = []
        by_company[match.company].append(match)
    
    html_parts = []
    
    # HTML header with inline CSS
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Matches</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .stats {
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        
        .stat {
            text-align: center;
            padding: 10px 20px;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .content {
            padding: 40px;
        }
        
        .company-section {
            margin-bottom: 40px;
        }
        
        .company-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        
        .company-name {
            font-size: 1.5em;
            font-weight: 600;
            color: #333;
        }
        
        .company-count {
            color: #6c757d;
            font-size: 0.9em;
            margin-left: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        
        td {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        tbody tr {
            transition: background-color 0.2s ease;
        }
        
        tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .job-title {
            font-weight: 500;
            color: #333;
        }
        
        .job-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }
        
        .job-link:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        
        .keywords {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        
        .keyword {
            background: #e7f3ff;
            color: #0066cc;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #e9ecef;
        }
        
        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }
        
        .no-results-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Job Matches</h1>
            <p>Results from your job board search</p>
        </div>
""")
    
    if not matches:
        html_parts.append("""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h2>No matching jobs found</h2>
            <p>Try adjusting your keywords or adding more companies to search.</p>
        </div>
""")
    else:
        # Stats section
        if new_matches is not None and existing_matches is not None:
            html_parts.append(f"""
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(matches)}</div>
                <div class="stat-label">Total Matches</div>
            </div>
            <div class="stat">
                <div class="stat-number">🆕 {len(new_matches)}</div>
                <div class="stat-label">New</div>
            </div>
            <div class="stat">
                <div class="stat-number">📋 {len(existing_matches)}</div>
                <div class="stat-label">Previously Found</div>
            </div>
            <div class="stat">
                <div class="stat-number">{datetime.now().strftime('%B %d, %Y')}</div>
                <div class="stat-label">Search Date</div>
            </div>
        </div>
        
        <div class="content">
""")
        else:
            html_parts.append(f"""
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(matches)}</div>
                <div class="stat-label">Total Matches</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(by_company)}</div>
                <div class="stat-label">Companies</div>
            </div>
            <div class="stat">
                <div class="stat-number">{datetime.now().strftime('%B %d, %Y')}</div>
                <div class="stat-label">Search Date</div>
            </div>
        </div>
        
        <div class="content">
""")
        
        # Generate sections based on whether we have new/existing split
        if new_matches is not None and existing_matches is not None:
            # NEW MATCHES SECTION
            if new_matches:
                html_parts.append("""
            <h2 style="color: #667eea; margin: 30px 0 20px 0; padding-left: 20px;">🆕 New Matches</h2>
""")
                new_by_company = {}
                for match in new_matches:
                    if match.company not in new_by_company:
                        new_by_company[match.company] = []
                    new_by_company[match.company].append(match)
                
                for company in sorted(new_by_company.keys()):
                    jobs = new_by_company[company]
                    html_parts.append(f"""
            <div class="company-section">
                <div class="company-header">
                    <span class="company-name">{company}</span>
                    <span class="company-count">{len(jobs)} match{'es' if len(jobs) != 1 else ''}</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Job Title</th>
                            <th>Matched Keywords</th>
                        </tr>
                    </thead>
                    <tbody>
""")
                    
                    for job in jobs:
                        keywords_html = ''.join([f'<span class="keyword">{kw}</span>' for kw in job.matched_keywords])
                        html_parts.append(f"""
                        <tr>
                            <td><a href="{job.url}" target="_blank" class="job-link">{job.title}</a></td>
                            <td><div class="keywords">{keywords_html}</div></td>
                        </tr>
""")
                    
                    html_parts.append("""
                    </tbody>
                </table>
            </div>
""")
            
            # EXISTING MATCHES SECTION
            if existing_matches:
                html_parts.append("""
            <h2 style="color: #6c757d; margin: 40px 0 20px 0; padding-left: 20px;">📋 Previously Found Matches</h2>
""")
                existing_by_company = {}
                for match in existing_matches:
                    if match.company not in existing_by_company:
                        existing_by_company[match.company] = []
                    existing_by_company[match.company].append(match)
                
                for company in sorted(existing_by_company.keys()):
                    jobs = existing_by_company[company]
                    html_parts.append(f"""
            <div class="company-section">
                <div class="company-header">
                    <span class="company-name">{company}</span>
                    <span class="company-count">{len(jobs)} match{'es' if len(jobs) != 1 else ''}</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Job Title</th>
                            <th>Matched Keywords</th>
                        </tr>
                    </thead>
                    <tbody>
""")
                    
                    for job in jobs:
                        keywords_html = ''.join([f'<span class="keyword">{kw}</span>' for kw in job.matched_keywords])
                        html_parts.append(f"""
                        <tr>
                            <td><a href="{job.url}" target="_blank" class="job-link">{job.title}</a></td>
                            <td><div class="keywords">{keywords_html}</div></td>
                        </tr>
""")
                    
                    html_parts.append("""
                    </tbody>
                </table>
            </div>
""")
        else:
            # Original behavior - no split
            for company in sorted(by_company.keys()):
                jobs = by_company[company]
                html_parts.append(f"""
            <div class="company-section">
                <div class="company-header">
                    <span class="company-name">{company}</span>
                    <span class="company-count">{len(jobs)} match{'es' if len(jobs) != 1 else ''}</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Job Title</th>
                            <th>Matched Keywords</th>
                        </tr>
                    </thead>
                    <tbody>
""")
                
                for job in jobs:
                    keywords_html = ''.join([f'<span class="keyword">{kw}</span>' for kw in job.matched_keywords])
                    html_parts.append(f"""
                        <tr>
                            <td><a href="{job.url}" target="_blank" class="job-link">{job.title}</a></td>
                            <td><div class="keywords">{keywords_html}</div></td>
                        </tr>
""")
                
                html_parts.append("""
                    </tbody>
                </table>
            </div>
""")
        
        html_parts.append("        </div>")
    
    # Footer
    html_parts.append(f"""
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
</body>
</html>
""")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))


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

