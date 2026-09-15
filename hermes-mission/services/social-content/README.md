# Social Media Content Service
## Mr Bubba Services

Automated social media content generation service for brands and businesses.

## Files

| File | Purpose |
|------|---------|
| `social_content.py` | Main content generator — creates captions, hashtags, image descriptions |
| `autoresponder.py` | AgentMail auto-responder — replies to client inquiries |
| `paypal_invoicing.py` | PayPal invoicing — creates invoices ($50-150/week) |
| `PRICING_GUIDE.md` | Full pricing guide with packages, FAQ, and service specs |
| `example_brand_info.json` | Sample brand details JSON for testing |

## Quick Start

### 1. Generate Content

```bash
# Weekly calendar (7 posts)
python social_content.py generate example_brand_info.json week

# Monthly calendar (30 posts)
python social_content.py generate example_brand_info.json month
```

### 2. Send Invoice

```bash
# Weekly package invoice
python paypal_invoicing.py invoice client@email.com week FitFuel

# Monthly package invoice
python paypal_invoicing.py invoice client@email.com monthly FitFuel
```

### 3. Run Auto-Responder

```bash
# Single check (for cron)
python autoresponder.py --once

# Continuous daemon
python autoresponder.py --daemon
```

### 4. Reply to Inquiry

```bash
python social_content.py reply inquiry.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENTMAIL_API_KEY` | No (has default) | AgentMail API key |
| `PAYPAL_CLIENT_ID` | No | PayPal API Client ID |
| `PAYPAL_CLIENT_SECRET` | No | PayPal API Secret |
| `PAYPAL_BASE_URL` | No | PayPal API URL (sandbox default) |
| `PAYPAL_WEBHOOK_ID` | No | PayPal webhook ID |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for notifications |

## Service Flow

```
Client emails brand details
        ↓
AgentMail auto-reply (acknowledgment + questions)
        ↓
Brand info collected → Generate content calendar
        ↓
PayPal invoice sent to client
        ↓
Payment received (Discord notification)
        ↓
Content delivered via email
        ↓
Revisions if requested
```

## Pricing

| Package | Price | Posts | Deliverables |
|---------|-------|-------|-------------|
| Weekly | $50/week | 7 posts | Caption + Hashtags + Image Description |
| Monthly | $150/month | 30 posts | Full content calendar + 2 revision rounds |

## Integrations

- **AgentMail** (am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7) — Email inbox at `mrbubba@agentmail.to`
- **PayPal** — Invoicing for $50-150/week packages
- **Discord** — Payment notifications via webhook
