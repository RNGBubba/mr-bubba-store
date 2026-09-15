#!/usr/bin/env python3
"""
Email Copywriter for Mr Bubba Services
Generates professional email sequences from client product/service details.

Usage:
    python3 generate_email_copy.py
    python3 generate_email_copy.py --config client_config.json
"""

import json
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Email Templates ──────────────────────────────────────────────────────

WELCOME_TEMPLATE = """Subject: Welcome to {product_name} — Let's Get Started

Hi {first_name},

Welcome to {product_name}! We're thrilled to have you on board.

At {product_name}, we {product_description}. Whether you're looking to {primary_benefit_1} or {primary_benefit_2}, we're here to make it happen.

Here's what you can expect:

• {feature_1} — because you deserve better
• {feature_2} — designed with you in mind
• {feature_3} — the smart way forward

Your next step: {cta_primary}

If you have any questions, just reply to this email. We're always happy to help.

Best,
The {product_name} Team
{company_url}
"""

PROMOTIONAL_TEMPLATE = """Subject: {headline}

Hi {first_name},

{greeting_line}

{product_name} is offering something special:

{discount_offer}

Here's why {target_audience} love {product_name}:

"{testimonial_quote}"
— {testimonial_author}

• {benefit_1}
• {benefit_2}
• {benefit_3}

{urgency_line}

{cta_primary}

{product_name}
{company_url}
"""

FOLLOW_UP_TEMPLATE = """Subject: Checking in, {first_name}

Hi {first_name},

I wanted to follow up and see how things are going with {product_name}.

If you have any questions or need help getting the most out of {feature_mention}, we're here for you.

Sometimes all it takes is a quick conversation to unlock the full potential.

Here's what we can do together:

1. {next_step_1}
2. {next_step_2}
3. {next_step_3}

{cta_secondary}

Talk soon,
{sender_name}
{product_name} Team
{company_url}
"""

NEWSLETTER_TEMPLATE = """Subject: {subject_line}

Hi {first_name},

{opening_hook}

📰 This week in {industry_topic}:

{news_item_1}

{news_item_2}

💡 Quick Tip:
{quick_tip}

🎯 Spotlight:
{spotlight_item}

{cta_primary}

Until next time,
{sender_name}
{product_name}
{company_url}
"""

RE_ENGAGEMENT_TEMPLATE = """Subject: We miss you, {first_name}!

Hi {first_name},

It's been a while since you last engaged with {product_name}, and we wanted to reach out.

A lot has changed since you were last here:

{update_1}
{update_2}
{update_3}

As a valued member of our community, we'd love to welcome you back with {comeback_offer}.

{cta_primary}

We hope to see you soon!
The {product_name} Team
{company_url}
"""


class EmailCopyGenerator:
    """Generates email copy from structured client input."""

    TEMPLATES = {
        "welcome": WELCOME_TEMPLATE,
        "promotional": PROMOTIONAL_TEMPLATE,
        "follow_up": FOLLOW_UP_TEMPLATE,
        "newsletter": NEWSLETTER_TEMPLATE,
        "re_engagement": RE_ENGAGEMENT_TEMPLATE,
    }

    def __init__(self, client_data: dict):
        self.data = self._validate_and_fill(client_data)

    def _validate_and_fill(self, data: dict) -> dict:
        """Validate required fields and fill defaults."""
        required = ["product_name", "product_description", "target_audience"]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Smart defaults
        data.setdefault("first_name", "{{first_name}}")
        data.setdefault("product_name", "Our Service")
        data.setdefault("company_url", "https://mrbubba-services.com")
        data.setdefault("cta_primary", "Get started today")
        data.setdefault("cta_secondary", "Reply to this email to continue the conversation")
        data.setdefault("sender_name", "The Mr Bubba Team")
        sender = data.get("sender_name", "The Mr Bubba Team")
        product = data.get("product_name", "Our Service")

        # Promotional defaults
        data.setdefault("headline", f"Something Special from {product}")
        data.setdefault("greeting_line", f"We've got exciting news for you.")
        data.setdefault("discount_offer", f"Exclusive offer for {data.get('target_audience', 'valued customers')}!")
        data.setdefault("testimonial_quote", f"'{product} transformed how I work.'")
        data.setdefault("testimonial_author", "— A Satisfied Customer")
        data.setdefault("benefit_1", data.get("primary_benefit_1", "Save time and effort"))
        data.setdefault("benefit_2", data.get("primary_benefit_2", "Get better results"))
        data.setdefault("benefit_3", "Seamless experience")
        data.setdefault("urgency_line", "Limited time offer — act now!")
        data.setdefault("feature_1", data.get("primary_benefit_1", "Core Feature"))
        data.setdefault("feature_2", "Easy Integration")
        data.setdefault("feature_3", "24/7 Support")

        # Follow-up defaults
        data.setdefault("feature_mention", data.get("feature_1", "our core features"))
        data.setdefault("next_step_1", "Schedule a quick check-in call")
        data.setdefault("next_step_2", "Review your current setup")
        data.setdefault("next_step_3", "Explore new features")

        # Newsletter defaults
        data.setdefault("subject_line", f"This Week from {product}")
        data.setdefault("opening_hook", "Here's what's new and noteworthy.")
        data.setdefault("industry_topic", data.get("product_name", "our industry"))
        data.setdefault("news_item_1", "📌 New feature release now available")
        data.setdefault("news_item_2", "📌 Industry trends you should know about")
        data.setdefault("quick_tip", "Pro tip: Set up automations to save 5+ hours/week")
        data.setdefault("spotlight_item", f"Customer success story with {product}")

        # Re-engagement defaults
        data.setdefault("update_1", "🆕 Brand new features")
        data.setdefault("update_2", "⚡ Improved performance")
        data.setdefault("update_3", "🎨 Redesigned experience")
        data.setdefault("comeback_offer", "20% off your next purchase")

        return data

    def generate(self, email_type: str) -> str:
        """Generate a single email of the specified type."""
        if email_type not in self.TEMPLATES:
            raise ValueError(f"Unknown email type: {email_type}. Available: {list(self.TEMPLATES.keys())}")
        return self.TEMPLATES[email_type].format(**self.data)

    def generate_sequence(self, sequence: list[str]) -> dict[str, str]:
        """Generate a full email sequence."""
        return {t: self.generate(t) for t in sequence}

    def generate_all(self) -> dict[str, str]:
        """Generate all available email types."""
        return {t: self.generate(t) for t in self.TEMPLATES}

    def export_to_file(self, output_dir: str = "."):
        """Export all emails to a timestamped output directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path(output_dir) / f"email_copy_{timestamp}"
        out_path.mkdir(parents=True, exist_ok=True)

        all_emails = self.generate_all()
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "product_name": self.data["product_name"],
            "target_audience": self.data["target_audience"],
            "emails": {},
        }

        for email_type, content in all_emails.items():
            filename = f"{email_type}.txt"
            (out_path / filename).write_text(content)
            manifest["emails"][email_type] = filename

        (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return out_path


# ── CLI Interface ─────────────────────────────────────────────────────────

def interactive_input() -> dict:
    """Gather client input interactively."""
    print("\n" + "=" * 60)
    print("Mr Bubba Services — Email Copy Generator")
    print("=" * 60)

    fields = [
        ("product_name", "Product/Service Name"),
        ("product_description", "Brief product description (one sentence)"),
        ("target_audience", "Target audience (e.g., 'small business owners')"),
        ("primary_benefit_1", "Primary benefit #1"),
        ("primary_benefit_2", "Primary benefit #2"),
        ("company_url", "Company URL (or press Enter for default)"),
        ("sender_name", "Sender name (or press Enter for default)"),
    ]

    data = {}
    for key, prompt in fields:
        val = input(f"\n{prompt}: ").strip()
        if val:
            data[key] = val

    # Optional: sequence selection
    print("\nSelect email types to generate:")
    print("  [1] Welcome")
    print("  [2] Promotional")
    print("  [3] Follow-up")
    print("  [4] Newsletter")
    print("  [5] Re-engagement")
    print("  [0] All of the above")
    choice = input("\nChoice (default: 0): ").strip() or "0"

    return data, choice


def main():
    parser = argparse.ArgumentParser(description="Mr Bubba Services Email Copy Generator")
    parser.add_argument("--config", "-c", help="Path to client config JSON file")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--type", "-t", choices=["welcome", "promotional", "follow_up", "newsletter", "re_engagement"],
                        help="Generate a single email type")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            data = json.load(f)
    elif args.interactive or len(sys.argv) == 1:
        data, choice = interactive_input()
        data.setdefault("company_url", "https://mrbubba-services.com")
        data.setdefault("sender_name", "The Mr Bubba Team")
    else:
        parser.print_help()
        return

    try:
        generator = EmailCopyGenerator(data)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.type:
        print(generator.generate(args.type))
    else:
        out_path = generator.export_to_file(args.output)
        print(f"\n✓ Email sequence generated!")
        print(f"  Output: {out_path}/")
        print(f"  Files: {', '.join(f.name for f in out_path.iterdir())}")


if __name__ == "__main__":
    main()
