#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Resume & Cover Letter Tailoring Service

Monitors inbox for new messages and sends automated responses
for common inquiries about the service.
"""

import json
import os
import sys
import time
from datetime import datetime

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None


# ── Configuration ───────────────────────────────────────────────────────────

AGENTMAIL_API_KEY = os.environ.get(
    "AGENTMAIL_API_KEY",
    "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
)
AGENTMAIL_INBOX = os.environ.get("AGENTMAIL_INBOX", "mrbubba@agentmail.to")
AGENTMAIL_API_BASE = "https://api.agentmail.to/v1"

SERVICE_NAME = "Mr Bubba Services — Resume & Cover Letter Tailoring"
PRICING_URL = "https://mrbubbaservices.com/pricing"
SUPPORT_EMAIL = AGENTMAIL_INBOX


# ── Response Templates ──────────────────────────────────────────────────────

TEMPLATES = {
    "pricing_inquiry": """Subject: Re: Resume Tailoring Service — Pricing

Hi {name},

Thanks for asking about pricing for the Resume & Cover Letter Tailoring service.

Resume Tailoring — $30
Includes ATS optimization, keyword matching, up to 2 revision rounds, and 48-hour delivery.

Cover Letter — $30
Custom-written for your target role with 48-hour delivery.

Resume + Cover Letter Bundle — $50
Save $10. Includes priority 24-hour delivery, 3 revision rounds, and an ATS compatibility report.

Premium Package — $60
Everything in the bundle plus LinkedIn profile tips, interview talking points, and same-day delivery (if submitted before 2pm EST).

To get started, just reply with your current resume, the job description, and which package you'd like. I'll send a PayPal invoice once we confirm the details.

Best,
Mr Bubba Services
{SUPPORT_EMAIL}
""",

    "service_inquiry": """Subject: Re: Resume Tailoring Service — How It Works

Hi {name},

Happy to explain how it works.

You send over your resume and the job description you're targeting. I'll analyze the posting for keywords and requirements, then rewrite your resume to match. I also write a cover letter tailored to the role.

What I do:
- Optimize your resume for applicant tracking systems
- Match your language to the job description
- Polish formatting and structure
- Write a targeted cover letter

What I don't do:
- Make up experience or qualifications
- Write a completely new resume from scratch
- Guarantee interviews (no one can promise that)

Turnaround times:
- Resume or Cover Letter only: 48 hours
- Bundle: 24 hours
- Premium: Same-day if submitted before 2pm EST

If you'd like to move forward, just send your resume and a job description and we'll get started.

Best,
Mr Bubba Services
{SUPPORT_EMAIL}
""",

    "general_inquiry": """Subject: Re: Resume Tailoring Service — Thanks for Reaching Out

Hi {name},

Thanks for getting in touch. I've received your message and will get back to you shortly.

In the meantime, if you haven't already, feel free to send over your resume and a job description so I can get started right away.

Pricing:
- Resume: $30 | Cover Letter: $30
- Resume + Cover Letter Bundle: $50
- Premium (everything plus extras): $60

Let me know if you have any questions.

Best,
Mr Bubba Services
{SUPPORT_EMAIL}
""",

    "follow_up": """Subject: Re: Resume Tailoring Service — Status Update

Hi {name},

Just checking in on your resume tailoring request.

Status: {status}
Estimated completion: {eta}

If you have any questions or need to send additional information, just let me know.

Best,
Mr Bubba Services
{SUPPORT_EMAIL}
""",
}


# ── Email Classification ────────────────────────────────────────────────────

def classify_email(subject: str, body: str) -> str:
    """Classify incoming email to determine appropriate response."""
    text = f"{subject} {body}".lower()
    
    pricing_keywords = ["price", "cost", "how much", "pricing", "rate", "fee", "pay", "invoice"]
    service_keywords = ["how does", "how do", "work", "process", "what do you", "explain"]
    
    if any(kw in text for kw in pricing_keywords):
        return "pricing_inquiry"
    elif any(kw in text for kw in service_keywords):
        return "service_inquiry"
    else:
        return "general_inquiry"


def generate_response(template_key: str, context: dict) -> str:
    """Generate email response from template."""
    template = TEMPLATES.get(template_key, TEMPLATES["general_inquiry"])
    
    defaults = {
        "name": "there",
        "status": "In Progress",
        "eta": "24-48 hours",
        "SUPPORT_EMAIL": SUPPORT_EMAIL,
    }
    defaults.update(context)
    
    return template.format(**defaults)


# ── AgentMail API ───────────────────────────────────────────────────────────

class AgentMailClient:
    """Client for AgentMail API."""
    
    def __init__(self, api_key: str, inbox: str):
        self.api_key = api_key
        self.inbox = inbox
        self.base_url = AGENTMAIL_API_BASE
    
    def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make API request to AgentMail."""
        url = f"{self.base_url}{path}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            return {"error": str(e), "status": e.code, "body": error_body}
        except Exception as e:
            return {"error": str(e)}
    
    def list_emails(self, unread_only: bool = True) -> list:
        """List emails in the inbox."""
        result = self._request("GET", f"/inboxes/{self.inbox}/messages")
        messages = result.get("messages", result.get("data", []))
        
        if unread_only:
            messages = [m for m in messages if not m.get("read", False)]
        
        return messages
    
    def send_email(self, to: str, subject: str, body: str) -> dict:
        """Send an email via AgentMail."""
        data = {
            "to": to,
            "subject": subject,
            "body": body,
        }
        return self._request("POST", f"/inboxes/{self.inbox}/messages", data)
    
    def mark_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        return self._request("PATCH", f"/inboxes/{self.inbox}/messages/{message_id}", {"read": True})


# ── Main Loop ───────────────────────────────────────────────────────────────

def process_inbox(client: AgentMailClient, dry_run: bool = False):
    """Check inbox for new messages and respond."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking inbox: {client.inbox}")
    
    emails = client.list_emails(unread_only=True)
    
    if not emails:
        print("  No new messages.")
        return 0
    
    print(f"  Found {len(emails)} unread message(s)")
    responded = 0
    
    for email in emails:
        sender = email.get("from", email.get("sender", "unknown"))
        subject = email.get("subject", "(no subject)")
        body = email.get("body", email.get("text", ""))
        msg_id = email.get("id", email.get("message_id", ""))
        
        print(f"\n  From: {sender}")
        print(f"     Subject: {subject}")
        
        # Extract sender name
        name = "there"
        if "<" in sender:
            name = sender.split("<")[0].strip().strip('"')
        elif "@" in sender:
            name = sender.split("@")[0].replace(".", " ").title()
        
        # Classify and respond
        template_key = classify_email(subject, body)
        print(f"     Classification: {template_key}")
        
        response = generate_response(template_key, {"name": name})
        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        
        if dry_run:
            print(f"     [DRY RUN] Would send {template_key} response to {sender}")
            print(f"     Subject: {reply_subject}")
        else:
            result = client.send_email(sender, reply_subject, response)
            if "error" not in result:
                print(f"     Response sent successfully")
                client.mark_read(msg_id)
                responded += 1
            else:
                print(f"     Failed to send: {result.get('error')}")
    
    return responded


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentMail Auto-Responder")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300,
                       help="Check interval in seconds (default: 300)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be sent without sending")
    args = parser.parse_args()
    
    client = AgentMailClient(AGENTMAIL_API_KEY, AGENTMAIL_INBOX)
    
    print("=" * 50)
    print(f"AgentMail Auto-Responder: {SERVICE_NAME}")
    print(f"Inbox: {AGENTMAIL_INBOX}")
    print(f"Mode: {'Dry Run' if args.dry_run else 'Live'}")
    print("=" * 50)
    
    if args.once:
        process_inbox(client, dry_run=args.dry_run)
    else:
        print(f"Starting polling loop (interval: {args.interval}s)")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                process_inbox(client, dry_run=args.dry_run)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped.")


if __name__ == "__main__":
    main()
