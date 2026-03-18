"""Tests for customer management."""

import pytest
from lyra.customers import (
    add_customer,
    delete_customer,
    get_customer,
    import_customers,
    list_customers,
    record_contact,
    update_customer,
)
from lyra.database import init_db
from lyra.models import Customer, CustomerStatus


@pytest.fixture
def db(tmp_path):
    """Provide a fresh temporary database path for each test."""
    path = tmp_path / "test.db"
    init_db(path)
    return path


def _make_customer(**kwargs) -> Customer:
    defaults = dict(
        name="John Doe",
        phone="555-0100",
        email="john@example.com",
        address="100 Elm St",
        city="Springfield",
        zip_code="12345",
        status=CustomerStatus.LEAD,
    )
    defaults.update(kwargs)
    return Customer(**defaults)


class TestAddCustomer:
    def test_returns_customer_with_id(self, db):
        c = add_customer(_make_customer(), db)
        assert c.id is not None
        assert c.id > 0

    def test_persists_all_fields(self, db):
        original = _make_customer(
            name="Alice Smith",
            phone="555-9999",
            email="alice@example.com",
            address="42 Oak Ave",
            city="Shelbyville",
            zip_code="99999",
            status=CustomerStatus.ACTIVE,
            notes="VIP customer",
            tags=["repeat", "residential"],
        )
        added = add_customer(original, db)
        fetched = get_customer(added.id, db)
        assert fetched.name == "Alice Smith"
        assert fetched.email == "alice@example.com"
        assert fetched.status == CustomerStatus.ACTIVE
        assert fetched.notes == "VIP customer"
        assert "repeat" in fetched.tags
        assert "residential" in fetched.tags


class TestGetCustomer:
    def test_returns_none_for_missing_id(self, db):
        assert get_customer(999, db) is None

    def test_returns_correct_customer(self, db):
        c = add_customer(_make_customer(name="Bob"), db)
        fetched = get_customer(c.id, db)
        assert fetched.name == "Bob"


class TestListCustomers:
    def test_returns_all_customers(self, db):
        add_customer(_make_customer(name="A"), db)
        add_customer(_make_customer(name="B"), db)
        assert len(list_customers(db_path=db)) == 2

    def test_filter_by_status(self, db):
        add_customer(_make_customer(name="Lead1", status=CustomerStatus.LEAD), db)
        add_customer(_make_customer(name="Active1", status=CustomerStatus.ACTIVE), db)
        leads = list_customers(status=CustomerStatus.LEAD, db_path=db)
        assert len(leads) == 1
        assert leads[0].name == "Lead1"

    def test_filter_by_zip(self, db):
        add_customer(_make_customer(name="Near", zip_code="10001"), db)
        add_customer(_make_customer(name="Far", zip_code="99999"), db)
        near = list_customers(zip_code="10001", db_path=db)
        assert len(near) == 1
        assert near[0].name == "Near"

    def test_filter_by_tag(self, db):
        add_customer(_make_customer(name="Tagged", tags=["vip"]), db)
        add_customer(_make_customer(name="Plain"), db)
        vips = list_customers(tag="vip", db_path=db)
        assert len(vips) == 1
        assert vips[0].name == "Tagged"


class TestUpdateCustomer:
    def test_updates_fields(self, db):
        c = add_customer(_make_customer(), db)
        c.name = "Updated Name"
        c.status = CustomerStatus.ACTIVE
        update_customer(c, db)
        fetched = get_customer(c.id, db)
        assert fetched.name == "Updated Name"
        assert fetched.status == CustomerStatus.ACTIVE

    def test_raises_without_id(self, db):
        c = _make_customer()
        with pytest.raises(ValueError, match="id"):
            update_customer(c, db)


class TestDeleteCustomer:
    def test_removes_customer(self, db):
        c = add_customer(_make_customer(), db)
        delete_customer(c.id, db)
        assert get_customer(c.id, db) is None


class TestRecordContact:
    def test_sets_last_contacted(self, db):
        c = add_customer(_make_customer(), db)
        assert get_customer(c.id, db).last_contacted is None
        record_contact(c.id, db)
        assert get_customer(c.id, db).last_contacted is not None


class TestImportCustomers:
    def test_bulk_insert(self, db):
        customers = [_make_customer(name=f"Customer {i}") for i in range(5)]
        count = import_customers(customers, db)
        assert count == 5
        assert len(list_customers(db_path=db)) == 5
