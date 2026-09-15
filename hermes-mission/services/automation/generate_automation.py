#!/usr/bin/env python3
"""
Custom Automation Generator
Takes a client description and generates a custom automation script
based on available templates and modules.
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime


# Automation modules available
AUTOMATION_MODULES = {
    'file_organizer': {
        'name': 'File Organizer',
        'description': 'Organize files by type, date, or keyword',
        'triggers': ['organize', 'sort', 'files', 'folder', 'move', 'rename'],
        'complexity': 1,
        'template': 'file_organizer',
    },
    'report_generator': {
        'name': 'Report Generator',
        'description': 'Generate reports from CSV/Excel data',
        'triggers': ['report', 'chart', 'graph', 'summary', 'analytics', 'dashboard'],
        'complexity': 2,
        'template': 'report_generator',
    },
    'email_sender': {
        'name': 'Email Sender',
        'description': 'Send automated/bulk emails',
        'triggers': ['email', 'mail', 'send', 'notify', 'newsletter', 'bulk', 'smtp'],
        'complexity': 2,
        'template': 'email_sender',
    },
    'data_converter': {
        'name': 'Data Converter',
        'description': 'Convert between CSV, JSON, XML, Excel',
        'triggers': ['convert', 'transform', 'csv', 'json', 'xml', 'excel', 'format'],
        'complexity': 1,
        'template': 'data_converter',
    },
    'web_scraper': {
        'name': 'Web Scraper',
        'description': 'Scrape data from websites',
        'triggers': ['scrape', 'website', 'extract', 'crawl', 'web', 'url', 'html'],
        'complexity': 2,
        'template': 'web_scraper',
    },
    'pdf_processor': {
        'name': 'PDF Processor',
        'description': 'Merge, split, extract text from PDFs',
        'triggers': ['pdf', 'merge', 'split', 'watermark', 'extract'],
        'complexity': 2,
        'template': 'pdf_processor',
    },
    'database_backup': {
        'name': 'Database Backup',
        'description': 'Backup MySQL/PostgreSQL/SQLite databases',
        'triggers': ['backup', 'database', 'mysql', 'postgresql', 'sqlite', 'dump'],
        'complexity': 2,
        'template': 'database_backup',
    },
    'excel_automator': {
        'name': 'Excel Automator',
        'description': 'Read, write, transform Excel files',
        'triggers': ['excel', 'spreadsheet', 'xlsx', 'xls', 'sheet', 'pivot', 'merge'],
        'complexity': 2,
        'template': 'excel_automator',
    },
    'social_scheduler': {
        'name': 'Social Scheduler',
        'description': 'Schedule social media posts',
        'triggers': ['social', 'twitter', 'reddit', 'linkedin', 'post', 'schedule'],
        'complexity': 2,
        'template': 'social_scheduler',
    },
    'api_integrator': {
        'name': 'API Integrator',
        'description': 'Sync data between APIs',
        'triggers': ['api', 'sync', 'webhook', 'endpoint', 'rest', 'integrate'],
        'complexity': 3,
        'template': 'api_integrator',
    },
}


def analyze_description(description):
    """Analyze client description to determine needed automation."""
    description_lower = description.lower()
    matches = []

    for module_id, module in AUTOMATION_MODULES.items():
        score = 0
        for trigger in module['triggers']:
            if trigger in description_lower:
                score += 1
        if score > 0:
            matches.append((module_id, score, module))

    # Sort by score
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def estimate_complexity(matches, description):
    """Estimate project complexity and pricing."""
    word_count = len(description.split())

    if len(matches) == 0:
        return {
            'level': 'Unknown',
            'modules': [],
            'base_price': 300,
            'adjusted_price': 350,
            'timeline': '5-7 days',
            'notes': ['Manual review required - unclear requirements']
        }

    max_complexity = max(m[2]['complexity'] for m in matches)
    total_modules = len(matches)

    # Base pricing
    if max_complexity == 1:
        base_price = 150
        level = 'Simple'
        timeline = '1-2 days'
    elif max_complexity == 2:
        base_price = 250
        level = 'Standard'
        timeline = '2-4 days'
    else:
        base_price = 400
        level = 'Advanced'
        timeline = '5-7 days'

    # Adjust for number of modules
    if total_modules > 2:
        adjusted_price = base_price + (total_modules - 2) * 50
    else:
        adjusted_price = base_price

    # Cap at max
    adjusted_price = min(adjusted_price, 500)

    notes = []
    if word_count < 20:
        notes.append('Brief description - more details needed for accurate quote')
    if total_modules > 3:
        notes.append('Multiple automation needs detected - consider breaking into phases')

    return {
        'level': level,
        'modules': [m[2]['name'] for m in matches],
        'base_price': base_price,
        'adjusted_price': adjusted_price,
        'timeline': timeline,
        'notes': notes,
    }


def generate_custom_script(matches, description, output_dir='output'):
    """Generate a custom automation script based on matches."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    script_name = f"custom_automation_{timestamp}"
    script_file = output_path / f"{script_name}.py"

    # Build imports
    imports = [
        '#!/usr/bin/env python3',
        '"""',
        'Custom Automation Script',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Description: {description[:100]}',
        '"""',
        '',
        'import argparse',
        'import sys',
        'import os',
        'import logging',
        'from pathlib import Path',
        'from datetime import datetime',
        '',
        '# Configure logging',
        'logging.basicConfig(',
        '    level=logging.INFO,',
        '    format="%(asctime)s [%(levelname)s] %(message)s",',
        '    handlers=[',
        '        logging.FileHandler("automation.log"),',
        '        logging.StreamHandler()',
        '    ]',
        ')',
        'logger = logging.getLogger(__name__)',
        '',
    ]

    # Add module-specific imports based on matches
    module_imports = set()
    for _, _, module in matches:
        if module['template'] in ['web_scraper', 'api_integrator']:
            module_imports.add('import requests')
        if module['template'] in ['report_generator', 'data_converter', 'excel_automator']:
            module_imports.add('import pandas as pd')
        if module['template'] == 'email_sender':
            module_imports.add('import smtplib')
            module_imports.add('from email.mime.text import MIMEText')
        if module['template'] in ['database_backup']:
            module_imports.add('import subprocess')
            module_imports.add('import sqlite3')

    imports.extend(sorted(module_imports))
    imports.append('')

    # Build main function
    main_func = [
        '',
        'def main():',
        '    """Main automation function."""',
        '    logger.info("Starting custom automation...")',
        '    ',
        '    # TODO: Implement based on requirements',
        '    # This is a scaffold - customize based on client needs',
        '    ',
    ]

    for _, _, module in matches:
        main_func.append(f'    # {module["name"]}: {module["description"]}')

    main_func.extend([
        '    ',
        '    logger.info("Automation complete!")',
        '    return True',
        '',
    ])

    # Build argparse
    argparse_code = [
        '',
        'if __name__ == "__main__":',
        '    parser = argparse.ArgumentParser(description="Custom Automation Script")',
        '    parser.add_argument("--dry-run", action="store_true", help="Preview changes")',
        '    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")',
        '    args = parser.parse_args()',
        '    ',
        '    if args.verbose:',
        '        logging.getLogger().setLevel(logging.DEBUG)',
        '    ',
        '    try:',
        '        success = main()',
        '        sys.exit(0 if success else 1)',
        '    except KeyboardInterrupt:',
        '        logger.info("Automation cancelled by user")',
        '        sys.exit(130)',
        '    except Exception as e:',
        '        logger.error(f"Automation failed: {e}")',
        '        sys.exit(1)',
    ]

    # Write script
    script_content = '\n'.join(imports + main_func + argparse_code)
    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"\nCustom automation script generated: {script_file}")
    return str(script_file)


def generate_quote(description, output_file=None):
    """Generate a complete quote and project plan."""
    matches = analyze_description(description)
    complexity = estimate_complexity(matches, description)

    quote = {
        'timestamp': datetime.now().isoformat(),
        'description': description,
        'analysis': {
            'matched_modules': [m[2]['name'] for m in matches],
            'match_scores': {m[2]['name']: m[1] for m in matches},
        },
        'complexity': complexity,
    }

    # Save quote
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"quote_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(quote, f, indent=2)

    # Generate custom script
    if matches:
        script_file = generate_custom_script(matches, description)
        quote['generated_script'] = script_file

    # Print summary
    print("\n" + "=" * 60)
    print("AUTOMATION QUOTE & ANALYSIS")
    print("=" * 60)
    print(f"\nDescription: {description[:80]}...")
    print(f"\nComplexity Level: {complexity['level']}")
    print(f"Estimated Timeline: {complexity['timeline']}")
    print(f"Price Range: ${complexity['base_price']} - ${complexity['adjusted_price']}")
    print(f"\nMatched Modules:")
    for _, score, module in matches:
        print(f"  - {module['name']} (relevance: {score})")
    if complexity['notes']:
        print(f"\nNotes:")
        for note in complexity['notes']:
            print(f"  ⚠ {note}")
    print(f"\nQuote saved to: {output_file}")
    print("=" * 60)

    return quote


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Custom Automation Generator')
    subparsers = parser.add_subparsers(dest='command')

    # Analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyze description')
    analyze_parser.add_argument('description', help='Client problem description')

    # Quote
    quote_parser = subparsers.add_parser('quote', help='Generate full quote')
    quote_parser.add_argument('description', help='Client problem description')
    quote_parser.add_argument('-o', '--output', help='Output quote file')

    # List modules
    subparsers.add_parser('modules', help='List available modules')

    args = parser.parse_args()

    if args.command == 'analyze':
        matches = analyze_description(args.description)
        if matches:
            print("\nMatched automation modules:")
            for _, score, module in matches:
                print(f"  - {module['name']} (relevance: {score})")
                print(f"    {module['description']}")
        else:
            print("No matching modules found. Manual automation required.")

    elif args.command == 'quote':
        generate_quote(args.description, args.output)

    elif args.command == 'modules':
        print("\nAvailable Automation Modules:")
        print("=" * 50)
        for module_id, module in AUTOMATION_MODULES.items():
            print(f"\n  {module['name']} [{module_id}]")
            print(f"    {module['description']}")
            print(f"    Complexity: {'⭐' * module['complexity']}")
            print(f"    Triggers: {', '.join(module['triggers'][:5])}")

    else:
        parser.print_help()
