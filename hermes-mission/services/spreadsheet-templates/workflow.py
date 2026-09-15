#!/usr/bin/env python3
"""
End-to-end workflow for the Spreadsheet Template Builder service.
Orchestrates: receive request → generate template → deliver → invoice.

Usage:
    python3 workflow.py --request '{"client_email": "client@example.com", "description": "budget tracking", "tier": "standard"}'
    python3 workflow.py --interactive
"""

import json
import sys
import os
import argparse
from datetime import datetime

# Add service directory to path
SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SERVICE_DIR)

from spreadsheet_builder import generate_template, parse_client_description
from paypal_invoice import create_mock_invoice, PRICING
from automail_responder import generate_response, send_response


def process_client_request(client_email, description, tier='standard', client_name='Valued Client'):
    """Process a complete client request end-to-end."""
    
    print("=" * 60)
    print("  Mr Bubba Services - Template Order Processing")
    print("=" * 60)
    print(f"\n📧 Client: {client_email}")
    print(f"📝 Description: {description}")
    print(f"💰 Tier: {tier}")
    
    # Step 1: Detect template type
    template_type, config = parse_client_description(description)
    config['title'] = f"Custom {template_type.title()} Template"
    print(f"\n📊 Detected template: {template_type.title()}")
    
    # Step 2: Generate the template
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"{template_type}_{timestamp}.xlsx"
    output_path = os.path.join(SERVICE_DIR, 'output', output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        generate_template(template_type, config, output_path)
        print(f"✓ Template generated: {output_path}")
    except Exception as e:
        print(f"✗ Template generation failed: {e}")
        return False
    
    # Step 3: Create invoice
    pricing = PRICING.get(tier, PRICING['standard'])
    invoice = create_mock_invoice(
        client_email=pricing['description'],
        amount=pricing['amount'],
        description=pricing['description']
    )
    
    if invoice:
        print(f"✓ Invoice created: {invoice['id']} (${pricing['amount']})")
    
    # Step 4: Compose delivery email
    delivery_subject = f"Your Custom {template_type.title()} Template is Ready!"
    delivery_body = f"""Hi {client_name},

Thank you for your order! Your custom spreadsheet template has been generated.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TEMPLATE DETAILS:
• Type: {template_type.title()}
• File: {output_filename}
• Tier: {tier.title()}
• Price: ${pricing['amount']}

📎 ATTACHMENT:
The template file is attached to this email.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 GETTING STARTED:
1. Open the file in Microsoft Excel or Google Sheets
2. Fill in the yellow-highlighted input cells
3. Green-highlighted cells contain formulas — do not edit
4. Summary/dashboard sheets auto-populate from your data

📋 INVOICE:
An invoice for ${pricing['amount']} has been sent via PayPal.
Payment link: [PayPal Invoice #{invoice['id'] if invoice else 'PENDING'}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 REVISIONS:
Reply to this email if you need modifications.
• Standard: 1 revision ($10)
• Premium/Enterprise: 1 free revision included

Best regards,
Mr Bubba Services Team
mrbubba@agentmail.to
"""
    
    # Step 5: Send delivery email
    print(f"\n📤 Sending delivery email to {client_email}...")
    success, result = send_response(client_email, delivery_subject, delivery_body)
    
    if success:
        print(f"✓ Delivery email sent!")
    else:
        print(f"✗ Email send failed: {result}")
    
    # Summary
    print("\n" + "=" * 60)
    print("  Order Processing Complete")
    print("=" * 60)
    print(f"  Template: {output_path}")
    print(f"  Invoice:  {invoice['id'] if invoice else 'FAILED'} (${pricing['amount']})")
    print(f"  Email:    {'Sent' if success else 'Failed'}")
    print("=" * 60)
    
    return {
        'template_type': template_type,
        'template_path': output_path,
        'invoice_id': invoice['id'] if invoice else None,
        'amount': pricing['amount'],
        'email_sent': success,
    }


def interactive_workflow():
    """Run workflow interactively."""
    print("\n📝 Enter client request details:\n")
    
    client_email = input("Client email: ").strip()
    description = input("Describe your needs: ").strip()
    
    print("\nSelect tier:")
    print("  1. Standard ($25)")
    print("  2. Premium ($35)")
    print("  3. Enterprise ($50)")
    tier_choice = input("Choice [1]: ").strip() or "1"
    
    tier_map = {"1": "standard", "2": "premium", "3": "enterprise"}
    tier = tier_map.get(tier_choice, "standard")
    
    client_name = input("Client name [Valued Client]: ").strip() or "Valued Client"
    
    return process_client_request(client_email, description, tier, client_name)


def main():
    parser = argparse.ArgumentParser(description='Spreadsheet Template Workflow')
    parser.add_argument('--request', '-r', help='JSON request string')
    parser.add_argument('--interactive', '-i', action='store_true')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_workflow()
    elif args.request:
        req = json.loads(args.request)
        process_client_request(
            req.get('client_email', ''),
            req.get('description', ''),
            req.get('tier', 'standard'),
            req.get('client_name', 'Valued Client')
        )
    else:
        # Demo mode
        print("Running demo workflow...\n")
        process_client_request(
            client_email="demo@example.com",
            description="I need to track my monthly expenses and budget categories",
            tier="standard",
            client_name="Demo Client"
        )


if __name__ == '__main__':
    main()
