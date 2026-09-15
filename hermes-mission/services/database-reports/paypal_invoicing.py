#!/usr/bin/env python3
"""
PayPal Invoicing for Database Reports Service
Generates and sends invoices via PayPal API ($75-200 range).
"""

import argparse
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from decimal import Decimal

import requests


# Configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID", "")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"  # Use sandbox for testing
# PAYPAL_API_BASE = "https://api-m.paypal.com"  # Production

SERVICE_NAME = "Mr Bubba Services"
SERVICE_EMAIL = "mrbubba@agentmail.to"

# Invoice tiers
PRICING_TIERS = {
    "basic": {
        "name": "Basic Data Report",
        "description": "Single dataset analysis with distribution charts, summary statistics, and data quality assessment. Up to 100K rows.",
        "amount": "75.00",
        "delivery": "48 hours",
    },
    "standard": {
        "name": "Standard Data Report",
        "description": "Comprehensive analysis including correlation heatmaps, time series visualizations, automated AI insights. Up to 500K rows.",
        "amount": "125.00",
        "delivery": "48 hours",
    },
    "premium": {
        "name": "Premium Data Report",
        "description": "Full-service analysis with custom SQL queries, executive summary, interactive charts, and multi-source integration. Up to 2M rows.",
        "amount": "200.00",
        "delivery": "24 hours",
    },
}


class PayPalInvoiceManager:
    """Manage PayPal invoices for the Database Reports service."""

    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        """Obtain a PayPal OAuth2 access token."""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        url = f"{PAYPAL_API_BASE}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            self.access_token = result["access_token"]
            self.token_expires_at = time.time() + result.get("expires_in", 3600) - 60
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {response.status_code} — {response.text}")

    def create_invoice(self, client_email: str, client_name: str,
                       tier: str, custom_amount: str = None,
                       description: str = None, invoice_number: str = None) -> dict:
        """Create a PayPal invoice."""
        if tier not in PRICING_TIERS and not custom_amount:
            raise ValueError(f"Unknown tier: {tier}. Use: {list(PRICING_TIERS.keys())}")

        tier_info = PRICING_TIERS.get(tier, {})
        amount = custom_amount or tier_info.get("amount", "75.00")
        item_description = description or tier_info.get("description", "Data Analysis Report")
        item_name = tier_info.get("name", "Data Report")

        if not invoice_number:
            invoice_number = f"HDS-{datetime.now().strftime('%Y%m%d')}-{hashlib.md5(client_email.encode()).hexdigest()[:6].upper()}"

        url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        payload = {
            "detail": {
                "invoice_number": invoice_number,
                "reference": f"Order for {client_name}",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_code": "USD",
                "note": f"Thank you for choosing {SERVICE_NAME}! Report will be delivered via email.",
                "term": "Payment due upon receipt",
                "merchant_info": {
                    "email_address": SERVICE_EMAIL,
                    "business_name": SERVICE_NAME,
                },
                "billing_info": [
                    {
                        "email_address": client_email,
                        "business_name": client_name,
                    }
                ],
            },
            "invoicing_info": {
                "items": [
                    {
                        "name": item_name,
                        "description": item_description,
                        "quantity": "1",
                        "unit_amount": {
                            "currency_code": "USD",
                            "value": amount,
                        },
                    }
                ],
                "total_amount": {
                    "currency_code": "USD",
                    "value": amount,
                },
            },
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            result = response.json()
            print(f"✅ Invoice created: {invoice_number}")
            print(f"   Amount: ${amount}")
            print(f"   Client: {client_name} ({client_email})")
            return result
        else:
            print(f"❌ Failed to create invoice: {response.status_code} — {response.text}")
            return {"error": response.text}

    def send_invoice(self, invoice_id: str) -> dict:
        """Send a draft invoice to the client."""
        url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices/{invoice_id}/send"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        response = requests.post(url, headers=headers, timeout=30)

        if response.status_code in (200, 202):
            print(f"✅ Invoice {invoice_id} sent successfully")
            return {"status": "sent", "invoice_id": invoice_id}
        else:
            print(f"❌ Failed to send invoice: {response.status_code} — {response.text}")
            return {"error": response.text}

    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details."""
        url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices/{invoice_id}"
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get invoice: {response.status_code}")
            return {"error": response.text}

    def create_and_send(self, client_email: str, client_name: str,
                        tier: str = "standard", custom_amount: str = None,
                        description: str = None) -> dict:
        """Create and send an invoice in one step."""
        invoice = self.create_invoice(client_email, client_name, tier, custom_amount, description)

        if "error" not in invoice and "id" in invoice:
            invoice_id = invoice["id"]
            send_result = self.send_invoice(invoice_id)
            return {
                "invoice": invoice,
                "send_result": send_result,
                "invoice_id": invoice_id,
            }

        return invoice

    def record_payment(self, invoice_id: str, amount: str, transaction_id: str,
                       payment_date: str = None) -> dict:
        """Record a payment for an invoice."""
        url = f"{PAYPAL_API_BASE}/v2/invoicing/invoices/{invoice_id}/payments"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        payload = {
            "method": "PAYPAL",
            "payment_date": payment_date or datetime.now().strftime("%Y-%m-%d"),
            "amount": {
                "currency_code": "USD",
                "value": amount,
            },
            "transaction_id": transaction_id,
            "note": "Payment received via PayPal",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            print(f"✅ Payment recorded for invoice {invoice_id}")
            return response.json()
        else:
            print(f"❌ Failed to record payment: {response.status_code}")
            return {"error": response.text}

    def verify_webhook_signature(self, headers: dict, body: str) -> bool:
        """Verify PayPal webhook signature."""
        auth_algo = headers.get("PAYPAL-AUTH-ALGO", "")
        cert_url = headers.get("PAYPAL-CERT-URL", "")
        transmission_id = headers.get("PAYPAL-TRANSMISSION-ID", "")
        transmission_sig = headers.get("PAYPAL-TRANSMISSION-SIG", "")
        transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME", "")

        url = f"{PAYPAL_API_BASE}/v1/notifications/verify-webhook-signature"
        payload = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": PAYPAL_WEBHOOK_ID,
            "webhook_event": json.loads(body),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result.get("verification_status") == "SUCCESS"

        return False


def generate_invoice_pdf_data(invoice_data: dict) -> dict:
    """Generate invoice data formatted for PDF creation or display."""
    return {
        "invoice_number": invoice_data.get("detail", {}).get("invoice_number", "N/A"),
        "date": invoice_data.get("detail", {}).get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
        "due_date": "Upon Receipt",
        "merchant": {
            "name": SERVICE_NAME,
            "email": SERVICE_EMAIL,
        },
        "client": invoice_data.get("detail", {}).get("billing_info", [{}])[0],
        "items": invoice_data.get("invoicing_info", {}).get("items", []),
        "total": invoice_data.get("invoicing_info", {}).get("total_amount", {}),
        "status": invoice_data.get("status", "DRAFT"),
    }


def main():
    parser = argparse.ArgumentParser(description="PayPal Invoicing for Database Reports")
    parser.add_argument("action", choices=["create", "send", "check", "record"],
                        help="Action to perform")
    parser.add_argument("--email", help="Client email address")
    parser.add_argument("--name", default="Client", help="Client name")
    parser.add_argument("--tier", choices=["basic", "standard", "premium"],
                        default="standard", help="Report tier")
    parser.add_argument("--amount", help="Custom amount (overrides tier)")
    parser.add_argument("--description", help="Custom item description")
    parser.add_argument("--invoice-id", help="Invoice ID for send/check actions")
    parser.add_argument("--transaction-id", help="Transaction ID for recording payments")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    manager = PayPalInvoiceManager()

    if args.action == "create":
        if not args.email:
            print("Error: --email is required for create action")
            return

        result = manager.create_and_send(
            client_email=args.email,
            client_name=args.name,
            tier=args.tier,
            custom_amount=args.amount,
            description=args.description,
        )

        if args.json_output:
            print(json.dumps(result, indent=2, default=str))
        else:
            if "invoice_id" in result:
                print(f"\n{'='*40}")
                print(f"Invoice Created & Sent!")
                print(f"  ID: {result['invoice_id']}")
                tier_info = PRICING_TIERS.get(args.tier, {})
                amount = args.amount or tier_info.get("amount", "N/A")
                print(f"  Amount: ${amount}")
                print(f"  Tier: {args.tier}")
                print(f"{'='*40}")

    elif args.action == "send":
        if not args.invoice_id:
            print("Error: --invoice-id is required")
            return
        result = manager.send_invoice(args.invoice_id)
        if args.json_output:
            print(json.dumps(result, indent=2))

    elif args.action == "check":
        if not args.invoice_id:
            print("Error: --invoice-id is required")
            return
        result = manager.get_invoice(args.invoice_id)
        if args.json_output:
            print(json.dumps(result, indent=2))
        else:
            status = result.get("status", "UNKNOWN")
            print(f"Invoice {args.invoice_id} status: {status}")

    elif args.action == "record":
        if not args.invoice_id or not args.amount or not args.transaction_id:
            print("Error: --invoice-id, --amount, and --transaction-id are required")
            return
        result = manager.record_payment(args.invoice_id, args.amount, args.transaction_id)
        if args.json_output:
            print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
