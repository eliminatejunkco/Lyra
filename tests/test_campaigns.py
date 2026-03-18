"""Tests for campaign management."""

import pytest
from lyra.campaigns import (
    create_campaign,
    delete_campaign,
    get_campaign,
    get_recipients,
    list_campaigns,
    record_click,
    record_open,
    record_response,
    record_unsubscribe,
    resolve_recipients,
    send_campaign,
    update_campaign,
)
from lyra.customers import add_customer
from lyra.database import init_db
from lyra.models import Campaign, CampaignStatus, CampaignType, Customer, CustomerStatus


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


def _make_campaign(**kwargs) -> Campaign:
    defaults = dict(
        name="Test Campaign",
        subject="Hello!",
        body="Body text",
        campaign_type=CampaignType.EMAIL,
    )
    defaults.update(kwargs)
    return Campaign(**defaults)


def _make_customer(**kwargs) -> Customer:
    defaults = dict(
        name="Jane Smith",
        phone="555-0200",
        email="jane@example.com",
        address="200 Oak St",
        city="Springfield",
        zip_code="12345",
        status=CustomerStatus.LEAD,
    )
    defaults.update(kwargs)
    return Customer(**defaults)


class TestCreateCampaign:
    def test_returns_campaign_with_id(self, db):
        c = create_campaign(_make_campaign(), db)
        assert c.id is not None

    def test_persists_fields(self, db):
        c = create_campaign(
            _make_campaign(name="Spring Sale", subject="Big Sale!", body="Come buy!"), db
        )
        fetched = get_campaign(c.id, db)
        assert fetched.name == "Spring Sale"
        assert fetched.subject == "Big Sale!"


class TestGetCampaign:
    def test_returns_none_for_missing_id(self, db):
        assert get_campaign(999, db) is None


class TestListCampaigns:
    def test_returns_all(self, db):
        create_campaign(_make_campaign(name="A"), db)
        create_campaign(_make_campaign(name="B"), db)
        assert len(list_campaigns(db_path=db)) == 2

    def test_filter_by_status(self, db):
        c = create_campaign(_make_campaign(name="Draft"), db)
        add_customer(_make_customer(), db)
        send_campaign(c.id, db)
        drafts = list_campaigns(status=CampaignStatus.DRAFT, db_path=db)
        sent = list_campaigns(status=CampaignStatus.SENT, db_path=db)
        assert len(drafts) == 0
        assert len(sent) == 1


class TestUpdateCampaign:
    def test_updates_name(self, db):
        c = create_campaign(_make_campaign(), db)
        c.name = "Updated"
        update_campaign(c, db)
        assert get_campaign(c.id, db).name == "Updated"

    def test_raises_without_id(self, db):
        c = _make_campaign()
        with pytest.raises(ValueError, match="id"):
            update_campaign(c, db)


class TestDeleteCampaign:
    def test_removes_campaign(self, db):
        c = create_campaign(_make_campaign(), db)
        delete_campaign(c.id, db)
        assert get_campaign(c.id, db) is None


class TestResolveRecipients:
    def test_returns_all_when_no_filters(self, db):
        add_customer(_make_customer(name="A"), db)
        add_customer(_make_customer(name="B"), db)
        campaign = create_campaign(_make_campaign(), db)
        recipients = resolve_recipients(campaign, db)
        assert len(recipients) == 2

    def test_filters_by_zip(self, db):
        add_customer(_make_customer(name="Near", zip_code="10001"), db)
        add_customer(_make_customer(name="Far", zip_code="99999"), db)
        campaign = create_campaign(
            _make_campaign(target_zip_codes=["10001"]), db
        )
        recipients = resolve_recipients(campaign, db)
        assert len(recipients) == 1
        assert recipients[0].name == "Near"

    def test_filters_by_status(self, db):
        add_customer(_make_customer(name="Lead1", status=CustomerStatus.LEAD), db)
        add_customer(_make_customer(name="Active1", status=CustomerStatus.ACTIVE), db)
        campaign = create_campaign(
            _make_campaign(target_statuses=["lead"]), db
        )
        recipients = resolve_recipients(campaign, db)
        assert len(recipients) == 1
        assert recipients[0].name == "Lead1"

    def test_filters_by_tag(self, db):
        add_customer(_make_customer(name="VIP", tags=["vip"]), db)
        add_customer(_make_customer(name="Plain"), db)
        campaign = create_campaign(
            _make_campaign(target_tags=["vip"]), db
        )
        recipients = resolve_recipients(campaign, db)
        assert len(recipients) == 1


class TestSendCampaign:
    def test_marks_campaign_as_sent(self, db):
        add_customer(_make_customer(), db)
        c = create_campaign(_make_campaign(), db)
        send_campaign(c.id, db)
        assert get_campaign(c.id, db).status == CampaignStatus.SENT

    def test_creates_recipient_records(self, db):
        add_customer(_make_customer(name="R1"), db)
        add_customer(_make_customer(name="R2"), db)
        c = create_campaign(_make_campaign(), db)
        count = send_campaign(c.id, db)
        assert count == 2
        assert len(get_recipients(c.id, db)) == 2

    def test_cannot_resend(self, db):
        add_customer(_make_customer(), db)
        c = create_campaign(_make_campaign(), db)
        send_campaign(c.id, db)
        with pytest.raises(ValueError, match="already been sent"):
            send_campaign(c.id, db)

    def test_raises_for_missing_campaign(self, db):
        with pytest.raises(ValueError, match="not found"):
            send_campaign(999, db)


class TestEngagementTracking:
    def _setup(self, db):
        cust = add_customer(_make_customer(), db)
        camp = create_campaign(_make_campaign(), db)
        send_campaign(camp.id, db)
        return camp, cust

    def test_record_open(self, db):
        camp, cust = self._setup(db)
        record_open(camp.id, cust.id, db)
        recipients = get_recipients(camp.id, db)
        assert recipients[0].opened is True

    def test_record_click(self, db):
        camp, cust = self._setup(db)
        record_click(camp.id, cust.id, db)
        assert get_recipients(camp.id, db)[0].clicked is True

    def test_record_response(self, db):
        camp, cust = self._setup(db)
        record_response(camp.id, cust.id, db)
        assert get_recipients(camp.id, db)[0].responded is True

    def test_record_unsubscribe(self, db):
        camp, cust = self._setup(db)
        record_unsubscribe(camp.id, cust.id, db)
        assert get_recipients(camp.id, db)[0].unsubscribed is True
