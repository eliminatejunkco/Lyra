'use strict';

// Integration tests for the Lyra API using Node's built-in test runner.
// Uses a temporary in-memory database so tests don't touch the real data file.

const { test, before, after, describe } = require('node:test');
const assert = require('node:assert/strict');
const http   = require('node:http');
const path   = require('node:path');

// Point the server at an in-memory database before requiring it
process.env.DB_PATH = ':memory:';
const app = require('../server');

let server;
let baseUrl;

before(() => new Promise(resolve => {
  server = app.listen(0, '127.0.0.1', () => {
    const { port } = server.address();
    baseUrl = `http://127.0.0.1:${port}`;
    resolve();
  });
}));

after(() => new Promise(resolve => server.close(resolve)));

// ── Helper ────────────────────────────────────────────────────────────────────

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {})
      }
    };
    const req = http.request(baseUrl + path, options, res => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('GET /api/stats', () => {
  test('returns zeroed stats on empty database', async () => {
    const { status, body } = await request('GET', '/api/stats');
    assert.equal(status, 200);
    assert.equal(body.total, 0);
    assert.equal(body.Lead, 0);
    assert.equal(body.Completed, 0);
    assert.equal(body.revenue, 0);
  });
});

describe('POST /api/jobs', () => {
  test('creates a job with minimum required fields', async () => {
    const { status, body } = await request('POST', '/api/jobs', { customer: 'Alice Smith' });
    assert.equal(status, 201);
    assert.equal(body.customer, 'Alice Smith');
    assert.equal(body.status, 'Lead');
    assert.ok(body.id);
  });

  test('rejects a job with missing customer', async () => {
    const { status, body } = await request('POST', '/api/jobs', { phone: '555-1234' });
    assert.equal(status, 400);
    assert.ok(Array.isArray(body.errors));
    assert.ok(body.errors.some(e => /customer/i.test(e)));
  });

  test('rejects invalid status value', async () => {
    const { status, body } = await request('POST', '/api/jobs', { customer: 'Bob', status: 'Unknown' });
    assert.equal(status, 400);
    assert.ok(body.errors.some(e => /status/i.test(e)));
  });

  test('stores all optional fields', async () => {
    const payload = {
      customer: 'Carol', phone: '626-555-0100', email: 'carol@test.com',
      address: '123 Main St', description: 'Garage cleanout',
      status: 'Quoted', estimate: 350, actual: '', job_date: '2026-04-01', notes: 'Big haul'
    };
    const { status, body } = await request('POST', '/api/jobs', payload);
    assert.equal(status, 201);
    assert.equal(body.phone, '626-555-0100');
    assert.equal(body.estimate, 350);
    assert.equal(body.actual, null);
    assert.equal(body.job_date, '2026-04-01');
  });
});

describe('GET /api/jobs', () => {
  test('returns a list of jobs', async () => {
    const { status, body } = await request('GET', '/api/jobs');
    assert.equal(status, 200);
    assert.ok(Array.isArray(body));
  });

  test('filters by status', async () => {
    await request('POST', '/api/jobs', { customer: 'Dave', status: 'Completed', actual: 200 });
    const { body } = await request('GET', '/api/jobs?status=Completed');
    assert.ok(body.every(j => j.status === 'Completed'));
    assert.ok(body.length >= 1);
  });

  test('searches by customer name', async () => {
    await request('POST', '/api/jobs', { customer: 'UniqueNameXYZ' });
    const { body } = await request('GET', '/api/jobs?q=UniqueNameXYZ');
    assert.ok(body.length >= 1);
    assert.ok(body.some(j => j.customer === 'UniqueNameXYZ'));
  });
});

describe('GET /api/jobs/:id', () => {
  test('returns a single job', async () => {
    const { body: created } = await request('POST', '/api/jobs', { customer: 'Eve' });
    const { status, body } = await request('GET', '/api/jobs/' + created.id);
    assert.equal(status, 200);
    assert.equal(body.id, created.id);
  });

  test('returns 404 for unknown id', async () => {
    const { status } = await request('GET', '/api/jobs/99999');
    assert.equal(status, 404);
  });
});

describe('PUT /api/jobs/:id', () => {
  test('updates job fields', async () => {
    const { body: created } = await request('POST', '/api/jobs', { customer: 'Frank' });
    const { status, body } = await request('PUT', '/api/jobs/' + created.id, {
      customer: 'Frank Updated', status: 'Scheduled'
    });
    assert.equal(status, 200);
    assert.equal(body.customer, 'Frank Updated');
    assert.equal(body.status, 'Scheduled');
  });

  test('returns 404 for unknown id', async () => {
    const { status } = await request('PUT', '/api/jobs/99999', { customer: 'X' });
    assert.equal(status, 404);
  });
});

describe('DELETE /api/jobs/:id', () => {
  test('deletes a job', async () => {
    const { body: created } = await request('POST', '/api/jobs', { customer: 'Grace' });
    const { status, body } = await request('DELETE', '/api/jobs/' + created.id);
    assert.equal(status, 200);
    assert.equal(body.deleted, true);

    const { status: s2 } = await request('GET', '/api/jobs/' + created.id);
    assert.equal(s2, 404);
  });

  test('returns 404 for unknown id', async () => {
    const { status } = await request('DELETE', '/api/jobs/99999');
    assert.equal(status, 404);
  });
});

describe('GET /api/stats (after inserts)', () => {
  test('revenue only counts Completed jobs', async () => {
    // Create a completed job with actual value
    await request('POST', '/api/jobs', { customer: 'Henry', status: 'Completed', actual: 500 });
    const { body } = await request('GET', '/api/stats');
    assert.ok(body.revenue >= 500);
    assert.ok(body.Completed >= 1);
  });
});
