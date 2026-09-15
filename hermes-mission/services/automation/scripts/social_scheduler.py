#!/usr/bin/env python3
"""
Social Media Scheduler Automation Script
Schedule and manage social media posts (Twitter/X, Reddit, generic webhooks).
"""

import argparse
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta


def load_schedule(schedule_file):
    """Load posting schedule from a CSV or JSON file."""
    path = Path(schedule_file)
    if path.suffix.lower() == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif path.suffix.lower() == '.csv':
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        print("Unsupported schedule format. Use CSV or JSON.")
        return []


def validate_schedule(schedule):
    """Validate and sort the posting schedule."""
    validated = []
    now = datetime.now()

    for item in schedule:
        platform = item.get('platform', '').lower()
        content = item.get('content', '')
        time_str = item.get('time', item.get('scheduled_time', ''))

        if not content:
            print(f"Warning: Skipping item with no content: {item}")
            continue

        try:
            if time_str:
                scheduled_time = datetime.fromisoformat(time_str)
            else:
                scheduled_time = now
        except ValueError:
            print(f"Warning: Invalid time format '{time_str}', using now")
            scheduled_time = now

        validated.append({
            'platform': platform,
            'content': content,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'pending'
        })

    validated.sort(key=lambda x: x['scheduled_time'])
    return validated


def generate_calendar(schedule, output_file='posting_calendar.html'):
    """Generate an HTML calendar view of the posting schedule."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Social Media Posting Calendar</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #333; }
        .post { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .platform { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; color: white; }
        .twitter { background: #1DA1F2; }
        .reddit { background: #FF4500; }
        .linkedin { background: #0077B5; }
        .generic { background: #666; }
        .time { color: #888; font-size: 0.9em; }
        .content { margin-top: 10px; line-height: 1.5; }
        .status { float: right; font-size: 0.85em; padding: 2px 8px; border-radius: 4px; }
        .pending { background: #fff3cd; color: #856404; }
        .posted { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 Social Media Posting Calendar</h1>
"""

    for item in schedule:
        platform = item.get('platform', 'generic')
        content = item.get('content', '')
        time_str = item.get('scheduled_time', '')
        status = item.get('status', 'pending')

        html += f"""
        <div class="post">
            <span class="platform {platform}">{platform.upper()}</span>
            <span class="status {status}">{status}</span>
            <div class="time">📆 {time_str}</div>
            <div class="content">{content}</div>
        </div>
"""

    html += """
    </div>
</body>
</html>"""

    with open(output_file, 'w') as f:
        f.write(html)
    print(f"Calendar generated: {output_file}")
    return output_file


def generate_sample_schedule(output_file='schedule.csv'):
    """Generate a sample posting schedule."""
    sample = """platform,content,time
twitter,"Check out our latest blog post about automation! #automation #productivity",2024-01-15T09:00:00
reddit,"We built a tool that automates repetitive data tasks. Happy to share details!",2024-01-15T14:00:00
linkedin,"Excited to announce our new automation service for small businesses.",2024-01-16T10:00:00
twitter,"5 signs your business needs workflow automation 🧵",2024-01-17T08:00:00"""

    with open(output_file, 'w') as f:
        f.write(sample)
    print(f"Sample schedule created: {output_file}")
    return output_file


def export_for_buffer(schedule, output_file='buffer_import.csv'):
    """Export schedule in Buffer-compatible format."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Profile', 'Text', 'Date', 'Time'])
        for item in schedule:
            dt = datetime.fromisoformat(item['scheduled_time'])
            writer.writerow([
                item.get('platform', 'Twitter'),
                item.get('content', ''),
                dt.strftime('%Y-%m-%d'),
                dt.strftime('%H:%M')
            ])
    print(f"Buffer import file created: {output_file}")
    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Social media scheduling')
    subparsers = parser.add_subparsers(dest='command')

    # Validate
    validate_parser = subparsers.add_parser('validate', help='Validate schedule')
    validate_parser.add_argument('schedule_file', help='Schedule file (CSV/JSON)')
    validate_parser.add_argument('-o', '--output', default='validated_schedule.json')

    # Calendar
    cal_parser = subparsers.add_parser('calendar', help='Generate calendar view')
    cal_parser.add_argument('schedule_file', help='Schedule file')
    cal_parser.add_argument('-o', '--output', default='posting_calendar.html')

    # Sample
    sample_parser = subparsers.add_parser('sample', help='Generate sample schedule')
    sample_parser.add_argument('-o', '--output', default='schedule.csv')

    # Buffer export
    buffer_parser = subparsers.add_parser('buffer', help='Export for Buffer')
    buffer_parser.add_argument('schedule_file', help='Schedule file')
    buffer_parser.add_argument('-o', '--output', default='buffer_import.csv')

    args = parser.parse_args()

    if args.command == 'validate':
        schedule = load_schedule(args.schedule_file)
        validated = validate_schedule(schedule)
        with open(args.output, 'w') as f:
            json.dump(validated, f, indent=2)
        print(f"Validated schedule saved: {args.output}")

    elif args.command == 'calendar':
        schedule = load_schedule(args.schedule_file)
        generate_calendar(schedule, args.output)

    elif args.command == 'sample':
        generate_sample_schedule(args.output)

    elif args.command == 'buffer':
        schedule = load_schedule(args.schedule_file)
        export_for_buffer(schedule, args.output)

    else:
        parser.print_help()
