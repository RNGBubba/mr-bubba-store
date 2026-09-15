#!/usr/bin/env python3
"""
Free Lead Scanner — No API Keys Required
=========================================

Scans for businesses without websites using FREE sources:
1. Yellow Pages (free directory)
2. BBB (Better Business Bureau)
3. Google search (browser fallback)

All free, no API keys needed.

Usage:
    python3 free_scanner.py --mode scan --city "Houston" --state "TX" --term "plumber" --limit 10
    python3 free_scanner.py --mode full --city "Houston" --state "TX"
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import re
import csv
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "/home/vboxuser/mrbubba-mission/website-scanner"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target cities (smaller = less competition)
CITIES = [
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"),
    ("San Antonio", "TX"), ("Fort Worth", "TX"), ("El Paso", "TX"),
    ("Miami", "FL"), ("Orlando", "FL"), ("Tampa", "FL"),
    ("Jacksonville", "FL"), ("Tallahassee", "FL"),
    ("Phoenix", "AZ"), ("Tucson", "AZ"), ("Mesa", "AZ"),
    ("Las Vegas", "NV"), ("Henderson", "NV"), ("Reno", "NV"),
    ("Denver", "CO"), ("Colorado Springs", "CO"), ("Aurora", "CO"),
    ("Portland", "OR"), ("Salem", "OR"), ("Eugene", "OR"),
    ("Seattle", "WA"), ("Spokane", "WA"), ("Tacoma", "WA"),
    ("Atlanta", "GA"), ("Augusta", "GA"), ("Columbus", "GA"),
    ("Charlotte", "NC"), ("Raleigh", "NC"), ("Greensboro", "NC"),
    ("Nashville", "TN"), ("Memphis", "TN"), ("Knoxville", "TN"),
]

BUSINESS_TYPES = [
    "plumber", "electrician", "HVAC", "roofing contractor",
    "landscaping", "auto repair shop", "dentist", "chiropractor",
    "hair salon", "nail salon", "gym", "pet groomer", "towing service",
    "pest control", "handyman", "cleaning service", "catering",
    "florist", "bakery", "coffee shop", "barber shop",
    "locksmith", "appliance repair", "carpet cleaning", "pressure washing",
    "tree service", "fence contractor", "painting contractor",
    "drywall contractor", "solar installers"
]


class YellowPagesScanner:
    """Scrape Yellow Pages for businesses."""
    
    BASE_URL = "https://www.yellowpages.com"
    
    def search(self, term, location, limit=50):
        """Search Yellow Pages."""
        businesses = []
        
        encoded_term = urllib.parse.quote(term)
        encoded_loc = urllib.parse.quote(location)
        
        for page in range(1, (limit // 10) + 1):
            url = f"{self.BASE_URL}/search?search_terms={encoded_term}&geo_location_terms={encoded_loc}&page={page}"
            
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    
                    # Parse business listings
                    listings = self.parse_listings(html)
                    businesses.extend(listings)
                    
                    print(f"    Page {page}: {len(listings)} listings")
                    
                    if len(listings) < 5:
                        break  # No more results
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                print(f"    Error on page {page}: {e}")
                break
        
        return businesses[:limit]
    
    def parse_listings(self, html):
        """Parse business listings from Yellow Pages HTML."""
        listings = []
        
        # Yellow Pages uses specific class patterns for listings
        # Look for business info patterns
        business_blocks = re.findall(
            r'<div class="v-card"[^>]*>.*?</div>\s*</div>\s*</div>',
            html,
            re.DOTALL
        )
        
        for block in business_blocks[:10]:
            business = self.parse_business_block(block)
            if business:
                listings.append(business)
        
        return listings
    
    def parse_business_block(self, html_block):
        """Parse a single business block."""
        business = {}
        
        # Name
        name_match = re.search(r'class="business-name"[^>]*>(.*?)</a>', html_block, re.DOTALL)
        if name_match:
            business["name"] = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()
        
        # Phone
        phone_match = re.search(r'class="phones phone primary"[^>]*>(.*?)</p>', html_block, re.DOTALL)
        if phone_match:
            business["phone"] = re.sub(r'<[^>]+>', '', phone_match.group(1)).strip()
        
        # Address
        street_match = re.search(r'street-address"[^>]*>(.*?)</span>', html_block, re.DOTALL)
        if street_match:
            business["street"] = re.sub(r'<[^>]+>', '', street_match.group(1)).strip()
        
        city_match = re.search(r'locality"[^>]*>(.*?)</span>', html_block, re.DOTALL)
        if city_match:
            business["city"] = re.sub(r'<[^>]+>', '', city_match.group(1)).strip().rstrip(',')
        
        state_match = re.search(r'region"[^>]*>(.*?)</span>', html_block, re.DOTALL)
        if state_match:
            business["state"] = re.sub(r'<[^>]+>', '', state_match.group(1)).strip()
        
        zip_match = re.search(r'postal-code"[^>]*>(.*?)</span>', html_block, re.DOTALL)
        if zip_match:
            business["zip"] = re.sub(r'<[^>]+>', '', zip_match.group(1)).strip()
        
        # Website URL (if they have one)
        website_match = re.search(r'href="(https?://[^"]+)"[^>]*>Website', html_block, re.DOTALL)
        if website_match:
            business["website"] = website_match.group(1)
        else:
            business["website"] = ""
        
        # Categories
        categories = re.findall(r'class="categories"[^>]*>.*?<a[^>]*>(.*?)</a>', html_block, re.DOTALL)
        business["categories"] = [re.sub(r'<[^>]+>', '', c).strip() for c in categories if c.strip()]
        
        business["source"] = "yellowpages"
        business["scanned_at"] = datetime.now().isoformat()
        
        if "name" in business and business["name"]:
            return business
        
        return None


class BBBScanner:
    """Scrape Better Business Bureau for businesses."""
    
    BASE_URL = "https://www.bbb.org"
    
    def search(self, term, location, limit=50):
        """Search BBB."""
        businesses = []
        
        encoded_term = urllib.parse.quote(term)
        encoded_loc = urllib.parse.quote(location)
        
        for page in range(1, (limit // 10) + 1):
            url = f"{self.BASE_URL}/search?find_country=USA&find_loc={encoded_loc}&find_text={encoded_term}&page={page}"
            
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    listings = self.parse_listings(html)
                    businesses.extend(listings)
                    
                    print(f"    BBB Page {page}: {len(listings)} listings")
                    
                    if len(listings) < 3:
                        break
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    BBB Error on page {page}: {e}")
                break
        
        return businesses[:limit]
    
    def parse_listings(self, html):
        """Parse BBB listings."""
        listings = []
        
        # BBB has structured data
        blocks = re.findall(
            r'<h3[^>]*class="[^"]*MuiTypography-root[^"]*"[^>]*>(.*?)</h3>',
            html,
            re.DOTALL
        )
        
        for block in blocks:
            name = re.sub(r'<[^>]+>', '', block).strip()
            if name and len(name) > 2:
                listings.append({
                    "name": name,
                    "phone": "",
                    "address": "",
                    "website": "",
                    "source": "bbb",
                    "scanned_at": datetime.now().isoformat()
                })
        
        return listings


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
            f"https://{clean.replace('and', '').replace('the', '')}.com",
        ]
        
        # Add city to domain if available
        if city:
            city_clean = re.sub(r'[^a-z0-9]', '', city.lower())
            domains.append(f"https://{clean}{city_clean}.com")
            domains.append(f"https://{city_clean}{clean}.com")
        
        for url in domains:
            try:
                import ssl
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


class BusinessResearcher:
    """Research a business to find email and other info."""
    
    def __init__(self):
        self.results_dir = os.path.join(OUTPUT_DIR, "results")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def research(self, business):
        """Full research on a business."""
        print(f"  Researching: {business['name']}...")
        
        research = {
            "has_website": False,
            "website_url": None,
            "email": None,
            "phone": business.get("phone", ""),
            "address": business.get("address", ""),
            "notes": []
        }
        
        # Check for website
        website = WebsiteChecker().check(
            business["name"],
            business.get("city")
        )
        
        if website:
            research["has_website"] = True
            research["website_url"] = website
            research["notes"].append(f"Found: {website}")
            return research  # Skip if they have a website
        
        # Try to find email
        email = self.find_email(business)
        if email:
            research["email"] = email
        
        # Save research
        safe_name = re.sub(r'[^a-z0-9]', '_', business["name"].lower())
        filepath = os.path.join(self.results_dir, f"{safe_name}.json")
        
        with open(filepath, "w") as f:
            json.dump({**business, **research}, f, indent=2)
        
        return research
    
    def find_email(self, business):
        """Try to find a business email."""
        name = business.get("name", "").lower().replace("'", "").replace(",", "")
        clean_name = re.sub(r'[^a-z0-9]', '', name)
        
        if len(clean_name) < 4:
            return None
        
        # Common business email patterns
        patterns = [
            f"info@{clean_name}.com",
            f"hello@{clean_name}.com",
            f"contact@{clean_name}.com",
            f"support@{clean_name}.com",
            f"admin@{clean_name}.com",
        ]
        
        # For now, return None - would need email verification service
        # Could use: hunter.io, snov.io, clearbit (some have free tiers)
        return None


def scan_free(city, state, term, limit=20):
    """Scan for businesses without websites using free sources."""
    print(f"\n{'='*50}")
    print(f"SCANNING: {term} in {city}, {state}")
    print(f"{'='*50}")
    
    location = f"{city}, {state}"
    
    # Scan sources
    yp_scanner = YellowPagesScanner()
    bbb_scanner = BBBScanner()
    researcher = BusinessResearcher()
    
    all_businesses = []
    
    # Yellow Pages
    print(f"\n  Scanning Yellow Pages...")
    try:
        yp_results = yp_scanner.search(term, location, limit=limit)
        print(f"  Found {len(yp_results)} on Yellow Pages")
        all_businesses.extend(yp_results)
    except Exception as e:
        print(f"  Yellow Pages error: {e}")
    
    # BBB
    print(f"\n  Scanning BBB...")
    try:
        bbb_results = bbb_scanner.search(term, location, limit=limit)
        print(f"  Found {len(bbb_results)} on BBB")
        all_businesses.extend(bbb_results)
    except Exception as e:
        print(f"  BBB error: {e}")
    
    # Filter and research
    no_website_leads = []
    seen_names = set()
    
    for biz in all_businesses:
        name = biz.get("name", "")
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        
        # Research
        research = researcher.research(biz)
        
        if not research["has_website"]:
            no_website_leads.append({
                **biz,
                "research": research,
                "status": "lead",
                "added_at": datetime.now().isoformat()
            })
    
    print(f"\n✅ Leads without websites: {len(no_website_leads)}")
    
    # Save leads
    leads_file = os.path.join(OUTPUT_DIR, "leads.json")
    
    # Append to existing leads
    existing = []
    if os.path.exists(leads_file):
        with open(leads_file, "r") as f:
            existing = json.load(f)
    
    # Add new leads
    existing.extend(no_website_leads)
    
    # Deduplicate by name
    seen = set()
    unique = []
    for lead in existing:
        name = lead.get("name", "")
        if name and name not in seen:
            seen.add(name)
            unique.append(lead)
    
    with open(leads_file, "w") as f:
        json.dump(unique, f, indent=2)
    
    print(f"✅ Total leads saved: {len(unique)}")
    
    return no_website_leads


def scan_all_terms(city, state, limit_per_term=5):
    """Scan all business types for a city."""
    all_leads = []
    
    for term in BUSINESS_TYPES:
        try:
            leads = scan_free(city, state, term, limit_per_term)
            all_leads.extend(leads)
            time.sleep(2)  # Rate limit between searches
        except Exception as e:
            print(f"Error scanning {term}: {e}")
            continue
    
    print(f"\n{'='*50}")
    print(f"COMPLETE: Found {len(all_leads)} leads in {city}, {state}")
    print(f"{'='*50}")
    
    return all_leads


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Free Lead Scanner")
    parser.add_argument("--mode", choices=["scan", "full", "city"], default="scan")
    parser.add_argument("--city", help="City to scan")
    parser.add_argument("--state", help="State abbreviation")
    parser.add_argument("--term", help="Business type to scan")
    parser.add_argument("--limit", type=int, default=10, help="Limit per search")
    
    args = parser.parse_args()
    
    if args.mode == "scan":
        if not args.city or not args.state or not args.term:
            print("Usage: python3 free_scanner.py --mode scan --city 'Houston' --state TX --term plumber")
            sys.exit(1)
        scan_free(args.city, args.state, args.term, args.limit)
    
    elif args.mode == "city":
        if not args.city or not args.state:
            print("Usage: python3 free_scanner.py --mode city --city 'Houston' --state TX")
            sys.exit(1)
        scan_all_terms(args.city, args.state, limit_per_term=3)
    
    elif args.mode == "full":
        # Scan multiple cities
        total = 0
        for city, state in CITIES[:5]:
            leads = scan_all_terms(city, state, limit_per_term=2)
            total += len(leads)
            time.sleep(5)
        
        print(f"\n{'='*50}")
        print(f"SCAN COMPLETE: {total} total leads found")
        print(f"{'='*50}")