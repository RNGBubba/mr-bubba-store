#!/usr/bin/env python3
"""
Mr Bubba Services — Payment Tracking & Discord Notifications.
Handles PayPal invoice tracking, payment status, and Discord webhook notifications
for the data cleanup service.

Features:
- Create PayPal invoices
- Track payment status
- Send Discord notifications on payment events
- Payment history and reporting
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

import requests

# ============================================================
# CONFIGURATION
# ============================================================
SERVICE_NAME = "Mr Bubba Data Cleanup Service"
SERVICE_EMAIL = "mrbubba@agentmail.to"
SERVICE_PRICE = 75.00

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "your_client_id")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "your_client_secret")
PAYPAL_BASE_URL = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
PAYPAL_INVOICE_URL = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices"

# Discord Configuration
DISCORD_WEBHOOK_URL = os.environ.get(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/your/webhook_id/your_webhook_token"
)

# Directories
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
PAYMENTS_DIR = BASE_DIR / "payments"
for d in [LOG_DIR, PAYMENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "payments.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("mr-bubba-payments")


# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class Invoice:
    """Represents a PayPal invoice for data cleanup service."""
    invoice_id: str
    client_email: str
    client_name: str
    filename: str
    ticket_id: str
    amount: float = SERVICE_PRICE
    currency: str = "USD"
    status: str = "pending"  # pending, sent, paid, cancelled, overdue
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    paid_at: Optional[str] = None
    paypal_invoice_id: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class PaymentNotification:
    """Notification payload for Discord webhook."""
    event: str  # invoice_created, payment_received, payment_overdue
    invoice: Invoice
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# PAYPAL API INTEGRATION
# ============================================================
class PayPalClient:
    """Client for interacting with PayPal's REST API."""

    def __init__(self):
        self.base_url = PAYPAL_BASE_URL
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self._access_token = None

    def _get_access_token(self) -> str:
        """Get OAuth2 access token from PayPal."""
        if self._access_token:
            return self._access_token

        auth_url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            resp = requests.post(
                auth_url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=30,
            )
            resp.raise_for_status()
            self._access_token = resp.json()["access_token"]
            logger.info("Obtained PayPal access token")
            return self._access_token
        except Exception as e:
            logger.error(f"Failed to get PayPal access token: {e}")
            raise

    def _headers(self) -> dict:
        """Get authenticated headers."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

    def create_invoice(
        self,
        client_email: str,
        client_name: str,
        description: str,
        amount: float = SERVICE_PRICE,
        currency: str = "USD",
    ) -> dict:
        """Create a PayPal invoice via the API."""
        payload = {
            "detail": {
                "invoice_number": f"HD-{datetime.now().strftime('%Y%m%d')}-{hashlib.md5(client_email.encode()).hexdigest()[:6].upper()}",
                "reference": description,
                "currency_code": currency,
                "note": f"Mr Bubba Data Cleanup Service - {description}",
                "terms_and_conditions": "Payment due within 7 days. Thank you!",
            },
            "invoicer": {
                "name": {
                    "given_name": "Mr Bubba",
                    "surname": "Data Services",
                },
                "email_address": SERVICE_EMAIL,
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "name": {
                            "given_name": client_name,
                        },
                        "email_address": client_email,
                    },
                }
            ],
            "items": [
                {
                    "name": "Data Cleanup Service",
                    "description": description,
                    "quantity": "1",
                    "unit_amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                }
            ],
            "configuration": {
                "allow_tip": False,
                "tax_calculated_after_discount": False,
                "tax_inclusive": False,
            },
        }

        try:
            resp = requests.post(
                PAYPAL_INVOICE_URL,
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"PayPal invoice created: {result.get('id', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"Failed to create PayPal invoice: {e}")
            return {"error": str(e)}

    def send_invoice(self, invoice_id: str) -> bool:
        """Send an existing PayPal invoice to the recipient."""
        url = f"{PAYPAL_INVOICE_URL}/{invoice_id}/send"
        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                json={},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"PayPal invoice sent: {invoice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send invoice {invoice_id}: {e}")
            return False

    def get_invoice_status(self, invoice_id: str) -> str:
        """Get the current status of a PayPal invoice."""
        url = f"{PAYPAL_INVOICE_URL}/{invoice_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            status = resp.json().get("status", "UNKNOWN")
            logger.info(f"Invoice {invoice_id} status: {status}")
            return status
        except Exception as e:
            logger.error(f"Failed to get invoice status {invoice_id}: {e}")
            return "ERROR"

    def list_invoices(self, page: int = 1, page_size: int = 10) -> list:
        """List recent PayPal invoices."""
        url = f"{PAYPAL_INVOICE_URL}?page={page}&page_size={page_size}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            return resp.json().get("invoices", [])
        except Exception as e:
            logger.error(f"Failed to list invoices: {e}")
            return []


# ============================================================
# PAYMENT TRACKER
# ============================================================
class PaymentTracker:
    """Tracks all invoices and payment history locally."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (PAYMENTS_DIR / "invoices.json")
        self.invoices: dict[str, Invoice] = {}
        self._load()

    def _load(self):
        """Load invoices from disk."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for inv_id, inv_data in data.items():
                    self.invoices[inv_id] = Invoice(**inv_data)
                logger.info(f"Loaded {len(self.invoices)} invoices")
            except Exception as e:
                logger.warning(f"Could not load invoices: {e}")

    def _save(self):
        """Persist invoices to disk."""
        data = {inv_id: inv.to_dict() for inv_id, inv in self.invoices.items()}
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))
        logger.info(f"Saved {len(self.invoices)} invoices")

    def create_invoice(
        self,
        client_email: str,
        client_name: str,
        filename: str,
        ticket_id: str,
        amount: float = SERVICE_PRICE,
    ) -> Invoice:
        """Create a new invoice entry."""
        invoice = Invoice(
            invoice_id=f"HD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            client_email=client_email,
            client_name=client_name,
            filename=filename,
            ticket_id=ticket_id,
            amount=amount,
        )
        self.invoices[invoice.invoice_id] = invoice
        self._save()
        logger.info(f"Created invoice: {invoice.invoice_id}")
        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Retrieve an invoice by ID."""
        return self.invoices.get(invoice_id)

    def mark_sent(self, invoice_id: str, paypal_invoice_id: str):
        """Mark an invoice as sent via PayPal."""
        if invoice_id in self.invoices:
            self.invoices[invoice_id].status = "sent"
            self.invoices[invoice_id].paypal_invoice_id = paypal_invoice_id
            self._save()

    def mark_paid(self, invoice_id: str, transaction_id: str = ""):
        """Mark an invoice as paid."""
        if invoice_id in self.invoices:
            self.invoices[invoice_id].status = "paid"
            self.invoices[invoice_id].paid_at = datetime.now().isoformat()
            self.invoices[invoice_id].transaction_id = transaction_id
            self._save()
            logger.info(f"Invoice {invoice_id} marked as paid")

    def get_pending(self) -> list[Invoice]:
        """Get all pending invoices."""
        return [inv for inv in self.invoices.values() if inv.status in ("pending", "sent")]

    def get_total_revenue(self) -> float:
        """Calculate total revenue from paid invoices."""
        return sum(inv.amount for inv in self.invoices.values() if inv.status == "paid")

    def get_weekly_summary(self, days: int = 7) -> dict:
        """Get summary for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            inv for inv in self.invoices.values()
            if datetime.fromisoformat(inv.created_at) >= cutoff
        ]
        return {
            "period_days": days,
            "total_invoices": len(recent),
            "paid": sum(1 for inv in recent if inv.status == "paid"),
            "pending": sum(1 for inv in recent if inv.status in ("pending", "sent")),
            "revenue": sum(inv.amount for inv in recent if inv.status == "paid"),
            "clients": list(set(inv.client_email for inv in recent)),
        }


# ============================================================
# DISCORD NOTIFICATIONS
# ============================================================
class DiscordNotifier:
    """Send payment event notifications to Discord."""

    def __init__(self, webhook_url: str = DISCORD_WEBHOOK_URL):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url and "your" not in webhook_url)

    def _send(self, payload: dict) -> bool:
        """Send payload to Discord webhook."""
        if not self.enabled:
            logger.info(f"[DISCORD DISABLED] Would send: {payload.get('content', '')[:100]}")
            return False

        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info("Discord notification sent")
            return True
        except Exception as e:
            logger.error(f"Discord webhook failed: {e}")
            return False

    def notify_invoice_created(self, invoice: Invoice):
        """Notify Discord that a new invoice was created."""
        embed = {
            "title": "🧾 Invoice Created",
            "color": 3447003,  # Blue
            "fields": [
                {"name": "Invoice ID", "value": invoice.invoice_id, "inline": True},
                {"name": "Client", "value": invoice.client_name, "inline": True},
                {"name": "Amount", "value": f"${invoice.amount:.2f}", "inline": True},
                {"name": "File", "value": invoice.filename, "inline": False},
                {"name": "Status", "value": "⏳ Pending", "inline": True},
            ],
            "timestamp": invoice.created_at,
            "footer": {"text": SERVICE_NAME},
        }
        self._send({"embeds": [embed]})

    def notify_payment_received(self, invoice: Invoice):
        """Notify Discord that payment was received."""
        embed = {
            "title": "💰 Payment Received!",
            "color": 3066993,  # Green
            "fields": [
                {"name": "Invoice ID", "value": invoice.invoice_id, "inline": True},
                {"name": "Client", "value": invoice.client_name, "inline": True},
                {"name": "Amount", "value": f"**${invoice.amount:.2f}**", "inline": True},
                {"name": "Transaction", "value": invoice.transaction_id or "N/A", "inline": True},
                {"name": "File", "value": invoice.filename, "inline": False},
                {"name": "Status", "value": "✅ Paid", "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": SERVICE_NAME},
        }
        self._send({"embeds": [embed]})

    def notify_payment_overdue(self, invoice: Invoice):
        """Notify Discord about an overdue payment."""
        embed = {
            "title": "⚠️ Payment Overdue",
            "color": 15158332,  # Red
            "fields": [
                {"name": "Invoice ID", "value": invoice.invoice_id, "inline": True},
                {"name": "Client", "value": invoice.client_name, "inline": True},
                {"name": "Amount", "value": f"${invoice.amount:.2f}", "inline": True},
                {"name": "Due Since", "value": invoice.created_at[:10], "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": SERVICE_NAME},
        }
        self._send({"embeds": [embed]})

    def notify_weekly_summary(self, summary: dict):
        """Send weekly summary to Discord."""
        embed = {
            "title": "📊 Weekly Payment Summary",
            "color": 10181046,  # Purple
            "fields": [
                {"name": "Period", "value": f"{summary['period_days']} days", "inline": True},
                {"name": "Invoices", "value": str(summary["total_invoices"]), "inline": True},
                {"name": "Paid", "value": str(summary["paid"]), "inline": True},
                {"name": "Pending", "value": str(summary["pending"]), "inline": True},
                {"name": "Revenue", "value": f"${summary['revenue']:.2f}", "inline": True},
                {"name": "Clients", "value": str(len(summary["clients"])), "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": SERVICE_NAME},
        }
        self._send({"embeds": [embed]})

    def notify_cleanup_completed(self, client_email: str, filename: str, rows: int, quality: float):
        """Notify Discord that a data cleanup job completed."""
        embed = {
            "title": "🧹 Cleanup Complete",
            "color": 3447003,  # Blue
            "fields": [
                {"name": "Client", "value": client_email, "inline": True},
                {"name": "File", "value": filename, "inline": True},
                {"name": "Rows Processed", "value": f"{rows:,}", "inline": True},
                {"name": "Quality Score", "value": f"{quality}%", "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": SERVICE_NAME},
        }
        self._send({"embeds": [embed]})


# ============================================================
# PAYPAL WEBHOOK HANDLER
# ============================================================
def handle_paypal_webhook(payload: dict) -> dict:
    """
    Handle incoming PayPal webhook events.
    Called when PayPal sends payment notifications.
    
    Expected event types:
    - PAYMENT.SALE.COMPLETED
    - INVOICING.INVOICE.PAID
    - INVOICING.INVOICE.CANCELLED
    """
    event_type = payload.get("event_type", "unknown")
    resource = payload.get("resource", {})

    logger.info(f"PayPal webhook received: {event_type}")

    result = {"event": event_type, "status": "processed"}

    if event_type in ("PAYMENT.SALE.COMPLETED", "INVOICING.INVOICE.PAID"):
        # Payment received
        sale_id = resource.get("id", "")
        invoice_id = resource.get("invoice_id", "")
        amount = resource.get("amount", {}).get("total", "0.00")
        currency = resource.get("amount", {}).get("currency", "USD")

        result["transaction_id"] = sale_id
        result["amount"] = amount

        logger.info(f"Payment received: {sale_id} for invoice {invoice_id}: {amount} {currency}")

        # Update local tracker
        tracker = PaymentTracker()
        # Find invoice by PayPal invoice ID
        for inv_id, inv in tracker.invoices.items():
            if inv.paypal_invoice_id == invoice_id:
                tracker.mark_paid(inv_id, sale_id)
                # Send Discord notification
                notifier = DiscordNotifier()
                notifier.notify_payment_received(tracker.invoices[inv_id])
                result["invoice_id"] = inv_id
                break

    elif event_type == "INVOICING.INVOICE.CANCELLED":
        invoice_id = resource.get("id", "")
        result["invoice_id"] = invoice_id
        logger.info(f"Invoice cancelled: {invoice_id}")

    return result


# ============================================================
# ORCHESTRATOR
# ============================================================
class PaymentOrchestrator:
    """Orchestrates the full payment flow for data cleanup service."""

    def __init__(self):
        self.paypal = PayPalClient()
        self.tracker = PaymentTracker()
        self.notifier = DiscordNotifier()

    def process_payment(
        self,
        client_email: str,
        client_name: str,
        filename: str,
        ticket_id: str,
        send_invoice: bool = True,
    ) -> Invoice:
        """Full payment flow: create invoice -> send -> notify."""
        # 1. Create local invoice
        invoice = self.tracker.create_invoice(
            client_email=client_email,
            client_name=client_name,
            filename=filename,
            ticket_id=ticket_id,
        )

        # 2. Create PayPal invoice
        paypal_result = self.paypal.create_invoice(
            client_email=client_email,
            client_name=client_name,
            description=f"Data cleanup: {filename}",
        )

        if "error" not in paypal_result:
            paypal_id = paypal_result.get("id", "")
            invoice.paypal_invoice_id = paypal_id

            # 3. Send invoice
            if send_invoice and paypal_id:
                self.paypal.send_invoice(paypal_id)
                self.tracker.mark_sent(invoice.invoice_id, paypal_id)

        # 4. Notify Discord
        self.notifier.notify_invoice_created(invoice)

        return invoice

    def check_and_notify_overdue(self):
        """Check for overdue invoices and send reminders."""
        pending = self.tracker.get_pending()
        overdue_count = 0
        for inv in pending:
            created = datetime.fromisoformat(inv.created_at)
            if datetime.now() - created > timedelta(days=7):
                self.notifier.notify_payment_overdue(inv)
                overdue_count += 1
        logger.info(f"Overdue check: {overdue_count} overdue invoices")
        return overdue_count


# ============================================================
# CLI
# ============================================================
def main():
    """CLI for payment operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Mr Bubba Services - Payment Tracker")
    parser.add_argument("command", choices=["create", "status", "list", "summary", "webhook-test"])
    parser.add_argument("--email", help="Client email")
    parser.add_argument("--name", help="Client name")
    parser.add_argument("--file", help="Processed filename")
    parser.add_argument("--ticket", help="Ticket ID")
    parser.add_argument("--invoice-id", help="Invoice ID to check")
    parser.add_argument("--days", type=int, default=7, help="Days for summary")
    args = parser.parse_args()

    orch = PaymentOrchestrator()

    if args.command == "create":
        if not all([args.email, args.name, args.file, args.ticket]):
            print("ERROR: --email, --name, --file, --ticket required")
            return
        invoice = orch.process_payment(args.email, args.name, args.file, args.ticket)
        print(f"Invoice created: {invoice.invoice_id}")
        print(f"Amount: ${invoice.amount:.2f}")
        print(f"Status: {invoice.status}")

    elif args.command == "status":
        if not args.invoice_id:
            print("ERROR: --invoice-id required")
            return
        inv = orch.tracker.get_invoice(args.invoice_id)
        if inv:
            print(json.dumps(inv.to_dict(), indent=2))
        else:
            print(f"Invoice not found: {args.invoice_id}")

    elif args.command == "list":
        pending = orch.tracker.get_pending()
        for inv in pending:
            print(f"{inv.invoice_id} | {inv.client_email} | ${inv.amount:.2f} | {inv.status}")

    elif args.command == "summary":
        summary = orch.tracker.get_weekly_summary(args.days)
        print(json.dumps(summary, indent=2))

    elif args.command == "webhook-test":
        # Simulate a payment webhook
        test_payload = {
            "event_type": "PAYMENT.SALE.COMPLETED",
            "resource": {
                "id": "TEST123",
                "amount": {"total": "75.00", "currency": "USD"},
            },
        }
        result = handle_paypal_webhook(test_payload)
        print(f"Webhook test result: {result}")


if __name__ == "__main__":
    main()
