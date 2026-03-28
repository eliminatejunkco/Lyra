'use strict';

const express   = require('express');
const rateLimit = require('express-rate-limit');
const Database  = require('better-sqlite3');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// ── Database setup ────────────────────────────────────────────────────────────

const db = new Database(process.env.DB_PATH || 'lyra.db');

db.exec(`
  CREATE TABLE IF NOT EXISTS jobs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer     TEXT    NOT NULL,
    phone        TEXT,
    email        TEXT,
    address      TEXT,
    description  TEXT,
    status       TEXT    NOT NULL DEFAULT 'Lead',
    estimate     REAL,
    actual       REAL,
    job_date     TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    notes        TEXT,
    before_photo TEXT,
    after_photo  TEXT
  );
`);

// Migrate: add photo columns to existing databases
const existingCols = db.prepare('PRAGMA table_info(jobs)').all().map(c => c.name);
if (!existingCols.includes('before_photo')) db.exec('ALTER TABLE jobs ADD COLUMN before_photo TEXT');
if (!existingCols.includes('after_photo'))  db.exec('ALTER TABLE jobs ADD COLUMN after_photo TEXT');

// ── Middleware ────────────────────────────────────────────────────────────────

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Rate limit all /api/* routes: max 120 requests per minute per IP
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 120,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', apiLimiter);

// ── Helpers ───────────────────────────────────────────────────────────────────

const VALID_STATUSES = ['Lead', 'Quoted', 'Scheduled', 'In Progress', 'Completed', 'Cancelled'];

function validateJob(body) {
  const errors = [];
  if (!body.customer || !body.customer.trim()) errors.push('customer is required');
  if (body.status && !VALID_STATUSES.includes(body.status)) {
    errors.push(`status must be one of: ${VALID_STATUSES.join(', ')}`);
  }
  if (body.estimate !== undefined && body.estimate !== null && body.estimate !== '' && isNaN(Number(body.estimate))) {
    errors.push('estimate must be a number');
  }
  if (body.actual !== undefined && body.actual !== null && body.actual !== '' && isNaN(Number(body.actual))) {
    errors.push('actual must be a number');
  }
  return errors;
}

// ── API ───────────────────────────────────────────────────────────────────────

// GET /api/stats  – dashboard counts
app.get('/api/stats', (req, res) => {
  const rows = db.prepare(`
    SELECT status, COUNT(*) AS count FROM jobs GROUP BY status
  `).all();

  const stats = { total: 0 };
  VALID_STATUSES.forEach(s => { stats[s] = 0; });
  rows.forEach(r => {
    stats[r.status] = r.count;
    stats.total += r.count;
  });

  const revenue = db.prepare(`
    SELECT COALESCE(SUM(actual), 0) AS total FROM jobs WHERE status = 'Completed'
  `).get();
  stats.revenue = revenue.total;

  res.json(stats);
});

// GET /api/jobs  – list all jobs (optional ?status= filter)
app.get('/api/jobs', (req, res) => {
  const { status, q } = req.query;
  let sql = 'SELECT * FROM jobs WHERE 1=1';
  const params = [];

  if (status) {
    sql += ' AND status = ?';
    params.push(status);
  }
  if (q) {
    sql += ' AND (customer LIKE ? OR address LIKE ? OR phone LIKE ? OR description LIKE ?)';
    const like = `%${q}%`;
    params.push(like, like, like, like);
  }

  sql += ' ORDER BY created_at DESC';
  res.json(db.prepare(sql).all(...params));
});

// POST /api/jobs  – create a job
app.post('/api/jobs', (req, res) => {
  const errors = validateJob(req.body);
  if (errors.length) return res.status(400).json({ errors });

  const { customer, phone, email, address, description, status, estimate, actual, job_date, notes, before_photo, after_photo } = req.body;
  const result = db.prepare(`
    INSERT INTO jobs (customer, phone, email, address, description, status, estimate, actual, job_date, notes, before_photo, after_photo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    customer.trim(),
    phone || null,
    email || null,
    address || null,
    description || null,
    status || 'Lead',
    estimate !== '' && estimate != null ? Number(estimate) : null,
    actual !== '' && actual != null ? Number(actual) : null,
    job_date || null,
    notes || null,
    before_photo || null,
    after_photo || null
  );

  res.status(201).json(db.prepare('SELECT * FROM jobs WHERE id = ?').get(result.lastInsertRowid));
});

// GET /api/jobs/:id
app.get('/api/jobs/:id', (req, res) => {
  const job = db.prepare('SELECT * FROM jobs WHERE id = ?').get(req.params.id);
  if (!job) return res.status(404).json({ error: 'Not found' });
  res.json(job);
});

// PUT /api/jobs/:id  – update a job
app.put('/api/jobs/:id', (req, res) => {
  const job = db.prepare('SELECT * FROM jobs WHERE id = ?').get(req.params.id);
  if (!job) return res.status(404).json({ error: 'Not found' });

  const merged = { ...job, ...req.body };
  const errors = validateJob(merged);
  if (errors.length) return res.status(400).json({ errors });

  const { customer, phone, email, address, description, status, estimate, actual, job_date, notes, before_photo, after_photo } = merged;
  db.prepare(`
    UPDATE jobs SET
      customer = ?, phone = ?, email = ?, address = ?, description = ?,
      status = ?, estimate = ?, actual = ?, job_date = ?, notes = ?,
      before_photo = ?, after_photo = ?,
      updated_at = datetime('now')
    WHERE id = ?
  `).run(
    customer.trim(),
    phone || null,
    email || null,
    address || null,
    description || null,
    status || 'Lead',
    estimate !== '' && estimate != null ? Number(estimate) : null,
    actual !== '' && actual != null ? Number(actual) : null,
    job_date || null,
    notes || null,
    before_photo || null,
    after_photo || null,
    req.params.id
  );

  res.json(db.prepare('SELECT * FROM jobs WHERE id = ?').get(req.params.id));
});

// DELETE /api/jobs/:id
app.delete('/api/jobs/:id', (req, res) => {
  const job = db.prepare('SELECT * FROM jobs WHERE id = ?').get(req.params.id);
  if (!job) return res.status(404).json({ error: 'Not found' });
  db.prepare('DELETE FROM jobs WHERE id = ?').run(req.params.id);
  res.json({ deleted: true });
});

// ── Start ─────────────────────────────────────────────────────────────────────

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Lyra running on http://localhost:${PORT}`);
  });
}

module.exports = app; // exported for testing
