"""
Builds a rich, developer-friendly README.md for every generated project.

Sections:
  1. Project overview & tech stack
  2. Local development (clone → install → run)
  3. .env setup (.env.example reference)
  4. How to obtain each env variable (MongoDB Atlas, JWT_SECRET, etc.)
  5. Deployment guide (Render for full-stack, GitHub Pages for static)
  6. Cosmetic / quick-edit cheat-sheet
"""

import datetime


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_readme(description: str, branding: dict, structure_info: dict, files: dict) -> str:
    """
    Build a complete README.md string.

    Args:
        description    - The original user description
        branding       - Dict with company_name, tagline, primary_color, secondary_color
        structure_info - Dict returned by determine_website_structure()
        files          - Dict of {filename: content} that was pushed to GitHub

    Returns:
        A Markdown string ready to commit as README.md
    """
    needs_backend  = structure_info.get('needs_backend',  False)
    needs_database = structure_info.get('needs_database', False)
    project_type   = structure_info.get('type', 'landing_page')

    company   = branding.get('company_name', 'My Project')
    tagline   = branding.get('tagline', description)
    primary   = branding.get('primary_color', '#667eea')
    secondary = branding.get('secondary_color', '#764ba2')

    file_list = sorted(files.keys())

    sections = [
        _header(company, tagline, description, project_type, needs_backend, needs_database),
        _tech_stack(project_type, needs_backend, needs_database),
        _file_tree(file_list),
        _local_dev(project_type, needs_backend, needs_database, company),
        _env_setup(needs_backend, needs_database, files),
        _env_variables_guide(needs_backend, needs_database),
        _deployment(project_type, needs_backend),
        _cosmetic_guide(project_type, needs_backend, needs_database, company, primary, secondary, file_list),
        _footer(),
    ]

    return "\n\n---\n\n".join(s for s in sections if s.strip())


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _header(company, tagline, description, project_type, needs_backend, needs_database):
    badges = []
    if needs_backend:
        badges.append("![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)")
        badges.append("![Express](https://img.shields.io/badge/Express-4.x-000000?logo=express)")
    if needs_database:
        badges.append("![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)")
    badges.append("![License](https://img.shields.io/badge/license-MIT-blue)")

    type_label = {
        'landing_page':   'Static Landing Page',
        'multi_page':     'Multi-Page Website',
        'full_stack_app': 'Full-Stack Web Application',
        'react_app':      'React Application',
    }.get(project_type, 'Web Project')

    return f"""# {company}

> {tagline}

{" ".join(badges)}

**Type:** {type_label}

{description}"""


def _tech_stack(project_type, needs_backend, needs_database):
    lines = ["## Tech Stack", ""]
    if project_type == 'react_app':
        lines += [
            "| Layer | Technology |",
            "|-------|-----------|",
            "| UI    | React 18 + CSS Modules |",
        ]
    elif needs_backend:
        lines += [
            "| Layer    | Technology |",
            "|----------|-----------|",
            "| Frontend | HTML5 · CSS3 · Vanilla JS |",
            "| Backend  | Node.js · Express 4 |",
        ]
        if needs_database:
            lines.append("| Database | MongoDB Atlas (Mongoose) |")
        lines.append("| Auth     | JWT · bcryptjs |")
    else:
        lines += [
            "| Layer | Technology |",
            "|-------|-----------|",
            "| UI    | HTML5 · CSS3 · Vanilla JS |",
        ]
    return "\n".join(lines)


def _file_tree(file_list):
    lines = ["## Project Files", "", "```"]
    for f in file_list:
        lines.append(f"  {f}")
    lines.append("```")
    return "\n".join(lines)


def _local_dev(project_type, needs_backend, needs_database, company):
    lines = ["## 1. Running Locally", ""]

    if project_type == 'react_app':
        lines += [
            "### Prerequisites",
            "- Node.js 18+  ([download](https://nodejs.org))",
            "",
            "### Steps",
            "```bash",
            "# 1. Clone the repository",
            "git clone <YOUR_REPO_URL>",
            f"cd <repo-folder>",
            "",
            "# 2. Install dependencies",
            "npm install",
            "",
            "# 3. Start the dev server",
            "npm start",
            "```",
            "",
            "Open **http://localhost:3000** in your browser.",
        ]

    elif needs_backend:
        lines += [
            "### Prerequisites",
            "- [Node.js 18+](https://nodejs.org)",
            "- A free [MongoDB Atlas](https://cloud.mongodb.com) account",
            "",
            "### Steps",
            "```bash",
            "# 1. Clone the repository",
            "git clone <YOUR_REPO_URL>",
            "cd <repo-folder>",
            "",
            "# 2. Install dependencies",
            "npm install",
            "",
            "# 3. Create your .env file (see Section 2 below)",
            "cp .env.example .env",
            "#    Then open .env and fill in your values",
            "",
            "# 4. Start the server",
            "npm start",
            "```",
            "",
            "Open **http://localhost:5000** in your browser.",
            "",
            "> **Tip:** Use [VS Code Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) "
            "or any modern browser — just make sure the backend is running first.",
        ]

    else:
        lines += [
            "No build step required — this is a static website.",
            "",
            "**Option A — Open directly:**",
            "```",
            "Double-click  index.html  (or the main HTML file)",
            "```",
            "",
            "**Option B — VS Code Live Server (recommended):**",
            "1. Install the [Live Server extension](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)",
            "2. Right-click `index.html` → **Open with Live Server**",
            "3. Browser auto-opens at `http://127.0.0.1:5500`",
            "",
            "**Option C — Python simple server:**",
            "```bash",
            "python -m http.server 8000",
            "# Open http://localhost:8000",
            "```",
        ]

    return "\n".join(lines)


def _env_setup(needs_backend, needs_database, files):
    if not needs_backend:
        return ""  # Static sites don't need .env

    has_example = any('.env.example' in f for f in files)

    lines = [
        "## 2. Environment Variables — `.env` Setup",
        "",
        "The project ships with a **`.env.example`** file that lists every required variable.",
        "**Never commit your real `.env` file** — it is already listed in `.gitignore`.",
        "",
        "```bash",
        "# Copy the template",
        "cp .env.example .env",
        "",
        "# Open .env in your editor and fill in the values",
        "```",
        "",
        "Your `.env` should look like this once filled:",
        "",
        "```env",
        "PORT=5000",
    ]

    if needs_database:
        lines += [
            "MONGO_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/<dbname>?retryWrites=true&w=majority",
        ]
    lines += [
        "JWT_SECRET=your_super_secret_random_string_here",
        "```",
    ]

    return "\n".join(lines)


def _env_variables_guide(needs_backend, needs_database):
    if not needs_backend:
        return ""

    lines = [
        "## 3. How to Get Each Variable",
        "",
    ]

    if needs_database:
        lines += [
            "### `MONGO_URI` — MongoDB Atlas Connection String",
            "",
            "1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) and sign in (free account).",
            "2. Create a new **Project**, then click **Build a Database** → choose **M0 Free**.",
            "3. Set a **username** and **password** for database access.",
            "4. Under **Network Access**, click **Add IP Address** → **Allow Access from Anywhere** (`0.0.0.0/0`).",
            "5. Once the cluster is ready, click **Connect** → **Drivers**.",
            "6. Copy the connection string — it looks like:",
            "   ```",
            "   mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/myapp-db?retryWrites=true&w=majority",
            "   ```",
            "7. Replace `<password>` with your actual password and `myapp-db` with your preferred database name.",
            "8. Paste the full string as the value of `MONGO_URI` in your `.env`.",
            "",
        ]

    lines += [
        "### `JWT_SECRET` — JSON Web Token Secret",
        "",
        "This must be a **long, random, secret string**. Never share or reuse it.",
        "",
        "Generate one instantly in your terminal:",
        "```bash",
        "# Node.js (recommended)",
        'node -e "console.log(require(\'crypto\').randomBytes(64).toString(\'hex\'))"',
        "",
        "# Python alternative",
        'python -c "import secrets; print(secrets.token_hex(64))"',
        "```",
        "Copy the output and paste it as `JWT_SECRET=<output>` in your `.env`.",
        "",
        "### `PORT` (optional)",
        "",
        "Defaults to `5000` locally. On Render / Railway this is set automatically — do **not** hardcode it.",
    ]

    return "\n".join(lines)


def _deployment(project_type, needs_backend):
    lines = ["## 4. Deployment", ""]

    if project_type == 'react_app':
        lines += [
            "### Deploy to Vercel (recommended for React)",
            "",
            "1. Push your code to GitHub (already done!).",
            "2. Go to [https://vercel.com](https://vercel.com) → **New Project**.",
            "3. Import this GitHub repository.",
            "4. Vercel auto-detects React — just click **Deploy**.",
            "5. Your app is live at `https://<your-app>.vercel.app`.",
            "",
            "### Deploy to GitHub Pages",
            "",
            "```bash",
            "npm install --save-dev gh-pages",
            "# Add to package.json scripts:",
            '#   "predeploy": "npm run build",',
            '#   "deploy": "gh-pages -d build"',
            "npm run deploy",
            "```",
        ]

    elif needs_backend:
        lines += [
            "### Deploy to Render (recommended — free tier available)",
            "",
            "1. Your code is already on GitHub ✓",
            "2. Go to [https://render.com](https://render.com) → **New** → **Web Service**.",
            "3. Connect your GitHub account and select **this repository**.",
            "4. Fill in the service settings:",
            "",
            "   | Setting | Value |",
            "   |---------|-------|",
            "   | **Environment** | `Node` |",
            "   | **Root Directory** | *(leave blank)* |",
            "   | **Build Command** | `npm install` |",
            "   | **Start Command** | `npm start` |",
            "",
            "5. Scroll down to **Environment Variables** and add:",
            "   - `MONGO_URI` → your Atlas connection string",
            "   - `JWT_SECRET` → your generated secret",
            "   *(Do NOT add PORT — Render injects it automatically)*",
            "",
            "6. Click **Create Web Service** — deployment starts automatically.",
            "7. Once live, your URL will be `https://<service-name>.onrender.com`.",
            "",
            "> **Free Tier Note:** Render spins down idle services after ~15 minutes. "
            "The first request after sleep takes ~30 seconds. "
            "Upgrade to a paid plan or use [UptimeRobot](https://uptimerobot.com) to keep it warm.",
            "",
            "### Alternative: Railway",
            "",
            "1. Go to [https://railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**.",
            "2. Select this repo.",
            "3. Add the same env variables in the **Variables** tab.",
            "4. Railway auto-detects Node.js and deploys.",
        ]

    else:
        lines += [
            "### Deploy to GitHub Pages (free, instant)",
            "",
            "1. Your code is already on GitHub ✓",
            "2. Go to the repository → **Settings** → **Pages**.",
            "3. Under **Branch**, select `main` and folder `/root`.",
            "4. Click **Save** — your site is live at:",
            "   ```",
            "   https://<your-github-username>.github.io/<repo-name>/",
            "   ```",
            "",
            "### Alternative: Netlify (drag & drop)",
            "",
            "1. Go to [https://netlify.com](https://netlify.com) → **Add new site** → **Deploy manually**.",
            "2. Drag the project folder onto the Netlify dashboard.",
            "3. Done — instant public URL.",
        ]

    return "\n".join(lines)


def _cosmetic_guide(project_type, needs_backend, needs_database, company, primary, secondary, file_list):
    lines = [
        "## 5. Cosmetic Changes — Quick Reference",
        "",
        "Use this table as a cheat-sheet when you need to tweak the look & feel.",
        "",
    ]

    if project_type == 'react_app':
        lines += [
            "| What to change | File | What to look for |",
            "|----------------|------|-----------------|",
            "| Brand colors | `App.css` | `--primary-color` / `--secondary-color` CSS variables |",
            "| Company name & tagline | `App.jsx` (or `src/components/Header.jsx`) | Text in `<h1>` / `<p>` tags |",
            "| Hero section content | Main component JSX | First large `<section>` or `<div class=\"hero\">` |",
            "| Navigation links | Header/Navbar component | `<nav>` or `<ul>` inside header |",
            "| Footer links | Footer component | `<footer>` tag |",
            "| Fonts | `App.css` or `index.css` | `font-family` on `body` |",
            "| Page title | `public/index.html` | `<title>` tag |",
        ]
    elif needs_backend:
        css_files  = [f for f in file_list if f.endswith('.css')]
        html_files = [f for f in file_list if f.endswith('.html')]
        js_files   = [f for f in file_list if f.endswith('.js') and 'backend' not in f and 'server' not in f and 'routes' not in f]

        css_ref  = css_files[0]  if css_files  else "public/css/style.css"
        html_ref = html_files[0] if html_files else "public/index.html"

        lines += [
            "| What to change | File | What to look for |",
            "|----------------|------|-----------------|",
            f"| Brand colors (primary `{primary}`, secondary `{secondary}`) | `{css_ref}` | `:root` block → `--primary-color`, `--secondary-color` |",
            f"| Company name **{company}** | All `*.html` files | Search & replace `{company}` |",
            "| Hero headline / subheading | `public/index.html` | `<h1>` inside `.hero` section |",
            "| Navigation links | All `*.html` files | `<nav>` → `<ul>` items |",
            "| Footer text & links | All `*.html` files | `<footer>` tag |",
            "| Fonts | `{css_ref}` | `@import` at top + `font-family` on `body` |",
            "| Button styles | `{css_ref}` | `.btn`, `.btn-primary` classes |",
            "| Card / section layout | `{css_ref}` | `.card`, `.section`, `.grid` classes |",
            "| Background images | `{html_ref}` | `<img src=\"...\">` tags or inline `background-image` in CSS |",
            "| API base URL | Frontend JS files | `const API_BASE = window.location.origin + '/api'` (no change needed) |",
            "| JWT expiry | `backend/routes/auth.js` | `expiresIn: '7d'` in `jwt.sign()` |",
        ]
    else:
        css_files  = [f for f in file_list if f.endswith('.css')]
        html_files = [f for f in file_list if f.endswith('.html')]
        css_ref  = css_files[0]  if css_files  else "style.css"
        html_ref = html_files[0] if html_files else "index.html"

        lines += [
            "| What to change | File | What to look for |",
            "|----------------|------|-----------------|",
            f"| Brand colors (primary `{primary}`, secondary `{secondary}`) | `{css_ref}` | `:root` block → `--primary-color`, `--secondary-color` |",
            f"| Company name **{company}** | All `*.html` files | Search & replace `{company}` |",
            "| Hero headline / subheading | `{html_ref}` | `<h1>` inside `.hero` section |",
            "| Navigation links | All `*.html` files | `<nav>` → `<ul>` items |",
            "| Footer text & links | All `*.html` files | `<footer>` tag |",
            "| Fonts | `{css_ref}` | `@import` at top + `font-family` on `body` |",
            "| Button styles | `{css_ref}` | `.btn`, `.btn-primary` or similar classes |",
            "| Background images | `{html_ref}` | `<img>` tags or `background-image` in CSS |",
            "| Animations / transitions | `{css_ref}` | `transition:`, `@keyframes`, `animation:` rules |",
        ]

    lines += [
        "",
        "> **VS Code tip:** Use **Ctrl + Shift + H** (Find & Replace across all files) "
        f"to rename `{company}` to your new brand name in one step.",
    ]

    return "\n".join(lines)


def _footer():
    year = datetime.datetime.now().year
    return f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d')} by AI Website Generator · {year}*"
