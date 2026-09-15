#!/usr/bin/env python3
"""
PayPal Invoicing for Data Visualization Service
Creates and sends PayPal invoices for completed visualization projects.

Pricing Tiers:
  - Simple (1 chart): $75
  - Standard (3-5 charts): $100
  - Full Dashboard: $125
  - Complex/Multi-sheet: $150

Usage:
    python3 paypal_invoice.py --email client@example.com --name "Client Name" --tier standard
    python3 paypal_invoice.py --email client@example.com --name "Client Name" --amount 125 --description "Custom dashboard"
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

# PayPal Sandbox/Live configuration
# Note: Replace with your actual PayPal API credentials
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_API_BASE = os.environ.get("PAYPAL_API_BASE", "https://api.sandbox.paypal.com")

# Service configuration
SERVICE_NAME = "Mr Bubba Data Visualization"
INVOICE_NOTES = """
Payment for data visualization services.
Thank you for your business!

• Charts are delivered upon payment confirmation
• Standard revisions included at no extra cost
• All files provided in high-resolution PNG format
"""

PRICING_TIERS = {
    "simple": {
        "amount": "75.00",
        "description": "Simple Data Visualization (1 chart)",
        "unit_name": "Single Chart",
    },
    "standard": {
        "amount": "100.00",
        "description": "Standard Package (3-5 charts)",
        "unit_name": "Chart Package",
    },
    "dashboard": {
        "amount": "125.00",
        "description": "Full Dashboard Visualization",
        "unit_name": "Dashboard",
    },
    "complex": {
        "amount": "150.00",
        "description": "Complex/Multi-sheet Data Visualization",
        "unit_name": "Complex Project",
    },
}


def get_paypal_access_token(client_id, client_secret):
    """Get PayPal OAuth2 access token."""
    url = f"{PAYPAL_API_BASE}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    payload = "grant_type=client_credentials".encode('utf-8')

    import base64
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers["Authorization"] = f"Basic {credentials}"

    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('access_token')
    except Exception as e:
        print(f"❌ Failed to get PayPal access token: {e}")
        return None


def create_invoice(access_token, recipient_email, recipient_name, amount, description,
                   currency="USD"):
    """Create a PayPal invoice."""
    url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    payload = {
        "detail": {
            "invoice_number": f"DV-{int(datetime.now().timestamp()) % 100000:05d}",
            "reference": "data-viz-project",
            "invoice_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            "currency_code": currency,
            "note": INVOICE_NOTES,
            "term": "Payment due upon receipt",
        },
        "invoicer": {
            "name": {
                "given_name": "Mr Bubba",
                "surname": "Data Services",
            },
            "email_address": "mrbubba@agentmail.to",
        },
        "primary_recipients": [
            {
                "billing_info": {
                    "name": {
                        "given_name": recipient_name.split()[0] if recipient_name else "Client",
                        "surname": " ".join(recipient_name.split()[1:]) if recipient_name else "",
                    },
                    "email_address": recipient_email,
                },
            }
        ],
        "items": [
            {
                "name": description[:100],
                "description": description,
                "quantity": "1",
                "unit_amount": {
                    "currency_code": currency,
                    "value": f"{float(amount):.2f}",
                },
            }
        ],
        "configuration": {
            "allow_tip": False,
            "tax_calculated_after_discount": True,
            "tax_inclusive": False,
        },
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"✅ Invoice created: {result.get('id')}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Failed to create invoice: {e.code} - {error_body}")
        return None
    except Exception as e:
        print(f"❌ Failed to create invoice: {e}")
        return None


def send_invoice(access_token, invoice_id):
    """Send a PayPal invoice to the recipient."""
    url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices/{invoice_id}/send"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = json.dumps({}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"✅ Invoice {invoice_id} sent successfully!")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Failed to send invoice: {e.code} - {error_body}")
        return False
    except Exception as e:
        print(f"❌ Failed to send invoice: {e}")
        return False


def generate_invoice_url(invoice_id):
    """Generate PayPal invoice URL for manual sharing."""
    base = "https://www.paypal.com/invoice" if "api.paypal.com" in PAYPAL_API_BASE \
        else "https://www.sandbox.paypal.com/invoice"
    return f"{base}/p/{invoice_id}"


def create_and_send_invoice(recipient_email, recipient_name, tier=None, amount=None,
                            description=None):
    """Full flow: create and send a PayPal invoice."""
    # Validate credentials
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("⚠️  PayPal credentials not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET env vars.")
        print("   Generating invoice details for manual creation...\n")
        # Fall back to printing invoice details
        if tier and tier in PRICING_TIERS:
            t = PRICING_TIERS[tier]
            amt = t["amount"]
            desc = t["description"]
        else:
            amt = f"{amount:.2f}" if amount else "0.00"
            desc = description or "Data Visualization Services"

        invoice_details = {
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "amount": amt,
            "description": desc,
            "invoice_number": f"DV-{int(datetime.now().timestamp()) % 100000:05d}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        print("📋 INVOICE DETAILS (Manual Creation)")
        print("=" * 50)
        for key, val in invoice_details.items():
            print(f"  {key}: {val}")
        print("=" * 50)
        print("\n⚠️  Invoice NOT sent automatically (no API credentials)")
        return invoice_details

    # Get access token
    print("🔐 Authenticating with PayPal...")
    access_token = get_paypal_access_token(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    if not access_token:
        return None

    # Determine amount and description
    if tier and tier in PRICING_TIERS:
        t = PRICING_TIERS[tier]
        amount = t["amount"]
        description = t["description"]
    elif not amount:
        print("❌ Must specify either --tier or --amount")
        return None

    description = description or "Data Visualization Services"

    print(f"📝 Creating invoice for {recipient_name} <{recipient_email}>")
    print(f"   Amount: ${amount} | {description}")

    # Create invoice
    invoice = create_invoice(access_token, recipient_email, recipient_name, amount, description)
    if not invoice:
        return None

    invoice_id = invoice.get('id')

    # Send invoice
    print(f"📤 Sending invoice {invoice_id}...")
    sent = send_invoice(access_token, invoice_id)

    if sent:
        print("\n" + "=" * 50)
        print("📧 INVOICE SENT SUCCESSFULLY")
        print("=" * 50)
        print(f"  Invoice ID:   {invoice_id}")
        print(f"  Recipient:    {recipient_name} <{recipient_email}>")
        print(f"  Amount:       ${amount}")
        print(f"  Description:  {description}")
        print(f"  Invoice URL:  {generate_invoice_url(invoice_id)}")
        print("=" * 50)

    return invoice


def main():
    parser = argparse.ArgumentParser(description='PayPal Invoicing for Data Viz Service')
    parser.add_argument('--email', required=True, help='Recipient email address')
    parser.add_argument('--name', required=True, help='Recipient name')
    parser.add_argument('--tier', choices=['simple', 'standard', 'dashboard', 'complex'],
                        help='Pricing tier')
    parser.add_argument('--amount', type=float, help='Custom amount (overrides tier)')
    parser.add_argument('--description', help='Custom invoice description')
    args = parser.parse_args()

    result = create_and_send_invoice(
        recipient_email=args.email,
        recipient_name=args.name,
        tier=args.tier,
        amount=args.amount,
        description=args.description,
    )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
