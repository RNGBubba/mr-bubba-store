#!/usr/bin/env python3
"""
Social Media Content Generator
Mr Bubba Services — Social Media Content Service

Generates captions, hashtags, and image descriptions for a client's social media
content calendar based on brand details and preferences.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import requests
from pathlib import Path

# AgentMail configuration
AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7")
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
AGENTMAIL_API_URL = "https://api.agentmail.to/v1"

# Content generation templates
HASHTAG_CATEGORIES = {
    "brand": ["#{brand}", "#{brand}life", "#{brand}daily", "love{brand}", "{brand}community"],
    "lifestyle": ["lifestyle", "dailylife", "life", "inspiration", "motivation", "dailyinspo"],
    "niche_fitness": ["fitness", "workout", "healthyliving", "fitlife", "gymlife", "wellness", "health"],
    "niche_food": ["foodie", "foodporn", "instafood", "yummy", "delicious", "homemade", "cooking"],
    "niche_tech": ["tech", "technology", "innovation", "startup", "ai", "digital", "coding"],
    "niche_fashion": ["fashion", "style", "ootd", "outfit", "fashionista", "lookbook", "trendy"],
    "niche_business": ["business", "entrepreneur", "hustle", "success", "marketing", "smallbusiness"],
    "engagement": ["commentbelow", "doubletag", "shareyourthoughts", "whatdoyouthink", "poll"],
}

CONTENT_PILLARS = [
    "educational", "entertaining", "inspirational", "promotional",
    "behind-the-scenes", "user-generated", "trending", "community"
]

POST_TEMPLATES = {
    "educational": [
        "Did you know? {fact} Learn more about how {brand} brings this to life. {hashtags}",
        "Pro tip from {brand}: {fact} Save this for later! {hashtags}",
        "Here's something we bet you didn't know: {fact} {hashtags}",
    ],
    "entertaining": [
        "POV: You just discovered {brand} and your {niche} game just leveled up 🔥 {hashtags}",
        "Tell us in the comments: {question} We want to hear your take! {hashtags}",
        "When {relatable_moment} 😂 Tag someone who needs to see this! {hashtags}",
    ],
    "inspirational": [
        "Every day is a new opportunity to {action}. {brand} is here to help you get there. {hashtags}",
        "Remember: {quote} Keep pushing forward! {hashtags}",
        "Success starts with a single step. Take yours today with {brand}. {hashtags}",
    ],
    "promotional": [
        "🎉 BIG NEWS from {brand}! {promo_detail} Link in bio to learn more! {hashtags}",
        "Your {niche} journey just got an upgrade. Try {brand} today! {hashtags}",
        "Limited offer: {promo_detail} Don't miss out — shop now! {hashtags}",
    ],
    "behind-the-scenes": [
        "A peek behind the scenes at {brand} 👀 Here's how we {behind_scenes_action}. {hashtags}",
        "The making of {behind_scenes_detail} It takes a village! {hashtags}",
        "Day in the life at {brand}: {behind_scenes_action} {hashtags}",
    ],
    "community": [
        "Shoutout to @{community_member} for this amazing {ugc_type}! 💛 {hashtags}",
        "Our community never disappoints! Here's what {community_member} shared: {ugc_type} {hashtags}",
        "Community spotlight: {community_member} showing us how it's done! {hashtags}",
    ],
    "trending": [
        "Jumping on the {trend_name} trend with our {niche} twist! What do you think? {hashtags}",
        "The {trend_name} trend but make it {brand} 🔥 {hashtags}",
        "Everyone's talking about {trend_name} — here's our take! {hashtags}",
    ],
}

IMAGE_DESCRIPTIONS = {
    "educational": [
        "Clean infographic-style image with brand colors ({brand_colors}), {brand} logo top-left. Central text: '{fact}' with relevant iconography. Minimalist layout with clear data visualization elements.",
        "Carousel-style educational post with numbered steps. Brand header with {brand} logo, soft gradient background using {brand_colors}. Each slide features one key point with supporting icon.",
    ],
    "entertaining": [
        "Meme-style image with bold Impact-style text overlay. Humorous image related to {niche} with {brand} logo watermark. Bright, eye-catching colors that pop in feed.",
        "Relatable {niche} scenario photo with text overlay at top: '{question}'. {brand} branding in corner. Authentic, candid photography style.",
    ],
    "inspirational": [
        "Stunning landscape or aspirational lifestyle photo with {brand_colors} overlay. Quote text centered in elegant serif font. {brand} logo subtle in bottom corner.",
        "Flat lay composition with {niche}-related items arranged artistically. Natural lighting with warm {brand_colors} tones. {brand} branding on a small card in the scene.",
    ],
    "promotional": [
        "Bold promotional graphic with {brand_colors} gradient background. Product/service hero image centered. 'LIMITED OFFER' badge element. {brand} logo prominent. Call-to-action text at bottom.",
        "Before/after comparison layout showing {brand} results. Split-screen design with {brand_colors} divider. {brand} logo top-center. Key stats or results highlighted.",
    ],
    "behind-the-scenes": [
        "Authentic candid photo of workspace or team at work. Natural lighting with {brand_colors} color grade. {brand} logo subtle overlay. Storytelling caption overlay optional.",
        "Time-lapse style composite showing process steps. Warm, authentic feel with {brand_colors} accents. {brand} branding on workspace elements naturally integrated.",
    ],
    "community": [
        "Repost of user content with {brand} frame/border overlay. {brand_colors} border with {brand} logo attribution. 'Community Spotlight' badge element.",
        "Quote card featuring community member's words. {brand_colors} gradient background with elegant typography. {brand} and community member attribution.",
    ],
    "trending": [
        "Video thumbnail style with bold text: '{trend_name} but {brand} edition!'. Dynamic composition with motion blur effect suggestion. {brand} logo overlay. {brand_colors} accent elements.",
        "Trend-jacking carousel post opening slide with bold '{trend_name}' text. {brand_colors} design elements. {brand} logo. Playful, trend-aware visual style.",
    ],
}

FACTS = {
    "fitness": [
        "Consistency beats intensity — 30 minutes daily outperforms sporadic 2-hour sessions.",
        "Rest days are growth days. Your muscles rebuild stronger during recovery.",
        "Hydration impacts performance by up to 25%. Water is your secret weapon.",
    ],
    "food": [
        "Meal prepping on Sundays can save you 5+ hours during the week.",
        "The way you plate food affects how it tastes — presentation matters!",
        "Fermented foods support gut health, which influences mood and energy.",
    ],
    "tech": [
        "The best code is the code you don't have to write. Simplicity wins.",
        "Automation can save businesses 20+ hours per week on repetitive tasks.",
        "User experience drives 88% of return customers in digital products.",
    ],
    "fashion": [
        "A capsule wardrobe of 30 pieces can create over 100 unique outfits.",
        "Sustainable fashion reduces environmental impact by up to 30% per garment.",
        "Quality over quantity: one timeless piece outlasts ten trend-driven items.",
    ],
    "business": [
        "Customer retention is 5-25x cheaper than acquisition.",
        "Personalized marketing delivers 6-10x higher conversion rates.",
        "Businesses that blog get 55% more website visitors than those that don't.",
    ],
    "general": [
        "Small daily improvements lead to stunning long-term results.",
        "Your brand is what people say about you when you're not in the room.",
        "Authenticity builds trust faster than perfection ever could.",
    ],
}

QUOTES = [
    "progress, not perfection.",
    "the journey is the destination.",
    "chase consistency, not results.",
    "show up even when it's hard.",
    "your future self will thank you.",
]

QUESTIONS = {
    "fitness": [
        "What's the one fitness goal you're crushing this month?",
        "Morning workout or evening sweat session?",
        "What's your go-to pre-workout fuel?",
    ],
    "food": [
        "What's the dish you could eat every day and never get tired of?",
        "Sweet or savory for breakfast?",
        "What's your controversial food opinion?",
    ],
    "tech": [
        "What's the one app you can't live without?",
        "Mac, Windows, or Linux — and why?",
        "What's your hot take on AI?",
    ],
    "fashion": [
        "Comfort or style — which wins when you can't have both?",
        "What's the oldest piece in your closet you still wear?",
        "Sneakers or boots for everyday wear?",
    ],
    "business": [
        "What's the best piece of business advice you've ever received?",
        "Coffee shop office or home office?",
        "What's your #1 productivity hack?",
    ],
    "general": [
        "What's one thing you're excited about this week?",
        "Describe your vibe in three words.",
        "What's the last thing that made you smile?",
    ],
}


def select_hashtags(brand_info: Dict) -> List[str]:
    """Generate relevant hashtags based on brand niche and details."""
    niche = brand_info.get("niche", "general").lower()
    brand_name = brand_info.get("brand_name", "brand")

    hashtags = []

    # Brand hashtags (2-3)
    brand_tags = [tag.format(brand=brand_name) for tag in HASHTAG_CATEGORIES["brand"]]
    hashtags.extend(random.sample(brand_tags, min(2, len(brand_tags))))

    # Niche-specific hashtags (3-5)
    niche_key = f"niche_{niche}"
    niche_tags = HASHTAG_CATEGORIES.get(niche_key, [])
    if niche_tags:
        hashtags.extend(random.sample(niche_tags, min(4, len(niche_tags))))
    else:
        hashtags.extend(random.sample(HASHTAG_CATEGORIES["lifestyle"], 3))

    # Engagement hashtags (1-2)
    engagement_tags = random.sample(HASHTAG_CATEGORIES["engagement"], 1)
    hashtags.extend(engagement_tags)

    # Always add generic reach tags
    hashtags.extend(["instagood", "photooftheday", "followforfollow"])

    # Shuffle and return unique
    random.shuffle(hashtags)
    return list(dict.fromkeys(hashtags))  # preserves order, removes duplicates


def generate_caption(brand_info: Dict, pillar: str, day: int) -> str:
    """Generate a single caption based on brand info and content pillar."""
    templates = POST_TEMPLATES.get(pillar, POST_TEMPLATES["educational"])
    template = random.choice(templates)

    brand_name = brand_info.get("brand_name", "Brand")
    niche = brand_info.get("niche", "general")
    brand_colors = brand_info.get("brand_colors", "#FF5733, #333333")

    facts_pool = FACTS.get(niche, FACTS["general"])
    questions_pool = QUESTIONS.get(niche, QUESTIONS["general"])

    # Select hashtags
    hashtags = select_hashtags(brand_info)
    hashtag_str = " ".join(hashtags[:10])

    # Fill in template variables
    caption = template.format(
        brand=brand_name,
        niche=niche,
        fact=random.choice(facts_pool),
        question=random.choice(questions_pool),
        quote=random.choice(QUOTES),
        hashtags=hashtag_str,
        action="take that first step toward your goals",
        relatable_moment="you check your phone in the morning and see 47 notifications",
        promo_detail="New launch dropping next week — stay tuned!",
        behind_scenes_action="craft each product with care",
        behind_scenes_detail="our latest collection",
        community_member="our amazing community",
        ugc_type="review and unboxing",
        trend_name="this viral audio",
        brand_colors=brand_colors,
    )

    return caption


def generate_image_description(brand_info: Dict, pillar: str, day: int) -> str:
    """Generate an image description for a post."""
    brand_name = brand_info.get("brand_name", "Brand")
    niche = brand_info.get("niche", "general")
    brand_colors = brand_info.get("brand_colors", "#FF5733, #333333")

    descriptions = IMAGE_DESCRIPTIONS.get(pillar, IMAGE_DESCRIPTIONS["educational"])
    description = random.choice(descriptions)

    # Add day-specific variation
    variation_note = f"\n\nNote for Day {day}: Consider adding a carousel (multiple slides) for higher engagement on this content pillar."

    return description.format(
        brand=brand_name,
        niche=niche,
        brand_colors=brand_colors,
        fact=random.choice(FACTS.get(niche, FACTS["general"])),
        question=random.choice(QUESTIONS.get(niche, QUESTIONS["general"])),
        trend_name="varying trend",
    ) + variation_note


def generate_content_calendar(brand_info: Dict, period: str = "week") -> Dict:
    """
    Generate a full content calendar for the specified period.
    
    Args:
        brand_info: Dictionary with brand_name, niche, brand_colors, tone, target_audience
        period: 'week' (7 days) or 'month' (30 days)
    
    Returns:
        Dictionary containing the full content calendar
    """
    days = 7 if period == "week" else 30
    start_date = datetime.now() + timedelta(days=1)

    calendar = {
        "brand": brand_info.get("brand_name", "Brand"),
        "period": period,
        "generated_date": datetime.now().isoformat(),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "posts": [],
    }

    for day in range(1, days + 1):
        post_date = start_date + timedelta(days=day - 1)
        pillar = CONTENT_PILLARS[(day - 1) % len(CONTENT_PILLARS)]

        caption = generate_caption(brand_info, pillar, day)
        image_desc = generate_image_description(brand_info, pillar, day)
        hashtags = select_hashtags(brand_info)

        post = {
            "day": day,
            "date": post_date.strftime("%Y-%m-%d"),
            "pillar": pillar,
            "caption": caption,
            "hashtags": hashtags,
            "image_description": image_desc,
            "posting_time": "10:00 AM",  # Default; client can customize
            "platforms": brand_info.get("platforms", ["Instagram", "Facebook"]),
        }

        calendar["posts"].append(post)

    return calendar


def generate_paypal_invoice(client_email: str, period: str, brand_name: str) -> Dict:
    """
    Generate a PayPal invoice for the social content service.
    
    Args:
        client_email: Client's email address
        period: 'week' or 'month'
        brand_name: Client's brand name
    
    Returns:
        Invoice details dictionary
    """
    if period == "week":
        amount = 50.00
        description = f"Social Media Content Package — Weekly ({brand_name})"
    elif period == "month":
        amount = 150.00
        description = f"Social Media Content Package — Monthly ({brand_name})"
    else:
        raise ValueError("Period must be 'week' or 'month'")

    invoice = {
        "client_email": client_email,
        "brand": brand_name,
        "period": period,
        "amount_usd": amount,
        "description": description,
        "service": "Social Media Content Generation",
        "deliverables": f"{'7' if period == 'week' else '30'} social media posts with captions, hashtags, and image descriptions",
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "status": "pending",
    }

    return invoice


def save_calendar(calendar: Dict, output_dir: str = "output") -> str:
    """Save the content calendar to a JSON file."""
    Path(output_dir).mkdir(exist_ok=True)
    filename = f"{output_dir}/{calendar['brand'].lower().replace(' ', '_')}_{calendar['period']}_calendar.json"
    with open(filename, "w") as f:
        json.dump(calendar, f, indent=2)
    return filename


def export_calendar_text(calendar: Dict, output_dir: str = "output") -> str:
    """Export the content calendar as a readable text file."""
    Path(output_dir).mkdir(exist_ok=True)
    filename = f"{output_dir}/{calendar['brand'].lower().replace(' ', '_')}_{calendar['period']}_calendar.txt"

    lines = []
    lines.append("=" * 60)
    lines.append(f"  SOCIAL MEDIA CONTENT CALENDAR")
    lines.append(f"  Brand: {calendar['brand']}")
    lines.append(f"  Period: {calendar['period'].capitalize()}")
    lines.append(f"  Generated: {calendar['generated_date'][:10]}")
    lines.append("=" * 60)
    lines.append("")

    for post in calendar["posts"]:
        lines.append(f"Day {post['day']} — {post['date']} [{post['pillar'].upper()}]")
        lines.append(f"Platforms: {', '.join(post['platforms'])}")
        lines.append(f"Post Time: {post['posting_time']}")
        lines.append("")
        lines.append("CAPTION:")
        lines.append(post["caption"])
        lines.append("")
        lines.append("HASHTAGS:")
        lines.append(" ".join(post["hashtags"]))
        lines.append("")
        lines.append("IMAGE DESCRIPTION:")
        lines.append(post["image_description"])
        lines.append("")
        lines.append("-" * 40)
        lines.append("")

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    return filename


def send_agentmail_reply(to_email: str, subject: str, body: str, api_key: str = AGENTMAIL_API_KEY) -> bool:
    """Send an auto-reply via AgentMail API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": AGENTMAIL_INBOX,
        "to": to_email,
        "subject": subject,
        "text": body,
    }
    try:
        response = requests.post(
            f"{AGENTMAIL_API_URL}/send",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send email: {e}")
        return False


def process_inquiry(email_data: Dict) -> str:
    """
    Process an incoming client inquiry and generate a response.
    
    Args:
        email_data: Dict with 'from', 'subject', 'body' fields
    
    Returns:
        Response text to send back
    """
    sender = email_data.get("from", "Client")
    body = email_data.get("body", "").lower()

    # Determine the inquiry type and respond
    if "price" in body or "cost" in body or "how much" in body:
        response = f"""Hi {sender.split('@')[0].title()},

Thanks for your interest in our Social Media Content packages!

Our pricing:
• Weekly Package: $50/week — 7 ready-to-post social media pieces
• Monthly Package: $150/month — 30 posts with content calendar

Each post includes:
✓ Engaging caption
✓ Relevant hashtags (10+ per post)
✓ Detailed image description
✓ Optimal posting times

Interested in getting started? Reply with:
1. Your brand name
2. Your industry/niche
3. Preferred package (weekly or monthly)
4. Brand colors (hex codes preferred)
5. Target platforms (Instagram, Facebook, TikTok, etc.)

Looking forward to creating content that connects!

— Mr Bubba Services"""

    elif "sample" in body or "example" in body or "demo" in body:
        response = f"""Hi {sender.split('@')[0].title()},

We'd love to show you what we can do! Here's a quick example of our content quality:

---
Sample Post — Day 1 [EDUCATIONAL]

Did you know? Consistency beats intensity — 30 minutes daily outperforms sporadic 2-hour sessions.

Learn more about how your brand brings this to life.

#YourBrand #YourBrandLife #Fitness #Workout #HealthyLiving #Wellness #Health #DailyInspo #Instagood #Photooftheday #FollowForFollow

Image Description: Clean infographic-style image with brand colors, logo top-left. Central text with key fact. Minimalist layout with clear data visualization elements.
---

Want a full week's sample calendar for your specific brand? Just reply with your brand details!

— Mr Bubba Services"""

    elif "start" in body or "begin" in body or "signup" in body or "sign up" in body:
        response = f"""Hi {sender.split('@')[0].title()},

Awesome! Let's get you started. Just send us:

1. Brand name & tagline
2. Industry/niche (fitness, food, tech, fashion, business, etc.)
3. Brand colors (hex codes, e.g., #FF5733)
4. Target audience description
5. Preferred package: Weekly ($50) or Monthly ($150)
6. Social platforms (Instagram, Facebook, TikTok, LinkedIn, etc.)
7. Any specific content themes or upcoming promotions

Once we have these details, we'll deliver your first content calendar within 24 hours!

— Mr Bubba Services"""

    else:
        # General inquiry response
        response = f"""Hi {sender.split('@')[0].title()},

Thanks for reaching out to Mr Bubba Services!

We create social media content (captions, hashtags, image descriptions) tailored to your brand.

Quick Overview:
• Weekly Package: $50/week (7 posts)
• Monthly Package: $150/month (30 posts)
• Each post includes caption, hashtags, and image description
• Content customized to your brand voice and niche

To get started or learn more, just reply with:
• "Pricing" for detailed pricing info
• "Sample" to see a content example
• "Start" to begin onboarding

Or tell us about your brand and we'll tailor our response!

— Mr Bubba Services"""

    return response


def main():
    """Main entry point for the social content generator CLI."""
    if len(sys.argv) < 2:
        print("Social Media Content Generator")
        print("Usage:")
        print("  python social_content.py generate <brand_json_file> [week|month]")
        print("  python social_content.py reply <inquiry_json_file>")
        print("  python social_content.py invoice <client_email> <week|month> <brand_name>")
        print()
        print("Example:")
        print('  python social_content.py generate brand_info.json week')
        print('  python social_content.py invoice client@email.com week MyBrand')
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        if len(sys.argv) < 3:
            print("Error: Please provide a brand JSON file path.")
            sys.exit(1)

        brand_file = sys.argv[2]
        period = sys.argv[3] if len(sys.argv) > 3 else "week"

        with open(brand_file, "r") as f:
            brand_info = json.load(f)

        print(f"\nGenerating {period} content calendar for '{brand_info.get('brand_name', 'Brand')}'...\n")
        calendar = generate_content_calendar(brand_info, period)

        # Save JSON and text versions
        json_file = save_calendar(calendar)
        text_file = export_calendar_text(calendar)

        print(f"✅ Content calendar generated!")
        print(f"   📄 JSON: {json_file}")
        print(f"   📄 Text: {text_file}")
        print(f"   📊 Total posts: {len(calendar['posts'])}")
        print(f"   📅 Period: {period}")

    elif command == "reply":
        if len(sys.argv) < 3:
            print("Error: Please provide an inquiry JSON file.")
            sys.exit(1)

        inquiry_file = sys.argv[2]
        with open(inquiry_file, "r") as f:
            inquiry = json.load(f)

        response = process_inquiry(inquiry)
        print(f"\nGenerated reply to {inquiry.get('from')}:")
        print("-" * 40)
        print(response)
        print("-" * 40)

        # Optionally send the reply
        send = input("\nSend this reply via AgentMail? (y/n): ").lower()
        if send == "y":
            success = send_agentmail_reply(
                inquiry.get("from", ""),
                f"Re: {inquiry.get('subject', 'Your Inquiry')}",
                response,
            )
            if success:
                print("✅ Reply sent successfully!")
            else:
                print("❌ Failed to send reply.")

    elif command == "invoice":
        if len(sys.argv) < 5:
            print("Error: Usage: python social_content.py invoice <client_email> <week|month> <brand_name>")
            sys.exit(1)

        client_email = sys.argv[2]
        period = sys.argv[3]
        brand_name = sys.argv[4]

        invoice = generate_paypal_invoice(client_email, period, brand_name)
        print(f"\n📋 Invoice Generated:")
        print(f"   Client: {invoice['client_email']}")
        print(f"   Brand: {invoice['brand']}")
        print(f"   Period: {invoice['period']}")
        print(f"   Amount: ${invoice['amount_usd']:.2f} USD")
        print(f"   Description: {invoice['description']}")
        print(f"   Due: {invoice['due_date']}")
        print()
        print("To send via PayPal, use the PayPal dashboard or API with these details.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
