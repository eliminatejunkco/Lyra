"""Analytics and reporting for the Lyra marketing system."""

from .campaigns import get_recipients, list_campaigns
from .customers import list_customers
from .database import get_connection
from .models import CampaignStats, CustomerStatus


def campaign_stats(campaign_id: int, db_path=None) -> CampaignStats:
    """Return engagement statistics for a single campaign."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, name FROM campaigns WHERE id=?", (campaign_id,)
        ).fetchone()
    if row is None:
        raise ValueError(f"Campaign {campaign_id} not found.")

    recipients = get_recipients(campaign_id, db_path)
    stats = CampaignStats(
        campaign_id=campaign_id,
        campaign_name=row["name"],
        total_recipients=len(recipients),
        sent=sum(1 for r in recipients if r.sent_at is not None),
        opened=sum(1 for r in recipients if r.opened),
        clicked=sum(1 for r in recipients if r.clicked),
        responded=sum(1 for r in recipients if r.responded),
        unsubscribed=sum(1 for r in recipients if r.unsubscribed),
    )
    return stats


def all_campaign_stats(db_path=None) -> list[CampaignStats]:
    """Return stats for every campaign."""
    campaigns = list_campaigns(db_path=db_path)
    return [campaign_stats(c.id, db_path) for c in campaigns]


def customer_summary(db_path=None) -> dict:
    """Return a summary of customers broken down by status."""
    customers = list_customers(db_path=db_path)
    summary: dict = {s.value: 0 for s in CustomerStatus}
    summary["total"] = len(customers)
    for customer in customers:
        status_val = customer.status.value if isinstance(customer.status, CustomerStatus) else customer.status
        summary[status_val] = summary.get(status_val, 0) + 1
    return summary


def top_zip_codes(limit: int = 10, db_path=None) -> list[dict]:
    """Return the top zip codes by customer count."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT zip_code, COUNT(*) AS count
            FROM customers
            GROUP BY zip_code
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [{"zip_code": r["zip_code"], "count": r["count"]} for r in rows]


def campaign_performance_report(db_path=None) -> list[dict]:
    """Return a list of campaigns sorted by response rate (best first)."""
    stats_list = all_campaign_stats(db_path)
    sorted_stats = sorted(stats_list, key=lambda s: s.response_rate, reverse=True)
    return [s.to_dict() for s in sorted_stats]


def monthly_contacts_report(db_path=None) -> list[dict]:
    """Return number of customers contacted per month."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', last_contacted) AS month,
                   COUNT(*) AS contacts
            FROM customers
            WHERE last_contacted IS NOT NULL
            GROUP BY month
            ORDER BY month DESC
            """,
        ).fetchall()
    return [{"month": r["month"], "contacts": r["contacts"]} for r in rows]
