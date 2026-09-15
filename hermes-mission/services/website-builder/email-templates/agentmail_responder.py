#!/usr/bin/env python3
"""
Mr Bubba Services - AgentMail Auto-Responder Templates
Email templates and handler for website builder service inquiries via AgentMail.
"""

import json
from datetime import datetime
from typing import Optional


# ════════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES FOR AGENTMAIL AUTO-RESPONDER
# ════════════════════════════════════════════════════════════════════════════════

# Template 1: Initial Inquiry Response
INITIAL_RESPONSE = """Subject: Re: Website Builder Service

Hi {client_name},

Thanks for reaching out about the Website Builder service. I'd be happy to help you get a professional website up and running.

Here's what I need from you to get started:

1. Business name
2. Business type (plumbing, landscaping, roofing, cleaning, restaurant, retail, etc.)
3. City and location
4. Contact info (phone, email, address)
5. Services you offer

Optional but helpful:
- Your logo (attach or link)
- Photos of your work or team
- Social media links
- Websites you like for inspiration
- Any specific features you want (booking, gallery, etc.)

Pricing is $299 flat. This includes:
- 5-page website (Home, About, Services, Portfolio, Contact)
- Professional custom design
- Mobile-responsive layout
- Contact form
- Google Maps embed
- Testimonials section
- SEO-ready pages
- Deployed and live on GitHub Pages
- 7 days of free revisions

How it works:
1. You send me your business info (reply to this email)
2. I build your custom website (24-48 hours)
3. I send you a preview link
4. You approve and pay via PayPal ($299)
5. Your site goes live

Just reply with your business details and I'll get started.

Best,
Mr Bubba Services
mrbubba@agentmail.to

Most sites are ready within 24 hours of receiving your info.
"""

# Template 2: After Receiving Business Info
INFO_RECEIVED = """Subject: Got Your Info — Building {business_name}'s Website

Hi {client_name},

Thanks for sending over the details. I'm starting on {business_name}'s website now.

Here's what I'm building:
- Home page with hero section, services overview, and testimonials
- About page with your story and team
- Services page with a full list of what you offer
- Portfolio page to showcase your work
- Contact page with a form, map, phone, email, and hours

I'll have a preview ready for you within {timeframe}. You'll get a link to review everything before any payment is due. Once you approve, it's $299 via PayPal to go live.

Talk soon,
Mr Bubba Services
"""

# Template 3: Preview Ready - Time to Pay
PREVIEW_READY = """Subject: Your Website Preview is Ready — {business_name}

Hi {client_name},

Good news — {business_name}'s website is ready for your review.

Preview link: {preview_url}

Take a look at all 5 pages:
- Home: {preview_url}/
- About: {preview_url}/about.html
- Services: {preview_url}/services.html
- Portfolio: {preview_url}/portfolio.html
- Contact: {preview_url}/contact.html

To go live, send $299 via PayPal:
- Direct payment: {paypal_email}
- Or reply "send invoice" and I'll send a formal PayPal invoice
- Or use this link: {payment_link}

Once payment is confirmed, your site goes live within 1-2 hours. You'll own the GitHub repository and can make changes anytime.

I'm happy to make minor adjustments after payment — just let me know.

Best,
Mr Bubba Services
mrbubba@agentmail.to
"""

# Template 4: Payment Confirmation & Site Live
PAYMENT_CONFIRMATION = """Subject: Payment Received — {business_name} Website is Live

Hi {client_name},

Your payment of $299 has been confirmed and {business_name}'s website is now live.

Your live website: {live_url}

What's next:
1. Save this URL — it's your permanent website address
2. Share it with customers, on social media, and Google Business
3. Need changes? Reply to this email — minor updates are free for 7 days
4. Want a custom domain (like www.{business_domain})? Reply and I can help set that up

Your website is hosted on GitHub Pages, which means reliable uptime, fast loading, free hosting, and HTTPS security.

Thanks for choosing Mr Bubba Services. If you're happy with the result, I'd appreciate a testimonial or referral.

Best,
Mr Bubba Services
mrbubba@agentmail.to
"""

# Template 5: Payment Reminder
PAYMENT_REMINDER = """Subject: Friendly Reminder — {business_name} Website Ready for Payment

Hi {client_name},

Just checking in. Your website preview is ready and I wanted to make sure you got the link.

Preview: {preview_url}

When you're ready to go live, send $299 via PayPal:
- Direct payment: {paypal_email}
- Or reply "send invoice" for a formal invoice

Your site will go live as soon as payment is confirmed.

Let me know if you have any questions or want any changes before going live.

Best,
Mr Bubba Services
"""

# Template 6: Follow-up after 3 days
FOLLOW_UP = """Subject: Following Up — {business_name} Website

Hi {client_name},

I wanted to follow up about the website I built for {business_name}. Your preview is still available:

{preview_url}

If you have any questions, want changes, or are ready to go live, just let me know.

If the timing isn't right, no worries — I'll keep your preview available for 30 days.

Best,
Mr Bubba Services
"""

# Template 7: "Not Interested" Response
NOT_INTERESTED = """Subject: No Problem

Hi {client_name},

No worries at all. Things come up and timing isn't always right.

Your website preview will remain available at: {preview_url}

When you're ready to move forward (now or months from now), just reach back out. The $299 price includes everything with no hidden fees.

Wishing you the best with {business_name}.

Best,
Mr Bubba Services
"""


# ════════════════════════════════════════════════════════════════════════════════
# AGENTMAIL INBOX PARSER
# ════════════════════════════════════════════════════════════════════════════════

def classify_inquiry(email_subject: str, email_body: str) -> str:
    """Classify an incoming email to determine which template to use."""
    subject_lower = (email_subject or "").lower()
    body_lower = (email_body or "").lower()
    combined = subject_lower + " " + body_lower

    # Keywords for classification
    payment_keywords = ["pay", "invoice", "send invoice", "bill", "payment", "how much", "ready to pay", "purchase", "buy"]
    info_keywords = ["my business", "here's my", "i own", "category", "located in", "services i offer"]
    not_interested_keywords = ["not interested", "no thanks", "too expensive", "can't afford", "maybe later", "pass"]
    question_keywords = ["how", "what", "when", "can you", "do you", "?"]

    if any(k in combined for k in not_interested_keywords):
        return "not_interested"
    
    if any(k in combined for k in payment_keywords):
        return "payment_inquiry"
    
    if any(k in combined for k in info_keywords):
        return "info_received"
    
    if any(k in combined for k in question_keywords):
        return "question"
    
    return "initial_response"


def extract_business_info(email_body: str) -> dict:
    """Extract business information from email body using basic NLP."""
    import re
    
    info = {
        "business_name": "",
        "category": "",
        "city": "",
        "phone": "",
        "email": "",
        "address": "",
    }
    
    lines = email_body.split("\n")
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Business name patterns
        if any(k in line_lower for k in ["business name", "company name", "my business", "i own", "called"]):
            match = re.search(r'(?:name|called|is)\s+["\']?([A-Z][A-Za-z\s&\']+?)["\']?(?:\s*$|\s*,)', line)
            if match:
                info["business_name"] = match.group(1).strip()
        
        # Category patterns
        if any(k in line_lower for k in ["category", "type", "we are", "we're a", "we do", "services"]):
            for cat in ["plumbing", "landscaping", "roofing", "cleaning", "restaurant", "retail", 
                       "construction", "electrician", "hvac", "painting", "legal", "accounting",
                       "consulting", "real estate", "dental", "medical", "auto", "fitness"]:
                if cat in line_lower:
                    info["category"] = cat
                    break
        
        # City patterns
        if any(k in line_lower for k in ["city", "located in", "based in", "serve", "area"]):
            match = re.search(r'(?:in|at|near)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', line)
            if match:
                info["city"] = match.group(1).strip()
        
        # Phone
        phone_match = re.search(r'[\(]?[\d]{3}[\)\s\-\.]?[\d]{3}[\-\.\s]?[\d]{4}', line)
        if phone_match and not info["phone"]:
            info["phone"] = phone_match.group(0)
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
        if email_match and not info["email"]:
            info["email"] = email_match.group(0)
    
    return info


def generate_response(email_subject: str, email_body: str, client_name: str = "there") -> dict:
    """Generate the appropriate response based on the incoming email."""
    classification = classify_inquiry(email_subject, email_body)
    business_info = extract_business_info(email_body)
    
    template_map = {
        "initial_response": INITIAL_RESPONSE,
        "info_received": INFO_RECEIVED,
        "payment_inquiry": PREVIEW_READY,
        "not_interested": NOT_INTERESTED,
        "question": INITIAL_RESPONSE,
    }
    
    template = template_map.get(classification, INITIAL_RESPONSE)
    
    response = template.format(
        client_name=client_name.split("@")[0].title() if "@" in client_name else client_name,
        business_name=business_info.get("business_name", "your business"),
        timeframe="24-48 hours",
        preview_url="https://RNGBubba.github.io/preview-site",
        live_url="https://RNGBubba.github.io/live-site",
        payment_link="https://www.paypal.com/paypalme/mrbubba/299",
        paypal_email="mrbubba@agentmail.to",
        business_domain=business_info.get("business_name", "yourbusiness").lower().replace(" ", ""),
    )
    
    return {
        "classification": classification,
        "response": response,
        "business_info": business_info,
    }


if __name__ == "__main__":
    # Demo: test classification
    test_cases = [
        ("Website Inquiry", "Hi, I'm interested in your website service. My company is ABC Plumbing located in Dallas, TX. Call me at (214) 555-1234."),
        ("Send Invoice", "Hey, please send me the invoice for the website. Ready to pay!"),
        ("Not interested right now", "Thanks but we're not interested at this time. Too expensive."),
        ("How does it work?", "Can you tell me more about how this works? What do you need from me?"),
    ]
    
    for subject, body in test_cases:
        result = generate_response(subject, body, "John")
        print(f"\n{'='*60}")
        print(f"Subject: {subject}")
        print(f"Classification: {result['classification']}")
        print(f"Extracted: {result['business_info']}")
        print(f"--- Response Preview ---")
        print(result['response'][:300] + "...")
