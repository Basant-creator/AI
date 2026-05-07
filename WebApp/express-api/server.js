require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;
const FLASK_BASE_URL = process.env.FLASK_BASE_URL || 'https://bob-ai-xv2g.onrender.com';

// ─── Middleware ──────────────────────────────────────────────────────────────
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept']
}));
app.options('*', cors());
app.use(express.json());

// Request logger (lightweight, no external package needed)
app.use((req, _res, next) => {
  console.log(`→ ${req.method} ${req.path}`);
  next();
});

// ─── Routes ──────────────────────────────────────────────────────────────────

/**
 * GET /health
 * Forwards to Flask GET /health
 * Returns Flask's own health payload so operators have a single status call.
 */
app.use(express.static(path.join(__dirname, "..")));

app.get('/homepage', async (req, res) => {
  res.sendFile(path.join(__dirname, '../index.html'));
});
app.get('/homepage/dashboard', async (req, res) => {
  res.sendFile(path.join(__dirname, '../DashBoard/dashboard.html'));
});
app.get('/health', async (_req, res) => {
  // Liveness endpoint for Render: only reports gateway process status.
  // Do not depend on upstream Flask availability here.
  res.status(200).json({
    gateway: 'ok',
    service: 'ai-express-gateway',
    timestamp: new Date().toISOString(),
  });
});

app.get('/health/upstream', async (_req, res) => {
  try {
    const flaskRes = await axios.get(`${FLASK_BASE_URL}/health`);
    res.status(flaskRes.status).json({
      gateway: 'ok',
      flask: flaskRes.data,
    });
  } catch (err) {
    forwardError(err, res, 'health');
  }
});

/**
 * POST /generate-site
 * Forwards to Flask POST /generate-website
 *
 * Expected body:
 *   { "description": "...", "type": "vanilla" }
 *
 * Flask returns the generated HTML/CSS/JS files.
 */
app.post('/generate-site', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/generate-website`, req.body, {
      timeout: 120_000, // AI generation can take up to ~2 min
      headers: {
        Authorization: req.headers.authorization || '',
      },
    });
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'generate-site');
  }
});

/**
 * POST /generate-and-deploy
 * Forwards to Flask POST /generate-and-push-to-github
 *
 * Expected body:
 *   {
 *     "description": "...",
 *     "type": "vanilla" | "react",
 *     "website_type": "landing_page" | "multi_page" | "portfolio" | "blog" | "web_application" | "ecommerce" | "",  // optional, auto-detects if empty
 *     "github_token": "ghp_...",   // required unless user has saved encrypted token
 *     "make_private": false,
 *     ... other fields (colors, social, contact)
 *   }
 *
 * Flask generates the site AND creates/pushes a GitHub repo.
 * If website_type is provided, uses that template; otherwise auto-detects from description.
 * Returns { success, repo_url, files } (or Flask's native shape).
 */
app.post('/generate-and-deploy', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/generate-and-push-to-github`, req.body, {
      timeout: 180_000,
      headers: {
        Authorization: req.headers.authorization || '',
      },
    }, // generation + GitHub push — allow 3 min
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'generate-and-deploy');
  }
});

app.get('/job/:jobId', async (req, res) => {
  try {
    const flaskRes = await axios.get(`${FLASK_BASE_URL}/job/${req.params.jobId}`, {
      timeout: 10_000
    });
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'job-status');
  }
});

/**
 * Auth routes proxy to Flask auth service.
 */
app.post('/auth/signup', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/auth/signup`, req.body, { timeout: 60_000 },
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-signup');
  }
});

app.post('/auth/login', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/auth/login`, req.body, { timeout: 60_000 },
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-login');
  }
});

app.post('/auth/signin', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/auth/signin`, req.body, { timeout: 60_000 },
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-signin');
  }
});

app.post('/contact', async (req, res) => {
  try {
    const flaskRes = await axios.post(`${FLASK_BASE_URL}/contact`, req.body, { timeout: 15_000 },
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'contact');
  }
});

app.get('/auth/me', async (req, res) => {
  try {
    const flaskRes = await axios.get(`${FLASK_BASE_URL}/auth/me`, {
      timeout: 60_000,
      headers: {
        Authorization: req.headers.authorization || '',
      },
    });
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-me');
  }
});

app.get('/auth/profile', async (req, res) => {
  try {
    const flaskRes = await axios.get(`${FLASK_BASE_URL}/auth/profile`, {
      timeout: 10_000,
      headers: {
        Authorization: req.headers.authorization || '',
      },
    });
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-profile');
  }
});

app.put('/auth/github-token', async (req, res) => {
  try {
    const flaskRes = await axios.put(`${FLASK_BASE_URL}/auth/github-token`, req.body, {
      timeout: 10_000,
      headers: {
        Authorization: req.headers.authorization || '',
      },
    });
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'auth-github-token');
  }
});

// ─── 404 catch-all ────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found on Express gateway' });
});

// ─── Error helper ─────────────────────────────────────────────────────────────
/**
 * Translates axios errors into meaningful HTTP responses.
 *
 * axios wraps three error shapes:
 *   err.response   — Flask returned a non-2xx status (4xx / 5xx)
 *   err.request    — Request was sent but no response received (Flask down / timeout)
 *   (neither)      — Something went wrong setting up the request
 */
function forwardError(err, res, route) {
  if (err.response) {
    // Flask replied with an error — forward it as-is so the frontend sees it
    console.error(`[${route}] Flask error ${err.response.status}:`, err.response.data);
    return res.status(err.response.status).json(err.response.data);
  }

  if (err.code === 'ECONNREFUSED') {
    console.error(`[${route}] Flask is not reachable`);
    return res.status(503).json({
      error: 'Flask AI engine is unavailable',
      detail: `Could not connect to the Python AI engine — make sure "python app.py" is running.`,
    });
  }

  if (err.code === 'ETIMEDOUT' || err.code === 'ECONNABORTED') {
    console.error(`[${route}] Flask timed out`);
    return res.status(504).json({
      error: 'Flask AI engine timed out',
      detail: 'The request took too long. Try again or increase the timeout.',
    });
  }

  // Unexpected error (config mistake, etc.)
  console.error(`[${route}] Unexpected proxy error:`, err.message);
  res.status(500).json({ error: 'Internal gateway error', detail: err.message });
}

// ─── Keep-Alive Ping ──────────────────────────────────────────────────────────
// Pings the server every 10 minutes to prevent Render free tier from sleeping
const KEEP_ALIVE_URL = process.env.KEEP_ALIVE_URL || 'https://bob-ai-1-jsgn.onrender.com/health/upstream';
const KEEP_ALIVE_INTERVAL = 10 * 60 * 1000; // 10 minutes

setInterval(() => {
  console.log(`[Keep-Alive] Pinging ${KEEP_ALIVE_URL}...`);
  axios.get(KEEP_ALIVE_URL)
    .then((res) => console.log(`[Keep-Alive] Ping successful (Express: ${res.data.gateway}, Flask: ${res.data.flask?.status || 'ok'})`))
    .catch(err => console.error(`[Keep-Alive] Ping failed:`, err.message));
}, KEEP_ALIVE_INTERVAL);

// ─── Start ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`Express gateway  →  http://localhost:${PORT}`);
  console.log(`Flask AI engine  →  ${FLASK_BASE_URL}`);
  console.log('Routes: GET /health | GET /health/upstream | POST /generate-site | POST /generate-and-deploy | POST /auth/signup | POST /auth/login | POST /auth/signin | GET /auth/me | GET /auth/profile | PUT /auth/github-token');
});
