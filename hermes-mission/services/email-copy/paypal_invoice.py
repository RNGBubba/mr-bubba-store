#!/usr/bin/env python3
"""
PayPal Invoicing for Mr Bubba Services Email Copywriting
Creates and sends PayPal invoices for email copy services ($25-75/email).

Usage:
    python3 paypal_invoice.py --client "John Doe" --email "john@example.com" \
        --service "Welcome Email" --price 45
    python3 paypal_invoice.py --list-templates
    python3 paypal_invoice.py --webhook-verify  # For Discord webhook verification
"""

import json
import os
import argparse
import urllib.request
import urllib.error
import logging
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "YOUR_PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET", "YOUR_PAYPAL_SECRET")
PAYPAL_MERCHANT_EMAIL = os.environ.get("PAYPAL_MERCHANT_EMAIL", "mrbubba@agentmail.to")
PAYPAL_BASE_URL = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
INVOICE_DIR = os.environ.get("INVOICE_DIR", os.path.expanduser("~/.mr-bubba-mission/invoices"))

# ── Service Tiers ─────────────────────────────────────────────────────────

SERVICE_TIERS = {
    "basic": {
        "name": "Basic Email Copy",
        "description": "Single email copy (welcome, follow-up, or simple promotional)",
        "price": 25.00,
        "features": ["1 email draft", "1 revision", "48-hour delivery", "Standard tone"],
    },
    "professional": {
        "name": "Professional Email Copy",
        "description": "Single email copy with research + strategy",
        "price": 45.00,
        "features": ["1 email draft", "2 revisions", "24-hour delivery", "Targeted strategy", "CTA optimization"],
    },
    "premium": {
        "name": "Premium Email Copy",
        "description": "Complex email with deep audience research and A/B variants",
        "price": 75.00,
        "features": ["1 email + 2 A/B variants", "3 revisions", "Same-day delivery", "Deep audience research", "Subject line testing"],
    },
    "sequence_3x": {
        "name": "3-Email Sequence Bundle",
        "description": "Welcome + Promotional + Follow-up sequence (save 10%)",
        "price": 100.00,
        "features": ["3 emails", "2 revisions per email", "48-hour delivery per email", "Cohesive narrative", "Cross-email strategy"],
    },
    "sequence_5x": {
        "name": "5-Email Sequence Bundle",
        "description": "Full newsletter sequence (save 15%)",
        "price": 160.00,
        "features": ["5 emails", "2 revisions per email", "Rush delivery available", "Brand voice guide", "Monthly strategy call"],
    },
}


# ── PayPal API Client ─────────────────────────────────────────────────────

class PayPalClient:
    """Client for PayPal Invoicing API."""

    def __init__(self, client_id: str, secret: str, base_url: str = PAYPAL_BASE_URL):
        self.client_id = client_id
        self.secret = secret
        self.base_url = base_url
        self.access_token = None
        self.token_expires = None
        self.logger = logging.getLogger(__name__)

    def _get_access_token(self) -> str:
        """Obtain OAuth2 access token from PayPal."""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token

        url = f"{self.base_url}/v1/oauth2/token"
        credentials = f"{self.client_id}:{self.secret}"
        import base64
        auth = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = "grant_type=client_credentials".encode()
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=result.get("expires_in", 3600) - 60)
                return self.access_token
        except Exception as e:
            self.logger.error(f"Failed to get PayPal access token: {e}")
            raise

    def _api_request(self, method: str, path: str, data: dict = None) -> dict:
        """Make an authenticated PayPal API request."""
        token = self._get_access_token()
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            self.logger.error(f"PayPal API error {e.code}: {error_body}")
            return {"error": True, "status": e.code, "details": error_body}
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return {"error": True, "message": str(e)}

    def create_invoice(self, invoice_data: dict) -> dict:
        """Create a new PayPal invoice."""
        return self._api_request("POST", "/v2/invoicing/invoices", invoice_data)

    def send_invoice(self, invoice_id: str) -> dict:
        """Send an existing invoice."""
        return self._api_request("POST", f"/v2/invoicing/invoices/{invoice_id}/send")

    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details."""
        return self._api_request("GET", f"/v2/invoicing/invoices/{invoice_id}")

    def cancel_invoice(self, invoice_id: str) -> dict:
        """Cancel an invoice."""
        return self._api_request("POST", f"/v2/invoicing/invoices/{invoice_id}/cancel")


# ── Invoice Builder ───────────────────────────────────────────────────────

class InvoiceBuilder:
    """Builds PayPal invoice payloads for email copy services."""

    def __init__(self, merchant_email: str = PAYPAL_MERCHANT_EMAIL):
        self.merchant_email = merchant_email

    def build_invoice(
        self,
        client_name: str,
        client_email: str,
        service_tier: str,
        custom_price: float = None,
        project_description: str = "",
        invoice_number: str = None,
    ) -> dict:
        """Build a PayPal invoice payload."""
        tier = SERVICE_TIERS.get(service_tier)
        if not tier:
            raise ValueError(f"Unknown service tier: {service_tier}")

        price = custom_price or tier["price"]
        invoice_number = invoice_number or f"HDS-EC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        invoice = {
            "detail": {
                "invoice_number": invoice_number,
                "reference": f"email-copy-{service_tier}",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_code": "USD",
                "note": f"Thank you for choosing Mr Bubba Services for your email copywriting needs!\n\nProject: {project_description or tier['name']}\nService: {tier['description']}\n\nIncludes: {', '.join(tier['features'])}",
                "term": f"Payment due within 14 days. Net 14.",
                "payment_term": {
                    "term_type": "NET_14",
                    "due_date": due_date,
                },
            },
            "invoicer": {
                "name": {
                    "given_name": "Mr Bubba",
                    "surname": "Data Services",
                },
                "email_address": self.merchant_email,
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "name": {
                            "given_name": client_name.split()[0] if client_name else "Client",
                            "surname": " ".join(client_name.split()[1:]) if len(client_name.split()) > 1 else "",
                        },
                        "email_address": client_email,
                    },
                }
            ],
            "items": [
                {
                    "name": tier["name"],
                    "description": tier["description"],
                    "quantity": 1,
                    "unit_amount": {
                        "currency_code": "USD",
                        "value": f"{price:.2f}",
                    },
                    "unit_of_measure": "QUANTITY",
                }
            ],
            "configuration": {
                "allow_tip": False,
                "tax_calculated_after_discount": True,
                "tax_inclusive": False,
            },
        }

        return invoice

    def build_bulk_invoice(
        self,
        client_name: str,
        client_email: str,
        services: list[dict],
    ) -> dict:
        """Build invoice for multiple email copy services."""
        invoice_number = f"HDS-EC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        items = []
        total = 0.0

        for svc in services:
            tier_id = svc.get("tier", "professional")
            tier = SERVICE_TIERS.get(tier_id, SERVICE_TIERS["professional"])
            price = svc.get("price", tier["price"])
            quantity = svc.get("quantity", 1)

            items.append({
                "name": tier["name"],
                "description": svc.get("description", tier["description"]),
                "quantity": quantity,
                "unit_amount": {
                    "currency_code": "USD",
                    "value": f"{price:.2f}",
                },
                "unit_of_measure": "QUANTITY",
            })
            total += price * quantity

        invoice = {
            "detail": {
                "invoice_number": invoice_number,
                "reference": "email-copy-bulk",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_code": "USD",
                "note": f"Bulk email copywriting order from Mr Bubba Services\nTotal: ${total:.2f}\nIncludes {len(items)} service(s).",
                "payment_term": {
                    "term_type": "NET_14",
                    "due_date": due_date,
                },
            },
            "invoicer": {
                "name": {"given_name": "Mr Bubba", "surname": "Data Services"},
                "email_address": self.merchant_email,
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "name": {
                            "given_name": client_name.split()[0] if client_name else "Client",
                            "surname": " ".join(client_name.split()[1:]) if len(client_name.split()) > 1 else "",
                        },
                        "email_address": client_email,
                    },
                }
            ],
            "items": items,
        }

        return invoice


# ── Discord Notification ──────────────────────────────────────────────────

def send_discord_notification(invoice_data: dict, invoice_id: str = None):
    """Send invoice notification to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        logging.warning("Discord webhook URL not configured, skipping notification")
        return

    price = 0.0
    for item in invoice_data.get("items", []):
        qty = int(item.get("quantity", 1))
        amt = float(item.get("unit_amount", {}).get("value", 0))
        price += qty * amt

    payload = {
        "embeds": [
            {
                "title": "💰 New PayPal Invoice Created",
                "description": "Mr Bubba Services — Email Copywriting",
                "color": 0x00AA55,
                "fields": [
                    {"name": "Invoice #", "value": invoice_data.get("detail", {}).get("invoice_number", "N/A"), "inline": True},
                    {"name": "Amount", "value": f"${price:.2f}", "inline": True},
                    {"name": "Client Email", "value": invoice_data.get("primary_recipients", [{}])[0].get("billing_info", {}).get("email_address", "N/A"), "inline": True},
                    {"name": "Service", "value": invoice_data.get("items", [{}])[0].get("name", "N/A"), "inline": True},
                    {"name": "Due Date", "value": invoice_data.get("detail", {}).get("payment_term", {}).get("due_date", "N/A"), "inline": True},
                    {"name": "PayPal ID", "value": invoice_id or "pending", "inline": True},
                ],
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Mr Bubba Services | PayPal Invoicing"},
            }
        ]
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            logging.info(f"Discord notification sent: {resp.status}")
    except Exception as e:
        logging.error(f"Failed to send Discord notification: {e}")


# ── CLI Interface ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PayPal Invoicing for Mr Bubba Services")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Invoice command
    invoice_parser = subparsers.add_parser("create", help="Create and send an invoice")
    invoice_parser.add_argument("--client", "-c", required=True, help="Client name")
    invoice_parser.add_argument("--email", "-e", required=True, help="Client email")
    invoice_parser.add_argument("--tier", "-t", choices=SERVICE_TIERS.keys(), default="professional",
                                help="Service tier")
    invoice_parser.add_argument("--price", "-p", type=float, help="Custom price (overrides tier default)")
    invoice_parser.add_argument("--description", "-d", default="", help="Project description")
    invoice_parser.add_argument("--sandbox", action="store_true", help="Use PayPal sandbox")
    invoice_parser.add_argument("--dry-run", action="store_true", help="Build invoice but don't send")

    # Bulk command
    bulk_parser = subparsers.add_parser("bulk", help="Create bulk invoice")
    bulk_parser.add_argument("--client", "-c", required=True, help="Client name")
    bulk_parser.add_argument("--email", "-e", required=True, help="Client email")
    bulk_parser.add_argument("--services", "-s", required=True, help="JSON array of services")
    bulk_parser.add_argument("--sandbox", action="store_true", help="Use PayPal sandbox")
    bulk_parser.add_argument("--dry-run", action="store_true", help="Build invoice but don't send")

    # List templates
    subparsers.add_parser("tiers", help="List available service tiers")

    # Webhook listener
    webhook_parser = subparsers.add_parser("webhook", help="Run webhook listener for PayPal events")
    webhook_parser.add_argument("--port", type=int, default=8766, help="Webhook port")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if args.command == "create":
        builder = InvoiceBuilder(PAYPAL_MERCHANT_EMAIL)
        invoice_payload = builder.build_invoice(
            client_name=args.client,
            client_email=args.email,
            service_tier=args.tier,
            custom_price=args.price,
            project_description=args.description,
        )

        if args.dry_run:
            print(json.dumps(invoice_payload, indent=2))
            print("\n[DRY RUN] Invoice created but not sent to PayPal")
            return

        # Initialize PayPal client
        base_url = "https://api-m.sandbox.paypal.com" if args.sandbox else PAYPAL_BASE_URL
        paypal = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_SECRET, base_url)

        result = paypal.create_invoice(invoice_payload)

        if result.get("error"):
            print(json.dumps(result, indent=2))
            return

        invoice_id = result.get("id")

        if invoice_id:
            send_result = paypal.send_invoice(invoice_id)
            print(json.dumps({
                "status": "sent",
                "invoice_id": invoice_id,
                "invoice_number": invoice_payload["detail"]["invoice_number"],
                "amount": args.price or SERVICE_TIERS[args.tier]["price"],
                "paypal_response": send_result,
            }, indent=2))

            # Notify Discord
            send_discord_notification(invoice_payload, invoice_id)
        else:
            print(json.dumps(result, indent=2))

    elif args.command == "bulk":
        services = json.loads(args.services)
        builder = InvoiceBuilder(PAYPAL_MERCHANT_EMAIL)
        invoice_payload = builder.build_bulk_invoice(args.client, args.email, services)

        if args.dry_run:
            print(json.dumps(invoice_payload, indent=2))
            return

        base_url = "https://api-m.sandbox.paypal.com" if args.sandbox else PAYPAL_BASE_URL
        paypal = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_SECRET, base_url)

        result = paypal.create_invoice(invoice_payload)

        if result.get("error"):
            print(json.dumps(result, indent=2))
            return

        invoice_id = result.get("id")
        if invoice_id:
            paypal.send_invoice(invoice_id)
            send_discord_notification(invoice_payload, invoice_id)

        print(json.dumps(result, indent=2))

    elif args.command == "tiers":
        print("\n" + "=" * 60)
        print("Mr Bubba Services — Email Copywriting Service Tiers")
        print("=" * 60)
        for tier_id, tier in SERVICE_TIERS.items():
            print(f"\n[{tier_id}] {tier['name']}")
            print(f"  Description: {tier['description']}")
            print(f"  Price: ${tier['price']:.2f}")
            print(f"  Includes:")
            for feat in tier["features"]:
                print(f"    • {feat}")

    elif args.command == "webhook":
        # Start simple webhook listener for PayPal IPN/webhooks
        class PayPalWebhookHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))

                event_type = body.get("event_type", "unknown")
                resource = body.get("resource", {})
                logging.info(f"PayPal webhook: {event_type}")

                if "INVOICING" in event_type:
                    invoice_id = resource.get("invoice_id", resource.get("id", "unknown"))
                    status = resource.get("status", "unknown")
                    logging.info(f"Invoice {invoice_id}: {status}")

                    # Notify Discord
                    if DISCORD_WEBHOOK_URL and "PAID" in event_type.upper():
                        payload = {
                            "embeds": [{
                                "title": "✅ Invoice Paid!",
                                "description": f"Invoice {invoice_id} has been paid",
                                "color": 0x57F287,
                                "timestamp": datetime.now().isoformat(),
                            }]
                        }
                        try:
                            data = json.dumps(payload).encode()
                            req = urllib.request.Request(
                                DISCORD_WEBHOOK_URL, data=data,
                                headers={"Content-Type": "application/json"}, method="POST"
                            )
                            urllib.request.urlopen(req, timeout=10)
                        except Exception as e:
                            logging.error(f"Discord notification failed: {e}")

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')

            def log_message(self, format, *args):
                logging.info(f"HTTP: {format % args}")

        server = HTTPServer(("0.0.0.0", args.port), PayPalWebhookHandler)
        logging.info(f"PayPal webhook server listening on port {args.port}")
        print(f"Webhook server running at http://0.0.0.0:{args.port}/")
        server.serve_forever()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
