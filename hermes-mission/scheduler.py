#!/usr/bin/env python3
"""
"""Mr Bubba Autonomous Scheduler
============================

Runs all money-making tasks on a schedule.
Run via: python3 scheduler.py
Or via cron: 0 * * * * /usr/bin/python3 /home/vboxuser/mrbubba-mission/scheduler.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import subprocess
from datetime import datetime, timedelta

# Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
BASE_DIR = "/home/vboxuser/mrbubba-mission"
BUSINESS_NAME = "Mr Bubba Services"
BUSINESS_EMAIL = "mrbubba@agentmail.to"

# State file to track what we've done
STATE_FILE = f"{BASE_DIR}/scheduler-state.json"

def load_state():
    """Load scheduler state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "last_run": None,
        "emails_sent": [],
        "follow_ups_sent": [],
        "leads_found": [],
        "payments_received": [],
        "websites_delivered": []
    }

def save_state(state):
    """Save scheduler state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_inbox():
    """Check AgentMail for new messages and auto-respond."""
    print("\n📬 Checking inbox...")
    
    url = f"https://api.agentmail.to/v0/inboxes/{urllib.parse.quote(AGENTMAIL_INBOX)}/messages"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            messages = data.get("messages", [])
            
            # Filter unread received messages
            new_messages = [m for m in messages if "received" in m.get("labels", []) and "unread" in m.get("labels", [])]
            
            print(f"   Found {len(new_messages)} new messages")
            
            for msg in new_messages:
                handle_message(msg)
                
    except Exception as e:
        print(f"   Error checking inbox: {e}")

def handle_message(msg):
    """Handle a new inbound message."""
    sender = msg.get("from", "unknown")
    subject = msg.get("subject", "")
    text = msg.get("text", "").lower()
    
    print(f"   New message from: {sender}")
    print(f"   Subject: {subject}")
    
    # Auto-respond based on content
    if "yes" in text or "interested" in text or "quote" in text or "price" in text:
        send_reply(sender, "re: " + subject, """Hi there!

Thanks for getting back to me. I'd love to help you with your project.

Could you tell me a bit more about what you need?
- What's your business name?
- What's the main goal of the website/service?
- Do you have any examples of what you like?

Once I have these details, I can send you a firm quote and get started right away.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to""")
        
    elif "website" in text or "site" in text:
        send_reply(sender, "re: " + subject, """Hi there!

Thanks for your interest in getting a professional website.

Here's what I offer:
- Custom 5-page website: $299
- Mobile-friendly design
- Contact form and click-to-call
- Photo gallery
- Customer testimonials
- Google Maps integration
- SEO optimized
- Free hosting setup
- Delivery: 3-5 business days
- Unlimited revisions

Want me to send you a free draft? Just let me know:
1. Your business name
2. What your business does
3. Any examples of websites you like

I'll have a draft ready within 48 hours. If you like it, we proceed with payment via PayPal.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to""")
        
    elif "clean" in text or "data" in text or "spreadsheet" in text or "csv" in text:
        send_reply(sender, "re: " + subject, """Hi there!

I'd be happy to help you clean up your data.

My data cleanup service:
- $75 for a single file (CSV, Excel, or text)
- 24-hour delivery
- Remove duplicates
- Standardize formats (dates, phone numbers, addresses)
- Trim whitespace
- Add calculations and categories
- Data quality report included
- Unlimited revisions

Just reply with the file attached and I'll take a look. No obligation - if my quote doesn't work for you, no hard feelings.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to""")
        
    else:
        send_reply(sender, "re: " + subject, """Hi there!

Thanks for getting in touch. I help businesses with:

🌐 Professional websites ($299)
📊 Data cleanup ($75)
🤖 Business automation ($150)

Which one are you interested in? Let me know and I'll send more details.

Best regards,
Mr Bubba Services
mrbubba@agentmail.to""")
    
    # Mark as read (AgentMail doesn't have explicit mark-read, but we track state)

def send_reply(to, subject, text):
    """Send a reply via AgentMail."""
    data = json.dumps({"to": [to], "subject": subject, "text": text}).encode()
    url = f"https://api.agentmail.to/v0/inboxes/{urllib.parse.quote(AGENTMAIL_INBOX)}/messages/send"
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type": "application/json"
    }, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            print(f"   ✅ Auto-replied to {to}")
            return result.get("message_id", "")
    except Exception as e:
        print(f"   ❌ Failed to reply: {e}")
        return None

def send_follow_ups(state):
    """Send follow-up emails to leads who haven't responded."""
    print("\n📧 Checking for follow-ups...")
    
    now = datetime.now()
    follow_up_days = 3
    
    # Load leads from website scanner
    leads_file = f"{BASE_DIR}/website-scanner/leads.json"
    if not os.path.exists(leads_file):
        print("   No leads file found")
        return
    
    with open(leads_file, "r") as f:
        leads = json.load(f)
    
    for lead in leads:
        # Skip if already sent follow-up
        lead_id = lead.get("id", lead.get("name", ""))
        if lead_id in state.get("follow_ups_sent", []):
            continue
        
        # Check if original email was sent 3+ days ago
        added_at = lead.get("added_at", "")
        if not added_at:
            continue
        
        try:
            sent_date = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
            if now - sent_date < timedelta(days=follow_up_days):
                continue
        except:
            continue
        
        # Generate follow-up email
        email = lead.get("email", "")
        if not email:
            continue
        
        name = lead.get("name", "there").split()[0]
        subject = f"Quick follow-up — website for {lead.get('name', 'your business')}"
        
        text = f"""Hi {name},

I reached out a few days ago about building a professional website for {lead.get('name', 'your business')}.

Just wanted to bump this to the top of your inbox. I know you're busy.

Quick reminder:
- Custom 5-page website: $299
- Mobile-friendly, contact form, photo gallery
- 3-5 day delivery, unlimited revisions

Reply "yes" and I'll send a free draft. No obligation.

Best,
Mr Bubba Services
mrbubba@agentmail.to"""
        
        result = send_reply(email, subject, text)
        if result:
            state["follow_ups_sent"].append(lead_id)
            save_state(state)

def run_website_scanner(state):
    """Run the website scanner to find new leads."""
    print("\n🔍 Running website scanner...")
    
    scanner_script = f"{BASE_DIR}/website-scanner/scanner.py"
    if not os.path.exists(scanner_script):
        print("   Scanner script not found")
        return
    
    try:
        result = subprocess.run(
            ["python3", scanner_script, "--mode", "scan"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("   Scanner completed successfully")
            # Check if new leads were found
            leads_file = f"{BASE_DIR}/website-scanner/leads.json"
            if os.path.exists(leads_file):
                with open(leads_file, "r") as f:
                    leads = json.load(f)
                print(f"   Total leads: {len(leads)}")
        else:
            print(f"   Scanner error: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print("   Scanner timed out")
    except Exception as e:
        print(f"   Error running scanner: {e}")

def check_payments():
    """Check PayPal for new payments via webhook/Discord."""
    print("\n💰 Checking for payments...")
    # PayPal webhook sends to Discord, so we check the state file
    # In production, you'd query PayPal API directly
    
    state = load_state()
    payments = state.get("payments_received", [])
    
    if payments:
        total = sum(p.get("amount", 0) for p in payments)
        print(f"   Total received: ${total:.2f} ({len(payments)} payments)")
    else:
        print("   No payments yet")

def send_report(state):
    """Send daily report to Discord via webhook."""
    print("\n📊 Generating report...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""
📊 **Mr Bubba Mission Report** ({now})

**Inbox:** Checked
**Payments:** {len(state.get('payments_received', []))} received
**Leads:** {len(state.get('leads_found', []))} found
**Emails Sent:** {len(state.get('emails_sent', []))}
**Follow-ups Sent:** {len(state.get('follow_ups_sent', []))}

**Cash Balance:** ${sum(p.get('amount', 0) for p in state.get('payments_received', [])):.2f}
"""
    
    print(report)
    
    # Send to Discord webhook
    webhook_url = "https://ptb.discord.com/api/webhooks/1549099376381657230/ZvgrXZI46Cev81l1hN4_7EnIbsL0Sk9pS7EM4Th5145D_Y6xGs62nohDjj28OhcwFI2j"
    
    data = json.dumps({"content": report}).encode()
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("   ✅ Report sent to Discord")
    except Exception as e:
        print(f"   ❌ Failed to send report: {e}")

def main():
    """Main scheduler loop."""
    print("=" * 50)
    print("MR BUBBA AUTONOMOUS SCHEDULER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    state = load_state()
    state["last_run"] = datetime.now().isoformat()
    
    # Run all tasks
    check_inbox()
    send_follow_ups(state)
    check_payments()
    
    # Run scanner once per day (at 9 AM)
    if datetime.now().hour == 9:
        run_website_scanner(state)
    
    # Send report once per day (at 8 PM)
    if datetime.now().hour == 20:
        send_report(state)
    
    save_state(state)
    
    print("\n✅ Scheduler cycle complete")

if __name__ == "__main__":
    main()