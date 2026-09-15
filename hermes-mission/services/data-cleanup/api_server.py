#!/usr/bin/env python3
"""
Mr Bubba Services — REST API Wrapper.
Exposes the data cleanup pipeline as a web service.

Endpoints:
  POST /api/clean          - Upload and clean a file
  GET  /api/status/<id>    - Check processing status
  GET  /api/health         - Health check
  GET  /api/invoice/<id>   - Get invoice status
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, send_file

# Add parent to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from data_cleanup_service import clean_data, generate_text_report
from payment_tracker import PaymentOrchestrator, PaymentTracker
from email_templates import render_template

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max

# In-memory job tracking
jobs = {}


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Mr Bubba Data Cleanup Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/clean", methods=["POST"])
def clean():
    """Upload a file and clean it."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save uploaded file
    input_dir = BASE_DIR / "input"
    output_dir = BASE_DIR / "output"
    report_dir = BASE_DIR / "reports"

    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    file_path = input_dir / f"{job_id}_{file.filename}"
    file.save(file_path)

    # Run cleanup
    report = clean_data(file_path)

    if not report["success"]:
        return jsonify({"error": report.get("error", "Processing failed")}), 500

    # Store job info
    jobs[job_id] = {
        "status": "complete",
        "filename": file.filename,
        "created_at": datetime.now().isoformat(),
        "report": report,
    }

    text_report = generate_text_report(report)

    return jsonify({
        "job_id": job_id,
        "status": "complete",
        "original_rows": report.get("original_rows"),
        "cleaned_rows": report.get("final_rows"),
        "duplicates_removed": sum(
            s.get("rows_removed", 0)
            for s in report.get("steps", [])
            if "remove" in s.get("step", "")
        ),
        "quality_score": next(
            (c.get("score", 0) for c in report.get("calculations", []) if c[0] == "data_quality_score"),
            0,
        ),
        "report": text_report,
        "download_url": f"/api/download/{job_id}",
        "invoice_url": f"/api/invoice/{job_id}",
        "price": 75.00,
    })


@app.route("/api/download/<job_id>", methods=["GET"])
def download(job_id):
    """Download cleaned file."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    report = job.get("report", {})
    output_file = report.get("output_file")

    if not output_file or not Path(output_file).exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(
        output_file,
        as_attachment=True,
        download_name=f"cleaned_{job['filename']}.csv",
    )


@app.route("/api/status/<job_id>", methods=["GET"])
def status(job_id):
    """Get job status."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
        "created_at": job["created_at"],
    })


@app.route("/api/invoice/<job_id>", methods=["POST"])
def create_invoice(job_id):
    """Create PayPal invoice for a job."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json() or {}
    client_email = data.get("email", "")
    client_name = data.get("name", "Client")

    if not client_email:
        return jsonify({"error": "Email required"}), 400

    orch = PaymentOrchestrator()
    invoice = orch.tracker.create_invoice(
        client_email=client_email,
        client_name=client_name,
        filename=job["filename"],
        ticket_id=job_id,
    )
    orch.notifier.notify_invoice_created(invoice)

    return jsonify({
        "invoice_id": invoice.invoice_id,
        "amount": invoice.amount,
        "currency": invoice.currency,
        "status": invoice.status,
        "paypal_link": f"https://www.paypal.com/invoice/p/#{invoice.invoice_id}",
    })


@app.route("/api/webhook/paypal", methods=["POST"])
def paypal_webhook():
    """Handle PayPal payment webhook."""
    from payment_tracker import handle_paypal_webhook
    payload = request.get_json()
    result = handle_paypal_webhook(payload)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
