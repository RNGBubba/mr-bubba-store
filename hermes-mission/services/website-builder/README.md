# Mr Bubba Services — Website Builder Service Pipeline

A complete automated service that accepts business information via email, builds a professional 5-page website, deploys to GitHub Pages, sends a live preview, and handles payment ($299 via PayPal).

## Service Flow

```
Client emails business info → Auto-responder acknowledges → Agent builds site → 
Deploy to GitHub Pages → Send preview → Client pays $299 via PayPal → 
Webhook confirms → Site goes live → Discord notification
```

## Directory Structure

```
website-builder/
├── templates/                  # HTML/CSS/JS templates
│   ├── index.html             # Homepage template
│   ├── about.html             # About page template
│   ├── services.html          # Services page template
│   ├── portfolio.html         # Portfolio page template
│   ├── contact.html           # Contact page template
│   ├── css/
│   │   └── style.css          # Professional responsive CSS
│   └── js/
│       └── main.js            # Mobile menu, animations, form handling
├── scripts/
│   ├── build_site.py          # Main site generator (CLI + config)
│   ├── deploy.py              # GitHub Pages deployment
│   ├── payment.py             # PayPal invoice & webhook handling
│   ├── webhook_server.py      # HTTP server for PayPal/AgentMail webhooks
│   └── orchestrator.py        # Full pipeline orchestrator
├── email-templates/
│   └── agentmail_responder.py # Auto-responder templates & classifier
├── configs/
│   └── sample-business.json   # Example business config
└── output/                     # Generated sites (gitignored)
```

## Quick Start

### 1. Build a Site

```bash
# Using config file
python3 scripts/build_site.py --config configs/sample-business.json

# Using CLI args
python3 scripts/build_site.py \
  --business-name "ABC Plumbing" \
  --category plumbing \
  --city "Dallas" \
  --state TX \
  --phone "(214) 555-1234" \
  --email "info@abcplumbing.com"
```

### 2. Deploy to GitHub Pages

```bash
python3 scripts/deploy.py output/abc-plumbing --repo-name abc-plumbing-site
```

### 3. Run Full Pipeline

```bash
python3 scripts/orchestrator.py \
  --config configs/sample-business.json \
  --auto-deploy
```

### 4. Start Webhook Server

```bash
python3 scripts/webhook_server.py
# Listens on port 8765
# PayPal webhook: POST /webhook/paypal
# Health check: GET /health
```

## AgentMail Integration

**Inbox:** mrbubba@agentmail.to  
**API Key:** am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7

### Auto-Responder Templates

The `email-templates/agentmail_responder.py` module provides:

| Template | Trigger | Purpose |
|----------|---------|---------|
| `INITIAL_RESPONSE` | New inquiry | Asks for business info |
| `INFO_RECEIVED` | Client sends details | Acknowledges & starts build |
| `PREVIEW_READY` | Site built | Sends preview link + payment |
| `PAYMENT_CONFIRMATION` | PayPal webhook fires | Confirms live site |
| `PAYMENT_REMINDER` | 3 days no payment | Gentle reminder |
| `FOLLOW_UP` | 7 days no response | Check-in |
| `NOT_INTERESTED` | Client declines | Graceful exit |

### Email Classification

The classifier detects intent from subject/body:
- **Business info** → triggers `INFO_RECEIVED`
- **Payment request** → triggers `PREVIEW_READY`
- **Not interested** → triggers `NOT_INTERESTED`
- **Questions** → triggers `INITIAL_RESPONSE`

## Payment Flow ($299)

### PayPal Integration

```python
from payment import generate_paypal_buy_now_link, generate_paypal_invoice

# Generate payment link
link = generate_paypal_buy_now_link(
    client_name="John Smith",
    client_email="john@example.com",
    business_name="ABC Plumbing"
)

# Generate formal invoice
invoice = generate_paypal_invoice(
    client_name="John Smith",
    client_email="john@example.com",
    business_name="ABC Plumbing"
)
```

### Webhook Events Handled

- `PAYMENT.SALE.COMPLETED` → Deploy site, notify Discord
- `INVOICING.INVOICE.PAID` → Deploy site, notify Discord
- `PAYMENT.SALE.REFUNDED` → Handle refund

### Discord Notifications

Payment events are forwarded to Discord via webhook (configured via `DISCORD_WEBHOOK_URL` env var).

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MR_BUBBA_WEBHOOK_PORT` | Webhook server port | 8765 |
| `DISCORD_WEBHOOK_URL` | Discord notification webhook | (none) |
| `PAYPAL_CLIENT_ID` | PayPal API client ID | (none) |
| `PAYPAL_CLIENT_SECRET` | PayPal API secret | (none) |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook ID | (none) |

### Business Config JSON

```json
{
  "business_name": "Your Business",
  "category": "plumbing|landscaping|cleaning|roofing|...",
  "city": "Dallas",
  "state": "TX",
  "address": "123 Main St",
  "phone": "(214) 555-1234",
  "email": "info@yourbusiness.com",
  "social_links": {
    "facebook": "https://facebook.com/yourpage",
    "instagram": "https://instagram.com/yourpage"
  }
}
```

## Template Features

- ✅ 5 pages: Home, About, Services, Portfolio, Contact
- ✅ Mobile-responsive (breakpoints at 1024px, 768px, 480px)
- ✅ Professional typography (Inter + Playfair Display)
- ✅ Smooth scroll animations (Intersection Observer)
- ✅ Portfolio filtering
- ✅ Contact form with validation
- ✅ Google Maps embed
- ✅ Social media links
- ✅ Testimonials section
- ✅ SEO meta tags
- ✅ Fast loading (no external JS deps)

## Deployment

Sites are deployed to GitHub Pages under the `RNGBubba` account:
- URL format: `https://rngbubba.github.io/{repo-name}/`
- Custom domains supported via CNAME
- Automatic HTTPS via GitHub Pages
- 99.9% uptime SLA

## Pricing

**$299 flat rate** includes:
- 5-page custom website
- Professional design
- Mobile responsiveness
- Contact form
- Portfolio gallery
- Google Maps integration
- SEO optimization
- GitHub Pages deployment
- 7 days free revisions
- Free hosting (GitHub Pages)

## License

Mr Bubba Services — Proprietary
