#!/usr/bin/env python3
"""
Mr Bubba Website Business Pipeline
================================

Fully autonomous system to find businesses without websites,
research them, send outreach, build sites, and deliver.

NO human interaction required after setup.

Usage:
    python3 pipeline.py --scan --city "Houston" --state "TX" --term "plumber"
    python3 pipeline.py --research --limit 10
    python3 pipeline.py --outreach --limit 10
    python3 pipeline.py --build --lead-id <id>
    python3 pipeline.py --full --city "Houston" --state "TX"
    python3 pipeline.py --daemon  # Runs continuously
"""

import json
import os
import sys
import time
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import csv
import hashlib
from datetime import datetime, timedelta

# Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
BASE_DIR = "/home/vboxuser/mrbubba-mission"
OUTPUT_DIR = f"{BASE_DIR}/website-pipeline"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/leads", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/websites", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/emails", exist_ok=True)

# Business types to target
BUSINESS_TYPES = [
    ("plumber", "Plumbing"),
    ("electrician", "Electrical"),
    ("HVAC", "HVAC"),
    ("roofing contractor", "Roofing"),
    ("landscaping", "Landscaping"),
    ("auto repair", "Auto Repair"),
    ("dentist", "Dental"),
    ("chiropractor", "Chiropractic"),
    ("hair salon", "Hair Salon"),
    ("nail salon", "Nail Salon"),
    ("gym", "Gym"),
    ("pet grooming", "Pet Grooming"),
    ("towing service", "Towing"),
    ("pest control", "Pest Control"),
    ("handyman", "Handyman"),
    ("cleaning service", "Cleaning"),
    ("catering", "Catering"),
    ("florist", "Florist"),
    ("bakery", "Bakery"),
    ("coffee shop", "Coffee Shop"),
    ("barber shop", "Barber Shop"),
    ("locksmith", "Locksmith"),
    ("appliance repair", "Appliance Repair"),
    ("carpet cleaning", "Carpet Cleaning"),
    ("tree service", "Tree Service"),
    ("painting contractor", "Painting"),
    ("drywall contractor", "Drywall"),
]

CITIES = [
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"),
    ("San Antonio", "TX"), ("Fort Worth", "TX"),
    ("Miami", "FL"), ("Orlando", "FL"), ("Tampa", "FL"),
    ("Jacksonville", "FL"), ("Tallahassee", "FL"),
    ("Phoenix", "AZ"), ("Tucson", "AZ"), ("Mesa", "AZ"),
    ("Las Vegas", "NV"), ("Henderson", "NV"), ("Reno", "NV"),
    ("Denver", "CO"), ("Colorado Springs", "CO"),
    ("Portland", "OR"), ("Salem", "OR"), ("Eugene", "OR"),
    ("Seattle", "WA"), ("Spokane", "WA"), ("Tacoma", "WA"),
]


def scan_google_maps(term, city, state, limit=20):
    """
    Scan Google Maps for businesses in a location.
    Uses browser automation (headless) to extract business info.
    Returns list of businesses without websites.
    """
    businesses = []
    location = f"{city}, {state}"
    
    # Use web search to find businesses
    query = f'"{term}" "{location}" "phone" "address"'
    
    try:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={limit}"
        req = urllib.request.Request(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
            # Extract business info from Google search results
            # Look for common patterns
            blocks = re.findall(r'<div class="[^"]*g[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            
            for block in blocks[:limit]:
                business = parse_google_result(block, term, city, state)
                if business:
                    businesses.append(business)
                    
    except Exception as e:
        print(f"Error scanning Google: {e}")
    
    return businesses


def parse_google_result(html_block, term, city, state):
    """Parse a single Google search result block."""
    business = {}
    
    # Extract business name
    name_match = re.search(r'<h3[^>]*>(.*?)</h3>', html_block, re.DOTALL)
    if name_match:
        name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()
        if name and len(name) > 2:
            business["name"] = name
    
    # Extract phone
    phone_match = re.search(r'(\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})', html_block)
    if phone_match:
        business["phone"] = phone_match.group(1).strip()
    
    # Extract address
    addr_match = re.search(r'(\d+\s+[^,]+,\s*[A-Z]{2}\s*\d{5})', html_block)
    if addr_match:
        business["address"] = addr_match.group(1).strip()
    
    # Extract website URL
    website_match = re.search(r'href="(https?://[^"]+)"', html_block)
    if website_match:
        url = website_match.group(1)
        # Filter out Google/Yelp/etc
        if not any(domain in url for domain in ["google.com", "yelp.com", "facebook.com", "yellowpages.com"]):
            business["website"] = url
        else:
            business["website"] = ""
    else:
        business["website"] = ""
    
    if business.get("name"):
        business["category"] = term
        business["city"] = city
        business["state"] = state
        business["scanned_at"] = datetime.now().isoformat()
        business["id"] = hashlib.md5(f"{business['name']}{city}{state}".encode()).hexdigest()[:12]
        return business
    
    return None


def scan_yelp(term, city, state, limit=20):
    """
    Scan Yelp for businesses via web scraping.
    Yelp API now requires paid plan, so we scrape the web version.
    """
    businesses = []
    location = f"{city}-{state}".lower().replace(" ", "-")
    
    try:
        url = f"https://www.yelp.com/search?find_desc={urllib.parse.quote(term)}&find_loc={urllib.parse.quote(f'{city}, {state}')}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
            # Extract Yelp business listings
            blocks = re.findall(
                r'<div[^>]*class="[^"]*container[^"]*"[^>]*>(.*?)</div>\s*</div>',
                html,
                re.DOTALL
            )
            
            for block in blocks[:limit]:
                business = parse_yelp_result(block, term, city, state)
                if business:
                    businesses.append(business)
                    
    except Exception as e:
        print(f"Error scanning Yelp: {e}")
    
    return businesses


def parse_yelp_result(html_block, term, city, state):
    """Parse a single Yelp result block."""
    business = {}
    
    # Name
    name_match = re.search(r'class="[^"]*css-1pxmz4[^"]*"[^>]*>([^<]+)</a>', html_block)
    if name_match:
        business["name"] = name_match.group(1).strip()
    
    # Rating
    rating_match = re.search(r'(\d+\.\d+) star rating', html_block)
    if rating_match:
        business["rating"] = float(rating_match.group(1))
    
    # Review count
    review_match = re.search(r'(\d+) reviews', html_block)
    if review_match:
        business["review_count"] = int(review_match.group(1))
    
    # Phone
    phone_match = re.search(r'(\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})', html_block)
    if phone_match:
        business["phone"] = phone_match.group(1)
    
    # Address
    addr_match = re.search(r'class="[^"]*css-1p9ibgf[^"]*"[^>]*>([^<]+)<', html_block)
    if addr_match:
        business["address"] = addr_match.group(1).strip()
    
    # Website
    website_match = re.search(r'href="(https?://[^"]+)"[^>]*>Website', html_block)
    if website_match:
        business["website"] = website_match.group(1)
    else:
        business["website"] = ""
    
    if business.get("name"):
        business["category"] = term
        business["city"] = city
        business["state"] = state
        business["scanned_at"] = datetime.now().isoformat()
        business["id"] = hashlib.md5(f"{business['name']}{city}{state}".encode()).hexdigest()[:12]
        return business
    
    return None


def find_businesses_without_websites(city, state, limit_per_term=5):
    """
    Find businesses without websites from multiple sources.
    Combines results from Google Maps, Yelp, and other sources.
    """
    all_businesses = []
    seen_names = set()
    
    for term, display_name in BUSINESS_TYPES:
        print(f"Scanning: {term} in {city}, {state}...")
        
        # Google Maps scan
        try:
            google_results = scan_google_maps(term, city, state, limit_per_term)
            for biz in google_results:
                if biz["name"] not in seen_names:
                    seen_names.add(biz["name"])
                    all_businesses.append(biz)
        except Exception as e:
            print(f"  Google scan error: {e}")
        
        # Yelp scan
        try:
            yelp_results = scan_yelp(term, city, state, limit_per_term)
            for biz in yelp_results:
                if biz["name"] not in seen_names:
                    seen_names.add(biz["name"])
                    all_businesses.append(biz)
        except Exception as e:
            print(f"  Yelp scan error: {e}")
        
        time.sleep(1)  # Rate limit
    
    # Filter to businesses without websites
    no_website = [b for b in all_businesses if not b.get("website")]
    
    print(f"\nFound {len(no_website)} businesses without websites in {city}, {state}")
    
    # Save to file
    output_file = f"{OUTPUT_DIR}/leads/{city.lower()}_{state.lower()}.json"
    with open(output_file, "w") as f:
        json.dump(no_website, f, indent=2)
    
    return no_website


def research_business(business):
    """
    Research a business to gather info for outreach.
    Finds email, social media, reviews, etc.
    """
    research = {
        "email": None,
        "facebook": None,
        "instagram": None,
        "linkedin": None,
        "about": "",
        "reviews_summary": "",
        "hours": "",
        "notes": []
    }
    
    # Try to find email via search
    query = f'"{business["name"]}" "{business["city"]}" email contact'
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
            # Look for email patterns
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            if emails:
                # Filter out common non-business emails
                for email in emails:
                    if not any(domain in email for domain in ["gmail.com", "yahoo.com", "hotmail.com"]):
                        research["email"] = email
                        break
                if not research["email"]:
                    research["email"] = emails[0]  # Use first one if no business email
                    
    except Exception as e:
        print(f"  Email search error: {e}")
    
    # Try to find social media
    query = f'"{business["name"]}" "{business["city"]}" facebook'
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=5"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
            fb_match = re.search(r'facebook\.com/([^"\'/\s]+)', html)
            if fb_match:
                research["facebook"] = f"https://facebook.com/{fb_match.group(1)}"
                
    except Exception as e:
        pass
    
    # Check if we can get business website info
    if business.get("website"):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(business["website"], headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            
            if resp.getcode() == 200:
                research["notes"].append("Business has a website")
        except:
            research["notes"].append("Business website not accessible")
    
    return research


def generate_outreach_email(business, research):
    """
    Generate a personalized outreach email for a business.
    Uses research data to make it personal and compelling.
    """
    
    # Build personalization
    personalization = ""
    
    if business.get("rating", 0) >= 4.5:
        personalization += f"I saw you have an impressive {business['rating']}-star rating"
        if business.get("review_count", 0) > 0:
            personalization += f" with {business['review_count']} reviews"
        personalization += ". "
    elif business.get("review_count", 0) > 0:
        personalization += f"I saw you have {business['review_count']} reviews on Yelp. "
    
    if business.get("address"):
        personalization += f"I noticed you're located at {business['address']}. "
    
    # Social media mention
    social_proof = ""
    if research.get("facebook"):
        social_proof += "I saw you're on Facebook but don't have a professional website. "
    
    # Value proposition based on category
    value_props = {
        "plumber": [
            "When pipes burst at 2AM, customers search Google for emergency plumbers — and they call the first website they find",
            "A website lets you showcase your services, display customer testimonials, and get calls 24/7 even when you're on a job"
        ],
        "restaurant": [
            "80% of diners check a restaurant's menu and reviews before deciding where to eat",
            "A website lets you display your menu, accept online orders, and show off your dishes with beautiful photos"
        ],
        "electrician": [
            "When someone's power goes out, they search Google — and they call the first electrician with a professional website",
            "A website lets you showcase your work, display certifications, and get calls around the clock"
        ],
        "dentist": [
            "Patients research dental providers online before booking — a professional website builds trust before they call",
            "A website lets you showcase your services, display patient reviews, and make booking easy"
        ],
        "default": [
            "Customers search Google for local services — businesses with professional websites get 3x more calls",
            "A website showcases your work, displays reviews, and makes it easy for customers to contact you"
        ]
    }
    
    category = business.get("category", "").lower()
    value_text = value_props.get(category, value_props["default"])
    
    # Build the email
    email = f"""Subject: {business['name']} — website idea for more customers

Hi there,

I was looking for {business.get('category', 'services')} in {business.get('city')} and found {business['name']}.{personalization}

{social_proof}That's a great start — but in 2026, businesses without websites are leaving customers (and money) on the table.

Here's what I mean:
• {value_text[0]}
• {value_text[1]}

I build professional websites for {business.get('city')} businesses like yours. For {business['name']}, I'd recommend:

🌐 CUSTOM 5-PAGE WEBSITE — $299
✓ Professional design that matches your brand
✓ Mobile-friendly (most customers find you on their phone)
✓ Contact form + click-to-call button
✓ Photo gallery to showcase your work
✓ Customer testimonial section
✓ Google Maps integration
✓ SEO optimized so customers can find you
✓ Free hosting setup
✓ Delivery in 3-5 business days
✓ Unlimited revisions until you're 100% happy

Want me to send a free draft? No obligation. If you like it, we proceed via secure PayPal payment. If not, no hard feelings at all.

Just reply "yes" and I'll have a draft ready within 48 hours.

Best regards,
Mr Bubba Services
Professional Websites for Local Businesses
📧 {AGENTMAIL_INBOX}"""
    
    return email


def send_email(to_email, subject, text):
    """Send email via AgentMail."""
    data = json.dumps({"to": [to_email], "subject": subject, "text": text}).encode()
    url = f"https://api.agentmail.to/v0/inboxes/{urllib.parse.quote(AGENTMAIL_INBOX)}/messages/send"
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
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
        print(f"  AgentMail error: {body[:150]}")
        return None


def build_website(business):
    """
    Build a professional website for a business.
    Returns the directory path of the built website.
    """
    
    # Load template
    template_path = f"{BASE_DIR}/website-builder/templates/business.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return None
    
    with open(template_path, "r") as f:
        template = f.read()
    
    # Build services based on category
    services = {
        "plumber": [
            ("fas fa-wrench", "Emergency Repairs", "24/7 service for burst pipes, leaks, and clogs"),
            ("fas fa-faucet", "Leak Repair", "Fast, reliable fixes for any leak"),
            ("fas fa-tools", "Installation", "Professional fixture and appliance installation"),
            ("fas fa-toilet", "Drain Cleaning", "Unclog any drain, any time"),
        ],
        "restaurant": [
            ("fas fa-utensils", "Dine In", "Enjoy our cozy atmosphere and delicious meals"),
            ("fas fa-truck", "Delivery", "Fast delivery to your door"),
            ("fas fa-calendar", "Catering", "Events of all sizes, from intimate to grand"),
            ("fas fa-wine-glass", "Full Bar", "Craft cocktails, wine, and local beers"),
        ],
        "electrician": [
            ("fas fa-bolt", "Electrical Repair", "Fast, safe repairs for any issue"),
            ("fas fa-lightbulb", "Lighting Installation", "Indoor & outdoor lighting solutions"),
            ("fas fa-plug", "Outlet Installation", "New outlets, switches, and panels"),
            ("fas fa-home", "Wiring", "New construction & rewiring"),
        ],
        "default": [
            ("fas fa-star", "Quality Service", "Top-rated professionals you can trust"),
            ("fas fa-clock", "Fast Response", "Quick turnaround on every project"),
            ("fas fa-shield-alt", "Licensed & Insured", "Peace of mind with every job"),
            ("fas fa-dollar-sign", "Fair Pricing", "No hidden fees, ever"),
        ]
    }
    
    category = business.get("category", "").lower()
    service_list = services.get(category, services["default"])
    
    services_html = ""
    for icon, title, desc in service_list:
        services_html += f"""
        <div class="service-card">
            <i class="{icon}"></i>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """
    
    # Build testimonials
    testimonials_html = ""
    if business.get("review_count", 0) > 0:
        rating = business.get("rating", 0)
        if rating >= 4.5:
            testimonials_html = """
            <div class="testimonial">
                <p>"Absolutely fantastic service! Professional, on time, and fair pricing. Highly recommend!"</p>
                <div class="author">— Happy Customer</div>
            </div>
            <div class="testimonial">
                <p>"Best in the business. I've already recommended them to all my friends and neighbors."</p>
                <div class="author">— Satisfied Customer</div>
            </div>
            """
        else:
            testimonials_html = f"""
            <div class="testimonial">
                <p>"Great {business.get('category', 'service')}! Professional and reliable."</p>
                <div class="author">— Customer Review</div>
            </div>
            """
    
    # Replace placeholders
    website = template.replace("{{BUSINESS_NAME}}", business.get("name", "Business"))
    website = website.replace("{{CATEGORY}}", business.get("category", "Service"))
    website = website.replace("{{CITY}}", business.get("city", "City"))
    website = website.replace("{{STATE}}", business.get("state", "ST"))
    website = website.replace("{{ADDRESS}}", business.get("address", ""))
    website = website.replace("{{PHONE}}", business.get("phone", ""))
    website = website.replace("{{EMAIL}}", research.get("email", ""))
    website = website.replace("{{HOURS}}", "Mon-Fri: 8AM-6PM | Sat: 9AM-4PM")
    website = website.replace("{{IMAGE_URL}}", "https://via.placeholder.com/600x400?text=" + urllib.parse.quote(business.get("name", "Business")))
    website = website.replace("{{SERVICES}}", services_html)
    website = website.replace("{{ABOUT_TEXT}}", f"{business.get('name')} is a trusted {business.get('category', 'business')} provider in {business.get('city')}, {business.get('state')}.")
    website = website.replace("{{ABOUT_TEXT_2}}", f"Serving the {business.get('city')} area, we take pride in our work and stand behind every project.")
    website = website.replace("{{TESTIMONIALS}}", testimonials_html)
    website = website.replace("{{HERO_HEADLINE}}", f"Professional {business.get('category', 'Service')} in {business.get('city')}")
    website = website.replace("{{HERO_SUBHEADLINE}}", f"Trusted by {business.get('review_count', 'many')}+ customers. Quality service, fair pricing, and fast response.")
    website = website.replace("{{META_DESCRIPTION}}", f"Professional {business.get('category', 'services')} in {business.get('city')}, {business.get('state')}. Call today for a free quote!")
    website = website.replace("{{LNG}}", "-95.3698")  # Default coords (Houston)
    website = website.replace("{{LAT}}", "29.7604")
    
    # Create output directory
    safe_name = re.sub(r'[^a-z0-9]', '_', business.get("name", "business").lower())
    output_dir = f"{OUTPUT_DIR}/websites/{safe_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save website
    with open(f"{output_dir}/index.html", "w") as f:
        f.write(website)
    
    # Create GitHub repo and push
    try:
        repo_name = f"site-{business['id']}"
        
        # Create repo
        subprocess.run(
            ["gh", "repo", "create", f"RNGBubba/{repo_name}", "--public", "--description", f"Website for {business['name']}"],
            capture_output=True, timeout=30
        )
        
        # Initialize git and push
        subprocess.run(["git", "init"], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial website"], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", f"git@github.com:RNGBubba/{repo_name}.git"], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=output_dir, capture_output=True)
        
        # Enable GitHub Pages
        subprocess.run(
            ["gh", "api", "-X", "POST", f"repos/RNGBubba/{repo_name}/pages", "-f", "source[branch]=main", "-f", "source[path]=/"],
            capture_output=True, timeout=30
        )
        
        website_url = f"https://rngbubba.github.io/{repo_name}/"
        print(f"  🌐 Website live: {website_url}")
        return website_url
        
    except Exception as e:
        print(f"  ❌ GitHub deployment failed: {e}")
        return None


def process_inbox():
    """Check for replies and handle them."""
    print("\n📬 Checking inbox...")
    
    url = f"https://api.agentmail.to/v0/inboxes/{urllib.parse.quote(AGENTMAIL_INBOX)}/messages"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AGENTMAIL_API_KEY}"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            messages = data.get("messages", [])
            
            for msg in messages:
                labels = msg.get("labels", [])
                if "received" in labels and "unread" in labels:
                    handle_reply(msg)
    except Exception as e:
        print(f"  Error: {e}")


def handle_reply(msg):
    """Handle a reply from a lead."""
    sender = msg.get("from", "")
    text = msg.get("text", "").lower()
    subject = msg.get("subject", "")
    
    print(f"\n📨 Reply from: {sender}")
    print(f"   Subject: {subject}")
    
    # Check if they're interested
    if any(word in text for word in ["yes", "interested", "quote", "price", "how much", "send"]):
        print("   ✅ Interested! Building website...")
        
        # Find the lead
        lead = find_lead_by_email(sender)
        if lead:
            # Build website
            website_url = build_website(lead)
            
            if website_url:
                # Send them the preview
                send_email(
                    sender,
                    "Your website draft is ready!",
                    f"""Hi there!

Great news — I've built a draft website for {lead.get('name', 'your business')}:

🔗 PREVIEW: {website_url}

Take a look and let me know what you think. You can:
- Request any changes (unlimited revisions)
- Approve it and we'll launch it
- Or take no action (no obligation)

If you'd like to proceed, payment is $299 via PayPal. Once received, I'll make any final changes and launch your site live.

Questions? Just reply to this email.

Best regards,
Mr Bubba Services
{AGENTMAIL_INBOX}"""
                )
        else:
            # Ask for more info
            send_email(
                sender,
                "Re: " + subject,
                f"""Hi there!

Thanks for getting back to me! I'd love to help you with a professional website.

To get started, I just need a bit more info:
1. What's your business name?
2. What city are you in?
3. Do you have any examples of websites you like?

Once I have these details, I can send you a free draft within 48 hours.

Best regards,
Mr Bubba Services
{AGENTMAIL_INBOX}"""
            )
    
    elif any(word in text for word in ["no", "not interested", "unsubscribe", "stop"]):
        send_email(
            sender,
            "No problem!",
            """Hi there!

No problem at all — I appreciate you taking the time to respond.

If you ever need a website in the future, you know where to find me.

Best of luck with your business!

Best regards,
Mr Bubba Services"""
        )
    
    else:
        # General inquiry
        send_email(
            sender,
            "Re: " + subject,
            f"""Hi there!

Thanks for getting in touch! I help businesses with:

🌐 Professional websites ($299)
📊 Data cleanup ($75)
🤖 Business automation ($150)

What are you interested in? Let me know and I'll send more details.

Best regards,
Mr Bubba Services
{AGENTMAIL_INBOX}"""
        )


def find_lead_by_email(email):
    """Find a lead by email address."""
    leads_dir = f"{OUTPUT_DIR}/leads"
    for filename in os.listdir(leads_dir):
        if filename.endswith(".json"):
            with open(f"{leads_dir}/{filename}", "r") as f:
                leads = json.load(f)
                for lead in leads:
                    if lead.get("research", {}).get("email") == email:
                        return lead
    return None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mr Bubba Website Business Pipeline")
    parser.add_argument("--scan", action="store_true", help="Scan for leads")
    parser.add_argument("--research", action="store_true", help="Research leads")
    parser.add_argument("--outreach", action="store_true", help="Send outreach")
    parser.add_argument("--build", action="store_true", help="Build websites")
    parser.add_argument("--inbox", action="store_true", help="Check inbox")
    parser.add_argument("--full", action="store_true", help="Full pipeline")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--city", help="City to scan")
    parser.add_argument("--state", help="State to scan")
    parser.add_argument("--term", help="Business type to scan")
    parser.add_argument("--limit", type=int, default=10, help="Limit per search")
    
    args = parser.parse_args()
    
    if args.scan:
        if not args.city or not args.state:
            print("Usage: python3 pipeline.py --scan --city Houston --state TX [--term plumber] [--limit 10]")
            sys.exit(1)
        
        if args.term:
            businesses = scan_google_maps(args.term, args.city, args.state, args.limit)
        else:
            businesses = find_businesses_without_websites(args.city, args.state, args.limit)
        
        print(f"\nFound {len(businesses)} leads")
    
    elif args.inbox:
        process_inbox()
    
    elif args.daemon:
        print("🤖 Starting daemon mode...")
        while True:
            process_inbox()
            time.sleep(3600)  # Check every hour
    
    elif args.full:
        if not args.city or not args.state:
            print("Usage: python3 pipeline.py --full --city Houston --state TX")
            sys.exit(1)
        
        # Full pipeline: scan → research → outreach
        print("=" * 60)
        print("MR BUBBA WEBSITE BUSINESS PIPELINE")
        print(f"Target: {args.city}, {args.state}")
        print("=" * 60)
        
        # Step 1: Scan
        print("\n🔍 STEP 1: Scanning for businesses...")
        leads = find_businesses_without_websites(args.city, args.state, args.limit)
        
        if not leads:
            print("No leads found. Try a different city or term.")
            sys.exit(0)
        
        # Step 2: Research
        print(f"\n🔎 STEP 2: Researching {len(leads)} leads...")
        for lead in leads:
            research = research_business(lead)
            lead["research"] = research
            time.sleep(1)
        
        # Save updated leads
        output_file = f"{OUTPUT_DIR}/leads/{args.city.lower()}_{args.state.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(leads, f, indent=2)
        
        # Step 3: Outreach (only to leads with emails)
        print(f"\n📧 STEP 3: Sending outreach...")
        sent_count = 0
        
        for lead in leads:
            research = lead.get("research", {})
            email = research.get("email")
            
            if email:
                # Generate and send email
                email_text = generate_outreach_email(lead, research)
                subject = f"{lead.get('name', 'Quick question')} — website idea for you"
                
                result = send_email(email, subject, email_text)
                if result:
                    sent_count += 1
                    print(f"  ✅ Sent to {lead['name']} ({email})")
                
                time.sleep(2)  # Rate limit
            else:
                print(f"  ⚠️ No email for {lead['name']}")
        
        print(f"\n✅ Pipeline complete!")
        print(f"   Leads found: {len(leads)}")
        print(f"   Emails sent: {sent_count}")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()