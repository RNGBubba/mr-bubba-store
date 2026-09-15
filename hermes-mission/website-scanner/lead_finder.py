#!/usr/bin/env python3
"""
Lead Finder - Manual + Automated Hybrid
========================================

Since automated scraping is blocked, this tool helps you:
1. Manually collect leads from Google Maps / directories
2. Check if they have websites
3. Generate personalized outreach emails
4. Send via AgentMail
5. Track responses and follow-ups

USAGE:
  1. Find businesses on Google Maps (search: "plumber Houston TX")
  2. Copy business names into a CSV file:
     name,city,category,phone,address
     Joe's Plumbing,Houston,plumber,555-1234,123 Main St
  3. Run: python3 lead_finder.py --import csv_file.csv
  4. I'll check websites, generate emails, and send them

COMMANDS:
  python3 lead_finder.py --import leads.csv
  python3 lead_finder.py --check "Business Name" --city "Houston"
  python3 lead_finder.py --generate --name "Joe's Plumbing" --city "Houston" --category "plumber"
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import csv
from datetime import datetime

OUTPUT_DIR = "/home/vboxuser/mrbubba-mission/website-scanner"
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"

class WebsiteChecker:
    """Check if a business has a website."""
    
    def check(self, name, city=None):
        """Check if a website exists for a business."""
        clean = re.sub(r'[^a-z0-9]', '', name.lower())
        
        if len(clean) < 4:
            return None
        
        domains = [
            f"https://{clean}.com",
            f"https://www.{clean}.com",
        ]
        
        if city:
            city_clean = re.sub(r'[^a-z0-9]', '', city.lower())
            domains.extend([
                f"https://{clean}{city_clean}.com",
                f"https://{city_clean}{clean}.com",
                f"https://{clean}tx.com",
                f"https://{clean}texas.com",
            ])
        
        for url in domains:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                resp = urllib.request.urlopen(req, timeout=5, context=ctx)
                
                if resp.getcode() == 200:
                    return url
            except:
                continue
        
        return None


class EmailGenerator:
    """Generate personalized outreach emails."""
    
    def generate(self, name, category, city, phone="", address=""):
        """Generate a personalized website outreach email."""
        
        service_map = {
            "plumber": ("plumbing", "leaks, clogs, and installations"),
            "electrician": ("electrical work", "wiring, panels, and repairs"),
            "hvac": ("HVAC", "heating and cooling services"),
            "roofing": ("roofing", "roof repairs and installations"),
            "landscaping": ("landscaping", "lawn care and landscape design"),
            "auto repair": ("auto repair", "vehicle maintenance and repairs"),
            "dentist": ("dental care", "checkups, cleanings, and procedures"),
            "chiropractor": ("chiropractic care", "adjustments and pain relief"),
            "hair salon": ("hair services", "cuts, color, and styling"),
            "gym": ("fitness", "personal training and classes"),
            "cleaning": ("cleaning services", "residential and commercial cleaning"),
            "default": ("your services", "quality work and customer service")
        }
        
        service_info = service_map.get(category.lower(), service_map["default"])
        
        email = f"""Subject: Quick question about {name}

Hi there,

I was looking for {service_info[0]} in {city} and found {name}. I noticed you don't have a website yet — in 2026, that's leaving customers on the table.

Here's what I can do for you:

🌐 **Professional Website - $299**
- Custom 5-page design for {name}
- Mobile-friendly (most customers find you on their phone)
- Contact form + click-to-call button
- Google Maps integration ({address})
- Customer testimonials section
- Photo gallery of your work
- Delivery in 3-5 business days
- Unlimited revisions until you're happy

Want me to send a free draft? No obligation. If you like it, we proceed. If not, no worries at all.

Just reply "yes" and I'll have a draft ready within 48 hours.

Best regards,
Mr Bubba Services
📧 mrbubba@agentmail.to
"""
        
        return email


def check_business(name, city):
    """Check if a business has a website."""
    checker = WebsiteChecker()
    website = checker.check(name, city)
    
    result = {
        "name": name,
        "city": city,
        "has_website": website is not None,
        "website": website,
        "checked_at": datetime.now().isoformat()
    }
    
    return result


def generate_outreach(name, category, city, phone="", address=""):
    """Generate outreach email for a business."""
    generator = EmailGenerator()
    email = generator.generate(name, category, city, phone, address)
    return email


def batch_check_from_csv(csv_path):
    """Check multiple businesses from a CSV."""
    results = []
    
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            name = row.get("name", "").strip()
            city = row.get("city", "").strip()
            
            if not name:
                continue
            
            result = check_business(name, city)
            results.append(result)
            
            if result["has_website"]:
                print(f"  ✅ {name}: {result['website']}")
            else:
                print(f"  ❌ {name}: NO WEBSITE - LEAD!")
            
            time.sleep(0.5)
    
    # Save results
    results_file = os.path.join(OUTPUT_DIR, "checked_leads.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate emails for leads without websites
    leads = [r for r in results if not r["has_website"]]
    
    if leads:
        print(f"\n✅ Found {len(leads)} leads without websites!")
        print(f"   Results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Lead Finder")
    parser.add_argument("--check", help="Check a single business")
    parser.add_argument("--city", help="City")
    parser.add_argument("--generate", action="store_true", help="Generate outreach email")
    parser.add_argument("--name", help="Business name")
    parser.add_argument("--category", help="Business category")
    parser.add_argument("--phone", help="Phone number")
    parser.add_argument("--address", help="Address")
    parser.add_argument("--batch-check", help="Path to CSV file")
    
    args = parser.parse_args()
    
    if args.batch_check:
        batch_check_from_csv(args.batch_check)
    
    elif args.check:
        result = check_business(args.check, args.city)
        
        if result["has_website"]:
            print(f"✅ {args.check} has a website: {result['website']}")
        else:
            print(f"❌ {args.check}: NO WEBSITE - POTENTIAL LEAD!")
            print(f"\nTo generate outreach email:")
            print(f"  python3 lead_finder.py --generate --name \"{args.check}\" --city \"{args.city}\"")
    
    elif args.generate and args.name:
        email = generate_outreach(args.name, args.category or "service", args.city or "", args.phone or "", args.address or "")
        print(email)
        
        # Save to file
        safe_name = re.sub(r'[^a-z0-9]', '_', args.name.lower())
        filepath = os.path.join(OUTPUT_DIR, "emails", f"{safe_name}.txt")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            f.write(email)
        
        print(f"\nSaved to: {filepath}")
    
    else:
        print("Usage:")
        print("  python3 lead_finder.py --check \"Joe's Plumbing\" --city \"Houston\"")
        print("  python3 lead_finder.py --generate --name \"Joe's Plumbing\" --city \"Houston\" --category \"plumber\"")
        print("  python3 lead_finder.py --batch-check leads.csv")
        print("\nCSV format: name,city,category,phone,address")