# Proposal Writing Service — README

## Overview

Automated proposal writing service for Mr Bubba Services. Generates professional
business proposals in PDF/Word format, handles email inquiries via AgentMail,
and manages invoicing through PayPal.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Client Email Inquiry                    │
│                  (mrbubba@agentmail.to)                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              agentmail_responder.py                      │
│         (Auto-reply + inquiry processing)                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              generate_proposal.py                        │
│      (PDF/Word proposal generation engine)               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              paypal_invoicing.py                         │
│         (Invoice creation & delivery)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           PayPal Webhook → Discord                       │
│         (Payment notifications)                         │
└─────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `generate_proposal.py` | Core proposal generation (PDF/Word) |
| `agentmail_responder.py` | Auto-responder for AgentMail inbox |
| `paypal_invoicing.py` | PayPal invoice creation and management |
| `proposal_service.py` | Full orchestration flow (all-in-one) |
| `PRICING_GUIDE.md` | Pricing tiers and service details |
| `README.md` | This file |

## Quick Start

### Generate a proposal only
```bash
python3 generate_proposal.py \
    --client "Acme Corp" \
    --project "Data Dashboard" \
    --scope "Build interactive BI dashboard" \
    --timeline "3 weeks" \
    --budget "$2,500" \
    --output-format pdf
```

### Check inbox and auto-reply
```bash
python3 agentmail_responder.py --auto-reply-all
```

### Create an invoice
```bash
python3 paypal_invoicing.py \
    --create \
    --to "client@example.com" \
    --amount 100.00 \
    --service standard
```

### Full service flow
```bash
python3 proposal_service.py --full-flow \
    --client "Acme Corp" \
    --project "Data Dashboard" \
    --scope "Build interactive BI dashboard" \
    --timeline "3 weeks" \
    --budget "$2,500" \
    --email "client@acme.com" \
    --tier standard
```

## Configuration

Set environment variables or use defaults:

```bash
export AGENTMAIL_API_KEY="am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
export AGENTMAIL_EMAIL="mrbubba@agentmail.to"
export PAYPAL_CLIENT_ID="your_paypal_client_id"
export PAYPAL_CLIENT_SECRET="your_paypal_client_secret"
```

## Pricing Tiers

| Tier | Price | Delivery |
|------|-------|----------|
| Basic | $50 | 5 days |
| Standard | $100 | 3 days |
| Comprehensive | $175 | 2 days |
| Premium | $200 | 1-2 days |

See `PRICING_GUIDE.md` for full details.

## Webhook & Notifications

- **PayPal Webhook:** Configured for Discord notifications
- Events: `INVOICING.INVOICE.PAID`, `INVOICING.INVOICE.CANCELLED`
- **AgentMail:** Auto-responder active for mrbubba@agentmail.to

## Output Directory

Generated proposals are saved to:
```
/home/vboxuser/mr-bubba-mission/services/proposals/output/
```

## Dependencies

- `python-docx` — Word document generation
- `reportlab` — PDF generation
- `requests` — HTTP API calls
