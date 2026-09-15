#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Proposal Writing Service
Monitors inbox for new inquiries and responds automatically.

Requires: requests library
API Key: am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7
Inbox: mrbubba@agentmail.to

Usage:
    python3 agentmail_responder.py --check
    python3 agentmail_responder.py --auto-reply-all
    python3 agentmail_responder.py --process <message_id>
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7")
AGENTMAIL_EMAIL = os.environ.get("AGENTMAIL_EMAIL", "mrbubba@agentmail.to")
AGENTMAIL_BASE_URL = "https://api.agentmail.to/v1"
SERVICE_NAME = "Mr Bubba Services"


def get_inbox_messages(limit: int = 10, unread_only: bool = True) -> list:
    """Fetch messages from AgentMail inbox."""
    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{AGENTMAIL_BASE_URL}/inboxes/{AGENTMAIL_EMAIL}/messages"
    params = {"limit": limit}
    if unread_only:
        params["unread"] = "true"
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("messages", [])
    except requests.RequestException as e:
        print(f"Error fetching messages: {e}")
        return []


def send_reply(to_email: str, subject: str, body: str) -> dict:
    """Send a reply via AgentMail."""
    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{AGENTMAIL_BASE_URL}/send"
    payload = {
        "from": AGENTMAIL_EMAIL,
        "to": to_email,
        "subject": subject,
        "body": body,
        "html": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return {"status": "sent", "response": response.json()}
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


def generate_auto_reply(original_subject: str, sender_name: str = "") -> str:
    """Generate an automated response for proposal inquiries."""
    greeting = f"Hi {sender_name}," if sender_name else "Hi there,"
    
    body = f"""Hi {sender_name},

Thanks for reaching out about proposal writing services. I got your message and wanted to let you know I'm on it.

I'll review what you've sent and get back to you within a day or so. If I have any questions, I'll reach out.

To help me put together the best proposal, it would be useful to know:
- Your company name and main contact
- A brief description of the project
- Your timeline or deadline
- Budget range, if you have one in mind
- Any specific deliverables you're looking for

Pricing for proposals usually runs $50-$150 for a standard single-page scope, and $150-$200 for more comprehensive multi-phase proposals. Rush delivery (24-48 hours) is an extra $50.

Feel free to reply with any questions. I typically respond within a few hours during the workday.

Best,
Mr Bubba Services
{AGENTMAIL_EMAIL}
"""
    return body


def process_new_messages(auto_reply: bool = True) -> list:
    """Check for new messages and optionally auto-reply."""
    messages = get_inbox_messages(limit=20)
    results = []
    
    for msg in messages:
        msg_id = msg.get("id", "unknown")
        sender = msg.get("from", "unknown")
        subject = msg.get("subject", "No Subject")
        sender_name = sender.split("<")[0].strip() if "<" in sender else ""
        
        print(f"Message ID: {msg_id}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        
        result = {
            "id": msg_id,
            "from": sender,
            "subject": subject,
            "auto_replied": False
        }
        
        if auto_reply:
            reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
            reply_body = generate_auto_reply(subject, sender_name)
            
            send_result = send_reply(sender, reply_subject, reply_body)
            result["auto_replied"] = send_result["status"] == "sent"
            result["send_result"] = send_result
            
            if result["auto_replied"]:
                print(f"  ✓ Auto-reply sent to {sender}")
            else:
                print(f"  ✗ Failed to auto-reply: {send_result.get('error', 'Unknown error')}")
        
        results.append(result)
        print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description="AgentMail Auto-Responder for Proposal Service")
    parser.add_argument("--check", action="store_true", help="Check inbox for new messages")
    parser.add_argument("--auto-reply-all", action="store_true", help="Auto-reply to all unread messages")
    parser.add_argument("--process", metavar="MESSAGE_ID", help="Process a specific message")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without sending")
    
    args = parser.parse_args()
    
    if args.auto_reply_all or args.check:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking inbox...\n")
        results = process_new_messages(auto_reply=args.auto_reply_all and not args.dry_run)
        
        if not results:
            print("No new messages found.")
        else:
            print(f"Processed {len(results)} message(s)")
        
        print(json.dumps(results, indent=2))
    elif args.process:
        print(f"Processing message {args.process}")
        # TODO: Implement single message processing
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
