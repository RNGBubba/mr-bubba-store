#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Social Media Content Service
Mr Bubba Services

Listens for incoming emails via AgentMail API and automatically responds
to client inquiries about social media content packages.
"""

import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Configuration
AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7")
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
AGENTMAIL_API_URL = "https://api.agentmail.to/v1"
POLL_INTERVAL = 60  # seconds between inbox checks
REPLY_LOG_FILE = "reply_log.json"
SENT_REPLIES_FILE = "sent_replies.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("autoresponder.log"),
    ],
)
logger = logging.getLogger(__name__)


def load_sent_replies() -> Dict:
    """Load record of sent replies to avoid duplicates."""
    if Path(SENT_REPLIES_FILE).exists():
        with open(SENT_REPLIES_FILE, "r") as f:
            return json.load(f)
    return {"sent": []}


def save_sent_replies(record: Dict):
    """Save record of sent replies."""
    with open(SENT_REPLIES_FILE, "w") as f:
        json.dump(record, f, indent=2)


def check_inbox() -> List[Dict]:
    """Check the AgentMail inbox for new messages."""
    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            f"{AGENTMAIL_API_URL}/inbox/{AGENTMAIL_INBOX}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Parse messages from the inbox response
        messages = data.get("messages", [])
        if not messages:
            messages = data.get("data", [])
        return messages

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check inbox: {e}")
        return []


def extract_email_details(raw_message: Dict) -> Dict:
    """Extract relevant details from a raw email message."""
    return {
        "id": raw_message.get("id", raw_message.get("message_id", "")),
        "from": raw_message.get("from", raw_message.get("sender", "")),
        "subject": raw_message.get("subject", "No Subject"),
        "body": raw_message.get(
            "text",
            raw_message.get("body", raw_message.get("plain", ""))
        ),
        "received_at": raw_message.get("date", datetime.now().isoformat()),
    }


def is_already_replied(message_id: str, sent_record: Dict) -> bool:
    """Check if we've already replied to this message."""
    return message_id in sent_record.get("sent", [])


def generate_reply(email_data: Dict) -> str:
    """
    Generate an automated reply based on the incoming email content.
    Analyzes the email body for keywords and responds appropriately.
    """
    sender = email_data.get("from", "Client")
    body = email_data.get("body", "").lower()

    # Extract name from email
    name_part = sender.split("@")[0] if "@" in sender else sender
    name = name_part.replace(".", " ").replace("_", " ").title()

    # Detect intent
    if any(word in body for word in ["price", "cost", "how much", "pricing", "rate", "fee"]):
        return _pricing_response(name)

    elif any(word in body for word in ["sample", "example", "demo", "show me", "preview"]):
        return _sample_response(name)

    elif any(word in body for word in ["start", "begin", "signup", "sign up", "get started", "hire"]):
        return _onboarding_response(name)

    elif any(word in body for word in ["hello", "hi", "hey", "greetings"]):
        return _greeting_response(name)

    elif any(word in body for word in ["thank", "thanks", "appreciate"]):
        return _thank_you_response(name)

    elif any(word in body for word in ["cancel", "stop", "unsubscribe", "opt out"]):
        return _opt_out_response(name)

    else:
        return _default_response(name)


def _pricing_response(name: str) -> str:
    return f"""Hi {name},

Thanks for your interest in the Social Media Content packages.

Weekly — $50/week
7 ready-to-post social media pieces. Each post includes a caption, 10+ hashtags, and an image description. Content calendar delivered within 24 hours.

Monthly — $150/month
30 ready-to-post social media pieces with the same inclusions as weekly. Full month content calendar. Best value — save $50 compared to weekly.

What's included:
- Brand-customized captions
- Relevant hashtag sets (10+ per post)
- Detailed image descriptions
- Content pillar variety
- Platform optimization notes
- Posting time suggestions

To get started, just reply with:
1. Your brand name and tagline
2. Your industry or niche
3. Brand colors (hex codes preferred)
4. Target platforms (Instagram, Facebook, TikTok, etc.)
5. Preferred package

Looking forward to creating content that connects.

Best,
Mr Bubba Services
"""


def _sample_response(name: str) -> str:
    return f"""Hi {name},

Here's a sample of what we deliver.

Sample Post — Educational

"Did you know? Consistency beats intensity — 30 minutes daily outperforms sporadic 2-hour sessions."

Learn more about how your brand brings this to life.

#YourBrand #YourBrandLife #Fitness #Workout #HealthyLiving #Wellness #Health #DailyInspo

Image description: Clean infographic-style image with brand colors, logo top-left. Central text: "Consistency beats intensity" with relevant iconography. Minimalist layout with clear data visualization elements. Natural lighting with warm accent tones.

That's just one post. A full calendar includes varied content pillars: educational, entertaining, inspirational, promotional, behind-the-scenes, and community.

Want a custom sample for your specific brand? Send us your brand details.

Best,
Mr Bubba Services
"""


def _onboarding_response(name: str) -> str:
    return f"""Hi {name},

We'd love to get you started. Just reply with:

1. Brand name and tagline
2. Industry or niche (fitness, food, tech, fashion, business, etc.)
3. Brand colors (hex codes, e.g., #FF5733)
4. Target audience (age, interests, lifestyle)
5. Package: Weekly ($50) or Monthly ($150)
6. Platforms (Instagram, Facebook, TikTok, LinkedIn, etc.)
7. Any specific content themes or upcoming promotions

Once we have these details, we'll deliver your first content calendar within 24 hours, ready to post immediately and fully customized to your brand voice.

Reply to this email with your details and we'll get going.

Best,
Mr Bubba Services
"""


def _greeting_response(name: str) -> str:
    return f"""Hi {name},

Welcome to Mr Bubba Services.

We create social media content — captions, hashtags, and image descriptions — tailored to brands like yours.

Pricing:
- Weekly: $50 (7 posts)
- Monthly: $150 (30 posts)

Reply with "PRICING" for details, "SAMPLE" to see examples, or "START" to begin.

Happy to help,
Mr Bubba Services
"""


def _thank_you_response(name: str) -> str:
    return f"""Hi {name},

You're welcome. We're glad to help with your social media presence.

If you have any more questions or need anything else, just reach out.

Best,
Mr Bubba Services
"""


def _opt_out_response(name: str) -> str:
    return f"""Hi {name},

No problem. Your preferences have been noted and you won't receive further automated messages from us.

If you change your mind, we're always here to help.

Wishing you the best,
Mr Bubba Services
"""


def _default_response(name: str) -> str:
    return f"""Hi {name},

Thanks for reaching out to Mr Bubba Services.

We specialize in creating social media content (captions, hashtags, image descriptions) tailored to brands like yours.

Reply with:
- "PRICING" for package details and rates
- "SAMPLE" to see a content example
- "START" to begin onboarding

Or tell us about your brand and we'll put together a personalized response.

Best,
Mr Bubba Services

We're currently accepting new clients — weekly and monthly slots available.
"""


def send_reply(to_email: str, subject: str, body: str) -> bool:
    """Send a reply via AgentMail API."""
    headers = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": AGENTMAIL_INBOX,
        "to": to_email,
        "subject": subject,
        "text": body,
    }

    try:
        response = requests.post(
            f"{AGENTMAIL_API_URL}/send",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(f"Reply sent to {to_email}: {subject}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send reply to {to_email}: {e}")
        return False


def log_reply(email_data: Dict, response: str, success: bool):
    """Log the reply to a local file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "to": email_data.get("from"),
        "subject": email_data.get("subject"),
        "response_preview": response[:100] + "..." if len(response) > 100 else response,
        "success": success,
    }

    # Load existing log
    log_data = []
    if Path(REPLY_LOG_FILE).exists():
        with open(REPLY_LOG_FILE, "r") as f:
            log_data = json.load(f)

    log_data.append(log_entry)

    with open(REPLY_LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)


def mark_as_replied(message_id: str):
    """Mark a message as replied to avoid duplicate responses."""
    sent_record = load_sent_replies()
    sent_record.setdefault("sent", []).append(message_id)
    save_sent_replies(sent_record)


def process_inbox():
    """Main inbox processing loop — check for new emails and auto-respond."""
    logger.info("Checking inbox for new messages...")

    raw_messages = check_inbox()
    if not raw_messages:
        logger.debug("No new messages found.")
        return

    sent_record = load_sent_replies()
    new_replies_sent = 0

    for raw_msg in raw_messages:
        email_data = extract_email_details(raw_msg)
        message_id = email_data.get("id", "")
        sender = email_data.get("from", "")

        # Skip if no sender or already replied
        if not sender:
            continue
        if is_already_replied(message_id, sent_record):
            logger.debug(f"Already replied to {message_id}, skipping.")
            continue

        # Skip our own emails
        if AGENTMAIL_INBOX in sender:
            logger.debug(f"Skipping our own email: {sender}")
            continue

        logger.info(f"New message from {sender}: {email_data.get('subject', 'No Subject')}")

        # Generate and send reply
        response = generate_reply(email_data)
        subject = f"Re: {email_data.get('subject', 'Your Inquiry')}"

        success = send_reply(sender, subject, response)

        if success:
            mark_as_replied(message_id)
            new_replies_sent += 1
            logger.info(f"Auto-replied to {sender}")

        log_reply(email_data, response, success)

    if new_replies_sent > 0:
        logger.info(f"Processed {new_replies_sent} new messages.")
    else:
        logger.info("No new messages to respond to.")


def run_continuous():
    """Run the auto-responder continuously with polling."""
    logger.info("=" * 50)
    logger.info("AgentMail Auto-Responder Started")
    logger.info(f"Inbox: {AGENTMAIL_INBOX}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info("=" * 50)

    while True:
        try:
            process_inbox()
        except KeyboardInterrupt:
            logger.info("Auto-responder stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error during processing: {e}")

        time.sleep(POLL_INTERVAL)


def run_once():
    """Run the auto-responder once (for cron job integration)."""
    logger.info("Running single inbox check...")
    process_inbox()
    logger.info("Single check complete.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    elif len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        run_continuous()
    else:
        print("Usage:")
        print("  python autoresponder.py --once     # Run single check")
        print("  python autoresponder.py --daemon   # Run continuously")
        print()
        print("Default: Running single check...")
        run_once()
