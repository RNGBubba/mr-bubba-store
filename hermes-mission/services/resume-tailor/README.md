# Resume & Cover Letter Tailoring Service

Automated service for generating ATS-optimized resumes and tailored cover letters.

## Quick Start

### 1. Tailor Documents

```bash
# Using files
python3 tailor_resume.py path/to/resume.docx path/to/jd.txt -o output/

# Using JD text directly
python3 tailor_resume.py resume.txt "Job description text here" -c "Acme Corp" -p "Data Analyst"

# Specify format
python3 tailor_resume.py resume.docx jd.txt --format docx
```

### 2. Run Auto-Responder

```bash
# Dry run (preview without sending)
python3 autoresponder.py --dry-run --once

# Live mode (process and respond)
python3 autoresponder.py --once

# Continuous polling (every 5 minutes)
python3 autoresponder.py --interval 300
```

### 3. Send PayPal Invoice

```bash
# Show available packages
python3 paypal_invoice.py packages

# Send invoice (logs locally if PayPal not configured)
python3 paypal_invoice.py send client@email.com bundle

# List all invoices
python3 paypal_invoice.py list
```

## Service Flow

```
Client emails resume + JD
        ↓
Auto-reponder sends pricing info
        ↓
Client selects package & confirms
        ↓
PayPal invoice sent
        ↓
Payment received
        ↓
Resume tailored with tailor_resume.py
        ↓
Documents delivered via email
        ↓
Revision rounds (up to package limit)
```

## File Structure

```
resume-tailor/
├── tailor_resume.py      # Main tailoring engine
├── autoresponder.py      # AgentMail auto-responder
├── paypal_invoice.py     # PayPal invoicing
├── PRICING.md            # Pricing guide
└── README.md             # This file
```

## Configuration

Set environment variables or edit defaults in each script:

```bash
# AgentMail
export AGENTMAIL_API_KEY="am_us_inbox_..."
export AGENTMAIL_INBOX="mrbubba@agentmail.to"

# PayPal
export PAYPAL_CLIENT_ID="your_client_id"
export PAYPAL_CLIENT_SECRET="your_secret"
export PAYPAL_ENV="sandbox"  # or "live"
```

## Pricing Tiers

| Package | Price | Delivery | Revisions |
|---------|-------|----------|-----------|
| Resume Only | $30 | 48hr | 2 |
| Cover Letter Only | $30 | 48hr | 2 |
| Bundle | $50 | 24hr | 3 |
| Premium | $60 | Same-day* | 5 |

*Same-day if submitted before 2pm EST

## Requirements

- Python 3.8+
- python-docx
- openpyxl (for future Excel export features)
- pandas (for analytics)

## License

Mr Bubba Services — Internal Use
