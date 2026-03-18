"""Data models for the Lyra marketing system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CustomerStatus(str, Enum):
    LEAD = "lead"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"


class CampaignType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"


@dataclass
class Customer:
    name: str
    phone: str
    email: str
    address: str
    city: str
    zip_code: str
    status: CustomerStatus = CustomerStatus.LEAD
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "zip_code": self.zip_code,
            "status": self.status.value if isinstance(self.status, CustomerStatus) else self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_contacted": self.last_contacted.isoformat() if self.last_contacted else None,
            "tags": ",".join(self.tags) if isinstance(self.tags, list) else self.tags,
        }


@dataclass
class Campaign:
    name: str
    subject: str
    body: str
    campaign_type: CampaignType = CampaignType.EMAIL
    status: CampaignStatus = CampaignStatus.DRAFT
    target_zip_codes: list = field(default_factory=list)
    target_statuses: list = field(default_factory=list)
    target_tags: list = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "campaign_type": self.campaign_type.value if isinstance(self.campaign_type, CampaignType) else self.campaign_type,
            "status": self.status.value if isinstance(self.status, CampaignStatus) else self.status,
            "target_zip_codes": ",".join(self.target_zip_codes) if isinstance(self.target_zip_codes, list) else self.target_zip_codes,
            "target_statuses": ",".join(self.target_statuses) if isinstance(self.target_statuses, list) else self.target_statuses,
            "target_tags": ",".join(self.target_tags) if isinstance(self.target_tags, list) else self.target_tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


@dataclass
class CampaignRecipient:
    campaign_id: int
    customer_id: int
    sent_at: Optional[datetime] = None
    opened: bool = False
    clicked: bool = False
    responded: bool = False
    unsubscribed: bool = False
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "customer_id": self.customer_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "opened": self.opened,
            "clicked": self.clicked,
            "responded": self.responded,
            "unsubscribed": self.unsubscribed,
        }


@dataclass
class CampaignStats:
    campaign_id: int
    campaign_name: str
    total_recipients: int = 0
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    responded: int = 0
    unsubscribed: int = 0

    @property
    def open_rate(self) -> float:
        return (self.opened / self.sent * 100) if self.sent > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return (self.clicked / self.sent * 100) if self.sent > 0 else 0.0

    @property
    def response_rate(self) -> float:
        return (self.responded / self.sent * 100) if self.sent > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "total_recipients": self.total_recipients,
            "sent": self.sent,
            "opened": self.opened,
            "clicked": self.clicked,
            "responded": self.responded,
            "unsubscribed": self.unsubscribed,
            "open_rate": round(self.open_rate, 2),
            "click_rate": round(self.click_rate, 2),
            "response_rate": round(self.response_rate, 2),
        }
