#!/usr/bin/env python3
"""
AgentMail Auto-Responder for Mr Bubba Services
Handles automation service inquiries with automated responses.

This script connects to AgentMail API, checks for new emails,
and sends appropriate auto-responses based on content analysis.
"""

import argparse
import json
import re
import time
from pathlib import Path
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# AgentMail API Configuration
AGENTMAIL_API = "https://api.agentmail.io"
API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
INBOX = "mrbubba@agentmail.to"

# Keywords for categorization
KEYWORD_CATEGORIES = {
    'inquiry': ['automation', 'automate', 'script', 'workflow', 'task', 'process', 'help with', 'need help'],
    'quote_response': ['quote', 'price', 'cost', 'how much', 'pricing'],
    'technical': ['python', 'install', 'error', 'bug', 'issue', 'not working'],
    'payment': ['paypal', 'invoice', 'payment', 'paid', 'transaction'],
    'urgent': ['urgent', 'asap', 'emergency', 'critical', 'deadline'],
    'thank_you': ['thank', 'thanks', 'great', 'perfect', 'works', 'working'],
}

# Email templates
TEMPLATES = {
    'inquiry': {
        'subject': 'Re: {original_subject} - Mr Bubba Services',
        'body': '''Hi {client_name},

Thank you for reaching out to Mr Bubba Services! I received your inquiry about automating your workflow.

To provide you with an accurate quote and timeline, I need a few details:

1. What specific task or process do you want to automate?
2. What file formats are involved? (CSV, Excel, PDF, etc.)
3. How often does this task need to run? (daily, weekly, one-time)
4. Do you have any existing tools or systems I should integrate with?
5. What's your ideal timeline for completion?

Once I have these details, I'll prepare a custom quote within 24 hours.

Looking forward to helping you streamline your workflow!

Best regards,
Mr Bubba Services Team
{contact_email}'''
    },
    'clarification': {
        'subject': 'Re: {original_subject} - Follow-up',
        'body': '''Hi {client_name},

Thanks for providing those initial details! To ensure I build exactly what you need, I have a few clarifying questions:

1. INPUT: Where does your data currently live? (files, web URLs, database, API?)
2. OUTPUT: What should the final result look like? (email report, organized files, etc.)
3. TRIGGER: How should the automation run? (manually, on schedule, triggered by event?)
4. EXCEPTIONS: Any special cases or error conditions I should handle?
5. PREFERENCES: Any specific naming conventions or output formats?

Feel free to answer as many as you can - the more detail, the more accurate my quote!

Best,
Mr Bubba Services'''
    },
    'quote_delivery': {
        'subject': 'Re: {original_subject} - Your Automation Quote ${price}',
        'body': '''Hi {client_name},

Based on your requirements, I've prepared a custom automation solution:

PROJECT: {project_summary}

DELIVERABLES:
- Custom Python automation script
- Setup and installation documentation
- User guide with examples
- 30-day bug fix support

COMPLEXITY: {complexity}
TIMELINE: {timeline} business days
PRICE: ${price}

WHAT'S INCLUDED:
✓ Script development and testing
✓ Input/output configuration
✓ Error handling and logging
✓ Documentation and usage guide
✓ 30 days of email support

NEXT STEPS:
1. Reply to confirm you'd like to proceed
2. I'll send a PayPal invoice
3. Upon payment, I'll begin development
4. You'll receive the script within {timeline} days

Questions? Just reply to this email!

Best regards,
Mr Bubba Services'''
    },
    'script_delivery': {
        'subject': 'Re: {original_subject} - Your Automation Script is Ready!',
        'body': '''Hi {client_name},

Great news! Your custom automation script is complete and ready for use.

ATTACHED FILES:
- {script_name}.py (main automation script)
- README.md (setup and usage instructions)
- config.example.json (configuration template)

QUICK START:
1. Install dependencies: pip install -r requirements.txt
2. Configure settings in config.json
3. Run: python {script_name}.py --help

The script includes:
✓ Command-line interface with --help
✓ Error handling and logging
✓ Dry-run mode to preview changes
✓ Progress reporting

If you have any issues or questions, just reply to this email. I'm here to help for the next 30 days at no additional charge.

Thanks for choosing Mr Bubba Services!

Best,
Mr Bubba Services'''
    },
    'payment_confirmation': {
        'subject': 'Re: {original_subject} - Payment Received!',
        'body': '''Hi {client_name},

Thank you for your payment of ${amount}! I've received it and am now starting work on your automation script.

PROJECT TIMELINE:
- Start: {start_date}
- Delivery: {delivery_date}

I'll notify you if I have any questions during development. Otherwise, look for your completed script on {delivery_date}!

Best regards,
Mr Bubba Services'''
    },
    'follow_up': {
        'subject': 'Re: {original_subject} - How\'s Your Automation Running?',
        'body': '''Hi {client_name},

It's been a week since I delivered your automation script. I wanted to check in and see how things are going!

Quick questions:
1. Are you able to run the script successfully?
2. Is it producing the expected results?
3. Any features you'd like to add or modify?

Remember, you have {days_left} days of support remaining, so if you run into any issues or want to tweak anything, let me know.

I'd also love to hear your feedback!

Best,
Mr Bubba Services'''
    },
    'exploratory': {
        'subject': 'Re: {original_subject} - Automation Services',
        'body': '''Hi {client_name},

Great question! Here's what I can help with:

AUTOMATION CAPABILITIES:
• File organization and batch processing
• Report generation and data visualization
• Email automation and notifications
• Data format conversion (CSV, JSON, XML, Excel)
• Web scraping and data extraction
• PDF processing (merge, split, extract)
• Database backups and maintenance
• Excel/spreadsheet automation
• API integration and data syncing
• Social media scheduling

PRICING: $150 - $500 depending on complexity
TIMELINE: 1-7 business days

Share details about your specific workflow and I'll provide a precise quote!

Best,
Mr Bubba Services'''
    },
    'technical_support': {
        'subject': 'Re: {original_subject} - Technical Support',
        'body': '''Hi {client_name},

I'm sorry to hear you're experiencing an issue with the automation script.

To help diagnose the problem, please share:

1. What were you trying to do when the issue occurred?
2. What error message did you see? (screenshot or copy-paste)
3. What operating system are you using?
4. What Python version? (run: python --version)

Common fixes to try first:
- Ensure all dependencies installed: pip install -r requirements.txt
- Check that your configuration file is correct
- Try running with --verbose flag for more details

I'll respond with a solution as soon as possible!

Best,
Mr Bubba Services'''
    },
}


def categorize_email(subject, body):
    """Categorize an email based on its content."""
    text = f"{subject} {body}".lower()
    categories = {}
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            categories[category] = score
    
    if not categories:
        return 'inquiry'
    
    return max(categories, key=categories.get)


def get_new_emails(since_id=None):
    """Fetch new emails from AgentMail inbox."""
    if not HAS_REQUESTS:
        print("Error: requests library required.")
        return []
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    params = {'inbox': INBOX, 'limit': 10}
    if since_id:
        params['since_id'] = since_id
    
    try:
        response = requests.get(
            f"{AGENTMAIL_API}/v1/emails",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get('emails', [])
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []


def send_email(to, subject, body):
    """Send an email via AgentMail API."""
    if not HAS_REQUESTS:
        print("Error: requests library required.")
        return False
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'from': INBOX,
        'to': to,
        'subject': subject,
        'body': body
    }
    
    try:
        response = requests.post(
            f"{AGENTMAIL_API}/v1/emails/send",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        print(f"Email sent to: {to}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def process_inquiry(email):
    """Process a new inquiry email and send appropriate auto-response."""
    sender = email.get('from', 'client')
    sender_name = email.get('sender_name', 'there')
    subject = email.get('subject', '')
    body = email.get('body', '')
    
    # Extract client name (simple heuristic)
    client_name = sender_name
    if '@' in sender_name:
        client_name = sender_name.split('@')[0].replace('.', ' ').title()
    if not client_name or client_name == 'there':
        # Try to extract from email signature
        name_match = re.search(r'(?:regards|sincerely|thanks),?\s*\n+([A-Z][a-z]+)', body, re.I)
        if name_match:
            client_name = name_match.group(1)
        else:
            client_name = 'there'
    
    # Categorize and respond
    category = categorize_email(subject, body)
    
    if category == 'technical':
        template = TEMPLATES['technical_support']
        response_body = template['body'].format(client_name=client_name)
        response_subject = template['subject'].format(original_subject=subject)
    
    elif category == 'inquiry':
        template = TEMPLATES['inquiry']
        response_body = template['body'].format(
            client_name=client_name,
            contact_email=INBOX
        )
        response_subject = template['subject'].format(original_subject=subject)
    
    elif category == 'quote_response':
        # More info needed - send exploratory response
        template = TEMPLATES['exploratory']
        response_body = template['body'].format(client_name=client_name)
        response_subject = template['subject'].format(original_subject=subject)
    
    elif category == 'thank_you':
        # Just acknowledge, no need for full template
        response_subject = f"Re: {subject} - You're Welcome!"
        response_body = f"Hi {client_name},\n\nYou're very welcome! Glad I could help.\n\nBest,\nMr Bubba Services"
    
    else:
        # Default: send initial inquiry response
        template = TEMPLATES['inquiry']
        response_body = template['body'].format(
            client_name=client_name,
            contact_email=INBOX
        )
        response_subject = template['subject'].format(original_subject=subject)
    
    # Send response
    send_email(sender, response_subject, response_body)
    
    # Log the interaction
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'from': sender,
        'category': category,
        'response_template': category,
        'original_subject': subject
    }
    
    log_file = Path('email_log.json')
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return log_entry


def run_daemon(check_interval=60):
    """Run the auto-responder as a daemon, checking for new emails."""
    print(f"Starting Mr Bubba Services auto-responder...")
    print(f"Inbox: {INBOX}")
    print(f"Checking every {check_interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    processed_ids = set()
    
    while True:
        try:
            emails = get_new_emails()
            
            for email in emails:
                email_id = email.get('id')
                if email_id not in processed_ids:
                    print(f"New email from: {email.get('from')}")
                    print(f"Subject: {email.get('subject')}")
                    result = process_inquiry(email)
                    print(f"Category: {result['category']}")
                    print(f"Response sent!\n")
                    processed_ids.add(email_id)
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\nAuto-responder stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(check_interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AgentMail Auto-Responder')
    subparsers = parser.add_subparsers(dest='command')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check for new emails once')
    
    # Daemon command
    daemon_parser = subparsers.add_parser('daemon', help='Run as daemon')
    daemon_parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test with sample email')
    test_parser.add_argument('--type', choices=['inquiry', 'technical', 'quote'], default='inquiry')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send a template email')
    send_parser.add_argument('--to', required=True, help='Recipient email')
    send_parser.add_argument('--template', required=True, help='Template name')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        emails = get_new_emails()
        if emails:
            for email in emails:
                process_inquiry(email)
        else:
            print("No new emails.")
    
    elif args.command == 'daemon':
        run_daemon(args.interval)
    
    elif args.command == 'test':
        sample_emails = {
            'inquiry': {
                'from': 'test@example.com',
                'sender_name': 'Test Client',
                'subject': 'Need help with automation',
                'body': 'Hi, I need a script to organize my files. Can you help?'
            },
            'technical': {
                'from': 'test2@example.com',
                'sender_name': 'Test Client 2',
                'subject': 'Script error',
                'body': 'Your script is not working. I get an error when running it.'
            },
            'quote': {
                'from': 'test3@example.com',
                'sender_name': 'Test Client 3',
                'subject': 'How much does it cost?',
                'body': 'I want to automate my workflow. What is the price?'
            }
        }
        email = sample_emails[args.type]
        result = process_inquiry(email)
        print(f"\nProcessed: {result}")
    
    elif args.command == 'send':
        if args.template in TEMPLATES:
            template = TEMPLATES[args.template]
            body = template['body'].format(
                client_name='Client',
                original_subject='Test',
                price=250,
                complexity='Standard',
                timeline='3-5',
                project_summary='Test project',
                script_name='test_script',
                amount=250,
                start_date='2024-01-15',
                delivery_date='2024-01-20',
                days_left=25,
                contact_email=INBOX
            )
            subject = template['subject'].format(
                original_subject='Test Subject',
                price=250
            )
            send_email(args.to, subject, body)
        else:
            print(f"Unknown template: {args.template}")
            print(f"Available: {list(TEMPLATES.keys())}")
    
    else:
        parser.print_help()
