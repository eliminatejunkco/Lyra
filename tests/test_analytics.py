"""Tests for analytics and reporting."""

import pytest
from lyra.analytics import (
    all_campaign_stats,
    campaign_performance_report,
    campaign_stats,
    customer_summary,
    monthly_contacts_report,
    top_zip_codes,
)
from lyra.campaigns import create_campaign, send_campaign
from lyra.campaigns import record_open, record_response
from lyra.customers import add_customer, record_contact
from lyra.database import init_db
from lyra.models import Campaign, CampaignType, Customer, CustomerStatus


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


def _customer(name, zip_code="12345", status=CustomerStatus.LEAD, **kw) -> Customer:
    return Customer(
        name=name,
        phone="555-0000",
        email=f"{name.lower().replace(' ', '')}@example.com",
        address="1 Main St",
        city="Springfield",
        zip_code=zip_code,
        status=status,
        **kw,
    )


def _campaign(name="Test") -> Campaign:
    return Campaign(name=name, subject="Hi", body="Body")


class TestCampaignStats:
    def test_raises_for_missing_campaign(self, db):
        with pytest.raises(ValueError, match="not found"):
            campaign_stats(999, db)

    def test_counts_sent_and_engaged(self, db):
        cust1 = add_customer(_customer("C1"), db)
        cust2 = add_customer(_customer("C2"), db)
        camp = create_campaign(_campaign(), db)
        send_campaign(camp.id, db)
        record_open(camp.id, cust1.id, db)
        record_response(camp.id, cust2.id, db)

        stats = campaign_stats(camp.id, db)
        assert stats.sent == 2
        assert stats.opened == 1
        assert stats.responded == 1

    def test_rates_are_correct(self, db):
        cust = add_customer(_customer("C1"), db)
        camp = create_campaign(_campaign(), db)
        send_campaign(camp.id, db)
        record_open(camp.id, cust.id, db)

        stats = campaign_stats(camp.id, db)
        assert stats.open_rate == 100.0
        assert stats.response_rate == 0.0

    def test_rates_zero_when_no_sends(self, db):
        create_campaign(_campaign("Empty"), db)
        # Campaign with no recipients has 0 sent
        camps = create_campaign(_campaign("NoneYet"), db)
        stats = campaign_stats(camps.id, db)
        assert stats.open_rate == 0.0


class TestAllCampaignStats:
    def test_returns_one_entry_per_campaign(self, db):
        create_campaign(_campaign("A"), db)
        create_campaign(_campaign("B"), db)
        result = all_campaign_stats(db)
        assert len(result) == 2


class TestCustomerSummary:
    def test_counts_by_status(self, db):
        add_customer(_customer("L1", status=CustomerStatus.LEAD), db)
        add_customer(_customer("L2", status=CustomerStatus.LEAD), db)
        add_customer(_customer("A1", status=CustomerStatus.ACTIVE), db)
        summary = customer_summary(db)
        assert summary["total"] == 3
        assert summary["lead"] == 2
        assert summary["active"] == 1
        assert summary["inactive"] == 0

    def test_empty_db(self, db):
        summary = customer_summary(db)
        assert summary["total"] == 0


class TestTopZipCodes:
    def test_orders_by_count_descending(self, db):
        for i in range(3):
            add_customer(_customer(f"Z1C{i}", zip_code="11111"), db)
        add_customer(_customer("Z2C1", zip_code="22222"), db)
        result = top_zip_codes(db_path=db)
        assert result[0]["zip_code"] == "11111"
        assert result[0]["count"] == 3

    def test_respects_limit(self, db):
        for i in range(5):
            add_customer(_customer(f"C{i}", zip_code=str(10000 + i)), db)
        result = top_zip_codes(limit=3, db_path=db)
        assert len(result) == 3


class TestCampaignPerformanceReport:
    def test_sorted_by_response_rate(self, db):
        cust1 = add_customer(_customer("C1"), db)
        cust2 = add_customer(_customer("C2"), db)

        camp_a = create_campaign(_campaign("LowResp"), db)
        send_campaign(camp_a.id, db)

        camp_b = create_campaign(_campaign("HighResp"), db)
        send_campaign(camp_b.id, db)
        record_response(camp_b.id, cust1.id, db)
        record_response(camp_b.id, cust2.id, db)

        report = campaign_performance_report(db)
        assert report[0]["campaign_name"] == "HighResp"


class TestMonthlyContactsReport:
    def test_empty_when_no_contacts(self, db):
        add_customer(_customer("NoContact"), db)
        result = monthly_contacts_report(db)
        assert result == []

    def test_counts_after_record_contact(self, db):
        cust = add_customer(_customer("Contacted"), db)
        record_contact(cust.id, db)
        result = monthly_contacts_report(db)
        assert len(result) == 1
        assert result[0]["contacts"] == 1
