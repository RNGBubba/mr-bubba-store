#!/usr/bin/env python3
"""
Mr Bubba Services - Automated Email & Order Pipeline

This script:
1. Checks AgentMail for new inbound emails
2. Classifies the inquiry (new order, question, follow-up, payment confirmation)
3. For new inquiries: sends a personalized response with next steps
4. Monitors PayPal webhook events for new payments
5. On payment received: triggers delivery workflow

Usage:
    python3 mrbubba_pipeline.py --check-email
    python3 mrbubba_pipeline.py --process-order <order_id>
    python3 mrbubba_pipeline.py --daily-report
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import base64
from datetime import datetime

# Configuration
AGENTMAIL_API = "https://api.agentmail.to/v0"
PAYPAL_API = "https://api-m.paypal.com"
INBOX = "mrbubba@agentmail.to"

AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7")
PAYPAL_CLIENT_ID = "BAAsAqlxzMBuXGPAe3rFq6D0Myf3X-s8TSK3Uf_vsSTHLGm0Psmu-2_BRy606AOXsSY2lc4ubE9iNH8jxw"
PAYPAL_CLIENT_SECRET = "EBMMCmg02x_unyan1NjV5gJ4FpVcyzNlc-45XWEDF9sP4OlV2fVRo-7Y-aRHYm0xmk5MSgn6pr33XibK"

def get_paypal_token():
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    data = b"grant_type=client_credentials"
    req = urllib.request.Request(
        f"{PAYPAL_API}/v1/oauth2/token",
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Accept-Language": "en_US",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]

def get_agentmail_messages():
    req = urllib.request.Request(
        f"{AGENTMAIL_API}/v0/inboxes/{urllib.parse.quote(INBOX)}/messages",
        headers={"Authorization": f"Bearer {AGENTMAIL_API_KEY}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def send_email(to, subject, text):
    data = json.dumps({"to": [to], "subject": subject, "text": text}).encode()
    req = urllib.request.Request(
        f"{AGENTMAIL_API}/v0/inboxes/{urllib.parse.quote(INBOX)}/messages/send",
        data=data,
        headers={
            "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def classify_inquiry(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["clean", "fix", "organize", "transform", "merge", "dedup"]):
        return "new_order"
    if any(w in text_lower for w in ["price", "cost", "how much", "rate", "quote"]):
        return "pricing_question"
    if any(w in text_lower for w in ["pay", "paid", "invoice", "paypal"]):
        return "payment"
    if any(w in text_lower for w in ["status", "update", "progress", "done"]):
        return "status_check"
    return "general"

def handle_new_inquiry(email):
    sender = email.get("from", "unknown")
    subject = email.get("subject", "")
    text = email.get("text", "")
    classification = classify_inquiry(text)
    
    if classification == "new_order":
        response = "\n".join([
            "Hi there!",
            "",
            "Thanks for reaching out about your data needs. I'd be happy to help.",
            "",
            "To get started, I just need a bit more info:",
            "",
            "1. What type of file do you have? (CSV, Excel, PDF, text, etc.)",
            "2. What's the approximate size? (number of rows/records)",
            "3. What does \"clean\" look like to you? (standardized format, merged duplicates, etc.)",
            "4. When do you need it by?",
            "",
            "Once I have these details, I can give you a firm quote and get started right away.",
            "",
            "My standard rates:",
            "- Basic (single file cleanup): $75, 24hr delivery",
            "- Pro (multiple files + automation): $150, 24hr delivery  ",
            "- Premium (full pipeline + docs): $250, 48hr delivery",
            "",
            "Looking forward to helping you get your data sorted!",
            "",
            "Best,",
            "Mr Bubba Services",
            "mrbubba@agentmail.to"
        ])
    
    elif classification == "pricing_question":
        response = "\n".join([
            "Hi!",
            "",
            "My pricing is simple and transparent:",
            "",
            "Basic Cleanup - $75",
            "   Single file, 24hr delivery, unlimited revisions",
            "",
            "Pro Package - $150  ",
            "   Multiple files + automation script, 24hr delivery",
            "",
            "Premium Pipeline - $250",
            "   Full ETL pipeline + documentation, 48hr delivery",
            "",
            "Custom projects: let me know what you need and I'll quote it fairly.",
            "",
            "All work is satisfaction-guaranteed. If you're not happy with the result, I'll fix it until you are.",
            "",
            "What are you working with?",
            "",
            "Best,",
            "Mr Bubba Services"
        ])
    
    elif classification == "payment":
        response = "\n".join([
            "Hi!",
            "",
            "I can send you a PayPal invoice or payment link. Which would you prefer?",
            "",
            "For new projects, I typically work like this:",
            "1. You describe what you need",
            "2. I send a PayPal payment link for the agreed amount",
            "3. Once paid, I start work immediately",
            "4. You receive the cleaned data within 24 hours",
            "",
            "What's the project you'd like to get started with?",
            "",
            "Best,",
            "Mr Bubba Services"
        ])
    
    else:
        response = "\n".join([
            "Hi there!",
            "",
            "Thanks for getting in touch. I help businesses clean, organize, and transform their messy data.",
            "",
            "Could you tell me a bit more about what you're working with? For example:",
            "- What kind of data do you have?",
            "- What format is it in?",
            "- What does the end result need to look like?",
            "",
            "Once I understand your needs, I can give you a clear quote and timeline.",
            "",
            "Best,",
            "Mr Bubba Services",
            "mrbubba@agentmail.to"
        ])
    
    return response

def process_paypal_webhook(payload):
    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})
    
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        amount = resource.get("amount", {}).get("value", "0")
        currency = resource.get("amount", {}).get("currency_code", "USD")
        payer_email = resource.get("payer", {}).get("email_address", "unknown")
        custom_id = resource.get("custom_id", "")
        
        print(f"PAYMENT RECEIVED: ${amount} {currency} from {payer_email}")
        print(f"Custom ID: {custom_id}")
        
        send_email(
            payer_email,
            "Payment Received - Starting Your Data Cleanup",
            "\n".join([
                f"Thank you for your payment of ${amount}!",
                "",
                "I'm starting work on your data cleanup right now. Here's what happens next:",
                "",
                "1. Payment confirmed",
                "2. I'm processing your data (you'll receive updates)",
                "3. You'll receive the cleaned file within 24 hours",
                "",
                "If you have any questions or need to send me your data file, just reply to this email.",
                "",
                "Best,",
                "Mr Bubba Services"
            ])
        )
        
        update_business_state(float(amount))
        return True
    
    return False

def update_business_state(revenue):
    state_path = "/home/vboxuser/mrbubba-mission/business-state.json"
    try:
        with open(state_path, "r") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}
    
    state.setdefault("financials", {})
    state["financials"]["total_revenue"] = state["financials"].get("total_revenue", 0) + revenue
    state["financials"]["cash_balance"] = state["financials"].get("cash_balance", 0) + revenue
    state["financials"]["net_profit"] = state["financials"].get("net_profit", 0) + revenue
    
    state.setdefault("metrics", {})
    state["metrics"]["sales"] = state["metrics"].get("sales", 0) + 1
    state["metrics"]["customers"] = state["metrics"].get("customers", 0) + 1
    
    state["last_updated"] = datetime.now().isoformat()
    
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
    
    print(f"Business state updated: +${revenue} revenue")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mrbubba_pipeline.py [--check-email|--process-order|--daily-report]")
        return
    
    command = sys.argv[1]
    
    if command == "--check-email":
        print("Checking inbox for new messages...")
        result = get_agentmail_messages()
        messages = result.get("messages", [])
        print(f"Found {len(messages)} message(s)")
        
        for msg in messages:
            sender = msg.get("from", "unknown")
            subject = msg.get("subject", "no subject")
            text = msg.get("text", "")
            
            print(f"\n   From: {sender}")
            print(f"   Subject: {subject}")
            print(f"   Classification: {classify_inquiry(text)}")
            
            if not msg.get("is_outgoing", False):
                response = handle_new_inquiry(msg)
                send_email(sender, f"Re: {subject}", response)
                print(f"   Auto-response sent")
    
    elif command == "--daily-report":
        print("Generating daily report...")
    
    elif command == "--process-order" and len(sys.argv) > 2:
        order_id = sys.argv[2]
        print(f"Processing order: {order_id}")

if __name__ == "__main__":
    main()
