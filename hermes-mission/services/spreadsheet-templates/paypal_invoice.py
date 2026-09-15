#!/usr/bin/env python3
"""
PayPal Invoicing for Spreadsheet Template Builder Service.
Creates and sends PayPal invoices for template orders ($25-50 range).

Usage:
    python3 paypal_invoice.py --create --amount 25 --client client@example.com --description "Standard Budget Template"
    python3 paypal_invoice.py --list    # List recent invoices
    python3 paypal_invoice.py --check   # Check payment status
"""

import json
import sys
import os
import argparse
from datetime import datetime

import requests

# PayPal configuration
# Note: Use sandbox for testing, live for production
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_ENVIRONMENT = os.environ.get('PAYPAL_ENVIRONMENT', 'sandbox')

if PAYPAL_ENVIRONMENT == 'live':
    PAYPAL_BASE_URL = 'https://api.paypal.com'
else:
    PAYPAL_BASE_URL = 'https://api.sandbox.paypal.com'

INBOX_EMAIL = 'mrbubba@agentmail.to'
SERVICE_NAME = 'Mr Bubba Services - Custom Spreadsheet Templates'

# Pricing tiers
PRICING = {
    'standard': {'amount': 25, 'description': 'Standard Template (single sheet, basic formulas)'},
    'premium': {'amount': 35, 'description': 'Premium Template (multi-sheet, advanced formulas, dashboard)'},
    'enterprise': {'amount': 50, 'description': 'Enterprise Template (multi-sheet, VBA automation, custom branding)'},
}


def get_paypal_token():
    """Get PayPal OAuth access token."""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    
    auth = (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post(url, auth=auth, data=data, timeout=30)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting PayPal token: {e}")
        return None


def create_invoice(client_email, amount, description, client_name='Valued Client'):
    """Create a PayPal invoice."""
    token = get_paypal_token()
    if not token:
        print("Failed to authenticate with PayPal.")
        return None
    
    url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }
    
    # Build invoice payload
    payload = {
        'detail': {
            'invoice_number': f"HDS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'reference': f"SPREADSHEET-TEMPLATE-{datetime.now().strftime('%Y%m%d')}",
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'currency_code': 'USD',
            'note': 'Thank you for your business! Your custom spreadsheet template will be delivered within 2 hours of payment.',
            'term': 'Payment is due upon receipt. Template delivery within 2 hours of payment.',
            'payment_term': {
                'term_type': 'DUE_ON_RECEIPT',
            },
        },
        'invoicer': {
            'name': {
                'given_name': 'Mr Bubba Services',
            },
            'email_address': INBOX_EMAIL,
        },
        'primary_recipients': [
            {
                'billing_info': {
                    'name': {
                        'given_name': client_name,
                    },
                    'email_address': client_email,
                },
            }
        ],
        'items': [
            {
                'name': description[:100],
                'description': description,
                'quantity': '1',
                'unit_amount': {
                    'currency_code': 'USD',
                    'value': str(amount),
                },
                'unit_of_measure': 'AMOUNT',
            }
        ],
        'configuration': {
            'allow_tip': False,
            'tax_calculated_after_discount': True,
            'tax_inclusive': False,
            'payment_term': {
                'term_type': 'DUE_ON_RECEIPT',
            },
        },
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        invoice = response.json()
        print(f"Invoice created: {invoice.get('id', 'unknown')}")
        return invoice
    except requests.exceptions.RequestException as e:
        print(f"Error creating invoice: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


def send_invoice(invoice_id):
    """Send a created PayPal invoice via email."""
    token = get_paypal_token()
    if not token:
        return False
    
    url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}/send"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'send_to_recipient': True,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        print(f"Invoice {invoice_id} sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending invoice: {e}")
        return False


def list_invoices():
    """List recent invoices from PayPal."""
    token = get_paypal_token()
    if not token:
        return None
    
    url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices?page=1&page_size=10&total_required=true"
    
    headers = {
        'Authorization': f'Bearer {token}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing invoices: {e}")
        return None


def check_invoice_status(invoice_id):
    """Check the status of a specific invoice."""
    token = get_paypal_token()
    if not token:
        return None
    
    url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}"
    
    headers = {
        'Authorization': f'Bearer {token}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking invoice: {e}")
        return None


def quick_invoice(client_email, tier='standard'):
    """Quick invoice creation using predefined tiers."""
    if tier not in PRICING:
        print(f"Invalid tier: {tier}. Available: {list(PRICING.keys())}")
        return None
    
    pricing = PRICING[tier]
    return create_invoice(client_email, pricing['amount'], pricing['description'])


def create_mock_invoice(client_email, amount, description):
    """Create a mock invoice for testing (when PayPal credentials are not configured)."""
    invoice = {
        'id': f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'status': 'DRAFT',
        'detail': {
            'invoice_number': f"HDS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'payment_term': {'term_type': 'DUE_ON_RECEIPT'},
        },
        'invoicer': {
            'email_address': INBOX_EMAIL,
        },
        'primary_recipients': [
            {'billing_info': {'email_address': client_email}}
        ],
        'items': [
            {
                'name': description[:100],
                'quantity': '1',
                'unit_amount': {'currency_code': 'USD', 'value': str(amount)},
            }
        ],
    }
    print(f"\n[MOCK MODE] Invoice created (no real PayPal API call)")
    print(f"  Invoice ID: {invoice['id']}")
    print(f"  Amount: ${amount}")
    print(f"  Client: {client_email}")
    print(f"  Description: {description}")
    return invoice


def main():
    parser = argparse.ArgumentParser(description='PayPal Invoicing for Spreadsheet Templates')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create invoice
    create_parser = subparsers.add_parser('create', help='Create a new invoice')
    create_parser.add_argument('--email', required=True, help='Client email address')
    create_parser.add_argument('--amount', type=float, required=True, help='Invoice amount (25-50)')
    create_parser.add_argument('--description', required=True, help='Invoice description')
    create_parser.add_argument('--name', default='Valued Client', help='Client name')
    create_parser.add_argument('--send', action='store_true', help='Send invoice immediately')
    create_parser.add_argument('--mock', action='store_true', help='Create mock invoice (no API call)')
    
    # Quick tier invoice
    tier_parser = subparsers.add_parser('quick', help='Quick invoice from pricing tier')
    tier_parser.add_argument('--email', required=True, help='Client email')
    tier_parser.add_argument('--tier', choices=['standard', 'premium', 'enterprise'], default='standard')
    tier_parser.add_argument('--send', action='store_true', help='Send invoice')
    tier_parser.add_argument('--mock', action='store_true', help='Mock mode')
    
    # List invoices
    subparsers.add_parser('list', help='List recent invoices')
    
    # Check status
    status_parser = subparsers.add_parser('status', help='Check invoice status')
    status_parser.add_argument('--id', required=True, help='Invoice ID')
    
    args = parser.parse_args()
    
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("⚠️  PayPal credentials not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET env vars.")
        print("   Use --mock flag for testing.\n")
    
    if args.command == 'create':
        if args.mock or not PAYPAL_CLIENT_ID:
            invoice = create_mock_invoice(args.email, args.amount, args.description)
        else:
            invoice = create_invoice(args.email, args.amount, args.description, args.name)
            if args.send and invoice:
                send_invoice(invoice['id'])
    
    elif args.command == 'quick':
        if args.mock or not PAYPAL_CLIENT_ID:
            pricing = PRICING[args.tier]
            invoice = create_mock_invoice(args.email, pricing['amount'], pricing['description'])
        else:
            invoice = quick_invoice(args.email, args.tier)
            if args.send and invoice:
                send_invoice(invoice['id'])
    
    elif args.command == 'list':
        invoices = list_invoices()
        if invoices:
            print(json.dumps(invoices, indent=2))
    
    elif args.command == 'status':
        status = check_invoice_status(args.id)
        if status:
            print(json.dumps(status, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
