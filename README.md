# AI Website Generator

> Describe a website in plain English — get production-ready code pushed to GitHub in seconds.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask)
![Gemini](https://img.shields.io/badge/Gemini-2.5--flash-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 1. Project Overview

**AI Website Generator** is a Flask-based REST API that turns a plain-English description into a complete, deployable website — then pushes every file directly to a new GitHub repository.

**Who it is for:**
- Developers who need a production-ready scaffold fast
- Freelancers who want to kickstart client projects
- Anyone who wants a working website without starting from scratch

**Key features:**
- Automatically detects the right website structure (landing page, multi-page, portfolio, blog, or full-stack app)
- Generates HTML, CSS, JavaScript, backend Node.js/Express, Mongoose models, and `.env.example` in one API call
- Fetches real, royalty-free images from Pexels and injects them into the generated code
- Applies full branding: company name, tagline, primary/secondary colours, social links, and contact details
- Creates a GitHub repository and pushes all generated files — including a rich `README.md` — automatically
- Supports Vanilla HTML/CSS/JS, React, and full-stack (Node + MongoDB) output types

---

## 2. Features

- **Intelligent structure detection** — analyses the description and picks the appropriate file structure (landing page → multi-page → full-stack app)
- **AI code generation** — powered by Google Gemini 2.5-flash; generates complete, commented, production-ready code
- **Real image injection** — queries the Pexels API and embeds actual photo URLs into the generated HTML
- **Branding customisation** — company name, tagline, primary colour, secondary colour applied across all files
- **Social media & contact** — Instagram, Twitter, Facebook, LinkedIn, YouTube links and email/phone/address in the footer
- **GitHub integration** — creates a repository, commits all files, and returns the live repo URL
- **Auto README generation** — every pushed repo gets a tailored `README.md` with setup, deployment, and quick-edit guides
- **Multiple output modes** — Vanilla JS, React, or full-stack (Express + MongoDB + JWT auth)
- **Health check endpoint** — `/health` for uptime monitoring

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| API server | Python 3.10+ · Flask 3.x |
| AI model | Google Gemini 2.5-flash (`google-generativeai`) |
| Image source | Pexels REST API |
| GitHub integration | PyGithub |
| Environment config | python-dotenv |
| HTTP client | requests |

---

## 4. Project Structure

```
ai-website-generator/
├── app.py                  # Flask app — all API endpoints and core logic
├── prompt_builder.py       # Builds AI prompts for each file type and project structure
├── website_structures.py   # File-structure templates (landing page, blog, full-stack, etc.)
├── github_manager.py       # GitHub repo creation and file-push logic (uses PyGithub)
├── readme_builder.py       # Generates a tailored README.md for every pushed project
├── requirements.txt        # Python dependencies
├── test_api.py             # Manual API test script
├── test_generator.py       # Generation unit tests
└── .env                    # Local secrets — DO NOT commit (see Section 6)
```

**Key files explained:**

| File | Purpose |
|------|---------|
| `app.py` | Flask entry point; defines `/generate-website`, `/generate-and-push-to-github`, and `/health`; handles Pexels image fetching and AI response parsing |
| `prompt_builder.py` | Contains per-file-type instructions (HTML pages, CSS, JS, Express server, Mongoose models, etc.) and assembles the full prompt sent to Gemini |
| `website_structures.py` | Declares which files to generate for each project type and the NLP rules used to detect the right structure |
| `github_manager.py` | Wraps PyGithub; generates unique repo names, creates public repos, and pushes files with UPSERT logic |
| `readme_builder.py` | Builds the `README.md` committed to every generated repository |

---

## 5. Installation & Setup

### Prerequisites

- Python 3.10 or higher
- `pip` (comes with Python)
- A Google Gemini API key ([get one free](https://makersuite.google.com/app/apikey))
- A GitHub Personal Access Token with `repo` scope ([create one](https://github.com/settings/tokens))
- *(Optional)* A Pexels API key for real images ([get one free](https://www.pexels.com/api/))

### Clone & install

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/ai-website-generator.git
cd ai-website-generator

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run locally

```bash
# 4. Create your .env file (see Section 6)
copy .env.example .env      # Windows
cp  .env.example .env       # macOS / Linux
# Open .env and fill in your keys

# 5. Start the Flask development server
python app.py
```

The API will be available at `http://localhost:5000`.

### Development vs production

| Mode | Command | Notes |
|------|---------|-------|
| Development | `python app.py` | Debug mode on, auto-reloads on file save |
| Production | `gunicorn app:app` | Install `gunicorn` first: `pip install gunicorn` |

---

## 6. Environment Variables

> **Never commit your `.env` file.** It is listed in `.gitignore` and must stay local or be set via your hosting provider's secrets manager.

Create a `.env` file in the project root using the template below:

### `.env.example`

```env
# Google Gemini API key — used to generate website code
# Get yours at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=

# GitHub Personal Access Token — used to create repos and push files
# Required scopes: repo (full control of private repositories)
# Create one at: https://github.com/settings/tokens
GITHUB_TOKEN=

# Pexels API key — used to fetch real images for generated websites
# Optional: if omitted, image injection is skipped
# Get yours at: https://www.pexels.com/api/
PEXELS_API_KEY=
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Authenticates requests to Google Gemini 2.5-flash |
| `GITHUB_TOKEN` | Yes | Allows the app to create repositories and push files on your behalf |
| `PEXELS_API_KEY` | No | Enables real image fetching; without it, no images are injected |

---

## 7. API Documentation

All endpoints accept and return `application/json`.

### `GET /health`

Health check — confirms the server and Gemini API are operational.

**Response**
```json
{
  "status": "healthy",
  "message": "AI Website Generator API is running"
}
```

---

### `POST /generate-website`

Generates website files and returns them in the response. Does **not** push to GitHub.

**Request body**

```json
{
  "description": "A modern coffee shop website with an online menu and contact form",
  "type": "vanilla"
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `description` | string | Yes | Plain-English description of the website |
| `type` | string | No | `"vanilla"` (default) or `"react"` |

**Response**

```json
{
  "success": true,
  "project_type": "vanilla",
  "files": {
    "index.html": "<!DOCTYPE html>...",
    "style.css": "body { ... }",
    "script.js": "console.log(...);"
  },
  "file_count": 3
}
```

---

### `POST /generate-and-push-to-github`

Full pipeline: detects structure → generates code → pushes to GitHub.

**Request body**

```json
{
  "description": "A SaaS dashboard with user login, analytics charts, and settings page",
  "type": "vanilla",
  "company_name": "DashFlow",
  "tagline": "Analytics made simple",
  "primary_color": "#667eea",
  "secondary_color": "#764ba2",
  "instagram": "@dashflow",
  "twitter": "@dashflow",
  "linkedin": "dashflow",
  "facebook": "",
  "youtube": "",
  "email": "hello@dashflow.io",
  "phone": "+1 800 555 0100",
  "address": "123 Main St, San Francisco, CA"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Plain-English website description |
| `type` | string | No | `"vanilla"` (default) or `"react"` |
| `company_name` | string | No | Brand name applied across all files |
| `tagline` | string | No | Tagline used in hero section |
| `primary_color` | string | No | Hex code for main brand colour (default: `#667eea`) |
| `secondary_color` | string | No | Hex code for accent colour (default: `#764ba2`) |
| `instagram` … `youtube` | string | No | Social media handles/URLs added to footer |
| `email` / `phone` / `address` | string | No | Contact details added to footer/contact section |

**Response**

```json
{
  "success": true,
  "project_type": "vanilla",
  "structure": {
    "type": "full_stack_app",
    "description": "Full-stack web application with auth",
    "files_count": 12,
    "has_backend": true,
    "has_database": true
  },
  "files": { "public/index.html": "...", "backend/server.js": "..." },
  "file_count": 12,
  "github": {
    "success": true,
    "repo_name": "saas-dashboard-20260227-143022",
    "repo_url": "https://github.com/<username>/saas-dashboard-20260227-143022",
    "username": "<username>"
  },
  "customization": {
    "branding": { "company_name": "DashFlow", "tagline": "Analytics made simple", "primary_color": "#667eea", "secondary_color": "#764ba2" },
    "social_media": { "instagram": "@dashflow", "twitter": "@dashflow" },
    "contact": { "email": "hello@dashflow.io" }
  },
  "message": "Full-stack web application with auth generated and pushed to GitHub!"
}
```

**Authentication:** All endpoints are public. Secure the server behind a reverse proxy or API gateway before exposing it to the internet.

---

## 8. Testing

### Run the test scripts

```bash
# Make sure the Flask server is running in another terminal first
python app.py

# In a second terminal (with the venv activated):
python test_api.py
python test_generator.py
```

### Manual testing with curl

```bash
# Health check
curl http://localhost:5000/health

# Generate a vanilla website
curl -X POST http://localhost:5000/generate-website \
  -H "Content-Type: application/json" \
  -d '{"description": "A minimalist personal blog", "type": "vanilla"}'

# Full pipeline with branding
curl -X POST http://localhost:5000/generate-and-push-to-github \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A fitness studio website with class schedule and booking",
    "company_name": "IronPeak Fitness",
    "primary_color": "#e53e3e",
    "secondary_color": "#2d3748",
    "instagram": "@ironpeak",
    "email": "info@ironpeak.com"
  }'
```

### Manual testing with Postman

1. Import the base URL `http://localhost:5000`
2. Create a `POST` request to `/generate-and-push-to-github`
3. Set `Body` → `raw` → `JSON` and paste the request body above
4. Send — the response will include the live GitHub repo URL

---

## 9. Deployment

### Deploy to Render (recommended)

1. Push this repository to GitHub.
2. Go to [https://render.com](https://render.com) → **New** → **Web Service**.
3. Connect your GitHub account and select this repository.
4. Configure the service:

   | Setting | Value |
   |---------|-------|
   | **Environment** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |

5. Add environment variables under **Environment**:
   - `GEMINI_API_KEY`
   - `GITHUB_TOKEN`
   - `PEXELS_API_KEY` *(optional)*

6. Click **Create Web Service** — Render builds and deploys automatically.

> **Free tier note:** Render spins down idle services after ~15 minutes of inactivity. The first request after sleep may take up to 30 seconds. Use [UptimeRobot](https://uptimerobot.com) to send a ping every 10 minutes to keep the service warm.

### Common deployment issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `GEMINI_API_KEY not found` | Env var not set on host | Add `GEMINI_API_KEY` in the hosting dashboard |
| `No GitHub token provided` | `GITHUB_TOKEN` missing | Add `GITHUB_TOKEN` with `repo` scope |
| `Failed to parse files from AI response` | Gemini returned unexpected format | Retry — the model occasionally produces malformed output |
| `422 Unprocessable Entity` from GitHub | Repo name already exists | The app auto-retries with a timestamp suffix; check your GitHub account |
| `gunicorn: command not found` | Not in requirements | Run `pip install gunicorn` and add it to `requirements.txt` |

---

## 10. Security Notes

- **API keys** — stored exclusively in environment variables, never in source code. The `.env` file is `.gitignore`d.
- **GitHub token scope** — use a fine-grained token scoped to only the repositories this app needs to write to. Avoid classic tokens with full `repo` scope in production.
- **Gemini API key** — treat it like a password. Rotate it immediately if it is ever exposed.
- **No user data stored** — this API is stateless; no request data is persisted to disk or a database.
- **Input validation** — the `description` field is validated for presence before being sent to the AI model. Do not pass untrusted user input directly without rate-limiting.
- **Rate limiting** — add a reverse proxy (nginx, Cloudflare, or an API gateway) with rate limiting before exposing the `/generate-and-push-to-github` endpoint publicly. Each request consumes Gemini and Pexels API quota.

---

## 11. Crucial Concept: Overcoming Free-Tier Timeouts

One of the largest hurdles when deploying AI-generation platforms to free tier services (like Render) is the **strict 100-second HTTP connection timeout limit**. Because generating an entire codebase with AI natively takes anywhere from 1 to 3 minutes, a traditional synchronous HTTP request (`POST /generate-and-deploy`) would invariably get killed by the cloud provider's router, resulting in `504 Gateway Timeout` errors.

To solve this, we implemented an **Asynchronous Job Polling Architecture**:
1. When the frontend requests a generation, the `app.py` server spawns an independent Python `threading.Thread` and immediately returns a `202 Accepted` alongside a unique `job_id`. 
2. The HTTP connection closes instantly, making the request incredibly lightweight and immune to timeouts.
3. The frontend executes a passive `while (true)` loop, issuing a minimalist `GET /job/<job_id>` ping back to the server exactly every **10 seconds**.
4. Once the backend thread finishes pushing to GitHub, the status flips to `completed`, and the loop downloads the generated result seamlessly!

This architecture ensures the tool is **100% resilient** and entirely free to host, eliminating broken pipes and frozen frontends.

---

## 12. Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear, focused commits.
3. Ensure `test_api.py` and `test_generator.py` pass before opening a pull request.
4. Open a pull request with a description of what was changed and why.

For bug reports, open a GitHub issue with the request payload, the full error message, and the Flask console output.

---

## 13. License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
