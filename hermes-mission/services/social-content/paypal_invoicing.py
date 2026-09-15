#!/usr/bin/env python3
"""
PayPal Invoicing for Social Media Content Service
Mr Bubba Services

Handles PayPal invoice generation, sending, and webhook processing
for social content service billing ($50-150/week).
"""

import json
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_BASE_URL = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID", "")
MR_BUBBA_BUSINESS_EMAIL = os.environ.get("MR_BUBBA_BUSINESS_EMAIL", "mrbubba@agentmail.to")

# Discord webhook for notifications
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Pricing configuration
PRICING = {
    "weekly": {
        "amount": "50.00",
        "description": "Social Media Content Package — Weekly",
        "deliverables": "7 social media posts with captions, hashtags, and image descriptions",
        "delivery_hours": 24,
    },
    "monthly": {
        "amount": "150.00",
        "description": "Social Media Content Package — Monthly",
        "deliverables": "30 social media posts with captions, hashtags, and image descriptions",
        "delivery_hours": 24,
    },
}

INVOICE_LOG_FILE = "invoice_log.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("paypal_invoicing.log"),
    ],
)
logger = logging.getLogger(__name__)


def get_paypal_access_token() -> Optional[str]:
    """Get PayPal OAuth2 access token."""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        logger.error("PayPal credentials not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.")
        return None

    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    payload = {"grant_type": "client_credentials"}

    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            headers=headers,
            data=payload,
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get PayPal access token: {e}")
        return None


def _normalize_period(period: str) -> str:
    """Normalize period input to 'weekly' or 'monthly'."""
    p = period.lower().strip()
    if p in ("week", "w", "weekly"):
        return "weekly"
    elif p in ("month", "m", "monthly"):
        return "monthly"
    return p


def create_invoice(
    client_email: str,
    period: str,
    brand_name: str,
    access_token: str,
) -> Optional[Dict]:
    """Create a PayPal invoice."""
    period_key = _normalize_period(period)
    if period_key not in PRICING:
        logger.error(f"Invalid period: {period}")
        return None

    pricing = PRICING[period_key]
    due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    payload = {
        "detail": {
            "invoice_number": f"SC-{brand_name[:3].upper()}-{int(datetime.now().timestamp())}",
            "reference": f"social-content-{period_key}",
            "currency_code": "USD",
            "note": f"Social media content for {brand_name}. Delivery within {pricing['delivery_hours']} hours of payment.",
            "terms_and_conditions": "Payment due within 7 days. Content delivered via email after payment confirmation.",
            "due_date": due_date,
        },
        "invoicer": {
            "email_address": MR_BUBBA_BUSINESS_EMAIL,
            "business_name": {"business_name": "Mr Bubba Services"},
        },
        "primary_recipients": [
            {"billing_info": {"email_address": client_email, "business_name": brand_name}}
        ],
        "items": [
            {
                "name": pricing["description"],
                "description": pricing["deliverables"],
                "quantity": "1",
                "unit_amount": {"currency_code": "USD", "value": pricing["amount"]},
            }
        ],
        "configuration": {
            "allow_tip": False,
            "tax_before_discount": False,
            "tax_calculated_after_discount": False,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/invoicing/invoices",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create PayPal invoice: {e}")
        return None


def send_invoice(invoice_id: str, access_token: str) -> bool:
    """Send a created PayPal invoice to the client."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}/send",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(f"Invoice {invoice_id} sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send invoice {invoice_id}: {e}")
        return False


def generate_local_invoice(client_email: str, period: str, brand_name: str) -> Dict:
    """Generate invoice details locally (when PayPal API is not configured)."""
    period_key = _normalize_period(period)
    if period_key not in PRICING:
        raise ValueError(f"Invalid period: {period}")

    pricing = PRICING[period_key]
    invoice_number = f"SC-{brand_name[:3].upper()}-{int(datetime.now().timestamp())}"

    invoice = {
        "invoice_number": invoice_number,
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "client_email": client_email,
        "brand": brand_name,
        "period": period_key,
        "amount_usd": float(pricing["amount"]),
        "description": pricing["description"],
        "deliverables": pricing["deliverables"],
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "paypal_url": f"https://www.paypal.com/invoice/p/#{invoice_number}",
        "manual_instructions": (
            f"To manually create this invoice:\n"
            f"1. Go to https://www.paypal.com/invoice/create\n"
            f"2. Send to: {client_email}\n"
            f"3. Item: {pricing['description']}\n"
            f"4. Amount: ${pricing['amount']} USD\n"
            f"5. Note: {pricing['deliverables']}\n"
            f"6. Due date: {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}"
        ),
    }
    return invoice


def log_invoice(invoice: Dict):
    """Log invoice to local file."""
    log_data = []
    if Path(INVOICE_LOG_FILE).exists():
        with open(INVOICE_LOG_FILE, "r") as f:
            log_data = json.load(f)

    log_data.append({
        "timestamp": datetime.now().isoformat(),
        "invoice_number": invoice.get("invoice_number"),
        "client_email": invoice.get("client_email"),
        "brand": invoice.get("brand"),
        "period": invoice.get("period"),
        "amount": invoice.get("amount_usd"),
        "status": invoice.get("status", "draft"),
    })

    with open(INVOICE_LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)


def send_discord_notification(message: str):
    """Send notification to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        logger.debug("Discord webhook not configured, skipping notification.")
        return

    payload = {"content": message, "username": "Mr Bubba Billing Bot"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Discord notification sent.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")


def process_webhook(payload: Dict, headers: Dict) -> Dict:
    """Process an incoming PayPal webhook event."""
    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})

    logger.info(f"Processing webhook: {event_type}")

    if event_type == "INVOICING.INVOICE.PAID":
        invoice_id = resource.get("invoice_number", "unknown")
        amount = resource.get("amount", {})
        paid_amount = amount.get("value", "unknown")
        currency = amount.get("currency_code", "USD")
        recipient = resource.get("primary_recipients", [{}])[0]
        client_email = recipient.get("billing_info", {}).get("email_address", "unknown")

        message = (
            f"💰 **Payment Received!**\n"
            f"Invoice: {invoice_id}\n"
            f"Amount: {paid_amount} {currency}\n"
            f"Client: {client_email}\n"
            f"Action: Begin content generation"
        )
        logger.info(f"Payment received: {invoice_id} — {paid_amount} {currency}")
        send_discord_notification(message)
        return {"status": "processed", "action": "payment_received", "invoice_id": invoice_id}

    elif event_type == "INVOICING.INVOICE.CANCELLED":
        invoice_id = resource.get("invoice_number", "unknown")
        message = f"❌ **Invoice Cancelled**: {invoice_id}"
        logger.info(f"Invoice cancelled: {invoice_id}")
        send_discord_notification(message)
        return {"status": "processed", "action": "invoice_cancelled", "invoice_id": invoice_id}

    elif event_type == "INVOICING.INVOICE.REFUNDED":
        invoice_id = resource.get("invoice_number", "unknown")
        message = f"↩️ **Refund Processed**: {invoice_id}"
        logger.info(f"Refund processed: {invoice_id}")
        send_discord_notification(message)
        return {"status": "processed", "action": "refund_processed", "invoice_id": invoice_id}

    else:
        logger.info(f"Unhandled webhook event type: {event_type}")
        return {"status": "ignored", "event_type": event_type}


def verify_webhook_signature(payload: bytes, headers: Dict) -> bool:
    """Basic webhook signature structure check."""
    required_headers = [
        "PAYPAL-TRANSMISSION-ID",
        "PAYPAL-CERT-URL",
        "PAYPAL-AUTH-ALGO",
        "PAYPAL-TRANSMISSION-SIG",
        "PAYPAL-TRANSMISSION-TIME",
    ]
    for h in required_headers:
        if not headers.get(h):
            logger.warning(f"Missing webhook header: {h}")
            return False
    logger.info("Webhook signature structure valid")
    return True


def generate_invoice_link(client_email: str, period: str, brand_name: str) -> str:
    """Generate a direct PayPal payment link."""
    period_key = _normalize_period(period)
    pricing = PRICING.get(period_key, PRICING["weekly"])
    amount = pricing["amount"]
    paypal_link = f"https://www.paypal.com/paypalme/mrbubba/{amount}"
    logger.info(f"Generated PayPal link: {paypal_link}")
    return paypal_link


def create_paypal_invoice_flow(client_email: str, period: str, brand_name: str) -> Dict:
    """Full invoice creation flow — tries PayPal API first, falls back to local generation."""
    period_key = _normalize_period(period)
    logger.info(f"Creating invoice for {client_email} — {period_key} package for {brand_name}")

    # Try PayPal API first
    token = get_paypal_access_token()
    if token:
        invoice = create_invoice(client_email, period_key, brand_name, token)
        if invoice:
            invoice_id = invoice.get("id", "")
            if invoice_id:
                send_invoice(invoice_id, token)

            local_data = {
                "invoice_number": invoice_id,
                "status": "sent",
                "created_at": datetime.now().isoformat(),
                "client_email": client_email,
                "brand": brand_name,
                "period": period_key,
                "amount_usd": float(PRICING[period_key]["amount"]),
                "description": PRICING[period_key]["description"],
                "deliverables": PRICING[period_key]["deliverables"],
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "paypal_url": f"https://www.paypal.com/invoice/p/{invoice_id}",
            }

            log_invoice(local_data)
            send_discord_notification(
                f"📧 **Invoice Created**\n"
                f"To: {client_email}\n"
                f"Brand: {brand_name}\n"
                f"Period: {period_key.capitalize()}\n"
                f"Amount: ${PRICING[period_key]['amount']}"
            )
            return local_data

    # Fall back to local generation
    logger.info("PayPal API unavailable — generating local invoice draft.")
    local_invoice = generate_local_invoice(client_email, period, brand_name)
    log_invoice(local_invoice)
    return local_invoice


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("PayPal Invoicing — Social Media Content Service")
        print()
        print("Commands:")
        print("  invoice <client_email> <week|month> <brand_name>")
        print("  webhook <payload_json_file>")
        print("  link <client_email> <week|month> <brand_name>")
        print("  status")
        print()
        print("Examples:")
        print("  python paypal_invoicing.py invoice client@email.com week MyBrand")
        print("  python paypal_invoicing.py link client@email.com monthly AcmeCorp")
        sys.exit(1)

    command = sys.argv[1]

    if command == "invoice":
        if len(sys.argv) < 5:
            print("Error: Usage: python paypal_invoicing.py invoice <client_email> <week|month> <brand_name>")
            sys.exit(1)
        result = create_paypal_invoice_flow(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, indent=2))

    elif command == "webhook":
        if len(sys.argv) < 3:
            print("Error: Please provide a webhook payload JSON file.")
            sys.exit(1)
        with open(sys.argv[2], "r") as f:
            webhook_data = json.load(f)
        result = process_webhook(webhook_data, {})
        print(json.dumps(result, indent=2))

    elif command == "link":
        if len(sys.argv) < 5:
            print("Error: Usage: python paypal_invoicing.py link <client_email> <week|month> <brand_name>")
            sys.exit(1)
        link = generate_invoice_link(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"PayPal Link: {link}")

    elif command == "status":
        print("PayPal Invoicing Status")
        print("-" * 30)
        print(f"API Configured: {'✅' if PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET else '❌'}")
        print(f"Discord Webhook: {'✅' if DISCORD_WEBHOOK_URL else '❌'}")
        print(f"Webhook ID: {'✅' if PAYPAL_WEBHOOK_ID else '❌'}")
        if Path(INVOICE_LOG_FILE).exists():
            with open(INVOICE_LOG_FILE, "r") as f:
                invoices = json.load(f)
            print(f"\nTotal invoices logged: {len(invoices)}")
            for inv in invoices[-5:]:
                print(f"  {inv.get('invoice_number')} — {inv.get('status')} — ${inv.get('amount')}")
        else:
            print("\nNo invoices logged yet.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
