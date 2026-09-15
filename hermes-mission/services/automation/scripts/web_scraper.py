#!/usr/bin/env python3
"""
Web Scraper Automation Script
Scrape data from websites and export to CSV/JSON.
"""

import argparse
import csv
import json
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_page(url, headers=None, timeout=30):
    """Fetch a web page and return BeautifulSoup object."""
    if not HAS_REQUESTS:
        print("Error: requests and beautifulsoup4 required for web scraping.")
        return None

    default_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }
    if headers:
        default_headers.update(headers)

    response = requests.get(url, headers=default_headers, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def scrape_table(soup, table_index=0):
    """Scrape data from HTML tables."""
    tables = soup.find_all('table')
    if not tables or table_index >= len(tables):
        print("No tables found at the specified index.")
        return [], []

    table = tables[table_index]
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr')[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if cells:
            rows.append(cells)

    return headers, rows


def scrape_links(soup, pattern=None):
    """Scrape all links from a page, optionally filtered by pattern."""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)
        if pattern and not re.search(pattern, href):
            continue
        links.append({'text': text, 'href': href})
    return links


def scrape_by_selector(soup, selector, attributes=None):
    """Scrape elements by CSS selector."""
    elements = soup.select(selector)
    results = []
    for elem in elements:
        if attributes:
            data = {attr: elem.get(attr, '') for attr in attributes}
        else:
            data = {'text': elem.get_text(strip=True)}
        results.append(data)
    return results


def scrape_multiple_pages(base_url, pages, selector, delay=1):
    """Scrape the same selector across multiple pages."""
    all_results = []
    for page in pages:
        url = base_url.format(page=page)
        print(f"Scraping: {url}")
        soup = fetch_page(url)
        if soup:
            results = scrape_by_selector(soup, selector)
            all_results.extend(results)
            print(f"  Found {len(results)} items")
        time.sleep(delay)
    return all_results


def export_to_csv(data, output_file, headers=None):
    """Export scraped data to CSV."""
    if not data:
        print("No data to export.")
        return
    if not headers:
        headers = list(data[0].keys()) if isinstance(data[0], dict) else None

    with open(output_file, 'w', newline='') as f:
        if headers:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(f)
            writer.writerows(data)
    print(f"Data exported to CSV: {output_file}")


def export_to_json(data, output_file):
    """Export scraped data to JSON."""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data exported to JSON: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape data from websites')
    subparsers = parser.add_subparsers(dest='command')

    # Table scraping
    table_parser = subparsers.add_parser('table', help='Scrape HTML tables')
    table_parser.add_argument('url', help='URL to scrape')
    table_parser.add_argument('--index', type=int, default=0, help='Table index')
    table_parser.add_argument('--output', '-o', default='output.csv', help='Output file')
    table_parser.add_argument('--format', choices=['csv', 'json'], default='csv')

    # Link scraping
    link_parser = subparsers.add_parser('links', help='Scrape links')
    link_parser.add_argument('url', help='URL to scrape')
    link_parser.add_argument('--pattern', help='Regex pattern to filter links')
    link_parser.add_argument('--output', '-o', default='links.json', help='Output file')

    # Custom selector
    selector_parser = subparsers.add_parser('selector', help='Scrape by CSS selector')
    selector_parser.add_argument('url', help='URL to scrape')
    selector_parser.add_argument('--css', required=True, help='CSS selector')
    selector_parser.add_argument('--output', '-o', default='output.json', help='Output file')
    selector_parser.add_argument('--format', choices=['csv', 'json'], default='json')

    # Multi-page
    multi_parser = subparsers.add_parser('multi', help='Scrape multiple pages')
    multi_parser.add_argument('url', help='URL template with {page} placeholder')
    multi_parser.add_argument('--pages', nargs='+', required=True, help='Page identifiers')
    multi_parser.add_argument('--css', required=True, help='CSS selector')
    multi_parser.add_argument('--output', '-o', default='output.json', help='Output file')
    multi_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')

    args = parser.parse_args()

    if args.command == 'table':
        soup = fetch_page(args.url)
        if soup:
            headers, rows = scrape_table(soup, args.index)
            if args.format == 'csv':
                with open(args.output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)
            else:
                data = [dict(zip(headers, row)) for row in rows]
                export_to_json(data, args.output)
            print(f"Scraped {len(rows)} rows")

    elif args.command == 'links':
        soup = fetch_page(args.url)
        if soup:
            links = scrape_links(soup, args.pattern)
            export_to_json(links, args.output)
            print(f"Scraped {len(links)} links")

    elif args.command == 'selector':
        soup = fetch_page(args.url)
        if soup:
            results = scrape_by_selector(soup, args.css)
            if args.format == 'csv':
                export_to_csv(results, args.output)
            else:
                export_to_json(results, args.output)
            print(f"Scraped {len(results)} items")

    elif args.command == 'multi':
        results = scrape_multiple_pages(args.url, args.pages, args.css, args.delay)
        export_to_json(results, args.output)
        print(f"Total items scraped: {len(results)}")

    else:
        parser.print_help()
