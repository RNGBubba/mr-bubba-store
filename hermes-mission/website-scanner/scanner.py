#!/usr/bin/env python3
"""
Website Scanner & Outreach Pipeline
====================================

Scans for businesses without websites, researches them,
and sends personalized outreach emails.

Usage:
    python3 scanner.py --mode scan
    python3 scanner.py --mode research
    python3 scanner.py --mode outreach
    python3 scanner.py --mode full
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import socket
import ssl
import re
import csv
from datetime import datetime, timedelta

# Configuration
YELP_API_KEY = os.environ.get("YELP_API_KEY", "")
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"

# Search configuration
SEARCH_TERMS = [
    "restaurant", "plumber", "electrician", "HVAC", "roofing",
    "landscaping", "auto repair", "dentist", "chiropractor",
    "hair salon", "nail salon", "gym", "pet grooming", "towing",
    "pest control", "handyman", "cleaning service", "catering"
]

SEARCH_LOCATIONS = [
    "Houston TX", "Dallas TX", "Austin TX", "San Antonio TX",
    "Miami FL", "Orlando FL", "Tampa FL", "Jacksonville FL",
    "Phoenix AZ", "Tucson AZ", "Las Vegas NV", "Reno NV",
    "Denver CO", "Colorado Springs CO", "Portland OR", "Seattle WA"
]

class YelpScanner:
    """Scan Yelp for businesses without websites."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.yelp.com/v3"
    
    def search_businesses(self, term, location, limit=50):
        """Search Yelp for businesses."""
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/businesses/search"
        params = {
            "term": term,
            "location": location,
            "limit": limit,
            "sort_by": "review_count"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("businesses", [])
        except Exception as e:
            print(f"Error searching Yelp: {e}")
            return []
    
    def find_no_website_businesses(self, term, location, limit=50):
        """Find businesses that don't have a website."""
        businesses = self.search_businesses(term, location, limit)
        no_website = []
        
        for biz in businesses:
            website = biz.get("website", "")
            if not website or website == "http://" or website == "https://":
                no_website.append({
                    "id": biz.get("id", ""),
                    "name": biz.get("name", ""),
                    "phone": biz.get("phone", ""),
                    "rating": biz.get("rating", 0),
                    "review_count": biz.get("review_count", 0),
                    "category": biz.get("categories", [{}])[0].get("title", ""),
                    "address": " ".join(biz.get("location", {}).get("display_address", [])),
                    "city": biz.get("location", {}).get("city", ""),
                    "state": biz.get("location", {}).get("state", ""),
                    "zip": biz.get("location", {}).get("zip_code", ""),
                    "url": biz.get("url", ""),
                    "image_url": biz.get("image_url", ""),
                    "website": "",
                    "scanned_at": datetime.now().isoformat()
                })
        
        return no_website


class BusinessResearcher:
    """Research a business to gather info for outreach."""
    
    def __init__(self):
        self.results_dir = "/home/vboxuser/mrbubba-mission/website-scanner/results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def check_website_exists(self, business_name, city):
        """Try to find if a business has a website via common patterns."""
        clean_name = re.sub(r'[^a-z0-9]', '', business_name.lower())
        
        patterns = [
            f"https://www.{clean_name}.com",
            f"https://{clean_name}.com",
            f"https://www.{clean_name.replace(' ', '')}.com",
            f"https://{clean_name.replace(' ', '')}.com",
        ]
        
        for url in patterns:
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
    
    def get_yelp_page_info(self, yelp_url):
        """Extract info from Yelp page if available."""
        if not yelp_url:
            return {}
        
        try:
            req = urllib.request.Request(yelp_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                
                info = {}
                
                hours_match = re.search(r'"hours":({[^}]+})', html)
                if hours_match:
                    try:
                        info["hours"] = json.loads(hours_match.group(1))
                    except:
                        pass
                
                attrs = re.findall(r'"displayName":"([^"]+)"', html)
                if attrs:
                    info["amenities"] = attrs[:10]
                
                about_match = re.search(r'"description":"([^"]{50,500})"', html)
                if about_match:
                    info["about"] = about_match.group(1)
                
                return info
        except:
            return {}
    
    def research_business(self, business):
        """Full research on a single business."""
        print(f"  Researching: {business['name']}...")
        
        research = {
            "has_website": False,
            "domain": None,
            "hours": {},
            "amenities": [],
            "about": "",
            "competitor_analysis": [],
            "notes": []
        }
        
        domain = self.check_website_exists(business["name"], business.get("city", ""))
        if domain:
            research["has_website"] = True
            research["domain"] = domain
            research["notes"].append(f"Found website: {domain}")
            return research
        
        yelp_info = self.get_yelp_page_info(business.get("url", ""))
        research.update(yelp_info)
        
        if business.get("rating", 0) >= 4.0:
            research["notes"].append("High rated business (4+ stars)")
        
        if business.get("review_count", 0) >= 20:
            research["notes"].append("Good review count (20+ reviews)")
        
        safe_name = re.sub(r'[^a-z0-9]', '_', business["name"].lower())
        filepath = f"{self.results_dir}/{safe_name}.json"
        with open(filepath, "w") as f:
            json.dump({**business, **research}, f, indent=2)
        
        return research


class OutreachGenerator:
    """Generate personalized outreach emails."""
    
    def __init__(self):
        self.templates = {
            "restaurant": """Hi {name},

I was looking at restaurants in {city} and came across {business_name}. Your {review_text} reviews really stand out — especially the ones about {highlight}.

I noticed you don't have a website yet. In 2026, that's leaving money on the table:
- 80% of diners check a restaurant's menu before visiting
- Online ordering can increase revenue by 20-30%
- Your competitors with websites are getting your customers

I build professional restaurant websites for {city} businesses:
- Mobile-friendly design with your menu online
- Online ordering integration (DoorDash, UberEats)
- Reservation system
- Photo gallery of your dishes
- Google Maps integration

**Price: $299** for a complete 5-page website
**Delivery: 3-5 business days**

Want me to send you a free draft? No obligation — if you like it, we proceed. If not, no worries.

Reply "yes" and I'll have a draft ready within 48 hours.

Best,
Mr Bubba Services
{agentmail}""",

            "default": """Hi {name},

I was looking for {category} services in {city} and found {business_name}. With {review_count} reviews and a {rating}-star rating, you're clearly doing great work.

I noticed you don't have a professional website yet. For businesses like yours, a website can:
- Bring in 30-50% more calls/bookings
- Showcase your work and reviews 24/7
- Make it easy for customers to contact you
- Beat competitors who already have websites

I build professional websites for {city} {category} businesses:
- Mobile-friendly design (most customers find you on their phone)
- Contact form and click-to-call
- Photo gallery of your work
- Customer testimonial section
- Google Maps integration

**Price: $299** for a complete 5-page website
**Delivery: 3-5 business days**

Want me to send you a free draft? No obligation — if you like it, we proceed. If not, no worries.

Reply "yes" and I'll have a draft ready within 48 hours.

Best,
Mr Bubba Services
{agentmail}"""
        }
    
    def generate_email(self, business, research):
        """Generate a personalized outreach email."""
        category = business.get("category", "").lower()
        template_key = "default"
        
        for key in self.templates:
            if key in category:
                template_key = key
                break
        
        template = self.templates[template_key]
        
        review_count = business.get("review_count", 0)
        rating = business.get("rating", 0)
        
        if review_count >= 50:
            review_text = "strong"
        elif review_count >= 20:
            review_text = "great"
        else:
            review_text = "good"
        
        highlight = "your service quality"
        if research.get("about"):
            about = research["about"][:100]
            highlight = about
        elif research.get("amenities"):
            highlight = ", ".join(research["amenities"][:3])
        
        email = template.format(
            name=business.get("name", "there").split()[0] if business.get("name") else "there",
            business_name=business.get("name", "your business"),
            city=business.get("city", "your area"),
            state=business.get("state", ""),
            category=business.get("category", "service"),
            review_count=review_count,
            rating=rating,
            review_text=review_text,
            highlight=highlight,
            agentmail=AGENTMAIL_INBOX
        )
        
        return email
    
    def generate_subject(self, business):
        """Generate a subject line."""
        subjects = [
            f"{business.get('name', 'Quick question')} — website idea for you",
            f"Quick question about {business.get('name', 'your business')}",
            f"Found you on Yelp — idea for more customers",
            f"{business.get('city', 'Local')} {business.get('category', 'business')} website idea"
        ]
        
        if business.get("rating", 0) >= 4.5:
            return subjects[0]
        elif business.get("review_count", 0) >= 30:
            return subjects[2]
        else:
            return subjects[1]


class AgentMailSender:
    """Send emails via AgentMail API."""
    
    def __init__(self):
        self.api_key = AGENTMAIL_API_KEY
        self.inbox = AGENTMAIL_INBOX
        self.base_url = "https://api.agentmail.to/v0"
    
    def send(self, to_email, subject, text):
        """Send an email."""
        data = json.dumps({
            "to": [to_email],
            "subject": subject,
            "text": text
        }).encode()
        
        url = f"{self.base_url}/inboxes/{urllib.parse.quote(self.inbox)}/messages/send"
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                return result.get("message_id", "")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  AgentMail error {e.code}: {body[:100]}")
            return None


def scan_for_leads():
    """Scan Yelp for businesses without websites."""
    if not YELP_API_KEY:
        print("ERROR: YELP_API_KEY not set")
        print("Get a free key at: https://www.yelp.com/developers/v3/manage_app")
        return []
    
    scanner = YelpScanner(YELP_API_KEY)
    researcher = BusinessResearcher()
    all_leads = []
    
    for location in SEARCH_LOCATIONS[:3]:
        for term in SEARCH_TERMS[:5]:
            print(f"\nScanning: {term} in {location}")
            
            businesses = scanner.find_no_website_businesses(term, location, limit=10)
            print(f"  Found {len(businesses)} businesses without websites")
            
            for biz in businesses:
                research = researcher.research_business(biz)
                
                if not research["has_website"]:
                    all_leads.append({
                        **biz,
                        "research": research,
                        "status": "researched",
                        "added_at": datetime.now().isoformat()
                    })
            
            time.sleep(1)
    
    leads_file = "/home/vboxuser/mrbubba-mission/website-scanner/leads.json"
    with open(leads_file, "w") as f:
        json.dump(all_leads, f, indent=2)
    
    print(f"\n✅ Total leads found: {len(all_leads)}")
    print(f"   Saved to: {leads_file}")
    
    return all_leads


def send_outreach(leads):
    """Send outreach emails to leads."""
    sender = AgentMailSender()
    gen = OutreachGenerator()
    
    sent_count = 0
    
    for lead in leads:
        if lead.get("status") != "researched":
            continue
        
        email_text = gen.generate_email(lead, lead.get("research", {}))
        subject = gen.generate_subject(lead)
        
        # Try to construct email from business name
        clean_name = re.sub(r'[^a-z0-9]', '', lead["name"].lower())[:20]
        common_domains = ["gmail.com", "yahoo.com", "outlook.com"]
        
        # For now, skip if we don't have a real email
        print(f"  Would send to: {lead['name']} (need email)")
        
        # Save the email for review
        safe_name = re.sub(r'[^a-z0-9]', '_', lead["name"].lower())
        filepath = f"/home/vboxuser/mrbubba-mission/website-scanner/output/email_{safe_name}.txt"
        with open(filepath, "w") as f:
            f.write(f"To: {lead['name']}\n")
            f.write(f"Subject: {subject}\n\n")
            f.write(email_text)
        
        sent_count += 1
    
    print(f"\n✅ Generated {sent_count} emails")
    print(f"   Saved to: /home/vboxuser/mrbubba-mission/website-scanner/output/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scanner.py --mode scan     # Scan for leads")
        print("  python3 scanner.py --mode outreach # Generate/send emails")
        print("  python3 scanner.py --mode full     # Full pipeline")
        sys.exit(1)
    
    mode = sys.argv[1].lstrip("-")
    
    if mode in ["scan", "full"]:
        leads = scan_for_leads()
    
    if mode in ["outreach", "full"]:
        leads_file = "/home/vboxuser/mrbubba-mission/website-scanner/leads.json"
        if os.path.exists(leads_file):
            with open(leads_file, "r") as f:
                leads = json.load(f)
            send_outreach(leads)
        else:
            print("No leads found. Run scan first.")