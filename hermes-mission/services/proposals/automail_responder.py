#!/usr/bin/env python3
"""
Mr Bubba Services — AgentMail Auto-Responder
Monitors the inbox and sends automated replies to proposal inquiries.

Usage:
    python3 automail_responder.py --send "sender@example.com" --subject "Inquiry" --body "Tell me more"
    python3 automail_responder.py --test  (send a test auto-reply to yourself)
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# === Configuration ===
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
AGENTMAIL_API_BASE = "https://api.agentmail.to/v1"

COMPANY_INFO = {
    "name": "Mr Bubba Services",
    "inbox": AGENTMAIL_INBOX,
    "website": "https://mrbubba-services.com",
    "tagline": "Professional Proposal Writing Services",
}


# === Email Templates ===
def generate_acknowledgment(sender_name: str = "Valued Client") -> str:
    """Generate an acknowledgment email for a new inquiry."""
    return f"""Dear {sender_name},

Thank you for reaching out to Mr Bubba Services! We've received your inquiry about our proposal writing services.

WHAT HAPPENS NEXT:
1. Review: We review your project details within 24 hours.
2. Discovery: We may reach out with clarifying questions to ensure we fully understand your needs.
3. Proposal Draft: You receive a detailed proposal document (PDF or Word) outlining scope, timeline, and investment.
4. Delivery: Final proposal delivered to your inbox, ready for review and acceptance.

TO EXPEDITE YOUR PROPOSAL, PLEASE SHARE:
- Your name and company name
- Project title or description
- Key objectives and desired outcomes
- Target audience for the proposal
- Any specific format or content requirements
- Desired timeline or deadline

We're excited to help you create a compelling, professional proposal!

Best regards,
Mr Bubba Services Team
{COMPANY_INFO['inbox']}
"""


def generate_follow_up(sender_name: str = "Valued Client") -> str:
    """Generate a follow-up email for incomplete inquiries."""
    return f"""Dear {sender_name},

We noticed you reached out to Mr Bubba Services but we may need a bit more information to craft the perfect proposal for you.

To get started, it would be helpful if you could share:
- Your full name and company
- A brief description of the project or opportunity
- What you need the proposal for (grant, investor, client pitch, etc.)
- Your budget range (we offer services from $50 to $2000+)

The more detail you provide upfront, the more tailored and effective your proposal will be.

Feel free to reply to this email or send a new message to {COMPANY_INFO['inbox']}.

Best,
Mr Bubba Services
"""


def generate_pricing_info(sender_name: str = "Valued Client") -> str:
    """Generate pricing information email."""
    return f"""Dear {sender_name},

Thank you for your interest in Mr Bubba Services' proposal writing packages!

OUR PROPOSAL WRITING PACKAGES:

STARTER — $50-150
- 1-2 page proposal
- Standard business format
- 1 round of revisions
- 5 business day delivery

PROFESSIONAL — $150-500 ⭐ Most Popular
- 3-5 page proposal
- Executive summary + scope + timeline
- Custom formatting & branding
- 2 rounds of revisions
- 10 business day delivery

ENTERPRISE — $500-2000+
- 6-15+ page proposals
- Full business case development
- Financial modeling support
- Multiple revision rounds
- Rush delivery available (3-5 days)

CUSTOM — Let us know your needs!

READY TO GET STARTED?
Simply reply with your project details, and we'll prepare a custom proposal for you.

Best regards,
Mr Bubba Services Team
{COMPANY_INFO['inbox']}
"""


def generate_inquiry_response(inquiry_subject: str, inquiry_body: str, sender: str) -> str:
    """
    Generate an appropriate auto-response based on inquiry content.
    Analyzes keywords to determine the best template.
    """
    subject_lower = inquiry_subject.lower() if inquiry_subject else ""
    body_lower = inquiry_body.lower() if inquiry_body else ""
    combined = f"{subject_lower} {body_lower}"

    # Extract a name from sender email (before @)
    sender_name = sender.split("@")[0] if "@" in sender else "Valued Client"

    # Detect inquiry type
    pricing_keywords = ["price", "cost", "how much", "pricing", "fee", "rate", "budget", "quote", "package"]
    is_pricing_inquiry = any(kw in combined for kw in pricing_keywords)

    urgent_keywords = ["urgent", "asap", "rush", "deadline", "quick", "fast", "emergency"]
    is_urgent = any(kw in combined for kw in urgent_keywords)

    # Determine project complexity hints
    scope_keywords = ["scope", "details", "about", "project", "need", "want", "require"]
    has_details = any(kw in combined for kw in scope_keywords)

    # Build response
    if is_pricing_inquiry:
        return generate_pricing_info(sender_name)

    # Base response
    response = generate_acknowledgment(sender_name)

    # Add urgency note if detected
    if is_urgent:
        response += "\n---\nNOTE: We detected this may be time-sensitive. If you have a hard deadline, please mention it and we'll do our best to accommodate!"

    return response


class AgentMailClient:
    """Simple client for AgentMail API."""

    def __init__(self, api_key: str, inbox: str):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required: pip install requests")
        self.api_key = api_key
        self.inbox = inbox
        self.base_url = AGENTMAIL_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def send_email(self, to: str, subject: str, body: str) -> dict:
        """Send an email via AgentMail API."""
        payload = {
            "from": self.inbox,
            "to": to,
            "subject": subject,
            "text": body,
            "html": self._to_html(body),
        }

        try:
            resp = requests.post(
                f"{self.base_url}/emails",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def send_auto_reply(self, original_sender: str, original_subject: str = "", original_body: str = "") -> dict:
        """Send an automated reply to an inquiry."""
        reply_subject = "Re: Proposal Writing Services — Mr Bubba Services"
        if original_subject and not original_subject.startswith("Re:"):
            reply_subject = f"Re: {original_subject}"

        body = generate_inquiry_response(original_subject, original_body, original_sender)
        return self.send_email(original_sender, reply_subject, body)

    def _to_html(self, text: str) -> str:
        """Convert plain text to simple HTML."""
        html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = html.replace("\n\n", "</p><p>").replace("\n", "<br>")
        return f"<html><body><p>{html}</p></body></html>"


def main():
    parser = argparse.ArgumentParser(
        description="Mr Bubba Services — AgentMail Auto-Responder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 automail_responder.py --test
  python3 automail_responder.py --send "client@email.com" --subject "Pricing?" --body "How much?"
        """,
    )
    parser.add_argument("--send", help="Send auto-reply to this email address")
    parser.add_argument("--subject", default="", help="Original inquiry subject")
    parser.add_argument("--body", default="", help="Original inquiry body")
    parser.add_argument("--test", action="store_true", help="Send test auto-reply to self")
    parser.add_argument("--dry-run", action="store_true", help="Print response without sending")

    args = parser.parse_args()

    if not args.send and not args.test:
        parser.print_help()
        sys.exit(1)

    client = AgentMailClient(AGENTMAIL_API_KEY, AGENTMAIL_INBOX)

    if args.test:
        test_sender = AGENTMAIL_INBOX
        print(f"[TEST] Sending auto-reply to: {test_sender}")
        if args.dry_run:
            body = generate_inquiry_response("Proposal Inquiry", "Hi, I need a proposal for my business. What's the pricing?", test_sender)
            print(body)
        else:
            result = client.send_auto_reply(
                test_sender,
                "Proposal Inquiry",
                "Hi, I need a proposal for my business. What's the pricing?"
            )
            print(json.dumps(result, indent=2))
    elif args.send:
        print(f"[SEND] Auto-reply to: {args.send}")
        if args.dry_run:
            body = generate_inquiry_response(args.subject, args.body, args.send)
            print(body)
        else:
            result = client.send_auto_reply(args.send, args.subject, args.body)
            print(json.dumps(result, indent=2))
            if not result.get("success"):
                sys.exit(1)


if __name__ == "__main__":
    main()
