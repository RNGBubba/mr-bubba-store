#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Mr Bubba Services Email Copywriting
Handles incoming inquiries and sends automated responses.

Usage:
    python3 automail_responder.py --mode respond    # Check inbox and auto-respond
    python3 automail_responder.py --mode webhook     # Run as webhook server
    python3 automail_responder.py --mode test        # Test mode (print only)
"""

import json
import os
import time
import hashlib
import hmac
import logging
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import urllib.request
import urllib.error

# ── Configuration ─────────────────────────────────────────────────────────

AGENTMAIL_API_KEY = os.environ.get(
    "AGENTMAIL_API_KEY",
    "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
)
AGENTMAIL_INBOX = os.environ.get("AGENTMAIL_INBOX", "mrbubba@agentmail.to")
AGENTMAIL_BASE_URL = "https://api.agentmail.to/v1"

WELCOME_RESPONSE = """Subject: Thanks for Reaching Out — Mr Bubba Services

Hi there,

Thanks for reaching out about email copywriting. I'll review your message and get back to you within 24 hours.

To help me write the best copy for you, it'd be great to know:

- What your product or service is
- Who you're writing to
- What kind of emails you need (welcome, promotional, follow-up, newsletter, re-engagement)
- Any specific offers or key benefits to highlight
- Your preferred tone (professional, casual, friendly, etc.)

Pricing: $25–75 per email depending on complexity
Turnaround: 1–2 business days per email
Delivery: Copy sent directly to your email

Feel free to reply with any questions or additional details.

Best regards,
Mr Bubba Services
"""

CONFIRMATION_RESPONSE = """Subject: Email Copy Received — Mr Bubba Services

Hi there,

I've got everything I need to start on your email copy.

Here's what happens next:

1. I'll write your email copy based on the details you provided
2. You'll have the finished copy in your inbox within 1–2 business days
3. I'll send a PayPal invoice (payable via card or PayPal balance)

Need to add anything? Just reply to this email.

Best regards,
Mr Bubba Services
"""

ALREADY_RESPONDED = """Subject: Re: Your Email Copywriting Inquiry

Hi there,

I think we've already connected on this. If you have additional details or questions, feel free to reply here.

Otherwise, keep an eye on your inbox — your email copy is on its way.

Best regards,
Mr Bubba Services
"""

# ── Logging Setup ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/automail_responder.log"),
    ],
)
logger = logging.getLogger(__name__)


# ── AgentMail API Client ──────────────────────────────────────────────────

class AgentMailClient:
    """Minimal client for AgentMail API."""

    def __init__(self, api_key: str, inbox: str):
        self.api_key = api_key
        self.inbox = inbox
        self.base_url = AGENTMAIL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make an API request to AgentMail."""
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error(f"API error {e.code}: {error_body}")
            return {"error": True, "status": e.code, "body": error_body}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": True, "message": str(e)}

    def get_inbox(self, limit: int = 20) -> list:
        """Fetch recent inbox messages."""
        result = self._request("GET", f"/inboxes/{self.inbox}/messages?limit={limit}")
        if isinstance(result, dict) and "messages" in result:
            return result["messages"]
        if isinstance(result, list):
            return result
        logger.warning(f"Unexpected inbox response: {result}")
        return []

    def send_message(self, to: str, subject: str, body: str) -> dict:
        """Send an email via AgentMail."""
        data = {
            "to": to,
            "subject": subject,
            "text": body,
            "from": self.inbox,
        }
        return self._request("POST", f"/inboxes/{self.inbox}/messages", data)

    def get_message(self, message_id: str) -> dict:
        """Get a specific message by ID."""
        return self._request("GET", f"/inboxes/{self.inbox}/messages/{message_id}")


# ── Auto-Responder Logic ──────────────────────────────────────────────────

class AutoResponder:
    """Handles auto-responses for email copywriting inquiries."""

    def __init__(self, client: AgentMailClient, state_file: str = None):
        self.client = client
        self.state_file = state_file or os.path.join(
            os.path.expanduser("~"), ".mr-bubba-mission", "email_copy_state.json"
        )
        self.responded = self._load_state()

    def _load_state(self) -> set:
        """Load set of already-responded message IDs."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    return set(json.load(f).get("responded", []))
        except Exception:
            pass
        return set()

    def _save_state(self):
        """Persist responded message IDs."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({"responded": list(self.responded), "updated_at": datetime.now().isoformat()}, f, indent=2)

    def _classify_message(self, message: dict) -> str:
        """Classify incoming message type."""
        subject = message.get("subject", "").lower()
        body = message.get("text", "").lower() or message.get("body", "").lower()
        combined = subject + " " + body

        # Check for inquiry indicators
        inquiry_keywords = [
            "email copy", "email writing", "copywriting", "email sequence",
            "welcome email", "promotional email", "follow up email",
            "need email", "write email", "create email", "draft email",
            "inquiry", "interested", "quote", "pricing", "how much",
            "service", "product email", "campaign",
        ]

        for kw in inquiry_keywords:
            if kw in combined:
                return "inquiry"

        # Check if it's a follow-up to our work
        if "thank" in combined or "received" in combined or "got it" in combined:
            return "follow_up"

        # Check for payment/invoice related
        if "invoice" in combined or "pay" in combined or "payment" in combined:
            return "payment_query"

        return "other"

    def _get_response(self, classification: str) -> tuple:
        """Get appropriate response based on classification."""
        responses = {
            "inquiry": ("Re: Email Copywriting Inquiry — Mr Bubba Services", WELCOME_RESPONSE),
            "follow_up": ("Re: Your Email Copywriting Request", CONFIRMATION_RESPONSE),
            "payment_query": ("Re: Payment & Invoicing — Mr Bubba Services", ""),
            "other": ("Re: Your Message — Mr Bubba Services", ""),
        }
        return responses.get(classification, ("Re: Your Message", ""))

    def process_inbox(self, dry_run: bool = False) -> list:
        """Check inbox and auto-respond to new messages."""
        messages = self.client.get_inbox()
        results = []

        for msg in messages:
            msg_id = msg.get("id") or msg.get("message_id")
            sender = msg.get("from", "")

            # Skip own messages
            if AGENTMAIL_INBOX in sender:
                continue

            # Skip already responded
            if msg_id in self.responded:
                logger.info(f"Skipping already-responded message: {msg_id}")
                continue

            classification = self._classify_message(msg)
            subject, body = self._get_response(classification)

            if not body:
                logger.info(f"No template for classification '{classification}', skipping")
                continue

            result = {
                "message_id": msg_id,
                "from": sender,
                "classification": classification,
                "subject": subject,
                "sent": False,
            }

            if dry_run:
                logger.info(f"[DRY RUN] Would respond to {sender} ({classification})")
                result["dry_run"] = True
            else:
                resp = self.client.send_message(sender, subject, body)
                if not resp.get("error"):
                    result["sent"] = True
                    self.responded.add(msg_id)
                    self._save_state()
                    logger.info(f"Responded to {sender} ({classification})")
                else:
                    result["error"] = resp
                    logger.error(f"Failed to respond to {sender}: {resp}")

            results.append(result)

        return results

    def watch_loop(self, interval: int = 300, dry_run: bool = False):
        """Continuously poll inbox for new messages."""
        logger.info(f"Starting watch loop (interval: {interval}s, dry_run: {dry_run})")
        while True:
            try:
                results = self.process_inbox(dry_run=dry_run)
                if results:
                    logger.info(f"Processed {len(results)} messages")
            except Exception as e:
                logger.error(f"Watch loop error: {e}")
            time.sleep(interval)


# ── Webhook Handler ───────────────────────────────────────────────────────

class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for AgentMail webhook integration."""

    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
                logger.info(f"Webhook received: {data.get('event', 'unknown')}")

                # Process webhook event
                event_type = data.get("event", "")
                if event_type == "message.received":
                    message = data.get("data", {})
                    responder = AutoResponder(AgentMailClient(AGENTMAIL_API_KEY, AGENTMAIL_INBOX))
                    classification = responder._classify_message(message)
                    subject, response_body = responder._get_response(classification)

                    if response_body and message.get("from"):
                        responder.client.send_message(message["from"], subject, response_body)
                        logger.info(f"Webhook auto-responded to {message['from']}")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())

            except Exception as e:
                logger.error(f"Webhook error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.info(f"HTTP: {format % args}")


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AgentMail Auto-Responder for Mr Bubba Services")
    parser.add_argument("--mode", choices=["respond", "watch", "webhook", "test"], default="respond",
                        help="Operating mode")
    parser.add_argument("--interval", type=int, default=300, help="Watch loop interval (seconds)")
    parser.add_argument("--port", type=int, default=8765, help="Webhook server port")
    parser.add_argument("--dry-run", action="store_true", help="Test mode (no actual sending)")
    args = parser.parse_args()

    client = AgentMailClient(AGENTMAIL_API_KEY, AGENTMAIL_INBOX)
    responder = AutoResponder(client)

    if args.mode == "respond":
        results = responder.process_inbox(dry_run=args.dry_run)
        print(json.dumps(results, indent=2, default=str))

    elif args.mode == "watch":
        responder.watch_loop(interval=args.interval, dry_run=args.dry_run)

    elif args.mode == "webhook":
        server = HTTPServer(("0.0.0.0", args.port), WebhookHandler)
        logger.info(f"Webhook server listening on port {args.port}")
        print(f"Webhook server running at http://0.0.0.0:{args.port}/webhook")
        server.serve_forever()

    elif args.mode == "test":
        # Test: print sample auto-response
        sample_msg = {
            "subject": "Need email copy for my SaaS product",
            "text": "Hi, I need help writing welcome emails for my new SaaS tool. Can you help?",
            "from": "test@example.com",
        }
        classification = responder._classify_message(sample_msg)
        subject, body = responder._get_response(classification)
        print(f"Classification: {classification}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")


if __name__ == "__main__":
    main()
