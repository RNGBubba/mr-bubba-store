#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Data Visualization Service
Handles incoming emails, acknowledges receipt, provides info, and routes requests.

API Key: am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7
Inbox: mrbubba@agentmail.to

Usage:
    python3 auto_responder.py [--once] [--poll-interval 30]
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
INBOX_ID = "mrbubba@agentmail.to"
BASE_URL = "https://api.agentmail.to/v1"

# Service info
SERVICE_NAME = "Mr Bubba Data Visualization"
PRICE_RANGE = "$75 - $150"
TURNAROUND = "24-48 hours"
SUPPORTED_FORMATS = ["CSV", "Excel (.xlsx/.xls)"]
SUPPORTED_CHARTS = ["Line", "Bar", "Scatter", "Histogram", "Pie", "Heatmap", "Box Plot", "Area Chart", "Full Dashboard"]

RESPONSES = {
    "data_received": """Subject: Data Received — Visualization Project Started

Hi {name},

Thanks for sending your data! I've received your file and here's what happens next:

- File: {filename}
- Received: {timestamp}

I'll analyze your data and generate the charts you requested. You should have your visualizations within {turnaround}.

Pricing: {price_range}
You'll receive a PayPal invoice once the charts are ready.

Questions? Just reply to this email.

Best regards,
Mr Bubba Data Visualization
""",

    "inquiry": """Subject: Data Visualization Service

Hi {name},

Thanks for your interest in data visualization. Here's what I offer:

I turn raw data (CSV/Excel) into professional charts and dashboards using Python.

Accepted formats: CSV, Excel (.xlsx/.xls)

Chart types available:
{charts}

Pricing:
- Simple dataset (1 chart): $75
- Standard package (3-5 charts): $100
- Full dashboard: $125
- Complex/multi-sheet: up to $150

Turnaround: Usually {turnaround} depending on complexity.

To get started, just reply with your data file attached. I'll review it and send a PayPal invoice for the agreed scope.

Best regards,
Mr Bubba Data Visualization
""",

    "deliver": """Subject: Your Visualizations Are Ready

Hi {name},

Your visualizations are complete!

- {chart_count} chart(s) generated
- High-resolution PNG format (150 DPI)
- Professional styling

A PayPal invoice for {amount} has been sent to your email. Once payment is confirmed, I'll send the files directly.

Need changes? One round of revisions is included at no extra cost.

Thanks for your business.

Best regards,
Mr Bubba Data Visualization
""",
}


def send_email(to_email, to_name, subject, body, api_key=AGENTMAIL_API_KEY):
    """Send email via AgentMail API."""
    import urllib.request

    url = f"{BASE_URL}/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "text": body,
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"✅ Sent to {to_email}: {subject}")
            return result
    except Exception as e:
        print(f"❌ Failed to send to {to_email}: {e}")
        return None


def check_inbox(api_key=AGENTMAIL_API_KEY):
    """Check for new emails in inbox."""
    import urllib.request

    url = f"{BASE_URL}/inbox/{INBOX_ID}/messages?status=unread&limit=10"
    headers = {"Authorization": f"Bearer {api_key}"}

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Failed to check inbox: {e}")
        return None


def has_attachment(message):
    """Check if message has file attachments."""
    attachments = message.get('attachments', [])
    return len(attachments) > 0


def get_attachment_files(message):
    """Extract attachment file info from message."""
    return message.get('attachments', [])


def classify_email(message):
    """Classify incoming email type."""
    subject = message.get('subject', '').lower()
    body = message.get('body', '').lower()

    # Check for data submission (has attachments)
    if has_attachment(message) and any(
        ext in message.get('subject', '').lower() or
        any(ext in a.get('name', '').lower() for a in get_attachment_files(message))
        for ext in ['.csv', '.xlsx', '.xls']
    ):
        return "data_received"

    # Keywords for inquiry
    inquiry_keywords = ['price', 'cost', 'quote', 'how much', 'rate', 'service',
                        'do you', 'available', 'offer', 'package', 'info',
                        'what can', 'interested', 'help', 'question']

    if any(kw in subject or kw in body for kw in inquiry_keywords):
        return "inquiry"

    # Default: treat as inquiry for anything else
    return "inquiry"


def generate_project_id():
    """Generate unique project ID."""
    return f"DV-{int(time.time()) % 100000:05d}"


def process_message(message):
    """Process a single incoming message and send appropriate response."""
    sender = message.get('from', {})
    sender_email = sender.get('email', '')
    sender_name = sender.get('name', 'there').strip() or 'there'
    subject = message.get('subject', '(no subject)')

    msg_type = classify_email(message)
    project_id = generate_project_id()
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    print(f"📨 [{msg_type}] From: {sender_name} <{sender_email}> | Subject: {subject}")

    if msg_type == "data_received":
        attachments = get_attachment_files(message)
        filename = attachments[0].get('name', 'data_file') if attachments else 'unknown'
        body = RESPONSES["data_received"].format(
            name=sender_name,
            filename=filename,
            timestamp=timestamp,
            project_id=project_id,
            turnaround=TURNAROUND,
            price_range=PRICE_RANGE,
            SERVICE_NAME=SERVICE_NAME,
        )
        send_email(sender_email, sender_name, "Data Received - Visualization Project Started", body)

    elif msg_type == "inquiry":
        body = RESPONSES["inquiry"].format(
            name=sender_name,
            SERVICE_NAME=SERVICE_NAME,
            formats='\n'.join(f'  • {f}' for f in SUPPORTED_FORMATS),
            charts='\n'.join(f'  • {c}' for c in SUPPORTED_CHARTS),
            price_range=PRICE_RANGE,
            turnaround=TURNAROUND,
        )
        send_email(sender_email, sender_name, "Data Visualization Service - Quick Info", body)


def run_polling_loop(poll_interval=30):
    """Run continuous polling loop for new emails."""
    print(f"🤖 AgentMail Auto-Responder Started")
    print(f"📬 Inbox: {INBOX_ID}")
    print(f"⏱️  Polling every {poll_interval}s (Ctrl+C to stop)")
    print("-" * 50)

    while True:
        try:
            messages = check_inbox()
            if messages and 'data' in messages:
                for msg in messages.get('data', []):
                    process_message(msg)
                    # Mark as read
                    msg_id = msg.get('id')
                    if msg_id:
                        mark_read(msg_id)

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n👋 Auto-Responder stopped by user.")
            break
        except Exception as e:
            print(f"⚠️  Error in polling loop: {e}")
            time.sleep(poll_interval)


def mark_read(message_id, api_key=AGENTMAIL_API_KEY):
    """Mark a message as read."""
    import urllib.request

    url = f"{BASE_URL}/inbox/{INBOX_ID}/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"status": "read"}).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers=headers, method='PATCH')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True
    except Exception:
        return False


def run_once():
    """Run single check for new messages."""
    print("🤖 Checking for new messages...")
    messages = check_inbox()
    if not messages or 'data' not in messages:
        print("📭 No new messages.")
        return

    msgs = messages.get('data', [])
    print(f"📬 Found {len(msgs)} unread message(s)")

    for msg in msgs:
        process_message(msg)
        mark_read(msg.get('id'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AgentMail Auto-Responder for Data Viz Service')
    parser.add_argument('--once', action='store_true', help='Run single check and exit')
    parser.add_argument('--poll-interval', type=int, default=30,
                        help='Polling interval in seconds (default: 30)')
    args = parser.parse_args()

    if args.once:
        run_once()
    else:
        run_polling_loop(args.poll_interval)
