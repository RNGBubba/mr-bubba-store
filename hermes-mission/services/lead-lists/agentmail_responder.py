"""
Mr Bubba Services — AgentMail Auto-Responder
Handles incoming lead list inquiries via AgentMail API.
Automatically responds to quote requests and qualifies leads.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List

# Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_BASE_URL = "https://api.agentmail.to/v1"
INBOX_ID = "inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"

# Pricing tiers for auto-response
PRICING = {
    "starter": {"price": 60, "leads": 25, "delivery": "3-5 business days", "description": "Up to 25 verified leads"},
    "standard": {"price": 90, "leads": 50, "delivery": "5-7 business days", "description": "Up to 50 verified leads"},
    "premium": {"price": 120, "leads": 100, "delivery": "7-10 business days", "description": "Up to 100 verified leads"},
}


class AgentMailResponder:
    """Manages AgentMail inbox and auto-responds to inquiries."""

    def __init__(self, api_key: str = AGENTMAIL_API_KEY):
        self.api_key = api_key
        self.base_url = AGENTMAIL_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def get_inbox_messages(self, limit: int = 10, unread_only: bool = True) -> List[Dict]:
        """Fetch messages from AgentMail inbox."""
        try:
            url = f"{self.base_url}/messages"
            params = {
                "inbox_id": INBOX_ID,
                "limit": limit
            }
            if unread_only:
                params["status"] = "unread"
            
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("messages", [])
            else:
                print(f"Error fetching messages: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"AgentMail API error: {e}")
        return []

    def send_reply(self, to_email: str, subject: str, body: str, 
                   in_reply_to: Optional[str] = None) -> bool:
        """Send an email reply via AgentMail."""
        try:
            url = f"{self.base_url}/messages/send"
            payload = {
                "inbox_id": INBOX_ID,
                "to": to_email,
                "subject": subject,
                "body": body
            }
            if in_reply_to:
                payload["in_reply_to"] = in_reply_to
            
            resp = self.session.post(url, json=payload, timeout=15)
            success = resp.status_code == 200
            if success:
                print(f"  ✉️  Reply sent to {to_email}")
            else:
                print(f"  ❌ Failed to send: {resp.status_code}")
            return success
        except Exception as e:
            print(f"Send error: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            url = f"{self.base_url}/messages/{message_id}/read"
            resp = self.session.post(url, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_quote_response(self, client_name: str = "there") -> str:
        """Generate an auto-response with pricing information."""
        pricing_list = "\n".join([
            f"  {tier.capitalize()} — ${details['price']} for {details['description'].lower()} ({details['delivery']})"
            for tier, details in PRICING.items()
        ])
        
        body = f"""Hi {client_name},

Thanks for reaching out about our lead list service.

We build targeted B2B lead lists based on whatever criteria you need — industry, location, company size, revenue range, and so on.

Here are the typical packages:
{pricing_list}

Each list includes company names, websites, email addresses, phone numbers, industry classification, location data, and company size/revenue estimates. Everything comes as a CSV.

If you'd like to move forward, just let me know:
- What industry you're targeting
- Geographic location (city, state, country)
- Company size range
- Any specific keywords or criteria
- How many leads you need

Best,
Mr Bubba Services
mrbubba@agentmail.to
"""
        return body

    def generate_custom_response(self, inquiry_details: Dict, client_name: str = "there") -> str:
        """Generate a custom response based on parsed inquiry details."""
        industry = inquiry_details.get("industry", "your industry")
        location = inquiry_details.get("location", "your target area")
        size = inquiry_details.get("company_size", "")
        
        # Determine best pricing tier
        num_leads = inquiry_details.get("num_leads", 25)
        if num_leads <= 25:
            tier = "starter"
            price = 60
        elif num_leads <= 50:
            tier = "standard"
            price = 90
        else:
            tier = "premium"
            price = 120
        
        body = f"""Hi {client_name},

We can definitely help you build a lead list for {industry} in {location}.

Based on what you're looking for, I'd recommend the {tier.capitalize()} package at ${price}. That gets you {PRICING[tier]['description']} with delivery in {PRICING[tier]['delivery']}.

If you'd like to proceed, just reply to confirm and we'll send a PayPal invoice. Once paid, we'll start compiling your list right away.

Let me know if you have any questions.

Best,
Mr Bubba Services
mrbubba@agentmail.to
"""
        return body

    def process_inquiries(self):
        """Main loop to check and respond to new inquiries."""
        print("📬 Checking AgentMail for new inquiries...")
        
        messages = self.get_inbox_messages(limit=20, unread_only=True)
        print(f"   Found {len(messages)} unread messages")
        
        for msg in messages:
            sender = msg.get("from", "Unknown")
            subject = msg.get("subject", "No Subject")
            body = msg.get("body", "")
            msg_id = msg.get("id", "")
            
            print(f"\n  📨 Processing: {subject}")
            print(f"     From: {sender}")
            
            # Generate and send response
            response_body = self.generate_quote_response()
            reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
            
            self.send_reply(
                to_email=sender,
                subject=reply_subject,
                body=response_body,
                in_reply_to=msg_id
            )
            
            # Mark as read
            self.mark_as_read(msg_id)
            
            # Rate limiting
            time.sleep(1)


def run_daemon():
    """Run as a persistent daemon checking for new inquiries every 5 minutes."""
    responder = AgentMailResponder()
    print("🤖 AgentMail Auto-Responder Daemon Started")
    print("   Checking every 5 minutes for new inquiries...")
    print("   Press Ctrl+C to stop\n")
    
    while True:
        try:
            responder.process_inquiries()
            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\n⏹️  Daemon stopped.")
            break
        except Exception as e:
            print(f"Error in daemon loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        run_daemon()
    else:
        # Single check mode
        responder = AgentMailResponder()
        responder.process_inquiries()
