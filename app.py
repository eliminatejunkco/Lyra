"""Flask web application for the Lyra marketing system."""

import os
from flask import Flask, render_template, request, redirect, url_for, flash

from lyra.analytics import (
    campaign_performance_report,
    campaign_stats,
    customer_summary,
    monthly_contacts_report,
    top_zip_codes,
)
from lyra.campaigns import (
    create_campaign,
    delete_campaign,
    get_campaign,
    list_campaigns,
    resolve_recipients,
    send_campaign,
    update_campaign,
)
from lyra.customers import (
    add_customer,
    delete_customer,
    get_customer,
    list_customers,
    record_contact,
    update_customer,
)
from lyra.database import init_db
from lyra.models import Campaign, CampaignStatus, CampaignType, Customer, CustomerStatus
from lyra.templates import get_template, list_templates

app = Flask(__name__)
app.secret_key = os.environ.get("LYRA_SECRET_KEY", "lyra-dev-secret-change-in-production")

DB_PATH = os.environ.get("LYRA_DB", None)  # None → default ~/.lyra/marketing.db

# Ensure DB exists on startup
init_db(DB_PATH)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


STATUS_BADGE = {
    "lead": "secondary",
    "active": "success",
    "inactive": "warning",
    "churned": "danger",
    "draft": "secondary",
    "scheduled": "info",
    "sent": "success",
    "cancelled": "danger",
}

app.jinja_env.globals["STATUS_BADGE"] = STATUS_BADGE


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    summary = customer_summary(DB_PATH)
    campaigns = list_campaigns(db_path=DB_PATH)
    sent = [c for c in campaigns if c.status == CampaignStatus.SENT]
    drafts = [c for c in campaigns if c.status == CampaignStatus.DRAFT]
    perf = campaign_performance_report(DB_PATH)[:5]
    zips = top_zip_codes(5, DB_PATH)
    recent_customers = list_customers(db_path=DB_PATH)[:5]
    return render_template(
        "dashboard.html",
        summary=summary,
        campaigns=campaigns,
        sent_count=len(sent),
        draft_count=len(drafts),
        perf=perf,
        zips=zips,
        recent_customers=recent_customers,
    )


# ── Customers ─────────────────────────────────────────────────────────────────

@app.route("/customers")
def customers_list():
    status_filter = request.args.get("status") or None
    zip_filter = request.args.get("zip") or None
    tag_filter = request.args.get("tag") or None
    status_enum = CustomerStatus(status_filter) if status_filter else None
    customers = list_customers(status=status_enum, zip_code=zip_filter, tag=tag_filter, db_path=DB_PATH)
    return render_template(
        "customers/list.html",
        customers=customers,
        status_filter=status_filter or "",
        zip_filter=zip_filter or "",
        tag_filter=tag_filter or "",
        statuses=[s.value for s in CustomerStatus],
    )


@app.route("/customers/new", methods=["GET", "POST"])
def customer_new():
    if request.method == "POST":
        tags = _split_csv(request.form.get("tags", ""))
        customer = Customer(
            name=request.form["name"],
            phone=request.form["phone"],
            email=request.form["email"],
            address=request.form["address"],
            city=request.form["city"],
            zip_code=request.form["zip_code"],
            status=CustomerStatus(request.form.get("status", "lead")),
            notes=request.form.get("notes", ""),
            tags=tags,
        )
        add_customer(customer, DB_PATH)
        flash(f"Customer added: {customer.name}", "success")
        return redirect(url_for("customers_list"))
    return render_template(
        "customers/form.html",
        customer=None,
        statuses=[s.value for s in CustomerStatus],
        action_url=url_for("customer_new"),
        title="Add Customer",
    )


@app.route("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = get_customer(customer_id, DB_PATH)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("customers_list"))
    return render_template("customers/detail.html", customer=customer)


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def customer_edit(customer_id):
    customer = get_customer(customer_id, DB_PATH)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("customers_list"))
    if request.method == "POST":
        customer.name = request.form["name"]
        customer.phone = request.form["phone"]
        customer.email = request.form["email"]
        customer.address = request.form["address"]
        customer.city = request.form["city"]
        customer.zip_code = request.form["zip_code"]
        customer.status = CustomerStatus(request.form.get("status", "lead"))
        customer.notes = request.form.get("notes", "")
        customer.tags = _split_csv(request.form.get("tags", ""))
        update_customer(customer, DB_PATH)
        flash(f"Customer updated: {customer.name}", "success")
        return redirect(url_for("customer_detail", customer_id=customer_id))
    return render_template(
        "customers/form.html",
        customer=customer,
        statuses=[s.value for s in CustomerStatus],
        action_url=url_for("customer_edit", customer_id=customer_id),
        title="Edit Customer",
    )


@app.route("/customers/<int:customer_id>/contact", methods=["POST"])
def customer_record_contact(customer_id):
    record_contact(customer_id, DB_PATH)
    flash("Contact recorded.", "success")
    return redirect(url_for("customer_detail", customer_id=customer_id))


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def customer_delete(customer_id):
    customer = get_customer(customer_id, DB_PATH)
    if customer:
        delete_customer(customer_id, DB_PATH)
        flash(f"Customer deleted: {customer.name}", "success")
    return redirect(url_for("customers_list"))


# ── Campaigns ─────────────────────────────────────────────────────────────────

@app.route("/campaigns")
def campaigns_list():
    status_filter = request.args.get("status") or None
    status_enum = CampaignStatus(status_filter) if status_filter else None
    campaigns = list_campaigns(status=status_enum, db_path=DB_PATH)
    return render_template(
        "campaigns/list.html",
        campaigns=campaigns,
        status_filter=status_filter or "",
        statuses=[s.value for s in CampaignStatus],
    )


@app.route("/campaigns/new", methods=["GET", "POST"])
def campaign_new():
    message_templates = list_templates()
    if request.method == "POST":
        tpl_name = request.form.get("template_name", "")
        tpl = get_template(tpl_name) if tpl_name else None
        subject = request.form.get("subject") or (tpl["subject"] if tpl else "")
        body = request.form.get("body") or (tpl["body"] if tpl else "")
        if not subject or not body:
            flash("Please provide a subject and body, or choose a template.", "danger")
            return render_template(
                "campaigns/form.html",
                message_templates=message_templates,
                campaign_types=[t.value for t in CampaignType],
                statuses=[s.value for s in CustomerStatus],
            )
        campaign = Campaign(
            name=request.form["name"],
            subject=subject,
            body=body,
            campaign_type=CampaignType(request.form.get("campaign_type", "email")),
            target_zip_codes=_split_csv(request.form.get("target_zip_codes", "")),
            target_statuses=_split_csv(request.form.get("target_statuses", "")),
            target_tags=_split_csv(request.form.get("target_tags", "")),
        )
        created = create_campaign(campaign, DB_PATH)
        flash(f"Campaign created: {created.name}", "success")
        return redirect(url_for("campaign_detail", campaign_id=created.id))
    return render_template(
        "campaigns/form.html",
        message_templates=message_templates,
        campaign_types=[t.value for t in CampaignType],
        statuses=[s.value for s in CustomerStatus],
    )


@app.route("/campaigns/<int:campaign_id>")
def campaign_detail(campaign_id):
    campaign = get_campaign(campaign_id, DB_PATH)
    if not campaign:
        flash("Campaign not found.", "danger")
        return redirect(url_for("campaigns_list"))
    stats = campaign_stats(campaign_id, DB_PATH)
    recipients = resolve_recipients(campaign, DB_PATH)
    return render_template(
        "campaigns/detail.html",
        campaign=campaign,
        stats=stats,
        recipients=recipients,
    )


@app.route("/campaigns/<int:campaign_id>/send", methods=["POST"])
def campaign_send(campaign_id):
    try:
        count = send_campaign(campaign_id, DB_PATH)
        flash(f"Campaign sent to {count} recipient(s)!", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("campaign_detail", campaign_id=campaign_id))


@app.route("/campaigns/<int:campaign_id>/delete", methods=["POST"])
def campaign_delete(campaign_id):
    campaign = get_campaign(campaign_id, DB_PATH)
    if campaign:
        delete_campaign(campaign_id, DB_PATH)
        flash(f"Campaign deleted: {campaign.name}", "success")
    return redirect(url_for("campaigns_list"))


# ── Templates ─────────────────────────────────────────────────────────────────

@app.route("/message-templates")
def tmpl_list():
    type_filter = request.args.get("type") or None
    templates = list_templates(type_filter)
    return render_template("tmpl_list.html", templates=templates, type_filter=type_filter or "")


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.route("/analytics")
def analytics():
    summary = customer_summary(DB_PATH)
    perf = campaign_performance_report(DB_PATH)
    zips = top_zip_codes(10, DB_PATH)
    monthly = monthly_contacts_report(DB_PATH)
    return render_template(
        "analytics.html",
        summary=summary,
        perf=perf,
        zips=zips,
        monthly=monthly,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=port)
