#!/usr/bin/env python3
"""
AgentMail Auto-Responder for PDF Processing Service (Mr Bubba Services)
Handles incoming emails, processes attached PDFs, and sends responses.
"""

import argparse
import email
import imaplib
import json
import os
import smtplib
import sys
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

# Import the PDF processor
sys.path.insert(0, str(Path(__file__).parent))
from pdf_processor import PDFProcessor


# AgentMail configuration
AGENTMAIL_API_KEY = os.environ.get(
    "AGENTMAIL_API_KEY",
    "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7",
)
AGENTMAIL_INBOX = os.environ.get("AGENTMAIL_INBOX", "mrbubba@agentmail.to")

# Email templates
INQUIRY_RESPONSE = """Hi {sender_name},

Thanks for your interest in our PDF processing service.

I can help convert your PDFs into structured data — whether that's extracting text, pulling tables into CSV or Excel, or OCR-ing scanned documents. I work with invoices, reports, forms, and most other document types.

How it works is simple: email your PDF to this address, I'll process it automatically, and send back the extracted data in whatever format you need. Invoice comes via PayPal when it's done.

Pricing:
- Basic (1-5 pages, text extraction): $30
- Standard (6-20 pages, text + tables): $50
- Premium (21-100 pages, full extraction + OCR): $75
- Enterprise (100+ pages, bulk): $100
- Rush delivery (24hr): +$20

To give you the best service, it helps to know:
- How many pages your PDF has
- Whether it's a scanned document (needs OCR)
- What output format you'd prefer (CSV, Excel, Word, or all)
- If you need rush delivery

Just reply with your PDF attached whenever you're ready.

Best,
Mr Bubba Services
{inbox}
"""

PDF_RECEIVED_RESPONSE = """Hi {sender_name},

Got your PDF ({filename}) and it's been processed.

Here's what I found:
- {pages} pages
- {tables} tables detected
- {text_pages} pages of text extracted

The output files are attached. An invoice will be sent via PayPal for the service.

Let me know if anything looks off or if you need a different format.

Best,
Mr Bubba Services
"""

QUOTE_RESPONSE = """Hi {sender_name},

Thanks for asking about PDF processing.

For what you described — {pages} pages, {format} output, {needs_ocr}OCR needed, {rush}rush delivery — the estimated cost would be {cost}.

If that works for you, just reply with your PDF attached and we'll get started. I'll send a PayPal invoice once you confirm.

Best,
Mr Bubba Services
"""


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: Optional[list] = None,
    from_email: str = AGENTMAIL_INBOX,
) -> bool:
    """Send email with optional attachments using AgentMail SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachments:
            for filepath in attachments:
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(filepath)}"'
                    msg.attach(part)

        # AgentMail SMTP settings
        smtp_host = "smtp.agentmail.to"
        smtp_port = 587

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(AGENTMAIL_INBOX, AGENTMAIL_API_KEY)
            server.send_message(msg)

        print(f"Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def check_emails() -> list[dict]:
    """Check inbox for new emails using AgentMail IMAP."""
    emails = []
    try:
        imap_host = "imap.agentmail.to"
        imap_port = 993

        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(AGENTMAIL_INBOX, AGENTMAIL_API_KEY)
        mail.select("INBOX")

        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status == "OK":
            msg_ids = messages[0].split()
            for msg_id in msg_ids:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status == "OK":
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    sender = email.utils.parseaddr(email_message["From"])[1]
                    subject = email_message["Subject"] or ""
                    date = email_message["Date"] or ""

                    # Extract body
                    body = ""
                    attachments = []
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            elif part.get_content_disposition() == "attachment":
                                filename = part.get_filename()
                                if filename and filename.lower().endswith(".pdf"):
                                    attachments.append({
                                        "filename": filename,
                                        "data": part.get_payload(decode=True),
                                    })
                    else:
                        body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")

                    emails.append({
                        "id": msg_id,
                        "sender": sender,
                        "subject": subject,
                        "date": date,
                        "body": body,
                        "attachments": attachments,
                    })

        mail.logout()

    except Exception as e:
        print(f"Email check error: {e}")

    return emails


def determine_inquiry_type(body: str) -> str:
    """Determine the type of inquiry from email body."""
    body_lower = body.lower()

    if any(word in body_lower for word in ["quote", "pricing", "cost", "how much"]):
        return "quote"
    elif any(word in body_lower for word in ["hello", "hi", "hey", "inquiry", "interested", "services"]):
        return "inquiry"
    else:
        return "general"


def calculate_price(pages: int, needs_ocr: bool = False, rush: bool = False) -> int:
    """Calculate service price based on requirements."""
    if pages <= 5:
        base = 30
    elif pages <= 20:
        base = 50
    elif pages <= 100:
        base = 75
    else:
        base = 100

    if needs_ocr:
        base += 15
    if rush:
        base += 20

    return min(base, 150)


def process_incoming_emails(output_dir: str = "processed") -> list[str]:
    """Process all incoming emails and handle accordingly."""
    processed_files = []
    emails = check_emails()

    for email_data in emails:
        sender = email_data["sender"]
        subject = email_data["subject"]
        body = email_data["body"]
        attachments = email_data["attachments"]

        sender_name = sender.split("@")[0] if "@" in sender else "Valued Customer"

        # Check for PDF attachments
        pdf_files = [att for att in attachments if att["filename"].lower().endswith(".pdf")]

        if pdf_files:
            # Process PDFs
            for pdf_att in pdf_files:
                pdf_path = os.path.join(output_dir, pdf_att["filename"])
                os.makedirs(output_dir, exist_ok=True)

                with open(pdf_path, "wb") as f:
                    f.write(pdf_att["data"])

                # Process the PDF
                processor = PDFProcessor(output_dir=output_dir)
                start_time = time.time()
                results = processor.process_pdf(pdf_path)
                processing_time = time.time() - start_time

                # Generate outputs
                generated = []
                txt_file = processor.save_text()
                if txt_file:
                    generated.append(txt_file)
                csv_file = processor.save_to_csv()
                if csv_file:
                    generated.append(csv_file)
                xlsx_file = processor.save_to_excel()
                if xlsx_file:
                    generated.append(xlsx_file)
                docx_file = processor.save_to_word()
                if docx_file:
                    generated.append(docx_file)

                # Calculate price
                pages = results["pages"]
                needs_ocr = any(not t.strip() for t in results["text_content"])
                price = calculate_price(pages, needs_ocr)

                # Send response with files
                file_list_text = "\n".join([f"• {os.path.basename(f)}" for f in generated])
                response_body = PDF_RECEIVED_RESPONSE.format(
                    sender_name=sender_name,
                    filename=pdf_att["filename"],
                    pages=pages,
                    tables=len(results["tables"]),
                    text_pages=len(results["text_content"]),
                    file_list=file_list_text,
                    processing_time=processing_time,
                )

                send_email(
                    sender,
                    f"PDF Processed: {pdf_att['filename']}",
                    response_body,
                    attachments=generated,
                )

                processed_files.extend(generated)

        else:
            # Handle inquiry without PDF attachment
            inquiry_type = determine_inquiry_type(body)

            if inquiry_type == "quote":
                # Parse quote request details
                needs_ocr = "ocr" in body.lower() or "scan" in body.lower()
                rush = "rush" in body.lower() or "urgent" in body.lower()

                response_body = QUOTE_RESPONSE.format(
                    sender_name=sender_name,
                    pages="Please specify",
                    needs_ocr="Yes" if needs_ocr else "No/Unknown",
                    format="Please specify",
                    rush="Yes" if rush else "No",
                    cost="Please provide page count for accurate quote",
                )
            else:
                response_body = INQUIRY_RESPONSE.format(
                    sender_name=sender_name,
                    inbox=AGENTMAIL_INBOX,
                )

            send_email(
                sender,
                "Re: " + subject if subject else "Mr Bubba Services - PDF Processing",
                response_body,
            )

    return processed_files


def run_daemon(check_interval: int = 60):
    """Run as a daemon, checking for new emails periodically."""
    print(f"Starting PDF Processing Auto-Responder Daemon")
    print(f"Inbox: {AGENTMAIL_INBOX}")
    print(f"Check interval: {check_interval} seconds")
    print("-" * 60)

    while True:
        try:
            processed = process_incoming_emails()
            if processed:
                print(f"Processed {len(processed)} file(s)")
            time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Error in daemon loop: {e}")
            time.sleep(check_interval)


def main():
    parser = argparse.ArgumentParser(
        description="AgentMail Auto-Responder for PDF Processing Service"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a daemon (check emails periodically)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds for daemon mode (default: 60)",
    )
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Check emails once and exit",
    )
    parser.add_argument(
        "--output-dir",
        default="processed",
        help="Directory for processed files (default: processed)",
    )

    args = parser.parse_args()

    if args.daemon:
        run_daemon(args.interval)
    elif args.check_once:
        processed = process_incoming_emails(args.output_dir)
        print(f"Processed {len(processed)} file(s)")
    else:
        # Default: check once
        processed = process_incoming_emails(args.output_dir)
        print(f"Processed {len(processed)} file(s)")


if __name__ == "__main__":
    main()
