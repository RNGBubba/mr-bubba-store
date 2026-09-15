#!/usr/bin/env python3
"""
PayPal Invoicing for Resume & Cover Letter Tailoring Service

Creates and sends PayPal invoices for service packages.
Supports $30-$60 pricing tiers with webhook notifications.
"""

import json
import os
import sys
import base64
from datetime import datetime
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None


# ── Configuration ───────────────────────────────────────────────────────────

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "YOUR_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID", "YOUR_WEBHOOK_ID")
PAYPAL_ENV = os.environ.get("PAYPAL_ENV", "sandbox")  # or "live"

if PAYPAL_ENV == "live":
    PAYPAL_API_BASE = "https://api-m.paypal.com"
else:
    PAYPAL_API_BASE = "https://api-m.sandbox.paypay.com"

SERVICE_NAME = "Mr Bubba Services"
SERVICE_DESCRIPTION = "Resume & Cover Letter Tailoring"

# ── Pricing ─────────────────────────────────────────────────────────────────

PACKAGES = {
    "basic_resume": {
        "name": "Resume Tailoring",
        "description": "ATS-optimized resume rewrite with keyword analysis",
        "price": 30.00,
        "currency": "USD",
    },
    "cover_letter": {
        "name": "Cover Letter",
        "description": "Custom cover letter tailored to job description",
        "price": 30.00,
        "currency": "USD",
    },
    "bundle": {
        "name": "Resume + Cover Letter Bundle",
        "description": "Complete application package (resume + cover letter + ATS report)",
        "price": 50.00,
        "currency": "USD",
    },
    "premium": {
        "name": "Premium Package",
        "description": "Resume + Cover Letter + LinkedIn summary + Interview prep + Priority delivery",
        "price": 60.00,
        "currency": "USD",
    },
}


# ── PayPal API Client ───────────────────────────────────────────────────────

class PayPalClient:
    """PayPal REST API client for invoicing."""
    
    def __init__(self, client_id: str, client_secret: str, env: str = "sandbox"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.env = env
        
        if env == "live":
            self.base_url = "https://api-m.paypal.com"
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"
        
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Get OAuth2 access token."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=client_credentials".encode()
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result.get("access_token")
                return bool(self.access_token)
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make authenticated API request."""
        if not self.access_token:
            if not self.authenticate():
                return {"error": "Not authenticated"}
        
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            return {"error": str(e), "status": e.code, "body": error_body}
        except Exception as e:
            return {"error": str(e)}
    
    def create_invoice(self, invoice_data: dict) -> dict:
        """Create a new invoice."""
        return self._request("POST", "/v2/invoicing/invoices", invoice_data)
    
    def send_invoice(self, invoice_id: str) -> dict:
        """Send an invoice to the recipient."""
        return self._request(
            "POST",
            f"/v2/invoicing/invoices/{invoice_id}/send",
            {"send_to_recipient": True}
        )
    
    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details."""
        return self._request("GET", f"/v2/invoicing/invoices/{invoice_id}")
    
    def create_invoice_and_send(self, client_email: str, package_key: str,
                                 notes: str = "") -> dict:
        """Create and send an invoice for a package."""
        if package_key not in PACKAGES:
            return {"error": f"Unknown package: {package_key}"}
        
        pkg = PACKAGES[package_key]
        
        invoice_data = {
            "detail": {
                "invoice_number": f"HDS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "reference": f"resume-tailor-{package_key}",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_code": pkg["currency"],
                "note": notes or f"{SERVICE_DESCRIPTION} — {pkg['name']}",
                "term": "Due on receipt",
            },
            "invoicer": {
                "name": {
                    "given_name": "Mr Bubba Data",
                    "surname": "Services",
                },
                "website": "https://mrbubbaservices.com",
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "email_address": client_email,
                    }
                }
            ],
            "items": [
                {
                    "name": pkg["name"],
                    "description": pkg["description"],
                    "quantity": "1",
                    "unit_amount": {
                        "currency_code": pkg["currency"],
                        "value": f"{pkg['price']:.2f}",
                    },
                }
            ],
            "configuration": {
                "allow_tip": False,
                "tax_calculated_after_discount": True,
                "tax_inclusive": False,
            },
        }
        
        # Create invoice
        result = self.create_invoice(invoice_data)
        if "error" in result:
            return result
        
        invoice_id = result.get("id")
        
        # Send invoice
        send_result = self.send_invoice(invoice_id)
        if "error" in send_result:
            return {"invoice_id": invoice_id, "status": "created", "send_error": send_result}
        
        return {
            "invoice_id": invoice_id,
            "status": "sent",
            "amount": pkg["price"],
            "package": pkg["name"],
            "recipient": client_email,
        }


# ── Local Invoice Tracking ─────────────────────────────────────────────────

INVOICE_LOG = Path("invoices.json")


def load_invoice_log() -> list:
    """Load local invoice log."""
    if INVOICE_LOG.exists():
        return json.loads(INVOICE_LOG.read_text())
    return []


def save_invoice_log(invoices: list):
    """Save invoice log to file."""
    INVOICE_LOG.write_text(json.dumps(invoices, indent=2))


def log_invoice(invoice_record: dict):
    """Add invoice to local log."""
    invoices = load_invoice_log()
    invoices.append(invoice_record)
    save_invoice_log(invoices)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PayPal Invoicing for Resume Tailoring Service"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Send invoice command
    send_parser = subparsers.add_parser("send", help="Create and send invoice")
    send_parser.add_argument("email", help="Client email address")
    send_parser.add_argument("package", choices=list(PACKAGES.keys()),
                           help="Service package")
    send_parser.add_argument("--notes", default="", help="Additional notes")
    
    # Check status command
    status_parser = subparsers.add_parser("status", help="Check invoice status")
    status_parser.add_argument("invoice_id", help="PayPal invoice ID")
    
    # List invoices command
    subparsers.add_parser("list", help="List all logged invoices")
    
    # Show packages command
    subparsers.add_parser("packages", help="Show available packages")
    
    # Webhook handler (for testing)
    webhook_parser = subparsers.add_parser("webhook", help="Process webhook event")
    webhook_parser.add_argument("--file", help="Webhook event JSON file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    client = PayPalClient(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_ENV)
    
    if args.command == "send":
        print(f"Creating invoice for {args.email} — Package: {args.package}")
        
        if PAYPAL_CLIENT_ID == "YOUR_CLIENT_ID":
            print("\n[LOCAL MODE] PayPal credentials not configured — logging locally")
            record = {
                "id": f"LOCAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "email": args.email,
                "package": args.package,
                "amount": PACKAGES[args.package]["price"],
                "status": "pending_payment",
                "created_at": datetime.now().isoformat(),
                "notes": args.notes,
            }
            log_invoice(record)
            print(json.dumps(record, indent=2))
            return 0
        
        if not client.authenticate():
            print("Failed to authenticate with PayPal")
            return 1
        
        result = client.create_invoice_and_send(args.email, args.package, args.notes)
        print(json.dumps(result, indent=2))
        
        if "invoice_id" in result:
            record = {
                "id": result["invoice_id"],
                "email": args.email,
                "package": args.package,
                "amount": PACKAGES[args.package]["price"],
                "status": result["status"],
                "created_at": datetime.now().isoformat(),
            }
            log_invoice(record)
        
        return 0
    
    elif args.command == "status":
        if PAYPAL_CLIENT_ID == "YOUR_CLIENT_ID":
            print("[LOCAL MODE] Cannot check PayPal status without credentials")
            return 1
        
        if not client.authenticate():
            print("Failed to authenticate")
            return 1
        
        result = client.get_invoice(args.invoice_id)
        print(json.dumps(result, indent=2))
        return 0
    
    elif args.command == "list":
        invoices = load_invoice_log()
        if not invoices:
            print("No invoices logged yet.")
        else:
            print(f"\n{'='*60}")
            print(f"Invoice Log ({len(invoices)} records)")
            print(f"{'='*60}")
            for inv in invoices:
                print(f"  ID: {inv['id']}")
                print(f"  Client: {inv['email']}")
                print(f"  Package: {inv['package']} — ${inv['amount']:.2f}")
                print(f"  Status: {inv['status']}")
                print(f"  Created: {inv['created_at']}")
                print(f"  {'-'*40}")
        return 0
    
    elif args.command == "packages":
        print("\n" + "=" * 60)
        print(f"{SERVICE_NAME} — Service Packages")
        print("=" * 60)
        for key, pkg in PACKAGES.items():
            print(f"\n📦 {pkg['name']} ({key})")
            print(f"   Price: ${pkg['price']:.2f} {pkg['currency']}")
            print(f"   {pkg['description']}")
        print("\n" + "=" * 60)
        return 0
    
    elif args.command == "webhook":
        if args.file:
            event = json.loads(Path(args.file).read_text())
        else:
            event = json.loads(sys.stdin.read())
        
        event_type = event.get("event_type", "unknown")
        resource = event.get("resource", {})
        
        print(f"Webhook Event: {event_type}")
        
        if "PAYMENT" in event_type.upper():
            invoice_id = resource.get("invoice_id", resource.get("id", "unknown"))
            state = resource.get("state", resource.get("status", "unknown"))
            
            print(f"Payment update — Invoice: {invoice_id}, State: {state}")
            
            if state.upper() in ("PAID", "COMPLETED", "CAPTURED"):
                print("✅ Payment received! Proceed with service delivery.")
                # Log payment confirmation
                record = {
                    "invoice_id": invoice_id,
                    "event": event_type,
                    "status": "paid",
                    "processed_at": datetime.now().isoformat(),
                }
                log_invoice(record)
        else:
            print(f"Unhandled event type: {event_type}")
        
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
