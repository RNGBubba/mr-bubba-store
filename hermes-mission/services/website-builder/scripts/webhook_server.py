#!/usr/bin/env python3
"""
Mr Bubba Services - Website Builder Webhook Server
Handles PayPal webhooks and AgentMail polling for the website builder pipeline.
Runs a lightweight HTTP server for PayPal IPN/webhooks.
"""

import json
import logging
import os
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from payment import handle_payment_webhook, create_discord_notification, verify_paypal_webhook

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("mr-bubba-webhook")

# Configuration
PORT = int(os.environ.get("MR_BUBBA_WEBHOOK_PORT", 8765))
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
SITE_OUTPUT_DIR = SCRIPT_DIR / "output"


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook requests."""
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        if parsed.path == "/webhook/paypal":
            self._handle_paypal_webhook(body)
        elif parsed.path == "/webhook/agentmail":
            self._handle_agentmail_webhook(body)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')
    
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "mrbubba-website-builder"}).encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Mr Bubba Services - Website Builder</h1><p>Webhook endpoint active.</p>")
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_paypal_webhook(self, body: str):
        """Process PayPal payment webhook."""
        try:
            payload = json.loads(body)
            event_type = payload.get("event_type", "unknown")
            logger.info(f"PayPal webhook received: {event_type}")
            
            # Verify webhook authenticity (in production)
            # headers = {k: v for k, v in self.headers.items()}
            # if not verify_paypal_webhook(headers, body):
            #     self.send_response(400)
            #     self.end_headers()
            #     return
            
            # Process the payment event
            result = handle_payment_webhook(payload)
            logger.info(f"Payment result: {result}")
            
            if result.get("action") == "deploy_site":
                # Trigger deployment
                client_email = result.get("client_email", "")
                business_name = result.get("business_name", "")
                if business_name:
                    self._trigger_deploy(business_name, client_email)
            
            # Send Discord notification
            if DISCORD_WEBHOOK_URL:
                self._send_discord_notification(payload)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"received": True, "event": event_type}).encode())
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in PayPal webhook")
            self.send_response(400)
            self.end_headers()
        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _handle_agentmail_webhook(self, body: str):
        """Process AgentMail incoming email webhook."""
        try:
            payload = json.loads(body)
            logger.info(f"AgentMail webhook received: {payload.get('event', 'unknown')}")
            
            # Process incoming email
            # This would trigger the auto-responder logic
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"received": True}).encode())
            
        except Exception as e:
            logger.error(f"Error processing AgentMail webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _trigger_deploy(self, business_name: str, client_email: str):
        """Trigger site deployment after payment."""
        logger.info(f"Triggering deploy for {business_name} (email: {client_email})")
        # This would call deploy.py or build_site.py as needed
        repo_name = business_name.lower().replace(" ", "-").replace("&", "and")
        site_dir = SITE_OUTPUT_DIR / repo_name
        
        if site_dir.exists():
            logger.info(f"Deploying {repo_name} to GitHub Pages...")
            # subprocess.Popen(["python3", str(SCRIPT_DIR / "deploy.py"), str(site_dir), "--repo-name", repo_name])
        else:
            logger.warning(f"Site directory not found: {site_dir}")
    
    def _send_discord_notification(self, payload: dict):
        """Send notification to Discord webhook."""
        import urllib.request
        notification = create_discord_notification(payload)
        data = json.dumps(notification).encode()
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.client_address[0]} - {format % args}")


def start_server(port: int = PORT):
    """Start the webhook server."""
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logger.info(f"Mr Bubba Webhook Server running on port {port}")
    logger.info(f"PayPal webhook URL: http://your-domain:{port}/webhook/paypal")
    logger.info(f"Health check: http://your-domain:{port}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()


if __name__ == "__main__":
    import sys
    start_server()
