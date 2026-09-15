# Mr Bubba Services - Business Automation Script Service

Custom Python automation service for business workflows.

## Quick Start

1. **Inquiry**: Email your automation needs to mrbubba@agentmail.to
2. **Analysis**: I'll analyze your requirements and send a quote
3. **Payment**: PayPal invoice sent upon confirmation
4. **Delivery**: Custom script + documentation within 1-7 days

## Service Tiers

| Tier | Price | Timeline | Examples |
|------|-------|----------|----------|
| Simple | $150 | 1-2 days | File organizer, data converter |
| Standard | $250 | 2-4 days | Email automation, web scraper |
| Advanced | $400 | 5-7 days | API integration, data pipeline |
| Enterprise | $500+ | 7-14 days | Full workflow automation |

## Script Library

The following automation scripts are available as templates/modules:

1. **file_organizer.py** - Organize files by type, date, or keyword
2. **report_generator.py** - Generate HTML/Markdown reports from data
3. **email_sender.py** - Send automated/bulk emails via SMTP
4. **data_converter.py** - Convert between CSV, JSON, XML, Excel
5. **web_scraper.py** - Scrape data from websites
6. **pdf_processor.py** - Merge, split, watermark PDFs
7. **database_backup.py** - Backup MySQL/PostgreSQL/SQLite
8. **excel_automator.py** - Read, write, transform Excel files
9. **social_scheduler.py** - Schedule social media posts
10. **api_integrator.py** - Sync data between REST APIs

## Custom Automation Generator

Use the `generate_automation.py` script to analyze a client description
and generate a scaffold for custom automation:

```bash
# Analyze a client description
python generate_automation.py analyze "I need to organize my files and send reports"

# Generate a full quote with script scaffold
python generate_automation.py quote "I need to scrape data from websites and export to Excel"

# List available modules
python generate_automation.py modules
```

## AgentMail Auto-Responder Setup

See `templates/autoresponder_templates.md` for email templates.
Configure these in AgentMail dashboard with keyword triggers:

- Keywords: "automation", "automate", "script", "workflow"
- Auto-response: Template 1 (initial inquiry)
- Follow-up: Templates 2-8 as conversation progresses

## Payment

- Method: PayPal (invoice sent via email)
- Terms: Payment before development begins
- Refund: Full refund if requirements cannot be met

## Support

- 30 days email support included
- Response within 24 hours
- Monday-Friday, 9am-6pm UTC

## Configuration

Edit `config.json` to customize:
- Pricing tiers
- API key and inbox settings
- Service workflow
- Template references
