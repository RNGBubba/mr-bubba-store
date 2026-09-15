# Mr Bubba Services — Automated Data Cleanup Pipeline

Fully autonomous data cleanup service that accepts messy CSV/Excel/text files via AgentMail email, cleans them automatically, and sends back the cleaned file + report.

## How It Works

1. **Client emails** a messy CSV/Excel/text file to `mrbubba@agentmail.to`
2. **Pipeline picks it up** automatically (polling AgentMail inbox)
3. **File is cleaned**: duplicates removed, whitespace trimmed, dates/phones/addresses standardized, quality metrics added
4. **Cleaned file + report** emailed back to client
5. **PayPal invoice** created ($75 per file)
6. **Discord notification** sent on cleanup completion and payment

## Files

| File | Purpose |
|------|---------|
| `data_cleanup_service.py` | Core data cleaning engine |
| `email_templates.py` | AgentMail auto-responder email templates |
| `payment_tracker.py` | PayPal integration + Discord webhook notifications |
| `pipeline.py` | Main orchestrator — watches inbox, runs pipeline |
| `config.yaml` | Service configuration |
| `README.md` | This file |

## Setup

```bash
# Install dependencies
pip install pandas openpyxl numpy requests

# Set environment variables (optional — has defaults for dev)
export PAYPAL_CLIENT_ID="your_paypal_client_id"
export PAYPAL_CLIENT_SECRET="your_paypal_client_secret"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

## Usage

### Process inbox once:
```bash
python pipeline.py once
```

### Run as daemon (polls every 60 seconds):
```bash
python pipeline.py daemon --interval 60
```

### Clean a single file:
```bash
python pipeline.py test-clean --file my_data.csv
```

### Create payment invoice:
```bash
python payment_tracker.py create --email client@example.com --name "John Doe" --file data.csv --ticket HD-001
```

### Check payment status:
```bash
python payment_tracker.py list
python payment_tracker.py summary --days 7
```

## Data Cleaning Features

- ✅ **Header normalization** — lowercase, underscores, no special characters
- ✅ **Whitespace trimming** — all string columns
- ✅ **Duplicate removal** — exact + fuzzy matching
- ✅ **Empty row/column removal**
- ✅ **Date standardization** — auto-detects date columns, formats to `YYYY-MM-DD`
- ✅ **Phone formatting** — US format `(XXX) XXX-XXXX`
- ✅ **Address normalization** — USPS abbreviations, title case
- ✅ **Summary calculations** — sum, mean, median, min, max for numeric columns
- ✅ **Data quality score** — percentage completeness

## Payment Flow

```
Client Email → File Received → Cleanup → Delivery → Invoice Created → Payment → Discord Notification
```

- **PayPal invoices** created automatically via PayPal REST API
- **Local payment tracking** stored in `payments/invoices.json`
- **Discord webhook** notifies on:
  - Invoice created
  - Payment received
  - Payment overdue
  - Cleanup completed
  - Weekly summary

## Email Auto-Responder Templates

| Template | When Sent |
|----------|-----------|
| `welcome` | File received confirmation |
| `processing` | Processing started notification |
| `delivery` | Cleaned file + report delivery |
| `invoice` | PayPal invoice with payment link |
| `payment_confirmed` | Thank you + confirmation |
| `error` | Processing error notification |
| `weekly_summary` | Weekly stats report |

## Configuration

Edit `config.yaml` to customize:

```yaml
service:
  name: "Mr Bubba Data Cleanup Service"
  price: 75.00
  currency: "USD"
  email: "mrbubba@agentmail.to"

cleaning:
  fuzzy_duplicate_threshold: 0.9
  date_output_format: "%Y-%m-%d"
  phone_format: "US"
  remove_empty_rows: true
  remove_empty_columns: true

payments:
  paypal_base_url: "https://api-m.sandbox.paypal.com"
  currency: "USD"
  terms: "Payment due within 7 days"

notifications:
  discord_enabled: true
  notify_on_cleanup: true
  notify_on_payment: true
  notify_weekly_summary: true
```

## Architecture

```
┌──────────────────────────────────────────────┐
│              Client Email (with file)         │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           AgentMail API (Inbox)               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│          Pipeline Orchestrator                │
│  ┌─────────────────────────────────────────┐ │
│  │  1. Download attachment                  │ │
│  │  2. Run data_cleanup_service            │ │
│  │  3. Generate report                      │ │
│  │  4. Send delivery email                  │ │
│  │  5. Create PayPal invoice                │ │
│  │  6. Notify Discord                       │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│  PayPal API  │    │  Discord Webhook │
│  (Invoicing) │    │  (Notifications) │
└──────────────┘    └──────────────────┘
```

---

**Service by Mr Bubba Services** | Powered by AgentMail | Invoices via PayPal
