#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Spreadsheet Template Builder Service.
Monitors inbox for client inquiries and sends automated responses.

Usage:
    python3 automail_responder.py --check    # Check for new messages and respond
    python3 automail_responder.py --test     # Send a test message
"""

import json
import sys
import os
import argparse
from datetime import datetime

import requests

# AgentMail configuration
AGENTMAIL_API_KEY = os.environ.get(
    'AGENTMAIL_API_KEY',
    'am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7'
)
INBOX_EMAIL = 'mrbubba@agentmail.to'
AGENTMAIL_BASE_URL = 'https://api.agentmail.to/v1'

# Template type detection keywords
TEMPLATE_KEYWORDS = {
    'budget': ['budget', 'expense', 'spending', 'personal finance', 'cost tracking', 'monthly budget'],
    'invoice': ['invoice', 'billing', 'client payment', 'accounts receivable', 'money owed', 'payment tracking'],
    'project': ['project', 'task', 'assignment', 'team', 'deadline', 'milestone', 'kanban'],
    'sales': ['sales', 'pipeline', 'lead', 'deal', 'revenue', 'prospect', 'crm', 'sales tracker'],
    'inventory': ['inventory', 'stock', 'product', 'sku', 'warehouse', 'supply', 'stock management'],
    'payroll': ['payroll', 'employee', 'salary', 'wage', 'paycheck', 'staff payment', 'payroll calc'],
}


def detect_template_type(message_body):
    """Detect the most likely template type from message content."""
    body_lower = message_body.lower()
    
    scores = {}
    for template_type, keywords in TEMPLATE_KEYWORDS.items():
        scores[template_type] = sum(1 for kw in keywords if kw in body_lower)
    
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        return None
    return best_match


def generate_response(incoming_msg):
    """Generate an appropriate auto-response based on the incoming message."""
    sender = incoming_msg.get('from', 'there')
    subject = incoming_msg.get('subject', 'Your Inquiry')
    body = incoming_msg.get('body', '')
    
    # Extract name from sender email
    sender_name = sender.split('@')[0].replace('.', ' ').title() if '@' in sender else 'there'
    
    # Detect template type
    detected_type = detect_template_type(body)
    
    if detected_type:
        response = f"""Hi {sender_name},

Thanks for your interest in the Custom Spreadsheet Template service.

Based on your message, a {detected_type.title()} template sounds like a good fit. Here's what I can build for you:

- Pre-built formulas and calculations
- Professional formatting with multiple sheets for data entry and summaries
- Automated totals, averages, and conditional calculations
- Input cells highlighted for easy entry
- Print-ready layout

Pricing:
- Standard Template: $25
- Premium Template (advanced formulas + dashboard): $35
- Enterprise Template (multi-sheet + VBA automation): $50

To get started, just reply with:
1. Your name or company for the template header
2. Any specific fields or columns you need
3. Your preferred tier (Standard, Premium, or Enterprise)

I'll have your custom template ready within 2 hours of confirmation.

Best,
Mr Bubba Services
{INBOX_EMAIL}
"""
    else:
        response = f"""Hi {sender_name},

Thanks for reaching out to Mr Bubba Services.

I build custom spreadsheet templates for a range of business needs, including:

- Budget trackers for personal or business expense tracking
- Invoice trackers for client billing and accounts receivable
- Project managers for task tracking with deadlines
- Sales pipelines for lead and deal management
- Inventory managers for stock tracking with reorder alerts
- Payroll calculators for employee wage calculations

Pricing:
- Standard: $25 | Premium: $35 | Enterprise: $50

To get started, just reply and tell me what data you need to track and what you'll use it for. I'll recommend the right template and have it custom-built within 2 hours.

Best,
Mr Bubba Services
{INBOX_EMAIL}
"""
    
    return response


def send_response(to_email, subject, body):
    """Send an email response via AgentMail API."""
    url = f"{AGENTMAIL_BASE_URL}/send"
    
    headers = {
        'Authorization': f'Bearer {AGENTMAIL_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'from': INBOX_EMAIL,
        'to': to_email,
        'subject': subject,
        'text': body,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, str(e)


def check_inbox():
    """Check for new messages in the AgentMail inbox."""
    url = f"{AGENTMAIL_BASE_URL}/inbox"
    
    headers = {
        'Authorization': f'Bearer {AGENTMAIL_API_KEY}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking inbox: {e}")
        return None


def process_new_messages():
    """Check inbox and respond to new messages."""
    messages = check_inbox()
    
    if not messages:
        print("No new messages or error checking inbox.")
        return
    
    # Handle different response formats
    if isinstance(messages, dict):
        message_list = messages.get('messages', messages.get('data', []))
    elif isinstance(messages, list):
        message_list = messages
    else:
        print(f"Unexpected response format: {type(messages)}")
        return
    
    if not message_list:
        print("No new messages.")
        return
    
    print(f"Found {len(message_list)} message(s) to process.")
    
    for msg in message_list:
        sender = msg.get('from', '')
        subject = msg.get('subject', 'Re: Your Spreadsheet Template Inquiry')
        
        # Skip our own messages
        if INBOX_EMAIL in sender:
            continue
        
        print(f"\nProcessing message from: {sender}")
        print(f"Subject: {subject}")
        
        # Generate and send response
        response_body = generate_response(msg)
        response_subject = f"Re: {subject}"
        
        success, result = send_response(sender, response_subject, response_body)
        
        if success:
            print(f"Response sent to {sender}")
        else:
            print(f"Failed to send response: {result}")
    
    print(f"\nProcessed {len(message_list)} message(s).")


def test_mode():
    """Send a test response to verify the auto-responder works."""
    print("Running in test mode...\n")
    
    # Simulate an incoming message
    test_msg = {
        'from': 'test@example.com',
        'subject': 'Need a budget spreadsheet',
        'body': 'Hi, I need a spreadsheet to track my monthly expenses and budget categories.',
    }
    
    print("Test message:")
    print(f"  From: {test_msg['from']}")
    print(f"  Subject: {test_msg['subject']}")
    print(f"  Body: {test_msg['body']}")
    print()
    
    response = generate_response(test_msg)
    print("Generated response:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    
    # Send test response
    print("\nSending test response...")
    success, result = send_response(test_msg['from'], f"Re: {test_msg['subject']}", response)
    
    if success:
        print("Test response sent successfully!")
    else:
        print(f"Failed: {result}")
    
    return success


def main():
    parser = argparse.ArgumentParser(description='AgentMail Auto-Responder for Spreadsheet Templates')
    parser.add_argument('--check', action='store_true', help='Check inbox and respond to new messages')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (check every 60 seconds)')
    
    args = parser.parse_args()
    
    if args.test:
        test_mode()
    elif args.check:
        process_new_messages()
    elif args.daemon:
        import time
        print("Running in daemon mode. Checking every 60 seconds. Press Ctrl+C to stop.")
        try:
            while True:
                process_new_messages()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nDaemon stopped.")
    else:
        # Default: check inbox
        process_new_messages()


if __name__ == '__main__':
    main()
