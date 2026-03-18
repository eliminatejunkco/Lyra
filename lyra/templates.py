"""
Pre-built email and SMS message templates for junk removal marketing campaigns.

Each template is a dict with keys:
  name        – short identifier
  subject     – email subject (empty for SMS templates)
  body        – message body (supports {placeholders})
  type        – 'email' | 'sms'
"""

TEMPLATES: list[dict] = [
    # ── Email templates ──────────────────────────────────────────────────────
    {
        "name": "seasonal_cleanout",
        "subject": "Spring Cleaning? Let Us Haul It Away!",
        "body": (
            "Hi {name},\n\n"
            "Spring is the perfect time for a fresh start! "
            "Whether it's old furniture, appliances, or years of clutter, "
            "our team at Eliminate Junk Co is ready to haul it all away fast and affordably.\n\n"
            "📦  Same-day & next-day service available\n"
            "♻️  We recycle and donate whenever possible\n"
            "💲  Free, no-obligation quotes\n\n"
            "Book your pickup today by replying to this email or calling us directly.\n\n"
            "Best,\nThe Eliminate Junk Co Team"
        ),
        "type": "email",
    },
    {
        "name": "win_back",
        "subject": "We Miss You – Here's 10% Off Your Next Pickup",
        "body": (
            "Hi {name},\n\n"
            "It's been a while since we last helped you out, and we'd love to "
            "earn your business again.\n\n"
            "Use code COMEBACK10 at booking for 10% off your next junk removal.\n\n"
            "We're faster, greener, and friendlier than ever. "
            "Let's get your space cleared!\n\n"
            "Book online or give us a call.\n\n"
            "Cheers,\nThe Eliminate Junk Co Team"
        ),
        "type": "email",
    },
    {
        "name": "referral_ask",
        "subject": "Love Our Service? Share the Love 🎁",
        "body": (
            "Hi {name},\n\n"
            "We hope your last junk removal went smoothly! "
            "If you were happy with our service, we'd love a referral.\n\n"
            "For every friend or neighbor you refer who books a pickup, "
            "you'll both receive $20 off your next service.\n\n"
            "Just ask them to mention your name when they book.\n\n"
            "Thanks for helping us grow!\n\n"
            "The Eliminate Junk Co Team"
        ),
        "type": "email",
    },
    {
        "name": "new_lead_welcome",
        "subject": "Thanks for Your Interest – Here's What We Offer",
        "body": (
            "Hi {name},\n\n"
            "Thanks for reaching out to Eliminate Junk Co!\n\n"
            "Here's a quick overview of what we offer:\n"
            "✅  Full-service junk removal (furniture, appliances, yard waste & more)\n"
            "✅  Same-day and next-day appointments\n"
            "✅  Transparent, upfront pricing\n"
            "✅  Eco-friendly disposal – we recycle & donate\n\n"
            "Ready to get a free quote? Reply to this email or call us today.\n\n"
            "Looking forward to serving you,\nThe Eliminate Junk Co Team"
        ),
        "type": "email",
    },
    # ── SMS templates ─────────────────────────────────────────────────────────
    {
        "name": "sms_promo",
        "subject": "",
        "body": (
            "Hi {name}! Eliminate Junk Co here. "
            "Book a junk pickup this week & get $15 off. "
            "Reply STOP to opt out."
        ),
        "type": "sms",
    },
    {
        "name": "sms_follow_up",
        "subject": "",
        "body": (
            "Hi {name}, just following up from Eliminate Junk Co. "
            "Still need help clearing out? We have openings this week. "
            "Reply or call us! Reply STOP to opt out."
        ),
        "type": "sms",
    },
]


def get_template(name: str) -> dict | None:
    """Return a template by name, or None if not found."""
    for template in TEMPLATES:
        if template["name"] == name:
            return template
    return None


def list_templates(campaign_type: str | None = None) -> list[dict]:
    """Return all templates, optionally filtered by type ('email' or 'sms')."""
    if campaign_type is None:
        return TEMPLATES
    return [t for t in TEMPLATES if t["type"] == campaign_type]


def render_template(template_name: str, customer_data: dict) -> dict:
    """
    Return a copy of a template with {placeholders} filled in.

    customer_data keys that are used: name, address, city, zip_code, phone, email.
    """
    template = get_template(template_name)
    if template is None:
        raise ValueError(f"Template '{template_name}' not found.")
    return {
        "name": template["name"],
        "subject": template["subject"].format(**customer_data),
        "body": template["body"].format(**customer_data),
        "type": template["type"],
    }
