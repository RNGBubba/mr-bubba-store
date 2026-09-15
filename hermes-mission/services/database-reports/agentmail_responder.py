#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Database Reports Service
Handles incoming inquiries from clients about report services.
"""

import argparse
import json
import os
from datetime import datetime

import requests


AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7")
AGENTMAIL_INBOX = os.environ.get("AGENTMAIL_INBOX", "mrbubba@agentmail.to")
AGENTMAIL_API_BASE = "https://api.agentmail.to/v1"

SERVICE_NAME = "Mr Bubba Data Reports"


# Response templates for common inquiry types
RESPONSE_TEMPLATES = {
    "pricing": {
        "subject": "Re: Your Mr Bubba Data Reports Pricing Inquiry",
        "body": """Hi {client_name},

Thanks for your interest in our Database Reports Service.

Here's our pricing:

Basic Report — $75
- Single CSV/database analysis
- Distribution charts and histograms
- Summary statistics table
- Data quality assessment
- Up to 100K rows

Standard Report — $125
- Everything in Basic, plus:
- Correlation analysis and heatmaps
- Time series visualizations
- Automated insights
- Up to 500K rows
- Delivery within 48 hours

Premium Report — $200
- Everything in Standard, plus:
- Custom SQL queries on your database
- Executive summary and recommendations
- Interactive charts
- Multiple data source integration
- Up to 2M rows
- Priority delivery (24 hours)

To get started, just reply with:
1. Your data (CSV file or database connection details)
2. Any specific questions or areas of focus
3. Your preferred timeline

Best regards,
Mr Bubba Services
mrbubba@agentmail.to"""
    },

    "new_order": {
        "subject": "Re: Mr Bubba Data Reports — Order Received",
        "body": """Hi {client_name},

Thanks for submitting your data for analysis. Here's what happens next:

1. We'll review your data within 2-4 hours
2. We'll process your dataset and generate the report
3. You'll receive a professional report with charts and insights
4. Payment link will be sent upon delivery

Typical turnaround: 24-48 hours depending on data complexity.

If you have specific questions you'd like answered or areas to highlight, just reply to this email.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to"""
    },

    "follow_up": {
        "subject": "Re: Mr Bubba Data Reports — Follow Up",
        "body": """Hi {client_name},

Thanks for following up on your report request.

If you need any modifications, additional analysis, or have questions about your delivered report, we're happy to help. We offer one complimentary revision for every report.

Please let us know:
- What specific changes you'd like
- Any additional data to include
- Questions about the findings

Best regards,
Mr Bubba Services
mrbubba@agentmail.to"""
    },

    "general": {
        "subject": "Re: Mr Bubba Data Reports Inquiry",
        "body": """Hi {client_name},

Thanks for reaching out to Mr Bubba Services.

We specialize in turning raw data into professional, actionable reports with charts, summaries, and insights.

Our services include:
- CSV/Database analysis and reporting
- Distribution analysis and visualization
- Correlation and trend analysis
- Data quality assessment
- Custom insights and recommendations
- Time series analysis

Pricing starts at $75 for basic reports, $125 for standard, and $200 for premium analysis.

To get started, just send us your data file or database connection details along with any specific questions you have, and we'll take it from there.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to"""
    }
}


def send_agentmail(to_email: str, subject: str, body: str, attachments: list = None) -> dict:
    """Send an email via AgentMail API."""
    url = f"{AGENTMAIL_API_BASE}/send"

    payload = {
        "from": AGENTMAIL_INBOX,
        "to": to_email,
        "subject": subject,
        "text": body,
        "html": body.replace("\n", "<br>"),
    }

    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code == 200:
        print(f"✅ Email sent successfully to {to_email}")
        return response.json()
    else:
        print(f"❌ Failed to send email: {response.status_code} — {response.text}")
        return {"error": response.text}


def classify_inquiry(subject: str, body: str) -> str:
    """Classify an incoming email to determine the appropriate response."""
    text = (subject + " " + body).lower()

    pricing_keywords = ["price", "cost", "how much", "pricing", "rate", "fee", "quote", "budget", "$", "dollar"]
    order_keywords = ["send", "submit", "upload", "analyze", "process", "report for", "here is my data", "database", "csv"]
    followup_keywords = ["follow up", "status", "update", "progress", "when", "timeline", "revision", "modify", "change"]

    if any(kw in text for kw in pricing_keywords):
        return "pricing"
    elif any(kw in text for kw in followup_keywords):
        return "follow_up"
    elif any(kw in text for kw in order_keywords):
        return "new_order"
    else:
        return "general"


def auto_respond(to_email: str, client_name: str, subject: str, body: str) -> dict:
    """Send an automated response based on inquiry classification."""
    category = classify_inquiry(subject, body)
    template = RESPONSE_TEMPLATES[category]

    response_subject = template["subject"]
    response_body = template["body"].format(client_name=client_name)

    return send_agentmail(to_email, response_subject, response_body)


def check_inbox() -> list:
    """Check the AgentMail inbox for new messages."""
    url = f"{AGENTMAIL_API_BASE}/inbox"
    headers = {"Authorization": f"Bearer {AGENTMAIL_API_KEY}"}

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        print(f"📬 Found {len(messages)} messages in inbox")
        return messages
    else:
        print(f"❌ Failed to check inbox: {response.status_code}")
        return []


def process_incoming_emails():
    """Main loop: check for new emails and auto-respond."""
    print(f"[{datetime.now().isoformat()}] Checking for new emails...")

    messages = check_inbox()

    for msg in messages:
        if msg.get("status") == "unread":
            sender = msg.get("from", "Client")
            subject = msg.get("subject", "")
            body = msg.get("body", "")
            message_id = msg.get("id")

            print(f"\n📨 New message from: {sender}")
            print(f"   Subject: {subject}")

            # Extract client name from email or use default
            client_name = sender.split("@")[0] if "@" in sender else "there"

            # Send auto-response
            result = auto_respond(sender, client_name, subject, body)

            # Mark as processed/read if API supports it
            print(f"   Classification: {classify_inquiry(subject, body)}")

    print(f"\n[{datetime.now().isoformat()}] Auto-responder cycle complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentMail Auto-Responder for Database Reports")
    parser.add_argument("--check", action="store_true", help="Check inbox and respond once")
    parser.add_argument("--monitor", action="store_true", help="Continuously monitor inbox")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--test", action="store_true", help="Send a test response")

    args = parser.parse_args()

    if args.test:
        result = auto_respond(
            "test@example.com",
            "Test Client",
            "What are your pricing options?",
            "Hi, I'd like to know how much you charge for data reports."
        )
        print(json.dumps(result, indent=2))
    elif args.check:
        process_incoming_emails()
    elif args.monitor:
        import time
        print(f"Starting inbox monitor (checking every {args.interval}s)...")
        while True:
            process_incoming_emails()
            time.sleep(args.interval)
    else:
        process_incoming_emails()
