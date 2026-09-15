#!/usr/bin/env python3
"""
PayPal Invoicing Service for Proposal Writing
Creates and sends PayPal invoices for proposal services ($50-$200 range).

Requires: requests library
Webhook configured for Discord notifications.

Usage:
    python3 paypal_invoicing.py --create --to "client@example.com" --amount 150.00 \
        --description "Business Proposal - Project X" --service "standard"
    python3 paypal_invoicing.py --list
    python3 paypal_invoicing.py --status <invoice_id>
"""

import argparse
import json
import os
import sys
import base64
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"  # Sandbox for testing
# PAYPAL_BASE_URL = "https://api-m.paypal.com"  # Production

# Service Configuration
SERVICE_EMAIL = os.environ.get("AGENTMAIL_EMAIL", "mrbubba@agentmail.to")
SERVICE_NAME = "Mr Bubba Services"

# Pricing Tiers
PRICING_TIERS = {
    "basic": {"name": "Basic Proposal", "price": 50.00, "description": "Single-page proposal, 5-day delivery"},
    "standard": {"name": "Standard Proposal", "price": 100.00, "description": "3-5 page proposal, 3-day delivery"},
    "comprehensive": {"name": "Comprehensive Proposal", "price": 175.00, "description": "Full proposal with research, 2-day delivery"},
    "premium": {"name": "Premium Proposal", "price": 200.00, "description": "Enterprise proposal + presentation, rush delivery"},
    "rush_surcharge": {"name": "Rush Delivery Surcharge", "price": 50.00, "description": "24-48 hour expedited delivery"},
}


def get_paypal_access_token() -> str:
    """Obtain OAuth2 access token from PayPal."""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        return ""
    
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            headers=headers,
            data={"grant_type": "client_credentials"},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("access_token", "")
    except requests.RequestException as e:
        print(f"Error obtaining PayPal token: {e}")
        return ""


def create_invoice(to_email: str, amount: float, description: str,
                   service_type: str = "standard", custom_items: list = None) -> dict:
    """Create a PayPal invoice."""
    token = get_paypal_access_token()
    
    if not token:
        # Return a mock invoice for sandbox/testing
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{abs(hash(to_email)) % 10000:04d}"
        return {
            "status": "mock_created",
            "invoice_id": invoice_id,
            "to": to_email,
            "amount": amount,
            "description": description,
            "service_type": service_type,
            "message": "PayPal credentials not configured — mock invoice created for testing"
        }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Build invoice items
    items = custom_items or []
    if not items:
        tier = PRICING_TIERS.get(service_type, PRICING_TIERS["standard"])
        items.append({
            "name": tier["name"],
            "description": description or tier["description"],
            "quantity": 1,
            "unit_amount": {
                "currency_code": "USD",
                "value": f"{amount:.2f}"
            }
        })
    
    invoice_data = {
        "detail": {
            "invoice_number": f"HDS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "reference": f"Proposal Service - {service_type}",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "currency_code": "USD",
            "note": "Thank you for choosing Mr Bubba Services!",
            "term": "Payment due upon receipt"
        },
        "invoicer": {
            "name": {
                "given_name": SERVICE_NAME
            },
            "email_address": SERVICE_EMAIL
        },
        "primary_recipients": [{
            "billing_info": {
                "email_address": to_email
            }
        }],
        "items": items,
        "configuration": {
            "allow_tip": False,
            "tax_calculated_after_discount": True,
            "tax_inclusive": False
        }
    }
    
    try:
        # Create invoice
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/invoicing/invoices",
            headers=headers,
            json=invoice_data,
            timeout=30
        )
        response.raise_for_status()
        invoice_result = response.json()
        
        # Send invoice
        invoice_id = invoice_result.get("id", "")
        if invoice_id:
            send_response = requests.post(
                f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}/send",
                headers=headers,
                json={},
                timeout=30
            )
            send_response.raise_for_status()
            invoice_result["status"] = "sent"
            return invoice_result
        
        return invoice_result
        
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


def list_invoices(page: int = 1, page_size: int = 10) -> dict:
    """List invoices from PayPal."""
    token = get_paypal_access_token()
    
    if not token:
        return {"status": "mock", "invoices": [], "message": "PayPal not configured"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{PAYPAL_BASE_URL}/v2/invoicing/invoices?page={page}&page_size={page_size}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


def get_invoice_status(invoice_id: str) -> dict:
    """Get status of a specific invoice."""
    token = get_paypal_access_token()
    
    if not token:
        return {"status": "mock", "invoice_id": invoice_id, "state": "UNKNOWN"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


def validate_amount(amount: float) -> bool:
    """Validate invoice amount is within service range ($50-$200)."""
    return 50.0 <= amount <= 250.0  # 250 to account for rush surcharge


def main():
    parser = argparse.ArgumentParser(description="PayPal Invoicing for Proposal Services")
    parser.add_argument("--create", action="store_true", help="Create a new invoice")
    parser.add_argument("--to", help="Client email address")
    parser.add_argument("--amount", type=float, help="Invoice amount (USD)")
    parser.add_argument("--description", default="Business Proposal Services", help="Invoice description")
    parser.add_argument("--service", choices=list(PRICING_TIERS.keys()), default="standard",
                        help="Service tier")
    parser.add_argument("--list", dest="list_invoices", action="store_true", help="List recent invoices")
    parser.add_argument("--status", metavar="INVOICE_ID", help="Check invoice status")
    
    args = parser.parse_args()
    
    if args.create:
        if not args.to:
            print("ERROR: --to email required")
            sys.exit(1)
        
        amount = args.amount or PRICING_TIERS[args.service]["price"]
        
        if not validate_amount(amount):
            print(f"WARNING: Amount ${amount:.2f} outside typical range ($50-$200)")
        
        result = create_invoice(args.to, amount, args.description, args.service)
        print(json.dumps(result, indent=2))
    
    elif args.list_invoices:
        result = list_invoices()
        print(json.dumps(result, indent=2))
    
    elif args.status:
        result = get_invoice_status(args.status)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
