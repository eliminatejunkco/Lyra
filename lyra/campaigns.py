"""Campaign management for the Lyra marketing system."""

from datetime import datetime, timezone
from typing import Optional

from .database import get_connection, init_db
from .models import Campaign, CampaignRecipient, CampaignStatus, CampaignType, CustomerStatus
from .customers import list_customers


def _row_to_campaign(row) -> Campaign:
    def _split(val: str) -> list:
        return [v for v in (val or "").split(",") if v]

    return Campaign(
        id=row["id"],
        name=row["name"],
        subject=row["subject"],
        body=row["body"],
        campaign_type=CampaignType(row["campaign_type"]),
        status=CampaignStatus(row["status"]),
        target_zip_codes=_split(row["target_zip_codes"]),
        target_statuses=_split(row["target_statuses"]),
        target_tags=_split(row["target_tags"]),
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row["scheduled_at"] else None,
        sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
    )


def _row_to_recipient(row) -> CampaignRecipient:
    return CampaignRecipient(
        id=row["id"],
        campaign_id=row["campaign_id"],
        customer_id=row["customer_id"],
        sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
        opened=bool(row["opened"]),
        clicked=bool(row["clicked"]),
        responded=bool(row["responded"]),
        unsubscribed=bool(row["unsubscribed"]),
    )


def create_campaign(campaign: Campaign, db_path=None) -> Campaign:
    """Insert a new campaign and return it with its assigned id."""
    init_db(db_path)
    data = campaign.to_dict()
    data.pop("id", None)
    data.pop("created_at", None)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO campaigns
                (name, subject, body, campaign_type, status,
                 target_zip_codes, target_statuses, target_tags,
                 scheduled_at, sent_at)
            VALUES
                (:name, :subject, :body, :campaign_type, :status,
                 :target_zip_codes, :target_statuses, :target_tags,
                 :scheduled_at, :sent_at)
            """,
            data,
        )
        campaign.id = cursor.lastrowid
    return campaign


def get_campaign(campaign_id: int, db_path=None) -> Optional[Campaign]:
    """Fetch a single campaign by id."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
    return _row_to_campaign(row) if row else None


def list_campaigns(status: Optional[CampaignStatus] = None, db_path=None) -> list[Campaign]:
    """Return campaigns, optionally filtered by status."""
    query = "SELECT * FROM campaigns"
    params: list = []
    if status:
        query += " WHERE status = ?"
        params.append(status.value if isinstance(status, CampaignStatus) else status)
    query += " ORDER BY created_at DESC"
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_campaign(r) for r in rows]


def update_campaign(campaign: Campaign, db_path=None) -> Campaign:
    """Update an existing campaign record."""
    if campaign.id is None:
        raise ValueError("Campaign must have an id to be updated.")
    data = campaign.to_dict()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE campaigns
            SET name=:name, subject=:subject, body=:body,
                campaign_type=:campaign_type, status=:status,
                target_zip_codes=:target_zip_codes,
                target_statuses=:target_statuses,
                target_tags=:target_tags,
                scheduled_at=:scheduled_at, sent_at=:sent_at
            WHERE id=:id
            """,
            data,
        )
    return campaign


def delete_campaign(campaign_id: int, db_path=None) -> None:
    """Delete a campaign and its recipient records."""
    with get_connection(db_path) as conn:
        conn.execute(
            "DELETE FROM campaign_recipients WHERE campaign_id = ?", (campaign_id,)
        )
        conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))


def resolve_recipients(campaign: Campaign, db_path=None) -> list:
    """Return the list of customers that match the campaign's targeting criteria."""
    all_customers = list_customers(db_path=db_path)
    selected = []
    for customer in all_customers:
        # Filter by zip code
        if campaign.target_zip_codes and customer.zip_code not in campaign.target_zip_codes:
            continue
        # Filter by status
        if campaign.target_statuses:
            cust_status = customer.status.value if isinstance(customer.status, CustomerStatus) else customer.status
            if cust_status not in campaign.target_statuses:
                continue
        # Filter by tag
        if campaign.target_tags:
            if not any(t in customer.tags for t in campaign.target_tags):
                continue
        selected.append(customer)
    return selected


def send_campaign(campaign_id: int, db_path=None) -> int:
    """
    Mark a campaign as sent and create recipient records for matching customers.

    In a production system this would integrate with an email/SMS gateway.
    Returns the number of recipients targeted.
    """
    campaign = get_campaign(campaign_id, db_path)
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id} not found.")
    if campaign.status == CampaignStatus.SENT:
        raise ValueError(f"Campaign {campaign_id} has already been sent.")

    recipients = resolve_recipients(campaign, db_path)
    now = datetime.now(timezone.utc).isoformat()

    with get_connection(db_path) as conn:
        for customer in recipients:
            conn.execute(
                """
                INSERT OR IGNORE INTO campaign_recipients
                    (campaign_id, customer_id, sent_at)
                VALUES (?, ?, ?)
                """,
                (campaign_id, customer.id, now),
            )
        conn.execute(
            "UPDATE campaigns SET status='sent', sent_at=? WHERE id=?",
            (now, campaign_id),
        )

    return len(recipients)


def record_open(campaign_id: int, customer_id: int, db_path=None) -> None:
    """Record that a customer opened a campaign message."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE campaign_recipients
            SET opened=1
            WHERE campaign_id=? AND customer_id=?
            """,
            (campaign_id, customer_id),
        )


def record_click(campaign_id: int, customer_id: int, db_path=None) -> None:
    """Record that a customer clicked a link in a campaign message."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE campaign_recipients
            SET clicked=1
            WHERE campaign_id=? AND customer_id=?
            """,
            (campaign_id, customer_id),
        )


def record_response(campaign_id: int, customer_id: int, db_path=None) -> None:
    """Record that a customer responded to a campaign."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE campaign_recipients
            SET responded=1
            WHERE campaign_id=? AND customer_id=?
            """,
            (campaign_id, customer_id),
        )


def record_unsubscribe(campaign_id: int, customer_id: int, db_path=None) -> None:
    """Record that a customer unsubscribed via a campaign."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE campaign_recipients
            SET unsubscribed=1
            WHERE campaign_id=? AND customer_id=?
            """,
            (campaign_id, customer_id),
        )


def get_recipients(campaign_id: int, db_path=None) -> list[CampaignRecipient]:
    """Return all recipient records for a campaign."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM campaign_recipients WHERE campaign_id=?",
            (campaign_id,),
        ).fetchall()
    return [_row_to_recipient(r) for r in rows]
