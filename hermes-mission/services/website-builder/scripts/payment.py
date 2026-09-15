#!/usr/bin/env python3
"""
Mr Bubba Services - Payment Flow Handler
Handles PayPal invoicing for the $299 website builder service.
Provides payment link generation, webhook verification, and invoice templates.
"""

import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

# Configuration
PAYPAL_CLIENT_ID = ""
PAYPAL_CLIENT_SECRET = ""
PAYPAL_WEBHOOK_ID = ""
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"  # Use live URL for production
SERVICE_PRICE = 299.00
SERVICE_NAME = "Professional 5-Page Website Builder Service"
SERVICE_DESCRIPTION = "Custom professional website with 5 pages, responsive design, contact form, portfolio, and deployment to GitHub Pages"

# AgentMail Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"


def generate_paypal_invoice(
    client_name: str,
    client_email: str,
    business_name: str,
    invoice_id: str = None
) -> dict:
    """
    Generate a PayPal invoice for the website builder service.
    In production, this would call the PayPal Invoicing API.
    
    Returns a dict with invoice details and payment link.
    """
    if not invoice_id:
        invoice_id = f"HDW-{int(time.time())}"
    
    invoice = {
        "invoice_id": invoice_id,
        "status": "draft",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "amount": SERVICE_PRICE,
        "currency": "USD",
        "service_name": SERVICE_NAME,
        "service_description": SERVICE_DESCRIPTION,
        "client": {
            "name": client_name,
            "email": client_email,
        },
        "business_name": business_name,
        "payment_link": f"https://www.paypal.com/invoice/p/#{invoice_id}",
        "due_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() + 7 * 86400)),
    }
    
    return invoice


def generate_paypal_buy_now_link(
    client_name: str,
    client_email: str,
    business_name: str
) -> str:
    """
    Generate a PayPal Buy Now / Pay Now link for $299.
    Uses PayPal's standard payment flow.
    """
    # For PayPal hosted buttons or direct payment links
    params = {
        "cmd": "_xclick",
        "business": AGENTMAIL_INBOX,  # or PayPal merchant email
        "item_name": SERVICE_NAME,
        "item_number": f"WEB-{int(time.time())}",
        "amount": f"{SERVICE_PRICE:.2f}",
        "currency_code": "USD",
        "return": "https://mrbubba-services.com/thank-you",
        "cancel_return": "https://mrbubba-services.com/cancel",
        "notify_url": "https://mrbubba-services.com/webhook/paypal",
        "custom": json.dumps({
            "client_name": client_name,
            "client_email": client_email,
            "business_name": business_name,
            "service": "website-builder"
        }),
        "no_shipping": "1",
        "no_note": "1",
    }
    
    param_str = urllib.parse.urlencode(params)
    return f"https://www.paypal.com/cgi-bin/webscr?{param_str}"


def verify_paypal_webhook(headers: dict, body: str, webhook_id: str = "") -> bool:
    """
    Verify a PayPal webhook signature.
    Required for production use to ensure webhooks are authentic.
    """
    # PayPal webhook verification requires API call to /v1/notifications/verify-webhook-signature
    # This is a stub for the verification logic
    transmission_id = headers.get("PAYPAL-TRANSMISSION-ID", "")
    cert_url = headers.get("PAYPAL-CERT-URL", "")
    auth_algo = headers.get("PAYPAL-AUTH-ALGO", "")
    transmission_sig = headers.get("PAYPAL-TRANSMISSION-SIG", "")
    transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME", "")
    
    if not all([transmission_id, cert_url, auth_algo, transmission_sig, transmission_time]):
        return False
    
    # In production, verify against PayPal API
    # POST /v1/notifications/verify-webhook-signature
    return True  # Simplified for demo


def handle_payment_webhook(payload: dict) -> dict:
    """
    Handle a PayPal payment webhook event.
    Returns a result dict with the action to take.
    """
    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})
    
    if event_type == "PAYMENT.SALE.COMPLETED":
        sale = resource
        custom_data = json.loads(sale.get("custom", "{}"))
        amount = sale.get("amount", {}).get("total", "0")
        
        return {
            "action": "deploy_site",
            "payment_completed": True,
            "amount": amount,
            "client_name": custom_data.get("client_name", ""),
            "client_email": custom_data.get("client_email", ""),
            "business_name": custom_data.get("business_name", ""),
            "transaction_id": sale.get("id", ""),
        }
    
    elif event_type == "INVOICING.INVOICE.PAID":
        invoice = resource
        return {
            "action": "deploy_site",
            "payment_completed": True,
            "invoice_id": invoice.get("id", ""),
            "client_email": invoice.get("recipient_email", ""),
        }
    
    elif event_type == "PAYMENT.SALE.REFUNDED":
        return {
            "action": "handle_refund",
            "transaction_id": resource.get("id", ""),
        }
    
    return {"action": "unknown", "event_type": event_type}


def create_discord_notification(payload: dict) -> dict:
    """Create a Discord webhook notification for payment events."""
    event_type = payload.get("event_type", "unknown")
    resource = payload.get("resource", {})
    
    if "COMPLETED" in event_type or "PAID" in event_type:
        color = 0x00FF00  # Green
        title = "💰 Payment Received!"
        amount = resource.get("amount", {}).get("total", "299.00") if isinstance(resource.get("amount"), dict) else "299.00"
        description = f"**${amount}** received for Website Builder Service"
    elif "REFUND" in event_type:
        color = 0xFF0000  # Red
        title = "🔄 Refund Processed"
        description = "A refund has been issued"
    else:
        color = 0xFFA500  # Orange
        title = "📋 Payment Update"
        description = f"Event: {event_type}"
    
    return {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "Event", "value": event_type, "inline": True},
                {"name": "Time", "value": time.strftime("%Y-%m-%d %H:%M UTC"), "inline": True},
            ],
            "footer": {"text": "Mr Bubba Services - Website Builder"}
        }]
    }


def generate_invoice_email(invoice: dict) -> str:
    """Generate the invoice email body to send to a client."""
    payment_link = invoice.get("payment_link", generate_paypal_buy_now_link(
        invoice["client"]["name"],
        invoice["client"]["email"],
        invoice["business_name"]
    ))
    
    return f"""Subject: Your Website Invoice from Mr Bubba Services - ${{invoice['invoice_id']}}

Hi {invoice['client']['name']},

Great news! Your website is ready to go live. Here are the details:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧾 INVOICE #{invoice['invoice_id']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Service: {invoice['service_name']}
Business: {invoice['business_name']}
Amount: ${invoice['amount']:.2f} USD

{invoice['service_description']}

✅ 5-Page Professional Website
✅ Mobile-Responsive Design
✅ Contact Form with Validation
✅ Portfolio Gallery
✅ Google Maps Integration
✅ Testimonials Section
✅ SEO Optimization
✅ Deployed to GitHub Pages
✅ Free Revisions (7 days)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 PAYMENT OPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Option 1: Pay Online (PayPal)
{payment_link}

Option 2: Send PayPal payment directly to: {AGENTMAIL_INBOX}

Option 3: Invoice me — reply with "send invoice" and we'll send a formal PayPal invoice to your email.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once payment is received, your website will be live within 24 hours.

Questions? Just reply to this email.

Best regards,
Mr Bubba Services Team
mrbubba@agentmail.to
"""
