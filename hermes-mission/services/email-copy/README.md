# Mr Bubba Services — Email Copywriting Service

Professional email copywriting that converts. Welcome sequences, promotional campaigns, follow-ups, and more.

## Quick Start

### 1. Generate Email Copy
```bash
python3 generate_email_copy.py --interactive
```

Or with a config file:
```bash
python3 generate_email_copy.py --config client_config.json
```

### 2. Auto-Respond to Inquiries
```bash
# One-time check
python3 automail_responder.py --mode respond

# Continuous watch
python3 automail_responder.py --mode watch --interval 300

# Webhook server
python3 automail_responder.py --mode webhook --port 8765
```

### 3. Send PayPal Invoice
```bash
python3 paypal_invoice.py create \
  --client "John Doe" \
  --email "john@example.com" \
  --tier professional \
  --description "Welcome Email for SaaS Product"
```

### 4. View Pricing Tiers
```bash
python3 paypal_invoice.py tiers
```

## Files

| File | Purpose |
|------|---------|
| `generate_email_copy.py` | Generates email copy from client input |
| `automail_responder.py` | AgentMail auto-responder for inquiries |
| `paypal_invoice.py` | PayPal invoicing ($25-75/email) |
| `PRICING_GUIDE.md` | Complete pricing and service guide |
| `client_config.example.json` | Example client configuration |

## Configuration

Set environment variables or edit defaults in scripts:

```bash
export AGENTMAIL_API_KEY="am_us_inbox_..."
export AGENTMAIL_INBOX="mrbubba@agentmail.to"
export PAYPAL_CLIENT_ID="your_paypal_client_id"
export PAYPAL_SECRET="your_paypal_secret"
export PAYPAL_MERCHANT_EMAIL="mrbubba@agentmail.to"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

## Service Flow

```
Client emails product details + target audience
        ↓
AgentMail auto-responder sends acknowledgment
        ↓
Generate email copy using client details
        ↓
Deliver finished copy via email
        ↓
Send PayPal invoice ($25-75/email)
        ↓
Discord notification on invoice creation/payment
```

## Pricing Summary

| Tier | Price | Best For |
|------|-------|----------|
| Basic | $25 | Simple emails, announcements |
| Professional | $45 | Strategic, high-converting copy |
| Premium | $75 | A/B variants, deep research |
| 3-Email Bundle | $100 | Welcome + promo + follow-up |
| 5-Email Bundle | $160 | Full campaign sequence |

See [PRICING_GUIDE.md](PRICING_GUIDE.md) for full details.
