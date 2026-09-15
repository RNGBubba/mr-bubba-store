#!/usr/bin/env python3
"""
API Integration Code Generator
Mr Bubba Services - API Integrator Service

Accepts client API requirements and generates Python integration scripts
to connect services (e.g., Google Sheets to CRM, Shopify to email).
"""

import json
import sys
from datetime import datetime

# Integration templates for common service connections
INTEGRATION_TEMPLATES = {
    "google_sheets_to_crm": {
        "name": "Google Sheets to CRM Sync",
        "description": "Sync data from Google Sheets to a CRM system",
        "required_credentials": ["google_service_account_json", "crm_api_key", "crm_base_url"],
        "dependencies": ["google-auth", "google-api-python-client", "requests", "pandas"],
    },
    "shopify_to_email": {
        "name": "Shopify to Email Notification",
        "description": "Send email notifications for Shopify order events",
        "required_credentials": ["shopify_api_key", "shopify_store_url", "email_api_key"],
        "dependencies": ["requests", "pandas"],
    },
    "hubspot_to_google_sheets": {
        "name": "HubSpot to Google Sheets Export",
        "description": "Export HubSpot contacts/deals to Google Sheets",
        "required_credentials": ["hubspot_api_key", "google_service_account_json"],
        "dependencies": ["requests", "google-auth", "google-api-python-client", "pandas"],
    },
    "woocommerce_to_slack": {
        "name": "WooCommerce to Slack Notifier",
        "description": "Send Slack notifications for WooCommerce events",
        "required_credentials": ["woocommerce_url", "woocommerce_consumer_key", "woocommerce_consumer_secret", "slack_webhook_url"],
        "dependencies": ["requests"],
    },
    "airtable_to_notion": {
        "name": "Airtable to Notion Sync",
        "description": "Sync records between Airtable and Notion databases",
        "required_credentials": ["airtable_api_key", "airtable_base_id", "notion_api_key"],
        "dependencies": ["requests", "pandas"],
    },
}

def generate_google_sheets_to_crm(client_name: str, config: dict) -> str:
    google_sa = config.get("google_service_account_json", "path/to/service-account.json")
    spreadsheet_id = config.get("spreadsheet_id", "your-spreadsheet-id")
    sheet_range = config.get("sheet_range", "Sheet1!A1:Z1000")
    crm_base_url = config.get("crm_base_url", "https://your-crm.example.com/api/v1")
    crm_api_key = config.get("crm_api_key", "your-crm-api-key")
    crm_object_type = config.get("crm_object_type", "contacts")
    mapping_file = config.get("mapping_file", "field_mapping.json")

    script = '''#!/usr/bin/env python3
"""
Google Sheets to CRM Integration Script
Client: {client}
Generated: {ts}
"""

import json
import pandas as pd
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# === CONFIGURATION ===
GOOGLE_SERVICE_ACCOUNT = "{google_sa}"
SPREADSHEET_ID = "{spreadsheet_id}"
SHEET_RANGE = "{sheet_range}"
CRM_BASE_URL = "{crm_base_url}"
CRM_API_KEY = "{crm_api_key}"
CRM_OBJECT_TYPE = "{crm_object_type}"  # contacts, deals, leads
MAPPING_FILE = "{mapping_file}"

# === SETUP ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_sheets_data():
    """Fetch data from Google Sheets."""
    creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE
    ).execute()
    values = result.get("values", [])
    if not values:
        print("No data found in Google Sheets.")
        return pd.DataFrame()
    headers = values[0]
    data = values[1:]
    return pd.DataFrame(data, columns=headers)


def load_field_mapping():
    """Load field mapping configuration."""
    try:
        with open(MAPPING_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: " + MAPPING_FILE + " not found. Using identity mapping.")
        return None


def map_fields(df, mapping):
    """Map sheet columns to CRM fields."""
    if mapping is None:
        return df.to_dict("records")
    mapped_records = []
    for _, row in df.iterrows():
        record = {{}}
        for sheet_col, crm_field in mapping.items():
            if sheet_col in row.index:
                record[crm_field] = row[sheet_col]
        mapped_records.append(record)
    return mapped_records


def push_to_crm(records):
    """Push records to CRM via REST API."""
    headers = {{
        "Authorization": "Bearer " + CRM_API_KEY,
        "Content-Type": "application/json"
    }}
    results = {{"success": 0, "failed": 0, "errors": []}}
    for record in records:
        try:
            resp = requests.post(
                CRM_BASE_URL + "/" + CRM_OBJECT_TYPE,
                headers=headers,
                json=record,
                timeout=30
            )
            if resp.status_code in [200, 201]:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({{"record": record, "error": resp.text}})
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({{"record": record, "error": str(e)}})
    return results


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts + "] Starting Google Sheets -> CRM sync for {client}")
    df = get_sheets_data()
    print("  Retrieved " + str(len(df)) + " rows from Google Sheets")
    mapping = load_field_mapping()
    records = map_fields(df, mapping)
    results = push_to_crm(records)
    print("  Success: " + str(results["success"]) + " | Failed: " + str(results["failed"]))
    if results["errors"]:
        with open("sync_errors.log", "w") as f:
            json.dump(results["errors"], f, indent=2)
        print("  Errors logged to sync_errors.log")
    ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts2 + "] Sync complete.")


if __name__ == "__main__":
    main()
'''
    return script.format(
        client=client_name,
        ts=datetime.now().isoformat(),
        google_sa=google_sa,
        spreadsheet_id=spreadsheet_id,
        sheet_range=sheet_range,
        crm_base_url=crm_base_url,
        crm_api_key=crm_api_key,
        crm_object_type=crm_object_type,
        mapping_file=mapping_file,
    )

def generate_shopify_to_email(client_name: str, config: dict) -> str:
    store_url = config.get("shopify_store_url", "your-store.myshopify.com")
    api_key = config.get("shopify_api_key", "your-shopify-api-key")
    api_version = config.get("shopify_api_version", "2024-01")
    email_key = config.get("email_api_key", "your-email-api-key")
    email_url = config.get("email_api_url", "https://api.sendgrid.com/v3/mail/send")
    notif_email = config.get("notification_email", "client@example.com")

    script = '''#!/usr/bin/env python3
"""
Shopify to Email Integration Script
Client: {client}
Generated: {ts}
"""

import json
import requests
from datetime import datetime

# === CONFIGURATION ===
SHOPIFY_STORE_URL = "{store_url}"
SHOPIFY_API_KEY = "{api_key}"
SHOPIFY_API_VERSION = "{api_version}"
EMAIL_API_KEY = "{email_key}"
EMAIL_API_URL = "{email_url}"
NOTIFICATION_EMAIL = "{notif_email}"
EVENT_TYPES = ["orders/create", "orders/paid", "refunds/create"]

# === SETUP ===


def get_shopify_orders(since_id=None):
    """Fetch recent orders from Shopify."""
    headers = {{"X-Shopify-Access-Token": SHOPIFY_API_KEY}}
    params = {{"limit": 250, "status": "any"}}
    if since_id:
        params["since_id"] = since_id
    url = "https://" + SHOPIFY_STORE_URL + "/admin/api/" + SHOPIFY_API_VERSION + "/orders.json"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("orders", [])


def send_email_notification(subject, body):
    """Send email via SendGrid API."""
    headers = {{
        "Authorization": "Bearer " + EMAIL_API_KEY,
        "Content-Type": "application/json"
    }}
    payload = {{
        "personalizations": [{{"to": [{{"email": NOTIFICATION_EMAIL}}]}}],
        "from": {{"email": "integrations@mrbubbaservices.com", "name": "Mr Bubba Integrations"}},
        "subject": subject,
        "content": [{{"type": "text/plain", "value": body}}]
    }}
    resp = requests.post(EMAIL_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp


def format_order_email(order):
    """Format order data into email body."""
    order_id = order.get("order_number", order.get("id", "unknown"))
    total = order.get("total_price", "N/A")
    customer = order.get("customer", {{}})
    name = customer.get("first_name", "") + " " + customer.get("last_name", "")
    items = order.get("line_items", [])
    item_list = "\\n".join(["  - " + str(i.get("quantity", 1)) + "x " + i.get("title", "Unknown") for i in items])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = """New Shopify Order Notification

Order #{{order_id}}
Customer: {{customer_name}}
Total: ${{total}}

Items:
{{items}}

Received at: {{timestamp}}
""".format(order_id=order_id, customer_name=name.strip() or "Guest", total=total, items=item_list, timestamp=now)
    return body


def process_orders(orders):
    """Process and notify for each new order."""
    sent = 0
    for order in orders:
        try:
            oid = order.get("order_number", order.get("id", "N/A"))
            subject = "New Shopify Order #" + str(oid)
            body = format_order_email(order)
            send_email_notification(subject, body)
            sent += 1
        except Exception as e:
            print("  Failed to notify for order " + str(order.get("id", "?")) + ": " + str(e))
    return sent


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts + "] Shopify -> Email integration for {client}")
    print("  Store: " + SHOPIFY_STORE_URL)
    orders = get_shopify_orders()
    print("  Retrieved " + str(len(orders)) + " orders")
    sent = process_orders(orders)
    print("  Sent " + str(sent) + " notifications")
    ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + ts2 + "] Complete.")


if __name__ == "__main__":
    main()
'''
    return script.format(
        client=client_name,
        ts=datetime.now().isoformat(),
        store_url=store_url,
        api_key=api_key,
        api_version=api_version,
        email_key=email_key,
        email_url=email_url,
        notif_email=notif_email,
    )

def generate_webhook_listener(client_name: str, config: dict) -> str:
    port = config.get("listen_port", 8080)

    script = '''#!/usr/bin/env python3
"""
Webhook Listener for Integration Scripts
Client: {client}
Generated: {ts}
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
from datetime import datetime

LISTEN_PORT = {port}


class IntegrationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {{"raw": body.decode()}}

        # Log the webhook
        timestamp = datetime.now().isoformat()
        log_entry = {{
            "timestamp": timestamp,
            "path": self.path,
            "headers": dict(self.headers),
            "payload": payload
        }}
        with open("webhook_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\\n")

        # Process based on path
        if self.path == "/webhook/shopify":
            self.handle_shopify(payload)
        elif self.path == "/webhook/google-sheets":
            self.handle_google_sheets(payload)
        else:
            self.handle_generic(payload)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({{"status": "received"}}).encode())

    def handle_shopify(self, payload):
        """Handle Shopify webhook."""
        topic = self.headers.get("X-Shopify-Topic", "unknown")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[" + ts + "] Shopify event: " + topic)

    def handle_google_sheets(self, payload):
        """Handle Google Sheets webhook."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[" + ts + "] Google Sheets event received")

    def handle_generic(self, payload):
        """Handle generic webhook."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[" + ts + "] Generic webhook on " + self.path)

    def log_message(self, format, *args):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[" + ts + "] " + str(args[0]))


def main():
    print("Starting webhook listener on port " + str(LISTEN_PORT))
    server = HTTPServer(("0.0.0.0", LISTEN_PORT), IntegrationHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
'''
    return script.format(
        client=client_name,
        ts=datetime.now().isoformat(),
        port=port,
    )

def generate_requirements_file(template_key: str) -> str:
    template = INTEGRATION_TEMPLATES.get(template_key, {})
    deps = template.get("dependencies", ["requests", "pandas"])
    return "\n".join(deps) + "\n"

def generate_field_mapping_template(template_key: str) -> str:
    if template_key == "google_sheets_to_crm":
        return json.dumps({
            "Name": "name",
            "Email": "email",
            "Phone": "phone",
            "Company": "company",
            "Status": "lead_status",
            "Notes": "description"
        }, indent=2)
    return json.dumps({}, indent=2)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_integration.py <client_name> <template_key> [config_json]")
        print("\nAvailable templates:")
        for key, template in INTEGRATION_TEMPLATES.items():
            print("  " + key + ": " + template["name"])
        print("\nExample:")
        print('  python3 generate_integration.py "Acme Corp" google_sheets_to_cidr \'{"spreadsheet_id": "abc123"}\'')
        sys.exit(1)

    client_name = sys.argv[1]
    template_key = sys.argv[2]
    config = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

    generators = {
        "google_sheets_to_crm": generate_google_sheets_to_crm,
        "shopify_to_email": generate_shopify_to_email,
    }

    # Generate integration script
    if template_key in generators:
        script = generators[template_key](client_name, config)
        script_filename = "integration_" + template_key + "_" + client_name.lower().replace(" ", "_") + ".py"
        with open(script_filename, "w") as f:
            f.write(script)
        print("Generated: " + script_filename)
    else:
        # Generate generic webhook listener
        script = generate_webhook_listener(client_name, config)
        script_filename = "integration_generic_" + client_name.lower().replace(" ", "_") + ".py"
        with open(script_filename, "w") as f:
            f.write(script)
        print("Generated: " + script_filename)

    # Generate requirements.txt
    req_filename = "requirements_" + client_name.lower().replace(" ", "_") + ".txt"
    with open(req_filename, "w") as f:
        f.write(generate_requirements_file(template_key))
    print("Generated: " + req_filename)

    # Generate field mapping if applicable
    if template_key in ["google_sheets_to_crm"]:
        mapping_filename = "field_mapping_" + client_name.lower().replace(" ", "_") + ".json"
        with open(mapping_filename, "w") as f:
            f.write(generate_field_mapping_template(template_key))
        print("Generated: " + mapping_filename)

    print("\nAll files generated for client: " + client_name)
    print("Template: " + INTEGRATION_TEMPLATES.get(template_key, {}).get("name", template_key))

if __name__ == "__main__":
    main()
