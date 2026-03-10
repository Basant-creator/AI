require('dotenv').config();
const express = require('express');
const cors    = require('cors');
const axios   = require('axios');

const app  = express();
const PORT = process.env.PORT            || 3000;
const FLASK = process.env.FLASK_BASE_URL || 'http://localhost:5000';

// ─── Middleware ──────────────────────────────────────────────────────────────
app.use(cors());
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
app.get('/health', async (_req, res) => {
  try {
    const flaskRes = await axios.get(`${FLASK}/health`, { timeout: 5000 });
    res.status(flaskRes.status).json({
      gateway: 'ok',
      flask:   flaskRes.data,
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
    const flaskRes = await axios.post(
      `${FLASK}/generate-website`,
      req.body,
      { timeout: 120_000 }, // AI generation can take up to ~2 min
    );
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
 *     "type": "vanilla",
 *     "github_token": "ghp_...",   // optional — falls back to Flask's own env var
 *     "make_private": false
 *   }
 *
 * Flask generates the site AND creates/pushes a GitHub repo.
 * Returns { success, repo_url, files } (or Flask's native shape).
 */
app.post('/generate-and-deploy', async (req, res) => {
  try {
    const flaskRes = await axios.post(
      `${FLASK}/generate-and-push-to-github`,
      req.body,
      { timeout: 180_000 }, // generation + GitHub push — allow 3 min
    );
    res.status(flaskRes.status).json(flaskRes.data);
  } catch (err) {
    forwardError(err, res, 'generate-and-deploy');
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
    console.error(`[${route}] Flask is not reachable at ${FLASK}`);
    return res.status(503).json({
      error:  'Flask AI engine is unavailable',
      detail: `Could not connect to ${FLASK} — make sure "python app.py" is running.`,
    });
  }

  if (err.code === 'ETIMEDOUT' || err.code === 'ECONNABORTED') {
    console.error(`[${route}] Flask timed out`);
    return res.status(504).json({
      error:  'Flask AI engine timed out',
      detail: 'The request took too long. Try again or increase the timeout.',
    });
  }

  // Unexpected error (config mistake, etc.)
  console.error(`[${route}] Unexpected proxy error:`, err.message);
  res.status(500).json({ error: 'Internal gateway error', detail: err.message });
}

// ─── Start ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`Express gateway  →  http://localhost:${PORT}`);
  console.log(`Flask AI engine  →  ${FLASK}`);
  console.log('Routes: GET /health | POST /generate-site | POST /generate-and-deploy');
});
