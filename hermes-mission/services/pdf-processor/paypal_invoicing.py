#!/usr/bin/env python3
"""
PayPal Invoicing for Mr Bubba Services PDF Processing
Creates and sends PayPal invoices via the PayPal REST API.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode


# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "YOUR_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID", "YOUR_WEBHOOK_ID")

# Use sandbox for testing, live for production
PAYPAL_BASE_URL = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

# Discord webhook for payment notifications
DISCORD_WEBHOOK_URL = os.environ.get(
    "DISCORD_WEBHOOK_URL",
    "YOUR_DISCORD_WEBHOOK_URL",
)

# Service pricing tiers
PRICING = {
    "basic": {
        "name": "Basic PDF Processing",
        "description": "Text extraction from 1-5 pages",
        "price": 30.00,
        "pages": "1-5",
    },
    "standard": {
        "name": "Standard PDF Processing",
        "description": "Text + table extraction from 6-20 pages",
        "price": 50.00,
        "pages": "6-20",
    },
    "premium": {
        "name": "Premium PDF Processing",
        "description": "Full extraction + OCR for 21-100 pages",
        "price": 75.00,
        "pages": "21-100",
    },
    "enterprise": {
        "name": "Enterprise PDF Processing",
        "description": "Bulk processing for 100+ pages",
        "price": 100.00,
        "pages": "100+",
    },
    "ocr_addon": {
        "name": "OCR Add-on",
        "description": "OCR processing for scanned documents",
        "price": 15.00,
        "pages": "per document",
    },
    "rush": {
        "name": "Rush Delivery",
        "description": "24-hour delivery surcharge",
        "price": 20.00,
        "per": "per order",
    },
}


class PayPalClient:
    """PayPal REST API client for invoicing."""

    def __init__(self, client_id: str, client_secret: str, base_url: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or PAYPAL_BASE_URL
        self.access_token = None

    def get_access_token(self) -> str:
        """Get OAuth2 access token from PayPal."""
        url = f"{self.base_url}/v1/oauth2/token"
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = __import__("base64").b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = urlencode({"grant_type": "client_credentials"}).encode("utf-8")

        req = Request(url, data=data, headers=headers, method="POST")

        try:
            with urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                self.access_token = result["access_token"]
                return self.access_token
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"PayPal auth failed: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"PayPal auth error: {e}")

    def _api_call(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        retry: bool = True,
    ) -> dict:
        """Make an authenticated API call to PayPal."""
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"pdf-proc-{int(time.time())}",
        }

        body = json.dumps(data).encode("utf-8") if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 401 and retry:
                # Token expired, retry with new token
                self.get_access_token()
                return self._api_call(method, endpoint, data, retry=False)
            error_body = e.read().decode("utf-8")
            raise Exception(f"PayPal API error: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"PayPal API call failed: {e}")

    def create_invoice(
        self,
        recipient_email: str,
        recipient_name: str,
        items: list[dict],
        notes: str = "",
        invoice_number: Optional[str] = None,
        due_days: int = 7,
    ) -> dict:
        """Create a PayPal invoice."""
        if not invoice_number:
            invoice_number = f"PDF-{datetime.now().strftime('%Y%m%d')}-{int(time.time()) % 10000:04d}"

        due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

        # Build invoice items
        invoice_items = []
        for item in items:
            invoice_items.append({
                "name": item["name"],
                "description": item.get("description", ""),
                "quantity": str(item.get("quantity", 1)),
                "unit_amount": {
                    "currency_code": "USD",
                    "value": f"{item['price']:.2f}",
                },
            })

        invoice_data = {
            "detail": {
                "invoice_number": invoice_number,
                "reference": "pdf-processing",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_code": "USD",
                "note": notes or "Thank you for your business!",
                "terms_and_conditions": "Payment is due within 7 days. Files will be delivered upon payment confirmation.",
                "payment_term": {
                    "due_date": due_date,
                    "term_type": "DUE_ON_DATE_SPECIFIED",
                },
            },
            "invoicer": {
                "name": {
                    "given_name": "Mr Bubba Services",
                },
                "email_address": "mrbubba@agentmail.to",
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "name": {
                            "given_name": recipient_name,
                        },
                        "email_address": recipient_email,
                    },
                }
            ],
            "items": invoice_items,
            "configuration": {
                "partial_payment": {
                    "allow_partial_payment": False,
                },
                "allow_tip": False,
                "tax_after_discount": True,
            },
        }

        result = self._api_call("POST", "/v2/invoicing/invoices", invoice_data)
        return result

    def send_invoice(self, invoice_id: str) -> dict:
        """Send a PayPal invoice to the recipient."""
        url = f"/v2/invoicing/invoices/{invoice_id}/send"
        result = self._api_call("POST", url, {"send_to_invoicer": False, "send_to_recipient": True})
        return result

    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details."""
        result = self._api_call("GET", f"/v2/invoicing/invoices/{invoice_id}")
        return result

    def list_invoices(self, page: int = 1, page_size: int = 10) -> dict:
        """List invoices."""
        result = self._api_call(
            "GET",
            f"/v2/invoicing/invoices?page={page}&page_size={page_size}&total_required=true",
        )
        return result

    def cancel_invoice(self, invoice_id: str) -> dict:
        """Cancel an invoice."""
        result = self._api_call("POST", f"/v2/invoicing/invoices/{invoice_id}/cancel", {
            "subject": "Cancelled - No longer needed",
            "note": "This invoice has been cancelled.",
            "send_to_invoicer": False,
            "send_to_recipient": True,
        })
        return result


def notify_discord(invoice_data: dict, recipient_email: str):
    """Send payment notification to Discord webhook."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL":
        print("Discord webhook not configured, skipping notification")
        return

    total_amount = sum(
        float(item.get("unit_amount", {}).get("value", 0)) * int(item.get("quantity", 1))
        for item in invoice_data.get("items", [])
    )

    embed = {
        "title": "🧾 New PayPal Invoice Created",
        "color": 0x009CDE,  # PayPal blue
        "fields": [
            {"name": "Invoice #", "value": invoice_data.get("detail", {}).get("invoice_number", "N/A"), "inline": True},
            {"name": "Amount", "value": f"${total_amount:.2f}", "inline": True},
            {"name": "Recipient", "value": recipient_email, "inline": True},
            {"name": "Status", "value": "SENT", "inline": True},
        ],
        "timestamp": datetime.now().isoformat(),
    }

    payload = {"embeds": [embed]}

    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(DISCORD_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req) as response:
            print(f"Discord notification sent: {response.status}")
    except Exception as e:
        print(f"Discord notification failed: {e}")


def create_service_invoice(
    recipient_email: str,
    recipient_name: str,
    service_tier: str,
    page_count: int = 0,
    needs_ocr: bool = False,
    rush_delivery: bool = False,
    notes: str = "",
) -> Optional[dict]:
    """Create a PDF processing service invoice."""
    client = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)

    # Build items list
    items = []

    # Main service
    tier = PRICING.get(service_tier, PRICING["basic"])
    items.append({
        "name": tier["name"],
        "description": f"{tier['description']} | Pages: {page_count}",
        "quantity": 1,
        "price": tier["price"],
    })

    # OCR addon
    if needs_ocr:
        ocr = PRICING["ocr_addon"]
        items.append({
            "name": ocr["name"],
            "description": ocr["description"],
            "quantity": 1,
            "price": ocr["price"],
        })

    # Rush delivery
    if rush_delivery:
        rush = PRICING["rush"]
        items.append({
            "name": rush["name"],
            "description": rush["description"],
            "quantity": 1,
            "price": rush["price"],
        })

    # Build notes
    if not notes:
        notes = f"PDF Processing Service\nService Tier: {tier['name']}\nPages: {page_count}"
        if needs_ocr:
            notes += "\nOCR: Yes"
        if rush_delivery:
            notes += "\nRush Delivery: Yes"

    try:
        # Create invoice
        invoice = client.create_invoice(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            items=items,
            notes=notes,
        )

        print(f"Invoice created: {invoice.get('id')}")

        # Send invoice
        client.send_invoice(invoice["id"])
        print(f"Invoice sent to {recipient_email}")

        # Notify Discord
        notify_discord(invoice, recipient_email)

        return invoice

    except Exception as e:
        print(f"Invoice creation failed: {e}")
        return None


def process_paypal_webhook(payload: dict) -> dict:
    """Process incoming PayPal webhook event."""
    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})

    result = {
        "event_type": event_type,
        "processed": False,
    }

    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        # Payment received
        amount = resource.get("amount", {}).get("value", "0")
        currency = resource.get("amount", {}).get("currency_code", "USD")
        payer_email = resource.get("payer", {}).get("email_address", "unknown")

        result["processed"] = True
        result["amount"] = amount
        result["currency"] = currency
        result["payer_email"] = payer_email
        result["status"] = "paid"

        # Notify Discord
        if DISCORD_WEBHOOK_URL != "YOUR_DISCORD_WEBHOOK_URL":
            embed = {
                "title": "💰 Payment Received!",
                "color": 0x57F287,  # Green
                "fields": [
                    {"name": "Amount", "value": f"{currency} {amount}", "inline": True},
                    {"name": "Payer", "value": payer_email, "inline": True},
                    {"name": "Status", "value": "PAID", "inline": True},
                ],
                "timestamp": datetime.now().isoformat(),
            }
            try:
                data = json.dumps({"embeds": [embed]}).encode("utf-8")
                req = Request(
                    DISCORD_WEBHOOK_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req) as response:
                    print(f"Discord payment notification sent: {response.status}")
            except Exception as e:
                print(f"Discord notification failed: {e}")

    elif event_type == "INVOICING.INVOICE.PAID":
        # Invoice paid
        invoice_id = resource.get("invoice_id", "unknown")
        result["processed"] = True
        result["invoice_id"] = invoice_id
        result["status"] = "paid"

    elif event_type == "INVOICING.INVOICE.CANCELLED":
        # Invoice cancelled
        invoice_id = resource.get("invoice_id", "unknown")
        result["processed"] = True
        result["invoice_id"] = invoice_id
        result["status"] = "cancelled"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="PayPal Invoicing for PDF Processing Service"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create invoice command
    create_parser = subparsers.add_parser("create", help="Create and send an invoice")
    create_parser.add_argument("--email", required=True, help="Recipient email")
    create_parser.add_argument("--name", required=True, help="Recipient name")
    create_parser.add_argument(
        "--tier",
        choices=["basic", "standard", "premium", "enterprise"],
        default="basic",
        help="Service tier",
    )
    create_parser.add_argument("--pages", type=int, default=0, help="Number of pages")
    create_parser.add_argument("--ocr", action="store_true", help="Add OCR service")
    create_parser.add_argument("--rush", action="store_true", help="Add rush delivery")
    create_parser.add_argument("--notes", default="", help="Additional notes")

    # Get invoice command
    get_parser = subparsers.add_parser("get", help="Get invoice details")
    get_parser.add_argument("--id", required=True, help="Invoice ID")

    # List invoices command
    list_parser = subparsers.add_parser("list", help="List invoices")
    list_parser.add_argument("--page", type=int, default=1, help="Page number")
    list_parser.add_argument("--page-size", type=int, default=10, help="Page size")

    # Cancel invoice command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an invoice")
    cancel_parser.add_argument("--id", required=True, help="Invoice ID")

    # Webhook command (for testing)
    webhook_parser = subparsers.add_parser("webhook", help="Simulate webhook event")
    webhook_parser.add_argument("--event", default="PAYMENT.CAPTURE.COMPLETED")
    webhook_parser.add_argument("--amount", default="50.00")

    # Pricing info command
    subparsers.add_parser("pricing", help="Show pricing tiers")

    args = parser.parse_args()

    if args.command == "create":
        invoice = create_service_invoice(
            recipient_email=args.email,
            recipient_name=args.name,
            service_tier=args.tier,
            page_count=args.pages,
            needs_ocr=args.ocr,
            rush_delivery=args.rush,
            notes=args.notes,
        )
        if invoice:
            print(json.dumps(invoice, indent=2))
        else:
            print("Failed to create invoice")
            sys.exit(1)

    elif args.command == "get":
        client = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        try:
            invoice = client.get_invoice(args.id)
            print(json.dumps(invoice, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "list":
        client = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        try:
            invoices = client.list_invoices(args.page, args.page_size)
            print(json.dumps(invoices, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "cancel":
        client = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        try:
            result = client.cancel_invoice(args.id)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "webhook":
        payload = {
            "event_type": args.event,
            "resource": {
                "amount": {
                    "value": args.amount,
                    "currency_code": "USD",
                },
                "payer": {
                    "email_address": "test@example.com",
                },
            },
        }
        result = process_paypal_webhook(payload)
        print(json.dumps(result, indent=2))

    elif args.command == "pricing":
        print("=" * 60)
        print("MR BUBBA SERVICES - PDF PROCESSING PRICING")
        print("=" * 60)
        for tier_key, tier_info in PRICING.items():
            print(f"\n{tier_info['name']}")
            print(f"  Description: {tier_info['description']}")
            print(f"  Price: ${tier_info['price']:.2f}")
            if "pages" in tier_info:
                print(f"  Pages: {tier_info['pages']}")
        print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
