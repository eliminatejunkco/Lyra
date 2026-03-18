"""Customer management for the Lyra marketing system."""

from datetime import datetime, timezone
from typing import Optional

from .database import get_connection, init_db
from .models import Customer, CustomerStatus


def _row_to_customer(row) -> Customer:
    """Convert a sqlite3.Row to a Customer dataclass."""
    tags = [t for t in (row["tags"] or "").split(",") if t]
    return Customer(
        id=row["id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        address=row["address"],
        city=row["city"],
        zip_code=row["zip_code"],
        status=CustomerStatus(row["status"]),
        notes=row["notes"] or "",
        tags=tags,
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        last_contacted=datetime.fromisoformat(row["last_contacted"]) if row["last_contacted"] else None,
    )


def add_customer(customer: Customer, db_path=None) -> Customer:
    """Insert a new customer and return it with its assigned id."""
    init_db(db_path)
    data = customer.to_dict()
    data.pop("id", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO customers (name, phone, email, address, city, zip_code,
                                   status, notes, tags, last_contacted)
            VALUES (:name, :phone, :email, :address, :city, :zip_code,
                    :status, :notes, :tags, :last_contacted)
            """,
            data,
        )
        customer.id = cursor.lastrowid
    return customer


def get_customer(customer_id: int, db_path=None) -> Optional[Customer]:
    """Fetch a single customer by id, or None if not found."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
    return _row_to_customer(row) if row else None


def list_customers(
    status: Optional[CustomerStatus] = None,
    zip_code: Optional[str] = None,
    tag: Optional[str] = None,
    db_path=None,
) -> list[Customer]:
    """Return customers, optionally filtered by status, zip code, or tag."""
    query = "SELECT * FROM customers WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status.value if isinstance(status, CustomerStatus) else status)
    if zip_code:
        query += " AND zip_code = ?"
        params.append(zip_code)
    if tag:
        query += " AND (',' || tags || ',') LIKE ?"
        params.append(f"%,{tag},%")
    query += " ORDER BY name"
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_customer(r) for r in rows]


def update_customer(customer: Customer, db_path=None) -> Customer:
    """Update an existing customer record."""
    if customer.id is None:
        raise ValueError("Customer must have an id to be updated.")
    data = customer.to_dict()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE customers
            SET name=:name, phone=:phone, email=:email, address=:address,
                city=:city, zip_code=:zip_code, status=:status, notes=:notes,
                tags=:tags, last_contacted=:last_contacted, updated_at=:updated_at
            WHERE id=:id
            """,
            data,
        )
    return customer


def delete_customer(customer_id: int, db_path=None) -> None:
    """Delete a customer by id."""
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


def record_contact(customer_id: int, db_path=None) -> None:
    """Update last_contacted timestamp for a customer."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE customers SET last_contacted=?, updated_at=? WHERE id=?",
            (now, now, customer_id),
        )


def import_customers(customers: list[Customer], db_path=None) -> int:
    """Bulk-import customers; returns count of rows inserted."""
    init_db(db_path)
    inserted = 0
    for customer in customers:
        add_customer(customer, db_path)
        inserted += 1
    return inserted
