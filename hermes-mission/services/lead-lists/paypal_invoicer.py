"""
Mr Bubba Services — PayPal Invoicing Service
Creates and sends PayPal invoices for lead list orders.
Integrates with PayPal Invoicing API.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# PayPal Configuration
# Note: In production, use PayPal's REST API with OAuth2 tokens
# For sandbox testing, use sandbox endpoints
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "YOUR_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.paypal.com"  # Production
# PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"  # Sandbox

# Service pricing
SERVICE_PRICING = {
    "starter": {"price": 60, "description": "Starter Lead List — Up to 25 verified leads", "leads": 25},
    "standard": {"price": 90, "description": "Standard Lead List — Up to 50 verified leads", "leads": 50},
    "premium": {"price": 120, "description": "Premium Lead List — Up to 100 verified leads", "leads": 100},
}


class PayPalInvoicer:
    """Manages PayPal invoice creation and tracking."""

    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.session = requests.Session()

    def _get_access_token(self) -> Optional[str]:
        """Obtain OAuth2 access token from PayPal."""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        try:
            url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
            resp = requests.post(
                url,
                auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data["access_token"]
                self.token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 3600))
                return self.access_token
            else:
                print(f"PayPal auth error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"PayPal token error: {e}")
        return None

    def create_invoice(self, 
                       recipient_email: str,
                       recipient_name: str,
                       service_tier: str = "standard",
                       custom_amount: Optional[float] = None,
                       notes: str = "") -> Dict:
        """
        Create a PayPal invoice for lead list services.
        
        Args:
            recipient_email: Client's email address
            recipient_name: Client's name or company
            service_tier: starter/standard/premium
            custom_amount: Override price (optional)
            notes: Additional notes for the invoice
        """
        token = self._get_access_token()
        if not token:
            return {"error": "Failed to authenticate with PayPal"}
        
        pricing = SERVICE_PRICING.get(service_tier, SERVICE_PRICING["standard"])
        amount = custom_amount if custom_amount else pricing["price"]
        
        invoice_data = {
            "detail": {
                "invoice_number": f"HD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "reference": f"lead-list-{service_tier}",
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "note": notes or f"Lead list compilation service — {pricing['description']}",
                "terms_and_conditions": "Payment due upon receipt. Lead list delivery within specified timeframe after payment confirmation.",
                "payment_term": {
                    "term_type": "DUE_ON_RECEIPT"
                }
            },
            "invoicer": {
                "name": {
                    "given_name": "Mr Bubba Services"
                },
                "email_address": "mrbubba@agentmail.to"
            },
            "primary_recipients": [{
                "billing_info": {
                    "name": {
                        "given_name": recipient_name
                    },
                    "email_address": recipient_email
                }
            }],
            "items": [{
                "name": f"Lead List Research & Compilation — {service_tier.upper()}",
                "description": pricing["description"],
                "quantity": "1",
                "unit_amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}"
                },
                "unit_of_measure": "AMOUNT"
            }],
            "configuration": {
                "allow_tip": False,
                "tax_before_discount": False,
                "total_required": True
            }
        }
        
        try:
            url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices"
            resp = self.session.post(
                url,
                json=invoice_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                timeout=20
            )
            
            if resp.status_code in (200, 201):
                result = resp.json()
                print(f"✅ Invoice created: {result.get('id')}")
                return {"success": True, "invoice": result}
            else:
                print(f"PayPal invoice error: {resp.status_code} - {resp.text}")
                return {"success": False, "error": resp.text}
                
        except Exception as e:
            print(f"Invoice creation error: {e}")
            return {"success": False, "error": str(e)}

    def send_invoice(self, invoice_id: str) -> bool:
        """Send/draft the invoice to the recipient via PayPal."""
        token = self._get_access_token()
        if not token:
            return False
        
        try:
            # First, send the invoice
            url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}/send"
            resp = self.session.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={},
                timeout=15
            )
            
            if resp.status_code in (200, 202):
                print(f"✅ Invoice {invoice_id} sent successfully!")
                return True
            else:
                print(f"Send error: {resp.status_code} - {resp.text}")
                return False
                
        except Exception as e:
            print(f"Send invoice error: {e}")
            return False

    def get_invoice_status(self, invoice_id: str) -> Dict:
        """Check the status of an invoice."""
        token = self._get_access_token()
        if not token:
            return {"error": "Auth failed"}
        
        try:
            url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices/{invoice_id}"
            resp = self.session.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"error": f"Status {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def list_invoices(self, page: int = 1, page_size: int = 10) -> List[Dict]:
        """List all invoices."""
        token = self._get_access_token()
        if not token:
            return []
        
        try:
            url = f"{PAYPAL_BASE_URL}/v2/invoicing/invoices"
            params = {"page": page, "page_size": page_size}
            resp = self.session.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=15
            )
            
            if resp.status_code == 200:
                return resp.json().get("items", [])
        except Exception as e:
            print(f"List invoices error: {e}")
        return []


def create_lead_list_invoice(client_email: str, client_name: str, 
                              tier: str = "standard", notes: str = "") -> Dict:
    """
    Convenience function to create and send a lead list invoice.
    
    Usage:
        result = create_lead_list_invoice(
            client_email="client@example.com",
            client_name="Acme Corp",
            tier="standard"
        )
    """
    invoicer = PayPalInvoicer()
    
    # Create invoice
    result = invoicer.create_invoice(
        recipient_email=client_email,
        recipient_name=client_name,
        service_tier=tier,
        notes=notes
    )
    
    if result.get("success"):
        invoice_id = result["invoice"]["id"]
        # Send it
        invoicer.send_invoice(invoice_id)
        return {"status": "sent", "invoice_id": invoice_id}
    
    return result


def cli_main():
    """CLI entry point for manual invoice creation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mr Bubba PayPal Invoice Tool")
    parser.add_argument("--email", required=True, help="Client email address")
    parser.add_argument("--name", required=True, help="Client name or company")
    parser.add_argument("--tier", choices=["starter", "standard", "premium"], default="standard")
    parser.add_argument("--amount", type=float, help="Custom amount (overrides tier pricing)")
    parser.add_argument("--notes", default="", help="Additional notes")
    
    args = args = parser.parse_args()
    
    invoicer = PayPalInvoicer()
    result = invoicer.create_invoice(
        recipient_email=args.email,
        recipient_name=args.name,
        service_tier=args.tier,
        custom_amount=args.amount,
        notes=args.notes
    )
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    cli_main()
