"""
Command-line interface for the Lyra marketing system.

Usage examples
--------------
# Initialize the database
python -m lyra.cli init

# Add a customer
python -m lyra.cli customer add --name "Jane Doe" --phone "555-1234" \
    --email "jane@example.com" --address "123 Main St" \
    --city "Springfield" --zip "12345"

# List all customers
python -m lyra.cli customer list

# List customers filtered by status
python -m lyra.cli customer list --status lead

# List available message templates
python -m lyra.cli template list

# Create a campaign from a template
python -m lyra.cli campaign create --name "Spring 2025" \
    --template seasonal_cleanout --zip 12345 --status lead

# List campaigns
python -m lyra.cli campaign list

# Send a campaign (dry-run shows recipients without recording)
python -m lyra.cli campaign send 1

# Show analytics
python -m lyra.cli analytics summary
python -m lyra.cli analytics campaigns
python -m lyra.cli analytics zip-codes
"""

import argparse
import json
import sys
from datetime import datetime

from .analytics import (
    all_campaign_stats,
    campaign_performance_report,
    campaign_stats,
    customer_summary,
    monthly_contacts_report,
    top_zip_codes,
)
from .campaigns import (
    create_campaign,
    delete_campaign,
    get_campaign,
    list_campaigns,
    resolve_recipients,
    send_campaign,
)
from .customers import (
    add_customer,
    delete_customer,
    get_customer,
    list_customers,
    record_contact,
    update_customer,
)
from .database import init_db
from .models import Campaign, CampaignStatus, CampaignType, Customer, CustomerStatus
from .templates import list_templates, get_template


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_table(headers: list[str], rows: list[list]) -> None:
    """Print a simple ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    separator = "  ".join("-" * w for w in col_widths)
    print(fmt.format(*headers))
    print(separator)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


def _confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")


# ── Sub-command handlers ───────────────────────────────────────────────────────

def cmd_init(args) -> None:
    init_db(args.db)
    print("✅  Database initialized.")


# Customer commands

def cmd_customer_add(args) -> None:
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    customer = Customer(
        name=args.name,
        phone=args.phone,
        email=args.email,
        address=args.address,
        city=args.city,
        zip_code=args.zip,
        status=CustomerStatus(args.status),
        notes=args.notes or "",
        tags=tags,
    )
    added = add_customer(customer, args.db)
    print(f"✅  Customer added (id={added.id}): {added.name}")


def cmd_customer_list(args) -> None:
    status = CustomerStatus(args.status) if args.status else None
    customers = list_customers(status=status, zip_code=args.zip, tag=args.tag, db_path=args.db)
    if not customers:
        print("No customers found.")
        return
    rows = [
        [c.id, c.name, c.phone, c.email, c.zip_code, c.status.value, ",".join(c.tags)]
        for c in customers
    ]
    _print_table(["ID", "Name", "Phone", "Email", "Zip", "Status", "Tags"], rows)
    print(f"\n{len(customers)} customer(s)")


def cmd_customer_get(args) -> None:
    customer = get_customer(args.id, args.db)
    if not customer:
        print(f"Customer {args.id} not found.")
        sys.exit(1)
    print(json.dumps(customer.to_dict(), indent=2))


def cmd_customer_delete(args) -> None:
    if not args.yes and not _confirm(f"Delete customer {args.id}?"):
        print("Aborted.")
        return
    delete_customer(args.id, args.db)
    print(f"✅  Customer {args.id} deleted.")


def cmd_customer_contact(args) -> None:
    record_contact(args.id, args.db)
    print(f"✅  Recorded contact for customer {args.id}.")


# Template commands

def cmd_template_list(args) -> None:
    templates = list_templates(args.type)
    rows = [[t["name"], t["type"], t["subject"][:60]] for t in templates]
    _print_table(["Name", "Type", "Subject / Preview"], rows)


def cmd_template_show(args) -> None:
    template = get_template(args.name)
    if not template:
        print(f"Template '{args.name}' not found.")
        sys.exit(1)
    print(f"Name   : {template['name']}")
    print(f"Type   : {template['type']}")
    print(f"Subject: {template['subject']}")
    print(f"\n{template['body']}")


# Campaign commands

def cmd_campaign_create(args) -> None:
    template = get_template(args.template) if args.template else None
    subject = args.subject or (template["subject"] if template else "")
    body = args.body or (template["body"] if template else "")
    if not subject or not body:
        print("Error: provide --subject and --body, or a --template.")
        sys.exit(1)

    zip_codes = [z.strip() for z in (args.zip or "").split(",") if z.strip()]
    statuses = [s.strip() for s in (args.status or "").split(",") if s.strip()]
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    campaign = Campaign(
        name=args.name,
        subject=subject,
        body=body,
        campaign_type=CampaignType(args.type),
        target_zip_codes=zip_codes,
        target_statuses=statuses,
        target_tags=tags,
    )
    created = create_campaign(campaign, args.db)
    print(f"✅  Campaign created (id={created.id}): {created.name}")


def cmd_campaign_list(args) -> None:
    status = CampaignStatus(args.status) if args.status else None
    campaigns = list_campaigns(status=status, db_path=args.db)
    if not campaigns:
        print("No campaigns found.")
        return
    rows = [
        [c.id, c.name, c.campaign_type.value, c.status.value,
         c.sent_at.strftime("%Y-%m-%d") if c.sent_at else "-"]
        for c in campaigns
    ]
    _print_table(["ID", "Name", "Type", "Status", "Sent At"], rows)


def cmd_campaign_get(args) -> None:
    campaign = get_campaign(args.id, args.db)
    if not campaign:
        print(f"Campaign {args.id} not found.")
        sys.exit(1)
    print(json.dumps(campaign.to_dict(), indent=2))


def cmd_campaign_send(args) -> None:
    campaign = get_campaign(args.id, args.db)
    if not campaign:
        print(f"Campaign {args.id} not found.")
        sys.exit(1)
    recipients = resolve_recipients(campaign, args.db)
    if args.dry_run:
        print(f"Dry-run: {len(recipients)} recipient(s) would be targeted:")
        for r in recipients:
            print(f"  • {r.name} <{r.email}> ({r.phone})")
        return
    if not args.yes and not _confirm(
        f"Send campaign '{campaign.name}' to {len(recipients)} recipient(s)?"
    ):
        print("Aborted.")
        return
    count = send_campaign(args.id, args.db)
    print(f"✅  Campaign sent to {count} recipient(s).")


def cmd_campaign_delete(args) -> None:
    if not args.yes and not _confirm(f"Delete campaign {args.id}?"):
        print("Aborted.")
        return
    delete_campaign(args.id, args.db)
    print(f"✅  Campaign {args.id} deleted.")


# Analytics commands

def cmd_analytics_summary(args) -> None:
    summary = customer_summary(args.db)
    print("Customer Summary")
    print("────────────────")
    for key, val in summary.items():
        print(f"  {key:<15}: {val}")


def cmd_analytics_campaigns(args) -> None:
    report = campaign_performance_report(args.db)
    if not report:
        print("No campaign data available.")
        return
    rows = [
        [r["campaign_id"], r["campaign_name"], r["sent"],
         f"{r['open_rate']:.1f}%", f"{r['response_rate']:.1f}%"]
        for r in report
    ]
    _print_table(["ID", "Campaign", "Sent", "Open Rate", "Response Rate"], rows)


def cmd_analytics_zip_codes(args) -> None:
    results = top_zip_codes(limit=args.limit, db_path=args.db)
    if not results:
        print("No zip code data available.")
        return
    rows = [[r["zip_code"], r["count"]] for r in results]
    _print_table(["Zip Code", "Customers"], rows)


def cmd_analytics_monthly(args) -> None:
    results = monthly_contacts_report(args.db)
    if not results:
        print("No contact history available.")
        return
    rows = [[r["month"], r["contacts"]] for r in results]
    _print_table(["Month", "Contacts"], rows)


# ── Parser construction ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lyra",
        description="Lyra – Marketing system for junk removal businesses",
    )
    parser.add_argument("--db", metavar="PATH", default=None,
                        help="Path to the SQLite database file")
    sub = parser.add_subparsers(title="commands", dest="command")
    sub.required = True

    # init
    sub.add_parser("init", help="Initialise the database")

    # customer
    cust = sub.add_parser("customer", help="Manage customers")
    cust_sub = cust.add_subparsers(title="customer commands", dest="customer_cmd")
    cust_sub.required = True

    p_add = cust_sub.add_parser("add", help="Add a customer")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--phone", required=True)
    p_add.add_argument("--email", required=True)
    p_add.add_argument("--address", required=True)
    p_add.add_argument("--city", required=True)
    p_add.add_argument("--zip", required=True)
    p_add.add_argument("--status", default="lead",
                       choices=[s.value for s in CustomerStatus])
    p_add.add_argument("--notes", default="")
    p_add.add_argument("--tags", default="",
                       help="Comma-separated tags, e.g. 'residential,repeat'")

    p_list = cust_sub.add_parser("list", help="List customers")
    p_list.add_argument("--status", choices=[s.value for s in CustomerStatus])
    p_list.add_argument("--zip", metavar="ZIP_CODE")
    p_list.add_argument("--tag")

    p_get = cust_sub.add_parser("get", help="Get a customer by id")
    p_get.add_argument("id", type=int)

    p_del = cust_sub.add_parser("delete", help="Delete a customer")
    p_del.add_argument("id", type=int)
    p_del.add_argument("--yes", action="store_true", help="Skip confirmation")

    p_contact = cust_sub.add_parser("contact", help="Record a contact event")
    p_contact.add_argument("id", type=int)

    # template
    tmpl = sub.add_parser("template", help="Browse message templates")
    tmpl_sub = tmpl.add_subparsers(title="template commands", dest="template_cmd")
    tmpl_sub.required = True

    p_tlist = tmpl_sub.add_parser("list", help="List available templates")
    p_tlist.add_argument("--type", choices=["email", "sms"])

    p_tshow = tmpl_sub.add_parser("show", help="Show a template body")
    p_tshow.add_argument("name")

    # campaign
    camp = sub.add_parser("campaign", help="Manage campaigns")
    camp_sub = camp.add_subparsers(title="campaign commands", dest="campaign_cmd")
    camp_sub.required = True

    p_ccreate = camp_sub.add_parser("create", help="Create a campaign")
    p_ccreate.add_argument("--name", required=True)
    p_ccreate.add_argument("--template", help="Template name to pre-fill subject/body")
    p_ccreate.add_argument("--subject")
    p_ccreate.add_argument("--body")
    p_ccreate.add_argument("--type", default="email",
                           choices=[t.value for t in CampaignType])
    p_ccreate.add_argument("--zip", metavar="ZIP_CODES",
                           help="Comma-separated zip codes to target")
    p_ccreate.add_argument("--status", metavar="STATUSES",
                           help="Comma-separated customer statuses to target")
    p_ccreate.add_argument("--tags", metavar="TAGS",
                           help="Comma-separated tags to target")

    p_clist = camp_sub.add_parser("list", help="List campaigns")
    p_clist.add_argument("--status", choices=[s.value for s in CampaignStatus])

    p_cget = camp_sub.add_parser("get", help="Get a campaign by id")
    p_cget.add_argument("id", type=int)

    p_csend = camp_sub.add_parser("send", help="Send a campaign")
    p_csend.add_argument("id", type=int)
    p_csend.add_argument("--dry-run", action="store_true",
                         help="Preview recipients without sending")
    p_csend.add_argument("--yes", action="store_true", help="Skip confirmation")

    p_cdel = camp_sub.add_parser("delete", help="Delete a campaign")
    p_cdel.add_argument("id", type=int)
    p_cdel.add_argument("--yes", action="store_true", help="Skip confirmation")

    # analytics
    anal = sub.add_parser("analytics", help="View analytics and reports")
    anal_sub = anal.add_subparsers(title="analytics commands", dest="analytics_cmd")
    anal_sub.required = True

    anal_sub.add_parser("summary", help="Customer status summary")
    anal_sub.add_parser("campaigns", help="Campaign performance report")

    p_azips = anal_sub.add_parser("zip-codes", help="Top zip codes by customer count")
    p_azips.add_argument("--limit", type=int, default=10)

    anal_sub.add_parser("monthly", help="Monthly contact history")

    return parser


# ── Dispatch ──────────────────────────────────────────────────────────────────

CUSTOMER_HANDLERS = {
    "add": cmd_customer_add,
    "list": cmd_customer_list,
    "get": cmd_customer_get,
    "delete": cmd_customer_delete,
    "contact": cmd_customer_contact,
}

TEMPLATE_HANDLERS = {
    "list": cmd_template_list,
    "show": cmd_template_show,
}

CAMPAIGN_HANDLERS = {
    "create": cmd_campaign_create,
    "list": cmd_campaign_list,
    "get": cmd_campaign_get,
    "send": cmd_campaign_send,
    "delete": cmd_campaign_delete,
}

ANALYTICS_HANDLERS = {
    "summary": cmd_analytics_summary,
    "campaigns": cmd_analytics_campaigns,
    "zip-codes": cmd_analytics_zip_codes,
    "monthly": cmd_analytics_monthly,
}


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        cmd_init(args)
    elif args.command == "customer":
        CUSTOMER_HANDLERS[args.customer_cmd](args)
    elif args.command == "template":
        TEMPLATE_HANDLERS[args.template_cmd](args)
    elif args.command == "campaign":
        CAMPAIGN_HANDLERS[args.campaign_cmd](args)
    elif args.command == "analytics":
        ANALYTICS_HANDLERS[args.analytics_cmd](args)


if __name__ == "__main__":
    main()
