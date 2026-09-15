#!/usr/bin/env python3
"""
Mr Bubba Services - Website Builder Orchestrator
Main entry point that ties together the full pipeline:
1. Accept business info (from email or CLI)
2. Build the website
3. Deploy to GitHub Pages
4. Send preview to client
5. Handle payment
6. Confirm and go live

Usage:
  python3 orchestrator.py --business-name "ABC Plumbing" --category plumbing --city "Dallas" --state TX --client-email "client@example.com"
  python3 orchestrator.py --config business.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"
OUTPUT_DIR = SCRIPT_DIR / "output"

# Add scripts to path
sys.path.insert(0, str(SCRIPT_DIR))
from build_site import build_site, deploy_to_github_pages, DEFAULT_BUSINESS
from payment import generate_paypal_invoice, generate_paypal_buy_now_link, generate_invoice_email
from deploy import deploy_site


def run_pipeline(config: dict, auto_deploy: bool = False, send_email: bool = False) -> dict:
    """
    Run the full website builder pipeline.
    
    Args:
        config: Business info dict
        auto_deploy: Whether to auto-deploy to GitHub Pages
        send_email: Whether to send email to client (requires AgentMail setup)
    
    Returns:
        dict with pipeline results
    """
    results = {
        "business_name": config.get("business_name", ""),
        "steps": [],
        "success": False,
        "preview_url": "",
        "live_url": "",
        "payment_link": "",
    }
    
    # Step 1: Build the website
    print("\n" + "="*60)
    print("🔨 STEP 1: Building Website")
    print("="*60)
    
    repo_name = config["business_name"].lower().replace(" ", "-").replace("&", "and")
    output_path = OUTPUT_DIR / repo_name
    
    try:
        build_site(config, output_path)
        results["steps"].append({"step": "build", "status": "success", "path": str(output_path)})
        print(f"✅ Website built: {output_path}")
    except Exception as e:
        results["steps"].append({"step": "build", "status": "failed", "error": str(e)})
        print(f"❌ Build failed: {e}")
        return results
    
    # Step 2: Deploy to GitHub Pages (if auto_deploy)
    if auto_deploy:
        print("\n" + "="*60)
        print("🚀 STEP 2: Deploying to GitHub Pages")
        print("="*60)
        
        try:
            deploy_result = deploy_site(output_path, repo_name, config.get("cname", ""))
            if deploy_result.get("success"):
                results["steps"].append({"step": "deploy", "status": "success", "url": deploy_result["url"]})
                results["live_url"] = deploy_result["url"]
                results["preview_url"] = deploy_result["url"]
                print(f"✅ Deployed: {deploy_result['url']}")
            else:
                results["steps"].append({"step": "deploy", "status": "failed", "error": deploy_result.get("error", "")})
                print(f"⚠️ Deploy issue: {deploy_result.get('error', 'unknown')}")
        except Exception as e:
            results["steps"].append({"step": "deploy", "status": "failed", "error": str(e)})
            print(f"❌ Deploy failed: {e}")
    else:
        # Preview URL (local or GitHub Pages after manual deploy)
        results["preview_url"] = f"https://RNGBubba.github.io/{repo_name}"
        results["steps"].append({"step": "deploy", "status": "skipped", "note": "Use --auto-deploy to deploy automatically"})
        print("⏭️  Deploy skipped (use --auto-deploy)")
    
    # Step 3: Generate payment link
    print("\n" + "="*60)
    print("💳 STEP 3: Generating Payment Link")
    print("="*60)
    
    client_name = config.get("client_name", config.get("business_name", "Client"))
    client_email = config.get("email", "")
    
    payment_link = generate_paypal_buy_now_link(client_name, client_email, config["business_name"])
    results["payment_link"] = payment_link
    results["steps"].append({"step": "payment_link", "status": "success", "link": payment_link})
    print(f"✅ Payment link: {payment_link}")
    
    # Step 4: Generate invoice email
    print("\n" + "="*60)
    print("📧 STEP 4: Generating Invoice Email")
    print("="*60)
    
    invoice = generate_paypal_invoice(client_name, client_email, config["business_name"])
    invoice_email = generate_invoice_email(invoice)
    results["invoice_email"] = invoice_email
    results["steps"].append({"step": "invoice_email", "status": "success"})
    print("✅ Invoice email generated")
    
    # Save results
    results_path = output_path / "pipeline-results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n📄 Results saved: {results_path}")
    
    results["success"] = True
    return results


def main():
    parser = argparse.ArgumentParser(description="Mr Bubba Website Builder - Full Pipeline")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--business-name", help="Business name")
    parser.add_argument("--category", help="Business category")
    parser.add_argument("--city", help="City")
    parser.add_argument("--state", default="", help="State")
    parser.add_argument("--address", default="", help="Address")
    parser.add_argument("--phone", default="", help="Phone")
    parser.add_argument("--email", default="", help="Client email")
    parser.add_argument("--client-name", default="", help="Client contact name")
    parser.add_argument("--auto-deploy", action="store_true", help="Auto-deploy to GitHub Pages")
    parser.add_argument("--send-email", action="store_true", help="Send email to client")
    args = parser.parse_args()
    
    # Load config
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # CLI overrides
    for key in ["business_name", "category", "city", "state", "address", "phone", "email", "client_name"]:
        val = getattr(args, key, None)
        if val:
            config[key] = val
    
    # Validate
    required = ["business_name", "category", "city"]
    missing = [f for f in required if not config.get(f)]
    if missing:
        print(f"Missing required: {', '.join(missing)}")
        sys.exit(1)
    
    # Run pipeline
    results = run_pipeline(config, auto_deploy=args.auto_deploy, send_email=args.send_email)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PIPELINE SUMMARY")
    print("="*60)
    print(f"Business: {results['business_name']}")
    print(f"Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")
    print(f"Preview: {results.get('preview_url', 'N/A')}")
    print(f"Payment: {results.get('payment_link', 'N/A')}")
    print("="*60)


if __name__ == "__main__":
    main()
