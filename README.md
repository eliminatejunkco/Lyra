# Lyra – Marketing System for Junk Removal Businesses

Lyra is a lightweight, command-line marketing system that helps junk removal
businesses manage customers, run email and SMS campaigns, and track engagement
analytics — all backed by a local SQLite database.

---

## Features

| Feature | Description |
|---------|-------------|
| **Customer management** | Add, update, tag, and segment customers by status, zip code, or custom tags |
| **Campaigns** | Create email and SMS campaigns with flexible audience targeting |
| **Templates** | Six ready-to-use message templates (seasonal cleanout, win-back, referral, SMS promos, …) |
| **Engagement tracking** | Record opens, clicks, responses, and unsubscribes per campaign |
| **Analytics** | Customer summary, campaign performance report, top zip codes, monthly contact history |

---

## Quick Start

### Option A – Web UI (recommended)

The easiest way to use Lyra is through the built-in browser interface.

```bash
pip install -e .
python app.py
```

Then open **http://localhost:5000** in your browser. You'll see a dashboard
with customer stats, campaign performance, and top service areas. From there
you can add customers, create campaigns from ready-made templates, send
campaigns, and view analytics — all without touching the command line.

The database is created automatically at `~/.lyra/marketing.db` on first run.
To use a different file, set the `LYRA_DB` environment variable:

```bash
LYRA_DB=/path/to/my.db python app.py
```

---

### Option B – Command-Line Interface

### 1 – Install

```bash
pip install -e .
```

### 2 – Initialize the database

```bash
lyra init
```

The database is stored at `~/.lyra/marketing.db` by default. Override with
`--db /path/to/custom.db` on any command.

### 3 – Add customers

```bash
lyra customer add \
  --name "Jane Doe" \
  --phone "555-1234" \
  --email "jane@example.com" \
  --address "123 Main St" \
  --city "Springfield" \
  --zip "12345" \
  --status lead \
  --tags "residential,repeat"
```

### 4 – List available message templates

```bash
lyra template list
lyra template show seasonal_cleanout
```

### 5 – Create a campaign

```bash
lyra campaign create \
  --name "Spring Cleanout 2025" \
  --template seasonal_cleanout \
  --type email \
  --zip "12345,12346" \
  --status "lead,active"
```

### 6 – Preview recipients (dry run)

```bash
lyra campaign send 1 --dry-run
```

### 7 – Send the campaign

```bash
lyra campaign send 1
```

### 8 – View analytics

```bash
lyra analytics summary          # Customer breakdown by status
lyra analytics campaigns        # Campaign performance (open/response rates)
lyra analytics zip-codes        # Top zip codes by customer count
lyra analytics monthly          # Monthly contact history
```

---

## Project Layout

```
app.py                 Flask web application (run this to open the browser UI)

lyra/
├── __init__.py        Package entry point
├── models.py          Data models (Customer, Campaign, CampaignRecipient, …)
├── database.py        SQLite schema and connection helpers
├── customers.py       Customer CRUD and filtering
├── campaigns.py       Campaign CRUD, recipient resolution, and engagement tracking
├── analytics.py       Reporting and statistics
├── templates.py       Pre-built email/SMS templates
└── cli.py             Command-line interface

templates/             Jinja2 HTML templates for the web UI
static/                Bootstrap CSS/JS served locally (no internet required)

tests/
├── test_customers.py
├── test_campaigns.py
├── test_analytics.py
└── test_templates.py
```

---

## Running Tests

```bash
pip install pytest
pytest
```

---

## Customer Statuses

| Status | Meaning |
|--------|---------|
| `lead` | Prospect who has not yet booked |
| `active` | Current paying customer |
| `inactive` | Past customer who hasn't booked recently |
| `churned` | Lost customer |

---

## Available Templates

| Name | Type | Description |
|------|------|-------------|
| `seasonal_cleanout` | email | Spring cleaning promotion |
| `win_back` | email | Re-engagement offer with discount code |
| `referral_ask` | email | Ask happy customers for referrals |
| `new_lead_welcome` | email | Welcome message for new leads |
| `sms_promo` | sms | Short promotional SMS with discount |
| `sms_follow_up` | sms | Follow-up SMS for outstanding leads |
