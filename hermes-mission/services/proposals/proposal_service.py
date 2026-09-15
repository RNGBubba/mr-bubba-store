#!/usr/bin/env python3
"""
Full service orchestrator for Proposal Writing Service.
Combines proposal generation, email delivery, and invoicing.

Usage:
    python3 proposal_service.py --full-flow \
        --client "Acme Corp" \
        --project "Data Dashboard" \
        --scope "Build interactive BI dashboard" \
        --timeline "3 weeks" \
        --budget "$2,500" \
        --email "client@acme.com" \
        --tier standard
"""

import argparse
import json
import os
import sys
from datetime import datetime

from generate_proposal import generate_proposal, generate_proposal_content
from agentmail_responder import send_reply, generate_auto_reply
from paypal_invoicing import create_invoice, PRICING_TIERS, validate_amount

SERVICE_NAME = "Mr Bubba Services"
SERVICE_EMAIL = os.environ.get("AGENTMAIL_EMAIL", "mrbubba@agentmail.to")


def run_full_flow(client_name: str, project_title: str, scope: str,
                  timeline: str, budget: str, email: str, tier: str = "standard",
                  notes: str = "", output_format: str = "pdf") -> dict:
    """Run the full proposal service flow."""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "client": client_name,
        "project": project_title,
        "steps": {}
    }
    
    # Step 1: Generate proposal
    print(f"[1/4] Generating {tier} proposal for {client_name}...")
    output_dir = "/home/vboxuser/mr-bubba-mission/services/proposals/output"
    proposal_result = generate_proposal(
        client_name=client_name,
        project_title=project_title,
        scope=scope,
        timeline=timeline,
        budget=budget,
        notes=notes,
        output_format=output_format,
        output_dir=output_dir
    )
    results["steps"]["generate_proposal"] = proposal_result
    
    if proposal_result["files"]:
        print(f"  ✓ Generated: {', '.join(proposal_result['files'])}")
    else:
        print(f"  ⚠ No files generated: {proposal_result.get('warning', 'unknown')}")
    
    # Step 2: Send confirmation email
    print(f"[2/4] Sending confirmation email to {email}...")
    subject = f"Your Proposal Request Received — {project_title}"
    body = f"""
    <html>
    <body style="font-family: Calibri, Arial, sans-serif; color: #333;">
        <p>Hi {client_name},</p>
        <p>Thank you for choosing <strong>{SERVICE_NAME}</strong> for your 
        <em>{project_title}</em> project!</p>
        <p>We've received your requirements and are preparing your custom proposal. 
        You'll receive it within {timeline} as discussed.</p>
        <p><strong>Project Summary:</strong></p>
        <ul>
            <li><strong>Project:</strong> {project_title}</li>
            <li><strong>Scope:</strong> {scope}</li>
            <li><strong>Timeline:</strong> {timeline}</li>
            <li><strong>Investment:</strong> {budget}</li>
            <li><strong>Service Tier:</strong> {tier.title()}</li>
        </ul>
        <p>If you have any questions in the meantime, simply reply to this email.</p>
        <p>Best regards,<br>The {SERVICE_NAME} Team</p>
    </body>
    </html>
    """
    email_result = send_reply(email, subject, body)
    results["steps"]["send_email"] = email_result
    print(f"  ✓ Confirmation sent")
    
    # Step 3: Generate invoice
    print(f"[3/4] Creating PayPal invoice...")
    tier_price = PRICING_TIERS.get(tier, PRICING_TIERS["standard"])["price"]
    invoice_result = create_invoice(
        to_email=email,
        amount=tier_price,
        description=f"{PRICING_TIERS[tier]['name']} — {project_title}",
        service_type=tier
    )
    results["steps"]["create_invoice"] = invoice_result
    print(f"  ✓ Invoice created: {invoice_result.get('invoice_id', 'N/A')}")
    
    # Step 4: Final summary
    print(f"[4/4] Flow complete!")
    content = generate_proposal_content(client_name, project_title, scope, timeline, budget, notes)
    results["proposal_id"] = content["proposal_id"]
    results["invoice_id"] = invoice_result.get("invoice_id")
    results["status"] = "complete"
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Full Proposal Service Flow")
    parser.add_argument("--full-flow", action="store_true", help="Run complete service flow")
    parser.add_argument("--client", help="Client/company name")
    parser.add_argument("--project", help="Project title")
    parser.add_argument("--scope", help="Project scope")
    parser.add_argument("--timeline", help="Estimated timeline")
    parser.add_argument("--budget", help="Project budget")
    parser.add_argument("--email", help="Client email")
    parser.add_argument("--tier", choices=list(PRICING_TIERS.keys()), default="standard")
    parser.add_argument("--notes", default="", help="Additional notes")
    parser.add_argument("--output-format", choices=["pdf", "docx", "both"], default="pdf")
    
    args = parser.parse_args()
    
    if args.full_flow:
        required = ["client", "project", "scope", "timeline", "budget", "email"]
        missing = [f"--{r}" for r in required if not getattr(args, r)]
        if missing:
            print(f"ERROR: Missing required args: {', '.join(missing)}")
            sys.exit(1)
        
        results = run_full_flow(
            client_name=args.client,
            project_title=args.project,
            scope=args.scope,
            timeline=args.timeline,
            budget=args.budget,
            email=args.email,
            tier=args.tier,
            notes=args.notes,
            output_format=args.output_format
        )
        print("\n" + "="*60)
        print("SERVICE FLOW COMPLETE")
        print("="*60)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
