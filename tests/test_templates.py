"""Tests for message templates."""

import pytest
from lyra.templates import get_template, list_templates, render_template, TEMPLATES


class TestListTemplates:
    def test_returns_all(self):
        result = list_templates()
        assert len(result) == len(TEMPLATES)

    def test_filters_by_email(self):
        emails = list_templates("email")
        assert all(t["type"] == "email" for t in emails)
        assert len(emails) > 0

    def test_filters_by_sms(self):
        sms = list_templates("sms")
        assert all(t["type"] == "sms" for t in sms)
        assert len(sms) > 0


class TestGetTemplate:
    def test_returns_template_by_name(self):
        t = get_template("seasonal_cleanout")
        assert t is not None
        assert t["name"] == "seasonal_cleanout"

    def test_returns_none_for_unknown_name(self):
        assert get_template("nonexistent") is None


class TestRenderTemplate:
    def test_fills_placeholders(self):
        rendered = render_template(
            "seasonal_cleanout",
            {"name": "Alice", "address": "", "city": "", "zip_code": "", "phone": "", "email": ""},
        )
        assert "Alice" in rendered["body"]

    def test_raises_for_unknown_template(self):
        with pytest.raises(ValueError, match="not found"):
            render_template("no_such_template", {"name": "Bob"})
