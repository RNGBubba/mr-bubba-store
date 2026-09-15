#!/usr/bin/env python3
"""
PayPal Invoicing for API Integration Services
Mr Bubba Services

Creates and sends PayPal invoices for API integration scripts.
Pricing tiers: $100 (simple), $200 (medium), $300 (complex).
Sends Discord notification when invoice is paid via webhook.
"""

import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

# === CONFIGURATION ===
PAYPAL_CLIENT_ID = "YOUR_PAYPAL_CLIENT_ID"
PAYPAL_CLIENT_SECRET = "YOUR_PAYPAL_CLIENT_SECRET"
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"  # Use https://api-m.paypal.com for production

# Discord webhook for payment notifications
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

# Business details
BUSINESS_EMAIL = "mrbubba@agentmail.to"
BUSINESS_NAME = "Mr Bubba Services"
CURRENCY = "USD"

# === PRICING TIERS ===
PRICING = {
    "simple": {
        "amount": "100.00",
        "description": "Simple API Integration (2 services, standard endpoints)",
        "deliverables": [
            "Python integration script",
            "Error handling and logging",
            "Setup documentation",
        ]
    },
    "medium": {
        "amount": "200.00",
        "description": "Medium API Integration (3-5 services, custom logic)",
        "deliverables": [
            "Python integration script",
            "Custom field mapping",
            "Error handling and logging",
            "Webhook listener",
            "Setup and deployment documentation",
        ]
    },
    "complex": {
        "amount": "300.00",
        "description": "Complex API Integration (5+ services, custom workflows)",
        "deliverables": [
            "Python integration script (multi-service)",
            "Custom field mapping and data transformations",
            "Error handling, logging and retry logic",
            "Webhook listener with signature verification",
            "Setup and deployment documentation",
            "30 days post-delivery support",
        ]
    }
}


@dataclass
class InvoiceItem:
    name: str
    description: str
    quantity: int
    unit_price: str
    currency: str = "USD"


@dataclass
class InvoiceRecipient:
    email: str
    name: str
    business_name: Optional[str] = None


def get_paypal_access_token() -> str:
    """Obtain PayPal OAuth2 access token."""
    auth = (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}

    resp = requests.post(
        PAYPAL_API_BASE + "/v1/oauth2/token",
        auth=auth,
        headers=headers,
        data=data,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_invoice(
    recipient: InvoiceRecipient,
    item: InvoiceItem,
    note: str = "",
    due_days: int = 14,
    tier: str = "simple"
) -> dict:
    """Create a PayPal invoice."""
    token = get_paypal_access_token()
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")
    deliverables = PRICING[tier]["deliverables"]
    deliverables_text = "\n".join(["  - " + d for d in deliverables])
    full_description = item.description + "\n\nDeliverables:\n" + deliverables_text

    invoice_number = "MRBUBBA-" + datetime.now().strftime("%Y%m%d%H%M%S")
    today_str = datetime.now().strftime("%Y-%m-%d")
    note_text = note if note else ("API Integration Service - " + tier.capitalize() + " Tier")

    payload = {
        "detail": {
            "invoice_number": invoice_number,
            "reference": "mrbubba-api-integration-" + tier,
            "invoice_date": today_str,
            "currency_code": CURRENCY,
            "note": note_text,
            "term": "Net " + str(due_days),
            "payment_term": {
                "term_type": "NET",
                "due_date": due_date
            }
        },
        "invoicer": {
            "name": {
                "given_name": "Mr Bubba",
                "surname": "Data Services"
            },
            "email_address": BUSINESS_EMAIL
        },
        "primary_recipients": [{
            "billing_info": {
                "email_address": recipient.email,
                "name": {
                    "given_name": recipient.name,
                }
            }
        }],
        "items": [{
            "name": item.name,
            "description": full_description,
            "quantity": str(item.quantity),
            "unit_amount": {
                "currency_code": item.currency,
                "value": item.unit_price
            }
        }],
        "configuration": {
            "allow_tip": False,
            "tax_after_discount": False,
            "tax_calculated_after_discount": False
        }
    }

    if recipient.business_name:
        payload["primary_recipients"][0]["additional_info"] = [{
            "value": recipient.business_name
        }]

    resp = requests.post(
        PAYPAL_API_BASE + "/v2/invoicing/invoices",
        headers=headers,
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def send_invoice(invoice_id: str) -> dict:
    """Send an invoice to the recipient via PayPal."""
    token = get_paypal_access_token()
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    resp = requests.post(
        PAYPAL_API_BASE + "/v2/invoicing/invoices/" + invoice_id + "/send",
        headers=headers,
        json={},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def send_discord_notification(invoice_data: dict, recipient: InvoiceRecipient, tier: str) -> bool:
    """Send payment notification to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL":
        print("  (Discord webhook not configured - skipping notification)")
        return False

    amount = PRICING[tier]["amount"]
    invoice_id = invoice_data.get("id", "N/A")
    ts = datetime.utcnow().isoformat() + "Z"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    embed = {
        "embeds": [{
            "title": "New Invoice Sent - Mr Bubba Services",
            "color": 3066993,  # Green
            "fields": [
                {"name": "Client", "value": recipient.name, "inline": True},
                {"name": "Email", "value": recipient.email, "inline": True},
                {"name": "Tier", "value": tier.capitalize(), "inline": True},
                {"name": "Amount", "value": "$" + amount + " USD", "inline": True},
                {"name": "Invoice ID", "value": invoice_id, "inline": True},
                {"name": "Description", "value": PRICING[tier]["description"], "inline": False},
            ],
            "footer": {"text": "Generated " + now_str},
            "timestamp": ts
        }]
    }

    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=embed,
            timeout=10
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print("  Discord notification failed: " + str(e))
        return False


def generate_invoice(
    client_email: str,
    client_name: str,
    tier: str = "simple",
    business_name: str = "",
    note: str = "",
    send: bool = True
) -> dict:
    """
    Main function to generate and optionally send an invoice.

    Args:
        client_email: Client's email address
        client_name: Client's name
        tier: Pricing tier (simple/medium/complex)
        business_name: Optional company/business name
        note: Optional note to include on invoice
        send: Whether to send immediately or just create

    Returns:
        Dict with invoice details and status
    """
    if tier not in PRICING:
        return {"error": "Invalid tier '" + tier + "'. Choose from: " + str(list(PRICING.keys()))}

    pricing = PRICING[tier]
    recipient = InvoiceRecipient(
        email=client_email,
        name=client_name,
        business_name=business_name or None
    )
    item = InvoiceItem(
        name="API Integration Script - " + tier.capitalize() + " Tier",
        description=pricing["description"],
        quantity=1,
        unit_price=pricing["amount"]
    )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts + "] Creating invoice for " + client_name + " (" + client_email + ")")
    print("  Tier: " + tier.capitalize() + " | Amount: $" + pricing["amount"])

    # Create invoice
    invoice = create_invoice(recipient, item, note=note, tier=tier)
    invoice_id = invoice.get("id")
    print("  Created: Invoice ID " + str(invoice_id))

    # Send invoice
    status = "created"
    if send:
        try:
            send_invoice(invoice_id)
            status = "sent"
            print("  Sent to " + client_email)
        except Exception as e:
            print("  Failed to send: " + str(e))
            status = "send_failed"

    # Discord notification
    discord_sent = send_discord_notification(invoice, recipient, tier)

    result = {
        "invoice_id": invoice_id,
        "status": status,
        "tier": tier,
        "amount": pricing["amount"],
        "client_email": client_email,
        "client_name": client_name,
        "discord_notification": discord_sent,
        "timestamp": datetime.now().isoformat(),
        "paypal_url": "https://www.paypal.com/invoice/p/#" + str(invoice_id)
    }

    # Save invoice record
    with open("invoice_log.jsonl", "a") as f:
        f.write(json.dumps(result) + "\n")

    return result


def list_invoices(status: str = "ALL", page: int = 1, page_size: int = 10) -> dict:
    """List invoices from PayPal."""
    token = get_paypal_access_token()
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }
    params = {"status": status, "page": page, "page_size": page_size, "total_required": True}

    resp = requests.get(
        PAYPAL_API_BASE + "/v2/invoicing/invoices",
        headers=headers,
        params=params,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def check_invoice_status(invoice_id: str) -> dict:
    """Check the status of a specific invoice."""
    token = get_paypal_access_token()
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    resp = requests.get(
        PAYPAL_API_BASE + "/v2/invoicing/invoices/" + invoice_id,
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PayPal Invoicing for Mr Bubba Services")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Create invoice command
    create_parser = subparsers.add_parser("create", help="Create and send an invoice")
    create_parser.add_argument("email", help="Client email address")
    create_parser.add_argument("name", help="Client name")
    create_parser.add_argument("--tier", default="simple", choices=["simple", "medium", "complex"],
                              help="Pricing tier")
    create_parser.add_argument("--business", default="", help="Company/business name")
    create_parser.add_argument("--note", default="", help="Custom note for invoice")
    create_parser.add_argument("--no-send", action="store_true", help="Create but don't send")

    # List invoices command
    list_parser = subparsers.add_parser("list", help="List invoices")
    list_parser.add_argument("--status", default="ALL", choices=["DRAFT", "SENT", "PAID", "CANCELLED", "ALL"])
    list_parser.add_argument("--page", type=int, default=1)

    # Check status command
    status_parser = subparsers.add_parser("status", help="Check invoice status")
    status_parser.add_argument("invoice_id", help="Invoice ID to check")

    args = parser.parse_args()

    if args.command == "create":
        result = generate_invoice(
            client_email=args.email,
            client_name=args.name,
            tier=args.tier,
            business_name=args.business,
            note=args.note,
            send=not args.no_send
        )
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        invoices = list_invoices(status=args.status, page=args.page)
        print(json.dumps(invoices, indent=2))
    elif args.command == "status":
        invoice = check_invoice_status(args.invoice_id)
        print(json.dumps(invoice, indent=2))
    else:
        parser.print_help()
