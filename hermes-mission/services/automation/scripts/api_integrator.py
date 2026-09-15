#!/usr/bin/env python3
"""
API Integration Automation Script
Automate data sync between APIs (REST endpoints).
"""

import argparse
import json
import csv
import time
from pathlib import Path
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_api_data(url, method='GET', headers=None, params=None, data=None, auth=None):
    """Fetch data from a REST API."""
    if not HAS_REQUESTS:
        print("Error: requests library required.")
        return None

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=data,
        auth=auth,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def sync_apis(source_url, dest_url, transform_func=None, headers=None, auth=None):
    """Sync data from source API to destination API."""
    print(f"Fetching data from: {source_url}")
    data = fetch_api_data(source_url, headers=headers, auth=auth)

    if transform_func:
        data = transform_func(data)

    print(f"Posting data to: {dest_url}")
    response = requests.post(dest_url, json=data, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    print(f"Sync complete. Status: {response.status_code}")
    return response


def poll_api(url, interval=60, callback=None, headers=None, max_iterations=None):
    """Poll an API at regular intervals."""
    iteration = 0
    while True:
        try:
            data = fetch_api_data(url, headers=headers)
            if callback:
                callback(data)
            else:
                print(f"[{datetime.now().isoformat()}] Data received: {json.dumps(data)[:200]}...")
        except Exception as e:
            print(f"Error polling: {e}")

        iteration += 1
        if max_iterations and iteration >= max_iterations:
            break
        time.sleep(interval)


def export_api_to_csv(api_url, output_file, headers=None, data_key=None):
    """Fetch API data and export to CSV."""
    data = fetch_api_data(api_url, headers=headers)

    if data_key and isinstance(data, dict):
        data = data.get(data_key, [])

    if not data:
        print("No data to export.")
        return

    keys = data[0].keys() if isinstance(data[0], dict) else range(len(data[0]))
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"API data exported to: {output_file}")
    return output_file


def batch_process(items, process_func, delay=0.5):
    """Process a batch of items with a function."""
    results = []
    for i, item in enumerate(items):
        try:
            result = process_func(item)
            results.append(result)
            print(f"Processed {i + 1}/{len(items)}")
        except Exception as e:
            print(f"Error processing item {i}: {e}")
            results.append(None)
        time.sleep(delay)
    return results


def webhook_listener(port=8080, handler=None):
    """Start a simple webhook listener."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("Error: http.server required.")
        return

    class WebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            if handler:
                handler(data)
            else:
                print(f"Webhook received: {json.dumps(data, indent=2)}")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')

        def log_message(self, format, *args):
            pass  # Suppress default logging

    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f"Webhook listener running on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='API integration automation')
    subparsers = parser.add_subparsers(dest='command')

    # Fetch
    fetch_parser = subparsers.add_parser('fetch', help='Fetch data from API')
    fetch_parser.add_argument('url', help='API URL')
    fetch_parser.add_argument('-o', '--output', help='Output JSON file')
    fetch_parser.add_argument('--headers', help='Headers as JSON string')
    fetch_parser.add_argument('--csv', action='store_true', help='Export as CSV')

    # Sync
    sync_parser = subparsers.add_parser('sync', help='Sync between APIs')
    sync_parser.add_argument('--source', required=True, help='Source API URL')
    sync_parser.add_argument('--dest', required=True, help='Destination API URL')
    sync_parser.add_argument('--headers', help='Headers as JSON string')

    # Poll
    poll_parser = subparsers.add_parser('poll', help='Poll an API')
    poll_parser.add_argument('url', help='API URL')
    poll_parser.add_argument('--interval', type=int, default=60)
    poll_parser.add_argument('--max', type=int, help='Max iterations')

    # Webhook
    webhook_parser = subparsers.add_parser('webhook', help='Start webhook listener')
    webhook_parser.add_argument('--port', type=int, default=8080)

    args = parser.parse_args()

    if args.command == 'fetch':
        headers = json.loads(args.headers) if args.headers else None
        data = fetch_api_data(args.url, headers=headers)
        if args.csv:
            output = args.output or 'api_data.csv'
            export_api_to_csv(args.url, output, headers)
        elif args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data saved to: {args.output}")
        else:
            print(json.dumps(data, indent=2))

    elif args.command == 'sync':
        headers = json.loads(args.headers) if args.headers else None
        sync_apis(args.source, dest=args.dest, headers=headers)

    elif args.command == 'poll':
        poll_api(args.url, args.interval, max_iterations=args.max)

    elif args.command == 'webhook':
        webhook_listener(args.port)

    else:
        parser.print_help()
