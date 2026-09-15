#!/usr/bin/env python3
"""
Mr Bubba Services - Website Builder Generator
Takes business info (from email or CLI) and generates a customized 5-page website.
Usage: python3 build_site.py --config business.json
       python3 build_site.py --business-name "..." --city "..." --category "..."
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
PAYMENT_PRICE = 299

# Default business info template
DEFAULT_BUSINESS = {
    "business_name": "",
    "category": "",
    "city": "",
    "state": "",
    "address": "",
    "phone": "",
    "email": "",
    "hours": "Mon-Fri: 8AM-6PM, Sat: 9AM-2PM",
    "hero_headline": "",
    "hero_subheadline": "",
    "about_text": "",
    "about_text_2": "",
    "meta_description": "",
    "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800",
    "about_image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800",
    "years_experience": "10",
    "founding_year": str(datetime.now().year - 10),
    "lat": "-97.4775",
    "lng": "32.7767",
    "services": [],
    "testimonials": [],
    "team_members": [],
    "portfolio_items": [],
    "values": [],
    "process_steps": [],
    "social_links": {},
    "footer_tagline": "",
    "stat_1_num": "500+",
    "stat_1_label": "Happy Clients",
    "stat_2_num": "15+",
    "stat_2_label": "Years Experience",
    "stat_3_num": "98%",
    "stat_3_label": "Satisfaction Rate",
}


def generate_services(business_name: str, category: str) -> list:
    """Generate default services based on category."""
    common_services = [
        {
            "icon": "fas fa-briefcase",
            "title": "Consultation",
            "description": f"Professional consultation services tailored to your specific needs.",
            "features": ["Initial Assessment", "Custom Recommendations", "Strategy Session", "Follow-up Support"],
            "price": "Starting at $99"
        },
        {
            "icon": "fas fa-cogs",
            "title": "Implementation",
            "description": f"End-to-end implementation services with attention to detail.",
            "features": ["Project Planning", "Quality Assurance", "Timeline Management", "Documentation"],
            "price": "Custom Quote"
        },
        {
            "icon": "fas fa-headset",
            "title": "Support & Maintenance",
            "description": f"Ongoing support to keep your operations running smoothly.",
            "features": ["24/7 Support", "Regular Updates", "Performance Monitoring", "Quick Response"],
            "price": "$49/month"
        },
    ]

    category_services = {
        "plumbing": [
            {"icon": "fas fa-wrench", "title": "Emergency Repairs", "description": "24/7 emergency plumbing repairs for burst pipes, leaks, and urgent issues.", "features": ["Same-Day Service", "Licensed Plumbers", "Upfront Pricing", "Satisfaction Guaranteed"], "price": "Starting at $149"},
            {"icon": "fas fa-faucet", "title": "Installation", "description": "Professional installation of fixtures, water heaters, and plumbing systems.", "features": ["Fixture Installation", "Water Heater Setup", "Pipe Fitting", "Code Compliant"], "price": "Custom Quote"},
            {"icon": "fas fa-search", "title": "Inspection", "description": "Comprehensive plumbing inspections using camera technology.", "features": ["Camera Inspection", "Leak Detection", "Pipe Assessment", "Detailed Report"], "price": "$99"},
        ],
        "landscaping": [
            {"icon": "fas fa-leaf", "title": "Lawn Care", "description": "Complete lawn maintenance including mowing, fertilization, and weed control.", "features": ["Weekly Mowing", "Fertilization", "Weed Control", "Aeration"], "price": "Starting at $49/visit"},
            {"icon": "fas fa-tree", "title": "Tree Services", "description": "Professional tree trimming, removal, and health assessments.", "features": ["Tree Trimming", "Stump Removal", "Disease Treatment", "Emergency Removal"], "price": "Custom Quote"},
            {"icon": "fas fa-seedling", "title": "Garden Design", "description": "Beautiful garden design and installation customized to your space.", "features": ["Custom Design", "Plant Selection", "Hardscaping", "Irrigation Systems"], "price": "From $500"},
        ],
        "cleaning": [
            {"icon": "fas fa-broom", "title": "Residential Cleaning", "description": "Thorough home cleaning services that keep your living space spotless.", "features": ["Deep Cleaning", "Eco-Friendly Products", "Insured Staff", "Flexible Scheduling"], "price": "Starting at $120"},
            {"icon": "fas fa-building", "title": "Commercial Cleaning", "description": "Professional cleaning for offices, retail spaces, and commercial properties.", "features": ["Daily/Weekly Service", "Floor Care", "Window Cleaning", "Sanitization"], "price": "Custom Quote"},
            {"icon": "fas fa-spray-can", "title": "Specialty Cleaning", "description": "Carpet cleaning, window washing, and post-construction cleanup.", "features": ["Carpet Deep Clean", "Pressure Washing", "Post-Construction", "Move-In/Move-Out"], "price": "From $200"},
        ],
        "roofing": [
            {"icon": "fas fa-home", "title": "Roof Repair", "description": "Expert roof repair for leaks, storm damage, and wear.", "features": ["Leak Repair", "Shingle Replacement", "Flashing Repair", "Storm Damage"], "price": "Starting at $299"},
            {"icon": "fas fa-hard-hat", "title": "Roof Installation", "description": "Complete roof replacement and new construction installation.", "features": ["Material Selection", "Quality Installation", "Warranty Included", "Permit Handling"], "price": "Free Estimate"},
            {"icon": "fas fa-clipboard-check", "title": "Inspection", "description": "Detailed roof inspections for insurance claims and home purchases.", "features": ["Insurance Reports", "Drone Inspection", "Written Estimate", "Maintenance Plan"], "price": "$149"},
        ],
    }

    return category_services.get(category.lower(), common_services)


def generate_testimonials(business_name: str, city: str) -> list:
    """Generate sample testimonials."""
    return [
        {
            "text": f"{business_name} exceeded all my expectations. The team was professional, punctual, and delivered outstanding results.",
            "author": "Sarah M.",
            "role": "Homeowner",
            "stars": 5
        },
        {
            "text": f"After trying several providers in {city}, we finally found {business_name}. Their attention to detail is unmatched.",
            "author": "David R.",
            "role": "Business Owner",
            "stars": 5
        },
        {
            "text": f"From the initial consultation to project completion, {business_name} was fantastic. Fair pricing and beautiful results.",
            "author": "Jennifer K.",
            "role": "Property Manager",
            "stars": 5
        },
    ]


def generate_team(business_name: str) -> list:
    """Generate sample team members."""
    return [
        {
            "name": f"{business_name} Founder",
            "role": "Owner & Lead Specialist",
            "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200"
        },
        {
            "name": "Operations Manager",
            "role": "Operations & Client Relations",
            "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200"
        },
        {
            "name": "Senior Technician",
            "role": "Technical Lead",
            "image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200"
        },
    ]


def generate_portfolio(business_name: str) -> list:
    """Generate sample portfolio items."""
    return [
        {
            "title": "Residential Project",
            "category": "residential",
            "image": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=600"
        },
        {
            "title": "Commercial Installation",
            "category": "commercial",
            "image": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600"
        },
        {
            "title": "Renovation Project",
            "category": "residential",
            "image": "https://images.unsplash.com/photo-1581578731117-104f2a863a30?w=600"
        },
        {
            "title": "Large-Scale Project",
            "category": "commercial",
            "image": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=600"
        },
        {
            "title": "Custom Solution",
            "category": "specialty",
            "image": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600"
        },
        {
            "title": "Emergency Repair",
            "category": "residential",
            "image": "https://images.unsplash.com/photo-1560185127-6ed189bf02f4?w=600"
        },
    ]


def generate_values() -> list:
    """Generate company values."""
    return [
        {"icon": "fas fa-shield-alt", "title": "Trust & Reliability", "description": "We build lasting relationships through honesty, transparency, and consistent delivery."},
        {"icon": "fas fa-star", "title": "Quality First", "description": "We never cut corners. Every project receives our full attention and highest standards."},
        {"icon": "fas fa-handshake", "title": "Customer Focus", "description": "Your satisfaction is our priority. We listen, adapt, and deliver on your vision."},
        {"icon": "fas fa-leaf", "title": "Sustainability", "description": "We use eco-friendly practices and materials to protect our community."},
    ]


def generate_process_steps() -> list:
    """Generate process steps."""
    return [
        {"num": "1", "title": "Free Consultation", "description": "Discuss your needs and goals in a no-pressure initial meeting."},
        {"num": "2", "title": "Custom Proposal", "description": "Receive a detailed plan and transparent pricing for your project."},
        {"num": "3", "title": "Professional Execution", "description": "Our skilled team brings the plan to life with precision and care."},
        {"num": "4", "title": "Follow-Up & Support", "description": "We ensure everything is perfect and remain available for ongoing support."},
    ]


def generate_social_links(links: dict) -> str:
    """Generate social media links HTML."""
    icon_map = {
        "facebook": "fab fa-facebook-f",
        "twitter": "fab fa-twitter",
        "instagram": "fab fa-instagram",
        "linkedin": "fab fa-linkedin-in",
        "youtube": "fab fa-youtube",
        "yelp": "fab fa-yelp",
    }
    html = []
    for platform, url in links.items():
        icon = icon_map.get(platform, "fas fa-globe")
        html.append(f'<a href="{url}" aria-label="{platform.title()}" target="_blank"><i class="{icon}"></i></a>')
    return "\n".join(html) if html else '<a href="#"><i class="fab fa-facebook-f"></i></a>\n<a href="#"><i class="fab fa-instagram"></i></a>\n<a href="#"><i class="fab fa-google"></i></a>'


def generate_services_home(services: list) -> str:
    """Generate services grid HTML for homepage."""
    cards = []
    for s in services[:3]:
        cards.append(f'''<div class="service-card">
    <i class="{s.get("icon", "fas fa-star")}"></i>
    <h3>{s["title"]}</h3>
    <p>{s["description"]}</p>
    <div class="price">{s.get("price", "Contact Us")}</div>
</div>''')
    return "\n".join(cards)


def generate_services_full(services: list) -> str:
    """Generate detailed services HTML for services page."""
    cards = []
    for s in services:
        features = "\n".join(f'<li>{f}</li>' for f in s.get("features", []))
        cards.append(f'''<div class="service-detail">
    <div class="service-icon"><i class="{s.get("icon", "fas fa-star")}"></i></div>
    <h3>{s["title"]}</h3>
    <p>{s["description"]}</p>
    <ul class="features">{features}</ul>
    <div class="price">{s.get("price", "Contact Us")}</div>
</div>''')
    return "\n".join(cards)


def generate_testimonials_html(testimonials: list) -> str:
    """Generate testimonials HTML."""
    cards = []
    for t in testimonials:
        stars = "★" * t.get("stars", 5)
        cards.append(f'''<div class="testimonial-card">
    <div class="stars">{stars}</div>
    <p>{t["text"]}</p>
    <div class="author">{t["author"]}</div>
    <div class="author-role">{t.get("role", "")}</div>
</div>''')
    return "\n".join(cards)


def generate_team_html(team: list) -> str:
    """Generate team grid HTML."""
    cards = []
    for member in team:
        cards.append(f'''<div class="team-card">
    <img src="{member.get("image", "")}" alt="{member["name"]}">
    <h3>{member["name"]}</h3>
    <div class="role">{member["role"]}</div>
</div>''')
    return "\n".join(cards)


def generate_portfolio_html(items: list) -> str:
    """Generate portfolio grid HTML."""
    html_items = []
    for item in items:
        html_items.append(f'''<div class="portfolio-item" data-category="{item.get("category", "all")}">
    <img src="{item["image"]}" alt="{item["title"]}" loading="lazy">
    <div class="portfolio-overlay">
        <h3>{item["title"]}</h3>
        <span>{item.get("category", "").title()}</span>
    </div>
</div>''')
    return "\n".join(html_items)


def generate_portfolio_filters(items: list) -> str:
    """Generate portfolio filter buttons."""
    categories = sorted(set(item.get("category", "all") for item in items))
    buttons = []
    for cat in categories:
        buttons.append(f'<button class="filter-btn" data-filter="{cat}">{cat.title()}</button>')
    return "\n".join(buttons)


def generate_values_html(values: list) -> str:
    """Generate values grid HTML."""
    cards = []
    for v in values:
        cards.append(f'''<div class="value-card">
    <i class="{v.get("icon", "fas fa-star")}"></i>
    <h3>{v["title"]}</h3>
    <p>{v["description"]}</p>
</div>''')
    return "\n".join(cards)


def generate_process_html(steps: list) -> str:
    """Generate process steps HTML."""
    html_steps = []
    for step in steps:
        html_steps.append(f'''<div class="process-step">
    <div class="step-num">{step["num"]}</div>
    <h3>{step["title"]}</h3>
    <p>{step["description"]}</p>
</div>''')
    return "\n".join(html_steps)


def generate_about_features(business_name: str) -> str:
    """Generate about features list."""
    features = [
        "Licensed & Insured professionals with 10+ years experience",
        "100% satisfaction guarantee on all work",
        "Transparent pricing with no hidden fees",
        "Locally owned and operated in your community",
    ]
    return "\n".join(f'<li><i class="fas fa-check-circle"></i> {f}</li>' for f in features)


def generate_footer_services(services: list) -> str:
    """Generate footer services list."""
    return "\n".join(f'<li><a href="services.html">{s["title"]}</a></li>' for s in services[:4])


def generate_service_options(services: list) -> str:
    """Generate contact form service options."""
    return "\n".join(f'<option value="{s["title"]}">{s["title"]}</option>' for s in services)


def build_site(config: dict, output_path: Path) -> Path:
    """Build a complete website from config and template."""
    # Merge with defaults
    business = {**DEFAULT_BUSINESS, **config}

    # Generate dynamic content
    business.setdefault("services", generate_services(business["business_name"], business["category"]))
    business.setdefault("testimonials", generate_testimonials(business["business_name"], business["city"]))
    business.setdefault("team_members", generate_team(business["business_name"]))
    business.setdefault("portfolio_items", generate_portfolio(business["business_name"]))
    business.setdefault("values", generate_values())
    business.setdefault("process_steps", generate_process_steps())
    business.setdefault("footer_tagline", f"Professional {business['category']} services in {business['city']}, {business.get('state', '')}. Licensed, insured, and committed to excellence.")
    business.setdefault("hero_headline", f"Professional {business['category'].title()} Services in {business['city']}")
    business.setdefault("hero_subheadline", f"Trusted by hundreds of satisfied customers. Quality work, fair prices, and exceptional service guaranteed.")
    business.setdefault("about_text", f"At {business['business_name']}, we've been serving the {business['city']} community with excellence for over {business.get('years_experience', 10)} years. Our team of dedicated professionals takes pride in delivering outstanding results on every project.")
    business.setdefault("about_text_2", f"We believe in building lasting relationships with our clients through honest communication, superior craftsmanship, and unwavering commitment to your satisfaction. When you choose {business['business_name']}, you're choosing a partner who truly cares about your success.")
    business.setdefault("meta_description", f"{business['business_name']} offers professional {business['category']} services in {business['city']}. Call {business.get('phone', 'us today')} for a free quote.")

    # Generate social links HTML
    business["SOCIAL_LINKS"] = generate_social_links(business.get("social_links", {}))
    business["SERVICES_HOME"] = generate_services_home(business["services"])
    business["SERVICES_FULL"] = generate_services_full(business["services"])
    business["TESTIMONIALS"] = generate_testimonials_html(business["testimonials"])
    business["TEAM_MEMBERS"] = generate_team_html(business["team_members"])
    business["PORTFOLIO_ITEMS"] = generate_portfolio_html(business["portfolio_items"])
    business["PORTFOLIO_FILTERS"] = generate_portfolio_filters(business["portfolio_items"])
    business["VALUES"] = generate_values_html(business["values"])
    business["PROCESS_STEPS"] = generate_process_html(business["process_steps"])
    business["ABOUT_FEATURES"] = generate_about_features(business["business_name"])
    business["FOOTER_SERVICES"] = generate_footer_services(business["services"])
    business["SERVICE_OPTIONS"] = generate_service_options(business["services"])
    business["PHONE_LINK"] = re.sub(r'[^\d+]', '', business.get("phone", ""))
    business["SERVICES_META"] = ", ".join(s["title"] for s in business["services"][:3])

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Copy CSS and JS
    css_src = TEMPLATE_DIR / "css"
    js_src = TEMPLATE_DIR / "js"
    if css_src.exists():
        shutil.copytree(css_src, output_path / "css", dirs_exist_ok=True)
    if js_src.exists():
        shutil.copytree(js_src, output_path / "js", dirs_exist_ok=True)

    # Process each template HTML file
    template_files = ["index.html", "about.html", "services.html", "portfolio.html", "contact.html"]
    for tmpl_file in template_files:
        tmpl_path = TEMPLATE_DIR / tmpl_file
        if not tmpl_path.exists():
            continue
        content = tmpl_path.read_text(encoding="utf-8")

        # Replace all {{PLACEHOLDER}} variables
        for key, value in business.items():
            if isinstance(value, (str, int, float)):
                content = content.replace(f"{{{{{key.upper()}}}}}", str(value))

        # Handle lowercase placeholders too
        for key, value in business.items():
            if isinstance(value, (str, int, float)):
                content = content.replace(f"{{{{{key}}}}}", str(value))

        (output_path / tmpl_file).write_text(content, encoding="utf-8")

    # Create a CNAME file placeholder
    (output_path / "CNAME").write_text("", encoding="utf-8")

    return output_path


def deploy_to_github_pages(output_path: Path, repo_name: str, cname: str = "") -> str:
    """Deploy the generated site to GitHub Pages."""
    repo_url = f"https://github.com/RNGBubba/{repo_name}.git"

    try:
        # Initialize git repo in output path
        subprocess.run(["git", "init"], cwd=output_path, capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=output_path, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=output_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"Deploy {repo_name} website"], cwd=output_path, capture_output=True, check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=output_path, capture_output=True)
        result = subprocess.run(
            ["git", "push", "-u", "origin", "gh-pages", "--force"],
            cwd=output_path, capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            # Enable GitHub Pages via API
            subprocess.run(
                ["gh", "api", f"repos/RNGBubba/{repo_name}/pages",
                 "--method", "POST",
                 "-f", "source[branch]=gh-pages",
                 "-f", "source[path]=/"],
                capture_output=True, timeout=30
            )

            if cname:
                subprocess.run(
                    ["gh", "api", f"repos/RNGBubba/{repo_name}/pages",
                     "--method", "PUT",
                     "-f", f"cname={cname}"],
                    capture_output=True, timeout=30
                )

            return f"https://RNGBubba.github.io/{repo_name}"
        else:
            print(f"Push failed: {result.stderr}")
            return ""
    except subprocess.CalledProcessError as e:
        print(f"Deployment error: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description="Mr Bubba Website Builder - Generate professional business websites")
    parser.add_argument("--config", help="Path to JSON config file with business info")
    parser.add_argument("--business-name", help="Business name")
    parser.add_argument("--category", help="Business category (e.g., plumbing, landscaping)")
    parser.add_argument("--city", help="City")
    parser.add_argument("--state", default="", help="State")
    parser.add_argument("--address", default="", help="Street address")
    parser.add_argument("--phone", default="", help="Phone number")
    parser.add_argument("--email", default="", help="Business email")
    parser.add_argument("--deploy", action="store_true", help="Deploy to GitHub Pages")
    parser.add_argument("--repo-name", help="GitHub repository name for deployment")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    # Load config
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        config = {}

    # CLI args override config file
    if args.business_name:
        config["business_name"] = args.business_name
    if args.category:
        config["category"] = args.category
    if args.city:
        config["city"] = args.city
    if args.state:
        config["state"] = args.state
    if args.address:
        config["address"] = args.address
    if args.phone:
        config["phone"] = args.phone
    if args.email:
        config["email"] = args.email

    # Validate required fields
    required = ["business_name", "category", "city"]
    missing = [f for f in required if not config.get(f)]
    if missing:
        print(f"Missing required fields: {', '.join(missing)}")
        print("Provide them via --config or CLI args.")
        sys.exit(1)

    # Build site
    output_path = Path(args.output) / config["business_name"].lower().replace(" ", "-")
    print(f"Building website for {config['business_name']}...")
    print(f"Category: {config['category']} | City: {config['city']}")

    build_site(config, output_path)

    print(f"\n✅ Website generated successfully!")
    print(f"📁 Location: {output_path}")
    print(f"📄 Pages: index.html, about.html, services.html, portfolio.html, contact.html")

    if args.deploy:
        repo_name = args.repo_name or config["business_name"].lower().replace(" ", "-").replace("&", "and")
        print(f"\n🚀 Deploying to GitHub Pages...")
        live_url = deploy_to_github_pages(output_path, repo_name, config.get("cname", ""))
        if live_url:
            print(f"🌐 Live URL: {live_url}")
        else:
            print("⚠️ Deployment encountered an issue. Manual push may be needed.")

    return output_path


if __name__ == "__main__":
    main()
