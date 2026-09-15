#!/usr/bin/env python3
"""
AgentMail Auto-Responder for API Integration Inquiries
Mr Bubba Services

Handles incoming emails, classifies inquiry type, and sends appropriate
automated responses. Processes the inbox for new messages and responds
with relevant information or escalation.
"""

import json
import requests
import re
from datetime import datetime, timedelta

# === CONFIGURATION ===
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
INBOX_EMAIL = "mrbubba@agentmail.to"
AGENTMAIL_API_BASE = "https://api.agentmail.to/v1"

# === INQUIRY CLASSIFICATION PATTERNS ===
INQUIRY_PATTERNS = {
    "pricing": [
        r"price", r"cost", r"how much", r"quote", r"estimate", r"budget",
        r"afford", r"invest", r"rate", r"fee", r"charge"
    ],
    "technical": [
        r"api", r"integrat", r"connect", r"sync", r"webhook", r"endpoint",
        r"automat", r"python", r"script", r"code", r"development",
        r"google sheets", r"shopify", r"hubspot", r"crm", r"airtable"
    ],
    "availability": [
        r"when", r"timeline", r"how long", r"availab", r"schedule",
        r"deadline", r"urgent", r"asap", r"start"
    ],
    "support": [
        r"help", r"issue", r"bug", r"broken", r"error", r"fix",
        r"problem", r"not working", r"troubleshoot", r"support"
    ],
    "partnership": [
        r"partner", r"collab", r"resell", r"agency", r"referral",
        r"white.?label", r"affiliate"
    ],
}

# === AUTO-RESPONSE TEMPLATES ===
RESPONSES = {
    "pricing": """Subject: Re: Your API Integration Pricing Inquiry — Mr Bubba Services

Hi {name},

Thank you for your interest in our API Integration services!

Our pricing is tailored to the complexity and scope of each integration:

  • Simple API Integration (2 services, standard endpoints): $100
  • Medium Integration (3-5 services, custom logic): $200
  • Complex Integration (5+ services, custom workflows): $300+

Pricing factors include:
  - Number of services being connected
  - Data transformation requirements
  - Webhook/automation needs
  - Ongoing maintenance scope

Please reply with details about:
  1. Which services you'd like to connect
  2. Your expected data flow (one-time sync vs. real-time)
  3. Any specific endpoints or triggers needed

I'll prepare a detailed quote within 24 hours.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
""",

    "technical": """Subject: Re: Your Technical Inquiry — Mr Bubba Services

Hi {name},

Thanks for reaching out about API integrations!

We build custom Python scripts to connect services including:
  • Google Sheets ↔ CRM (HubSpot, Salesforce, Pipedrive)
  • Shopify ↔ Email notifications
  • WooCommerce ↔ Slack/Discord alerts
  • Airtable ↔ Notion sync
  • Custom REST API integrations

Each integration includes:
  ✓ Production-ready Python script
  ✓ Error handling & logging
  ✓ Setup documentation
  ✓ Field mapping configuration
  ✓ Webhook listener (if needed)

To get started, please share:
  1. Source service and authentication method
  2. Destination service and what data to send
  3. Trigger event (webhook, schedule, manual)

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
""",

    "availability": """Subject: Re: Project Timeline — Mr Bubba Services

Hi {name},

Thank you for considering Mr Bubba Services for your integration needs!

Our typical timelines:
  • Simple Integration (2 services): 1-2 business days
  • Medium Integration (3-5 services): 2-4 business days
  • Complex/Enterprise Integration: 5-10 business days

Current availability: We can typically start within 1-2 business days of project confirmation.

For urgent requests, please mention "URGENT" in your reply and I'll do my best to accommodate.

To move forward, please share:
  1. The services you need connected
  2. Your target deadline
  3. Any existing API documentation

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
""",

    "support": """Subject: Re: Support Request — Mr Bubba Services

Hi {name},

I'm sorry to hear you're experiencing an issue with your integration. Let me help!

Please provide the following so I can investigate quickly:
  1. The integration name/client it's for
  2. The error message or symptom
  3. When the issue started
  4. Any recent changes to connected services

For critical issues (integration down, data not flowing), I respond within 2 hours during business hours.

You can also check the integration logs at:
  - sync_errors.log (for data sync errors)
  - webhook_log.jsonl (for webhook delivery issues)

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
""",

    "partnership": """Subject: Re: Partnership Inquiry — Mr Bubba Services

Hi {name},

Thank you for your interest in partnering with Mr Bubba Services!

We're open to exploring:
  • Agency partnerships (white-label integration services)
  • Referral arrangements
  • Reseller programs
  • Collaborative projects

Please tell me more about:
  1. Your company and client base
  2. The type of partnership you're proposing
  3. Expected volume or scope

I'd be happy to schedule a call to discuss further.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
""",

    "default": """Subject: Re: Your Inquiry — Mr Bubba Services

Hi {name},

Thank you for contacting Mr Bubba Services! I've received your message and will respond personally within 24 hours.

If your inquiry is urgent, please reply with "URGENT" in the subject line.

For immediate reference:
  • Service: Custom API Integration Scripts
  • Range: $100-$300 per integration
  • Contact: mrbubba@agentmail.to

Best regards,
Mr Bubba Services
mrbubba@agentmail.to
"""
}


def classify_inquiry(email_body: str) -> str:
    """Classify the inquiry type based on email content."""
    body_lower = email_body.lower()
    scores = {}
    for category, patterns in INQUIRY_PATTERNS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, body_lower))
        if score > 0:
            scores[category] = score
    if not scores:
        return "default"
    return max(scores, key=scores.get)


def get_inbox_messages() -> list:
    """Fetch unread messages from AgentMail inbox."""
    headers = {"Authorization": f"Bearer {AGENTMAIL_API_KEY}"}
    try:
        resp = requests.get(
            f"{AGENTMAIL_API_BASE}/inboxes/{INBOX_EMAIL}/messages",
            headers=headers,
            params={"status": "unread", "limit": 10},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("messages", [])
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []


def send_reply(to_email: str, subject: str, body: str) -> bool:
    """Send email reply via AgentMail API."""
    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": to_email,
        "subject": subject,
        "body": body
    }
    try:
        resp = requests.post(
            f"{AGENTMAIL_API_BASE}/messages/send",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending reply to {to_email}: {e}")
        return False


def process_inquiry(message: dict) -> dict:
    """Process a single inquiry and return result."""
    sender_email = message.get("from", "")
    sender_name = message.get("from_name", sender_email.split("@")[0] if sender_email else "there")
    body = message.get("body", "")
    subject = message.get("subject", "")
    message_id = message.get("id", "")

    # Classify the inquiry
    inquiry_type = classify_inquiry(f"{subject} {body}")

    # Get response template
    response_template = RESPONSES.get(inquiry_type, RESPONSES["default"])
    response_body = response_template.format(name=sender_name.split("@")[0] if "@" in sender_name else sender_name)

    # Send reply
    reply_sent = send_reply(sender_email, f"Re: {subject}", response_body)

    return {
        "message_id": message_id,
        "sender": sender_email,
        "inquiry_type": inquiry_type,
        "reply_sent": reply_sent,
        "timestamp": datetime.now().isoformat()
    }


def run_auto_responder():
    """Main loop: check inbox and respond to inquiries."""
    print(f"[{datetime.now()}] AgentMail Auto-Responder started")
    print(f"  Inbox: {INBOX_EMAIL}")
    print(f"  API Key: {AGENTMAIL_API_KEY[:10]}...")

    messages = get_inbox_messages()
    print(f"  Unread messages: {len(messages)}")

    results = []
    for msg in messages:
        result = process_inquiry(msg)
        results.append(result)
        status = "✓" if result["reply_sent"] else "✗"
        print(f"  {status} [{result['inquiry_type']}] {result['sender']}")

    print(f"\n[{datetime.now()}] Processing complete. {len(results)} messages handled.")
    return results


if __name__ == "__main__":
    run_auto_responder()
