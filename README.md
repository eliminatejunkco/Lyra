# Lyra – Job Manager

**Lyra** is a simple Job & Lead Management CRM for **Eliminate Junk Co**. It helps you track every job from first call to final payment so nothing falls through the cracks.

![Lyra Dashboard](https://github.com/user-attachments/assets/3446491b-b0b5-49aa-9f1d-5902857892cc)

## Features

- **Pipeline tracking** — move jobs through Lead → Quoted → Scheduled → In Progress → Completed
- **Dashboard stats** — see at a glance how many leads, quotes, and scheduled jobs you have, plus total revenue
- **Search & filter** — find any job instantly by customer name, phone, address, or description
- **Add / Edit / Delete jobs** — full CRUD with a clean modal form
- **Persistent storage** — all data saved locally in a SQLite database file (`lyra.db`)

## Quick Start

**Requirements:** Node.js 18+

```bash
# Install dependencies
npm install

# Start the server (defaults to port 3000)
npm start
```

Then open **http://localhost:3000** in your browser.

To use a different port:
```bash
PORT=8080 npm start
```

## Running Tests

```bash
npm test
```

## Job Statuses

| Status | Meaning |
|---|---|
| Lead | New inquiry, not yet quoted |
| Quoted | Price sent to customer |
| Scheduled | Job booked on the calendar |
| In Progress | Crew is on-site |
| Completed | Job done and paid |
| Cancelled | Job did not go forward |
