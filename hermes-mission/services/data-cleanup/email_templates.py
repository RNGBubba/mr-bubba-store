#!/usr/bin/env python3
"""
Mr Bubba Services - Email Templates
=======================================
Human-sounding, professional email templates.
NOT automated-sounding. NOT corporate. NOT robotic.
"""

# ============================================================
# TEMPLATES
# ============================================================

def file_received(client_name, filename):
    return f"""Subject: Re: {filename}

Hi {client_name},

Got your file — thanks for sending it over.

I'll take a look and clean it up for you. Shouldn't take long. If anything looks off or you have specific requirements, just reply and let me know.

Best,
Mr Bubba"""


def file_ready(client_name, filename, dups_removed, rows_cleaned):
    return f"""Subject: {filename} — cleaned and ready

Hi {client_name},

Your file is done. Here's what I cleaned up:

- Removed {dups_removed} duplicate rows
- Fixed {rows_cleaned} formatting issues
- Standardized dates and phone numbers
- Trimmed extra spaces

Everything should be ready to use. Let me know if anything looks off or you need changes.

Best,
Mr Bubba"""


def quote_response(client_name, project_description, price_estimate):
    return f"""Subject: Re: Your project

Hi {client_name},

Thanks for reaching out. That sounds like a project I can help with.

Based on what you described, I'd estimate around ${price_estimate:.0f} for this. If that works for you, I can get started right away.

Any questions, just let me know.

Best,
Mr Bubba"""


def payment_received(client_name, amount):
    return f"""Subject: Payment received — thanks

Hi {client_name},

Got your payment of ${amount:.0f}. Appreciate it.

If you ever need anything else down the road, don't hesitate to reach out.

Best,
Mr Bubba"""


def project_update(client_name, status):
    return f"""Subject: Quick update

Hi {client_name},

Just wanted to let you know — {status}.

I'll send over more details soon.

Best,
Mr Bubba"""


def new_inquiry(client_name):
    return f"""Subject: Re: Your inquiry

Hi {client_name},

Thanks for your message. I got your email and will get back to you shortly with more details.

Best,
Mr Bubba"""


def website_demo(client_name, demo_url):
    return f"""Subject: Your demo is ready

Hi {client_name},

Here's the demo we discussed: {demo_url}

Take a look and let me know what you think. Happy to make changes.

Best,
Mr Bubba"""


def proposal_sent(client_name, service, price):
    return f"""Subject: {service} proposal

Hi {client_name},

Attached is the proposal for {service}. I've estimated ${price:.0f} based on the scope we discussed.

Take your time reviewing it. When you're ready, just reply and we can move forward.

Best,
Mr Bubba"""


def cold_outreach(business_name, service, recipient_name):
    return f"""Subject: Quick question about {business_name}

Hi {recipient_name},

I was looking at {business_name} and noticed you might benefit from {service}. I help businesses with this kind of work — usually pretty quick turnaround.

Worth a quick chat? No pressure either way.

Best,
Mr Bubba"""


def follow_up(client_name):
    return f"""Subject: Following up

Hi {client_name},

Just checking in on this. Let me know if you're still interested or if the timing isn't right.

Best,
Mr Bubba"""


# ============================================================
# AUTO-RESPONDER RULES
# ============================================================

AUTO_RESPONDER = {
    "triggers": [
        {
            "if": "email has attachment",
            "reply_with": "file_received",
            "delay_minutes": 5,
        },
        {
            "if": "email mentions price or quote",
            "reply_with": "quote_response",
            "delay_minutes": 10,
        },
        {
            "if": "email is general inquiry",
            "reply_with": "new_inquiry",
            "delay_minutes": 15,
        },
        {
            "if": "email mentions website or web app",
            "reply_with": "website_demo",
            "delay_minutes": 30,
        },
        {
            "if": "email mentions proposal",
            "reply_with": "proposal_sent",
            "delay_minutes": 60,
        },
        {
            "if": "paypal payment webhook fires",
            "reply_with": "payment_received",
            "delay_minutes": 5,
        },
    ],
    "signature": "Best,\nMr Bubba",
    "from_name": "Mr Bubba Services",
    "from_email": "mrbubba@agentmail.to",
}


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    print("=== FILE RECEIVED ===")
    print(file_received("John", "sales_data.csv"))
    print("\n=== FILE READY ===")
    print(file_ready("John", "sales_data.csv", 47, 1250))
    print("\n=== QUOTE RESPONSE ===")
    print(quote_response("Sarah", "data cleanup for 3 spreadsheets", 150))
    print("\n=== COLD OUTREACH ===")
    print(cold_outreach("Joe's Plumbing", "professional website", "Joe"))
