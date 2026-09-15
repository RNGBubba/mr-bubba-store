#!/usr/bin/env python3
"""
Mr Bubba Services — Full Pipeline Orchestrator.
Watches AgentMail inbox, processes incoming data files,
runs cleanup, sends reports, and manages payment flow.

This is the main entry point for the autonomous data cleanup service.
"""

import os
import re
import sys
import time
import json
import hashlib
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from data_cleanup_service import clean_data, generate_text_report, load_file, SERVICE_PRICE
from email_templates import render_template, AGENTMAIL_CONFIG
from payment_tracker import PaymentOrchestrator, PaymentTracker, DiscordNotifier

# ============================================================
# CONFIGURATION
# ============================================================
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
AGENTMAIL_BASE_URL = "https://api.agentmail.to/v1"

# Directories
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

for d in [INPUT_DIR, OUTPUT_DIR, REPORT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("mr-bubba-pipeline")

# Supported file extensions
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt", ".tsv"}


# ============================================================
# AGENTMAIL CLIENT
# ============================================================
class AgentMailClient:
    """Client for AgentMail API to receive and send emails."""

    def __init__(self, api_key: str = AGENTMAIL_API_KEY):
        self.api_key = api_key
        self.base_url = AGENTMAIL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_inbox_emails(self, unread_only: bool = True) -> list:
        """Fetch emails from inbox."""
        url = f"{self.base_url}/emails"
        params = {"inbox": AGENTMAIL_INBOX, "unread": unread_only}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("emails", [])
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def get_email(self, email_id: str) -> dict:
        """Get a specific email by ID."""
        url = f"{self.base_url}/emails/{email_id}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            return {}

    def download_attachment(self, attachment_url: str, save_path: Path) -> bool:
        """Download an email attachment."""
        try:
            resp = requests.get(attachment_url, headers=self.headers, timeout=60)
            resp.raise_for_status()
            save_path.write_bytes(resp.content)
            logger.info(f"Downloaded attachment: {save_path.name} ({len(resp.content)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to download attachment: {e}")
            return False

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[list[Path]] = None,
    ) -> bool:
        """Send an email via AgentMail."""
        url = f"{self.base_url}/emails/send"
        payload = {
            "from": AGENTMAIL_INBOX,
            "to": to,
            "subject": subject,
            "body": body,
        }

        try:
            if attachments:
                # Multipart upload for attachments
                files = []
                for att in attachments:
                    files.append(("attachments", (att.name, att.read_bytes())))
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=payload,
                    files=files,
                    timeout=60,
                )
            else:
                resp = requests.post(url, headers=self.headers, json=payload, timeout=30)

            resp.raise_for_status()
            logger.info(f"Sent email to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        url = f"{self.base_url}/emails/{email_id}/read"
        try:
            resp = requests.post(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False


# ============================================================
# TICKET MANAGER
# ============================================================
class TicketManager:
    """Generates and tracks support tickets."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (BASE_DIR / "tickets.json")
        self.tickets = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self.tickets = json.loads(self.storage_path.read_text())

    def _save(self):
        self.storage_path.write_text(json.dumps(self.tickets, indent=2, default=str))

    def create(self, client_email: str, filename: str) -> str:
        """Create a new ticket. Returns ticket ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        email_hash = hashlib.md5(client_email.encode()).hexdigest()[:4]
        ticket_id = f"HD-{timestamp}-{email_hash}"

        self.tickets[ticket_id] = {
            "client_email": client_email,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
            "status": "received",
        }
        self._save()
        return ticket_id

    def get(self, ticket_id: str) -> Optional[dict]:
        return self.tickets.get(ticket_id)

    def update_status(self, ticket_id: str, status: str):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["status"] = status
            self.tickets[ticket_id]["updated_at"] = datetime.now().isoformat()
            self._save()


# ============================================================
# PIPELINE ORCHESTRATOR
# ============================================================
class DataCleanupPipeline:
    """Full autonomous pipeline for data cleanup service."""

    def __init__(self):
        self.mail = AgentMailClient()
        self.tickets = TicketManager()
        self.payments = PaymentOrchestrator()
        self.notifier = DiscordNotifier()

    def process_inbox(self):
        """Check inbox for new files and process them."""
        logger.info("Checking inbox for new emails...")

        emails = self.mail.get_inbox_emails(unread_only=True)
        if not emails:
            logger.info("No new emails found.")
            return

        logger.info(f"Found {len(emails)} unread email(s)")

        for email in emails:
            email_id = email.get("id", "")
            sender = email.get("from", "")
            subject = email.get("subject", "")

            logger.info(f"Processing email from {sender}: {subject}")

            # Skip our own emails
            if AGENTMAIL_INBOX in sender:
                self.mail.mark_as_read(email_id)
                continue

            # Check for attachments
            attachments = email.get("attachments", [])
            file_attachments = [
                att for att in attachments
                if Path(att.get("filename", "")).suffix.lower() in SUPPORTED_EXTENSIONS
            ]

            if not file_attachments:
                # No file attachment — send error/warning
                self._send_no_file_reply(sender)
                self.mail.mark_as_read(email_id)
                continue

            # Process each file attachment
            for att in file_attachments:
                self._process_file(email_id, sender, att)

            self.mail.mark_as_read(email_id)

    def _process_file(self, email_id: str, sender: str, attachment: dict):
        """Process a single file attachment."""
        filename = attachment.get("filename", "unknown")
        file_size = attachment.get("size", 0)
        download_url = attachment.get("download_url", "")

        logger.info(f"Processing file: {filename} ({file_size} bytes) from {sender}")

        # Create ticket
        ticket_id = self.tickets.create(sender, filename)
        self.tickets.update_status(ticket_id, "processing")

        # Send welcome email
        subject, body = render_template(
            "welcome",
            client_name=self._extract_name(sender),
            filename=filename,
            file_size=self._format_size(file_size),
            ticket_id=ticket_id,
        )
        self.mail.send_email(sender, subject, body)

        # Download file
        file_path = INPUT_DIR / f"{ticket_id}_{filename}"
        if not self.mail.download_attachment(download_url, file_path):
            self._send_error(sender, filename, ticket_id, "Failed to download file from email.")
            self.tickets.update_status(ticket_id, "error")
            return

        # Run cleanup
        try:
            report = clean_data(file_path)
        except Exception as e:
            logger.error(f"Cleanup failed for {filename}: {e}")
            self._send_error(sender, filename, ticket_id, f"Processing error: {str(e)}")
            self.tickets.update_status(ticket_id, "error")
            return

        if not report.get("success"):
            self._send_error(sender, filename, ticket_id, report.get("error", "Unknown error"))
            self.tickets.update_status(ticket_id, "error")
            return

        # Send delivery email with attachments
        text_report = generate_text_report(report)
        report_path = Path(report.get("report_file", ""))

        # Save text report
        if report_path:
            text_report_path = report_path.with_suffix(".txt")
            text_report_path.write_text(text_report)

        delivery_subject, delivery_body = render_template(
            "delivery",
            client_name=self._extract_name(sender),
            filename=filename,
            ticket_id=ticket_id,
            original_rows=report.get("original_rows", 0),
            final_rows=report.get("final_rows", 0),
            dups_removed=sum(s.get("rows_removed", 0) for s in report.get("steps", []) if "remove" in s.get("step", "")),
            empty_rows=next((s.get("empty_rows_removed", 0) for s in report.get("steps", []) if s.get("step") == "remove_empty"), 0),
            dates_fixed=next((s.get("values_standardized", 0) for s in report.get("steps", []) if s.get("step") == "standardize_dates"), 0),
            phones_fixed=next((s.get("values_standardized", 0) for s in report.get("steps", []) if s.get("step") == "standardize_phones"), 0),
            addresses_fixed=next((s.get("values_standardized", 0) for s in report.get("steps", []) if s.get("step") == "standardize_addresses"), 0),
            quality_score=next((c.get("score", "N/A") for c in report.get("calculations", []) if c[0] == "data_quality_score"), "N/A"),
        )

        output_path = Path(report.get("output_file", ""))
        attachments_list = [p for p in [output_path, text_report_path] if p and p.exists()]
        self.mail.send_email(sender, delivery_subject, delivery_body, attachments=attachments_list)

        # Create payment invoice
        try:
            invoice = self.payments.process_payment(
                client_email=sender,
                client_name=self._extract_name(sender),
                filename=filename,
                ticket_id=ticket_id,
                send_invoice=False,  # We'll handle invoicing separately
            )
            logger.info(f"Invoice created: {invoice.invoice_id}")
        except Exception as e:
            logger.warning(f"Could not create invoice via PayPal API: {e}")
            # Create local invoice only
            invoice = self.payments.tracker.create_invoice(
                client_email=sender,
                client_name=self._extract_name(sender),
                filename=filename,
                ticket_id=ticket_id,
            )
            self.notifier.notify_invoice_created(invoice)

        # Discord notification
        self.notifier.notify_cleanup_completed(
            client_email=sender,
            filename=filename,
            rows=report.get("final_rows", 0),
            quality=next((c.get("score", 0) for c in report.get("calculations", []) if c[0] == "data_quality_score"), 0),
        )

        self.tickets.update_status(ticket_id, "complete")
        logger.info(f"Pipeline complete for ticket {ticket_id}")

    def _send_no_file_reply(self, recipient: str):
        """Send reply when no file is attached."""
        subject = "📎 No File Attached — Mr Bubba Data Cleanup"
        body = f"""Hi,

Thanks for your email! However, we didn't find any attached data files.

Please attach your CSV, Excel, or text file and resend.

We accept:
• CSV files (.csv)
• Excel files (.xlsx, .xls)
• Text files (.txt, .tsv)

Once you send a file, we'll automatically clean it and send it back within minutes.

Price: ${SERVICE_PRICE:.2f} per file

— Mr Bubba Services
"""
        self.mail.send_email(recipient, subject, body)

    def _send_error(self, recipient: str, filename: str, ticket_id: str, error: str):
        """Send error notification to client."""
        subject, body = render_template(
            "error",
            client_name=self._extract_name(recipient),
            filename=filename,
            ticket_id=ticket_id,
            error_message=error,
        )
        self.mail.send_email(recipient, subject, body)

    @staticmethod
    def _extract_name(email: str) -> str:
        """Extract a friendly name from an email address."""
        name = email.split("@")[0]
        name = re.sub(r"[._\-]+", " ", name).strip().title()
        return name or "Valued Client"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


# ============================================================
# DAEMON MODE
# ============================================================
def run_daemon(interval: int = 60):
    """Run the pipeline as a background daemon, checking inbox every N seconds."""
    logger.info(f"Starting Mr Bubba Data Cleanup Service daemon (poll interval: {interval}s)")
    pipeline = DataCleanupPipeline()

    while True:
        try:
            pipeline.process_inbox()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Pipeline error: {e}")

        time.sleep(interval)


# ============================================================
# CLI
# ============================================================
def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Mr Bubba Services - Pipeline Orchestrator")
    parser.add_argument(
        "command",
        choices=["process", "daemon", "once", "test-clean"],
        help="Command to run",
    )
    parser.add_argument("--file", help="File to clean (for test-clean)")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds for daemon")
    args = parser.parse_args()

    if args.command == "process" or args.command == "once":
        pipeline = DataCleanupPipeline()
        pipeline.process_inbox()

    elif args.command == "daemon":
        run_daemon(args.interval)

    elif args.command == "test-clean":
        if not args.file:
            print("ERROR: --file required for test-clean")
            return
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            return
        report = clean_data(file_path)
        if report["success"]:
            text = generate_text_report(report)
            print(text)
        else:
            print(f"Cleanup failed: {report.get('error')}")


if __name__ == "__main__":
    main()
