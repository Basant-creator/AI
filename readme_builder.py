"""
Builds a beginner-friendly README.md for every AI-generated project.

Sections:
  1. Project header (name, tagline, what it is)
  2. What does this project do? (plain-English overview)
  3. Technologies used (with plain-English explanations)
  4. What's inside? (file tree with per-file descriptions)
  5. Running it on your computer (step-by-step, zero assumed knowledge)
  6. Secret configuration (.env setup explained simply)
  7. How to get each variable (MongoDB, JWT — fully guided)
  8. Deploying it online (GitHub Pages / Render / Vercel)
  9. Changing the look & feel (cosmetic cheat-sheet)
 10. Footer
"""

import datetime


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_readme(description: str, branding: dict, structure_info: dict, files: dict) -> str:
    """
    Build a complete, beginner-friendly README.md string.

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
        _plain_english_overview(project_type, needs_backend, needs_database, company, description),
        _tech_stack(project_type, needs_backend, needs_database),
        _file_tree(file_list, project_type, needs_backend),
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

    badge_line = " ".join(badges)

    return f"""# {company}

> {tagline}

{badge_line}

**Project type:** {type_label}

{description}

> 👋 **New to coding?** Don't worry — this README walks you through every step in plain English.
> You don't need to understand how everything works under the hood.
> Just follow the numbered steps and you'll have this project running in minutes."""


def _plain_english_overview(project_type, needs_backend, needs_database, company, description):
    """A jargon-free explanation of what this project actually is."""

    if project_type == 'landing_page':
        what_it_is = (
            "This is a **static website** — meaning it is made up of plain HTML, CSS, and JavaScript files. "
            "There is no server required. You can open it directly in any web browser, or upload the files "
            "to a free hosting service and share it with the world."
        )
        how_it_works = (
            "When someone visits the site, their browser downloads the HTML file and displays it. "
            "The CSS file controls how everything looks (colours, fonts, layout), and the JavaScript file "
            "adds interactive behaviour (button clicks, animations, etc.)."
        )
    elif project_type == 'multi_page':
        what_it_is = (
            "This is a **multi-page static website** — a collection of HTML pages linked together with a "
            "navigation menu. Like the landing page version, no server is needed. "
            "Each page is its own HTML file that the browser loads when you click a link."
        )
        how_it_works = (
            "The CSS file(s) control the shared look across all pages. "
            "The JavaScript file(s) handle the navigation menu (including the mobile hamburger menu) "
            "and any animations or interactive sections."
        )
    elif project_type == 'react_app':
        what_it_is = (
            "This is a **React application** — a modern type of website built with a JavaScript library "
            "called React. React breaks the page into reusable 'components' (like Lego bricks) that can "
            "update themselves without refreshing the whole page."
        )
        how_it_works = (
            "You need Node.js installed on your computer to run this project locally. "
            "Running `npm start` launches a local development server, and your browser automatically "
            "shows the app at `http://localhost:3000`. When you save a file, the browser updates instantly."
        )
    else:  # full_stack_app
        db_line = (
            "- **Database**: MongoDB Atlas — a cloud database where all user data is securely stored.\n\n"
            if needs_database else ""
        )
        what_it_is = (
            "This is a **full-stack web application** — it has two parts:\n\n"
            "- **Frontend** (what users see): HTML, CSS, and JavaScript pages that run in the browser.\n"
            "- **Backend** (the engine): A Node.js server that handles logins, stores data, and responds "
            "to requests from the frontend.\n\n"
            + db_line +
            "Think of it like a restaurant: the frontend is the dining room customers see, "
            "the backend is the kitchen, and the database is the pantry."
        )
        how_it_works = (
            "When a user fills in the sign-up form, the browser sends the data to the Node.js server. "
            "The server hashes the password (turns it into a scrambled string so it can never be read), "
            "saves the user to MongoDB, and replies with a **JWT token** — a small encrypted ticket "
            "that proves the user is logged in. Every future request from the browser includes that ticket."
        )

    return f"""## What Does This Project Do?

{what_it_is}

### How it works

{how_it_works}"""


def _tech_stack(project_type, needs_backend, needs_database):
    """Tech stack table with plain-English descriptions for each technology."""

    lines = [
        "## Technologies Used",
        "",
        "Here is every tool this project uses, and a plain-English explanation of what each one does.",
        "",
    ]

    if project_type == 'react_app':
        lines += [
            "| Technology | What it does |",
            "|------------|-------------|",
            "| **React 18** | A JavaScript library that builds the whole UI out of small reusable components. |",
            "| **CSS Modules** | Scoped CSS files so each component's styles don't accidentally break another. |",
            "| **Node.js** | Runs JavaScript on your computer (needed to install packages and run the dev server). |",
            "| **npm** | The package manager that downloads and manages all the JavaScript libraries. |",
        ]
    elif needs_backend:
        lines += [
            "| Technology | What it does |",
            "|------------|-------------|",
            "| **HTML5** | The skeleton of every page — defines headings, buttons, forms, images, etc. |",
            "| **CSS3** | Controls how everything looks: colours, fonts, spacing, animations, and responsive layout. |",
            "| **JavaScript** | Makes the pages interactive — handles button clicks, form submissions, and API calls. |",
            "| **Node.js** | Runs JavaScript on the *server* (your backend). Handles incoming requests from the browser. |",
            "| **Express 4** | A lightweight framework on top of Node.js that makes it easy to define routes (URLs the server responds to). |",
        ]
        if needs_database:
            lines += [
                "| **MongoDB Atlas** | A cloud database. Stores all your data (users, posts, etc.) online so it persists between restarts. |",
                "| **Mongoose** | A helper library that lets you define the shape of your data and interact with MongoDB using simple JavaScript. |",
            ]
        lines += [
            "| **bcryptjs** | Hashes (scrambles) passwords before storing them so they can never be read, even by the server owner. |",
            "| **JSON Web Tokens (JWT)** | Creates a small encrypted 'ticket' that proves a user is logged in, included with every protected request. |",
            "| **dotenv** | Reads secret values (API keys, passwords) from a `.env` file so they are never written in the code. |",
        ]
    else:
        lines += [
            "| Technology | What it does |",
            "|------------|-------------|",
            "| **HTML5** | The skeleton of the page — defines headings, buttons, images, sections, etc. |",
            "| **CSS3** | Controls everything visual: colours, fonts, layout, spacing, hover effects, and animations. |",
            "| **JavaScript** | Adds interactivity — scroll effects, mobile menu toggle, form validation, animations. |",
        ]

    return "\n".join(lines)


def _describe_file(filename: str, needs_backend: bool) -> str:
    """Return a one-line plain-English description for a given filename."""
    f = filename.lower()

    if f == 'index.html' or f == 'public/index.html':
        return "The homepage — the first page visitors see."
    if f.endswith('.html') and 'login' in f:
        return "The login page — form where returning users enter their email and password."
    if f.endswith('.html') and 'signup' in f:
        return "The sign-up page — form where new users create an account."
    if f.endswith('.html') and 'dashboard' in f:
        return "The dashboard — the main page users see after logging in."
    if f.endswith('.html') and 'about' in f:
        return "The About page — background information about the company or project."
    if f.endswith('.html') and 'contact' in f:
        return "The Contact page — a form or details so visitors can get in touch."
    if f.endswith('.html') and 'services' in f:
        return "The Services page — lists what the business offers."
    if f.endswith('.html') and 'profile' in f:
        return "The Profile/Settings page — where a logged-in user can view and edit their details."
    if f.endswith('.html'):
        return "An HTML page displayed in the browser."

    if 'style' in f and f.endswith('.css'):
        return "The main stylesheet — controls colours, fonts, layout, and spacing across the site."
    if 'responsive' in f and f.endswith('.css'):
        return "Responsive styles — adjusts the layout so the site looks good on phones and tablets."
    if 'auth' in f and f.endswith('.css'):
        return "Styles specific to the login and sign-up pages."
    if 'dashboard' in f and f.endswith('.css'):
        return "Styles specific to the dashboard page."
    if f.endswith('.css'):
        return "A stylesheet that controls the visual appearance of one or more pages."

    if f in ('script.js', 'js/script.js', 'public/js/main.js'):
        return "Main JavaScript file — handles navigation, animations, and general interactivity."
    if 'auth' in f and f.endswith('.js') and 'backend' not in f and 'routes' not in f:
        return "Handles login/sign-up logic in the browser — sends form data to the server and saves the login token."
    if 'dashboard' in f and f.endswith('.js'):
        return "Fetches data from the server and updates the dashboard page for the logged-in user."
    if 'navigation' in f and f.endswith('.js'):
        return "Controls the navigation menu, including the mobile hamburger toggle."
    if 'filter' in f and f.endswith('.js'):
        return "Adds filtering or search functionality to the page."
    if f.endswith('.js') and 'routes' not in f and 'backend' not in f and 'server' not in f:
        return "JavaScript file that adds interactivity to the page."

    if 'server.js' in f:
        return "The Node.js/Express server — the heart of the backend. Receives requests, runs logic, and sends responses."
    if 'routes' in f and 'auth' in f:
        return "Defines the login and sign-up API endpoints (the URLs the browser calls to log in or register)."
    if 'routes' in f and 'users' in f:
        return "Defines user management API endpoints (get profile, update details, etc.)."
    if 'routes' in f:
        return "Defines a group of API endpoints (URLs the server responds to)."
    if 'models' in f or 'model' in f:
        return "Defines the shape of the data stored in MongoDB (like a table schema in a spreadsheet)."

    if f == 'package.json':
        return "Lists all the Node.js packages this project depends on and the commands to start/build it."
    if f == '.env.example':
        return "A template showing which secret values you need — copy this to `.env` and fill in your own values."
    if f == '.gitignore':
        return "Tells Git which files NOT to upload to GitHub (e.g. `node_modules/` and `.env`)."
    if f == 'readme.md':
        return "This file — the documentation you are reading right now."

    return "A supporting project file."


def _file_tree(file_list, project_type, needs_backend):
    lines = [
        "## What's Inside This Repository?",
        "",
        "Here is every file that was generated, and a plain-English explanation of what each one does.",
        "You don't need to edit most of these — but it's good to know where things live.",
        "",
        "```",
    ]
    for f in file_list:
        lines.append(f"  {f}")
    lines.append("```")
    lines.append("")
    lines.append("### File descriptions")
    lines.append("")
    lines.append("| File | What it does |")
    lines.append("|------|-------------|")
    for f in file_list:
        desc = _describe_file(f, needs_backend)
        lines.append(f"| `{f}` | {desc} |")

    return "\n".join(lines)


def _local_dev(project_type, needs_backend, needs_database, company):
    lines = ["## Running This Project on Your Computer", ""]

    if project_type == 'react_app':
        lines += [
            "### Step 1 — Install Node.js",
            "",
            "Node.js is a program that lets your computer run JavaScript files outside of a browser.",
            "It also includes `npm`, the tool that downloads project libraries.",
            "",
            "1. Go to [https://nodejs.org](https://nodejs.org)",
            "2. Click the **LTS** (Long-Term Support) download button — this is the stable version.",
            "3. Run the installer and follow the prompts.",
            "4. Confirm it installed correctly by opening a terminal and running:",
            "   ```bash",
            "   node --version",
            "   # Should print something like: v18.19.0",
            "   ```",
            "",
            "### Step 2 — Download the project",
            "",
            "```bash",
            "# 'git clone' downloads all the project files from GitHub to your computer",
            "git clone <YOUR_REPO_URL>",
            "",
            "# 'cd' means 'change directory' — moves your terminal into the project folder",
            "cd <repo-folder>",
            "```",
            "",
            "> **Don't have Git?** Download it from [https://git-scm.com](https://git-scm.com)",
            "",
            "### Step 3 — Install project libraries",
            "",
            "```bash",
            "# This reads package.json and downloads everything the project needs.",
            "# It creates a folder called 'node_modules' — this can take a minute.",
            "npm install",
            "```",
            "",
            "### Step 4 — Start the website",
            "",
            "```bash",
            "npm start",
            "```",
            "",
            "Your browser will automatically open at **http://localhost:3000**.",
            "The page refreshes every time you save a file — no need to reload manually.",
            "",
            "> **What is localhost?**",
            "> It's a special address that means 'this computer'.",
            "> `3000` is the port number — think of it as a numbered door the server opens on your machine.",
        ]

    elif needs_backend:
        lines += [
            "### What you need before you start",
            "",
            "| Requirement | Why you need it | Where to get it |",
            "|-------------|-----------------|----------------|",
            "| **Node.js 18+** | Runs the backend server on your computer | [nodejs.org](https://nodejs.org) — click **LTS** |",
            "| **A MongoDB Atlas account** | Free cloud database to store user data | [cloud.mongodb.com](https://cloud.mongodb.com) — sign up free |",
            "| **Git** | Downloads the project from GitHub to your computer | [git-scm.com](https://git-scm.com) |",
            "",
            "---",
            "",
            "### Step 1 — Download the project",
            "",
            "```bash",
            "# Downloads all project files from GitHub to your computer",
            "git clone <YOUR_REPO_URL>",
            "",
            "# Moves your terminal into the downloaded folder",
            "cd <repo-folder>",
            "```",
            "",
            "### Step 2 — Install the project's libraries",
            "",
            "```bash",
            "# Reads package.json and downloads all the required Node.js packages.",
            "# This creates a 'node_modules' folder — it may take a minute.",
            "npm install",
            "```",
            "",
            "### Step 3 — Set up your secret configuration file",
            "",
            "The project needs a file called `.env` that holds sensitive values (database password, secret keys).",
            "This file is **never uploaded to GitHub** — you create it yourself on your own machine.",
            "",
            "```bash",
            "# Copies the .env.example template to a new file called .env",
            "",
            "# On Windows:",
            "copy .env.example .env",
            "",
            "# On Mac / Linux:",
            "cp .env.example .env",
            "```",
            "",
            "Now open the `.env` file in any text editor and fill in your values.",
            "See the **Secret Configuration** section below for step-by-step instructions on getting each value.",
            "",
            "### Step 4 — Start the server",
            "",
            "```bash",
            "# Starts the Node.js backend server",
            "npm start",
            "```",
            "",
            "Open your browser and go to **http://localhost:5000**",
            "",
            "> **What is localhost:5000?**",
            "> `localhost` means 'this computer'. `5000` is the port the server listens on.",
            "> It's like a private website that only works on your machine while the server is running.",
            "",
            "> **Important:** Keep this terminal window open while you're working.",
            "> Closing it stops the server and the website will stop loading.",
        ]

    else:
        lines += [
            "This is a **static website** — no installation, no server, and no terminal commands required.",
            "Just open the files and you're done.",
            "",
            "---",
            "",
            "### Option A — Open directly in your browser (simplest)",
            "",
            "1. Find the downloaded project folder on your computer.",
            "2. Double-click `index.html`.",
            "3. It opens in your default browser instantly.",
            "",
            "> **Note:** Some browsers restrict certain features (like web fonts or API calls) when opening",
            "> a file directly from your hard drive. If something looks broken, use Option B instead.",
            "",
            "---",
            "",
            "### Option B — VS Code Live Server (recommended)",
            "",
            "This gives you a proper local web server that auto-refreshes the page every time you save a file.",
            "",
            "1. Install [Visual Studio Code](https://code.visualstudio.com) — it's free.",
            "2. Open VS Code, then open the project folder: **File → Open Folder**.",
            "3. Click the **Extensions** icon on the left sidebar (looks like four squares).",
            "4. Search for **Live Server** and install it (published by Ritwick Dey).",
            "5. Right-click `index.html` in the file explorer on the left → **Open with Live Server**.",
            "6. Your browser opens at `http://127.0.0.1:5500` and auto-refreshes on every save.",
            "",
            "---",
            "",
            "### Option C — Python's built-in server (if you have Python installed)",
            "",
            "```bash",
            "# In your terminal, navigate into the project folder, then run:",
            "python -m http.server 8000",
            "```",
            "",
            "Open your browser and go to **http://localhost:8000**",
        ]

    return "\n".join(lines)


def _env_setup(needs_backend, needs_database, files):
    if not needs_backend:
        return ""  # Static sites don't need .env

    lines = [
        "## Secret Configuration (the `.env` file)",
        "",
        "### What is a `.env` file?",
        "",
        "A `.env` file is a plain text file that stores **secret values** your app needs to run —",
        "things like database passwords and security keys.",
        "It lives in your project folder but is **never uploaded to GitHub**",
        "(the `.gitignore` file automatically excludes it).",
        "",
        "Think of it like a keychain: your code knows *that* a key exists,",
        "but the actual key value is only ever on your own machine (or your hosting provider's secure settings).",
        "",
        "> ⚠️ **Never share your `.env` file.**",
        "> Do not paste its contents into a chat, email, or GitHub issue.",
        "> Anyone with these values could access your database and all user data.",
        "",
        "### Creating your `.env` file",
        "",
        "A template called `.env.example` is already in the repository.",
        "It shows all the keys you need, without any real values filled in.",
        "",
        "```bash",
        "# Step 1: Copy the template to create your own .env file",
        "",
        "# On Windows:",
        "copy .env.example .env",
        "",
        "# On Mac / Linux:",
        "cp .env.example .env",
        "",
        "# Step 2: Open .env in any text editor and fill in your real values",
        "```",
        "",
        "Once filled in, your `.env` file will look something like this:",
        "",
        "```env",
        "PORT=5000",
    ]

    if needs_database:
        lines += [
            "MONGO_URI=mongodb+srv://youruser:yourpassword@cluster0.abcde.mongodb.net/myapp?retryWrites=true&w=majority",
        ]
    lines += [
        "JWT_SECRET=a_long_random_string_goes_here_never_share_this",
        "```",
        "",
        "See the **How to Get Your Secret Values** section below for exact instructions on generating each value.",
    ]

    return "\n".join(lines)


def _env_variables_guide(needs_backend, needs_database):
    if not needs_backend:
        return ""

    lines = [
        "## How to Get Your Secret Values",
        "",
        "Follow these steps to generate every value your `.env` file needs.",
        "",
    ]

    if needs_database:
        lines += [
            "### `MONGO_URI` — Your Database Connection String",
            "",
            "MongoDB Atlas is a free cloud database. `MONGO_URI` is the web address your app",
            "uses to connect to it — think of it as the database's full URL with your username and password baked in.",
            "",
            "**Step-by-step:**",
            "",
            "1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) and create a free account (or sign in).",
            "2. Click **New Project**, give it any name, and click **Create Project**.",
            "3. Click **Build a Database** → choose **M0 FREE** (the free tier) → click **Create**.",
            "4. You will be asked to create a database user:",
            "   - **Username:** choose any username (e.g. `admin`)",
            "   - **Password:** choose a strong password and **write it down** — you'll need it shortly",
            "   - Click **Create User**",
            "5. Under **Where would you like to connect from?** → click **Add My Current IP Address**, then **Finish and Close**.",
            "6. On the dashboard, click **Connect** next to your cluster.",
            "7. Choose **Drivers** from the connection options.",
            "8. You will see a connection string that looks like this:",
            "   ```",
            "   mongodb+srv://admin:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority",
            "   ```",
            "9. Make two changes to that string:",
            "   - Replace `<password>` with the actual password you chose in step 4.",
            "   - Replace `/?` with `/myapp?` (this sets the database name — change `myapp` to anything you like).",
            "10. The finished string should look like:",
            "    ```",
            "    mongodb+srv://admin:MyPassword123@cluster0.abcde.mongodb.net/myapp?retryWrites=true&w=majority",
            "    ```",
            "11. Copy this full string and paste it as `MONGO_URI=` in your `.env` file.",
            "",
            "> **Forgot the string?** Go back to Atlas → your cluster → **Connect** → **Drivers** and it will show it again.",
            "",
        ]

    lines += [
        "### `JWT_SECRET` — Your Login Security Key",
        "",
        "When a user logs in, the server creates a 'login token' — a small encrypted string",
        "that proves the user is who they say they are. `JWT_SECRET` is the secret key used to",
        "create and verify that token. If someone gets hold of this key, they can impersonate any user.",
        "",
        "**Rules:**",
        "- It must be a long, random string (at least 32 characters, ideally 64+).",
        "- Never reuse the same secret across different projects.",
        "- Never share it publicly.",
        "",
        "**Generate one now — pick any option:**",
        "",
        "**Option A — in your terminal (if you have Node.js):**",
        "```bash",
        'node -e "console.log(require(\'crypto\').randomBytes(64).toString(\'hex\'))"',
        "```",
        "",
        "**Option B — in your terminal (if you have Python):**",
        "```bash",
        'python -c "import secrets; print(secrets.token_hex(64))"',
        "```",
        "",
        "**Option C — online (no terminal needed):**",
        "Go to [https://generate-secret.vercel.app/64](https://generate-secret.vercel.app/64) — it generates one instantly.",
        "",
        "Copy the output and paste it into your `.env` file like this:",
        "```env",
        "JWT_SECRET=a3f9e2b1c84d7f0e6a5b2c9d1e4f7a0b3c6d9e2f5a8b1c4d7e0f3a6b9c2d5e8",
        "```",
        "(Your value will be different — that is expected.)",
        "",
        "### `PORT` — The Server Port Number",
        "",
        "This controls which port the server listens on when running locally.",
        "",
        "- **When running on your computer:** Set it to `5000`. Your site will be at `http://localhost:5000`.",
        "- **When deployed on Render / Railway / Heroku:** Do **not** set this yourself.",
        "  The hosting platform assigns the port automatically. If you hardcode it, the deployment will fail.",
        "",
        "```env",
        "PORT=5000",
        "```",
    ]

    return "\n".join(lines)


def _deployment(project_type, needs_backend):
    lines = [
        "## Putting Your Site Online (Deployment)",
        "",
        "Once you are happy with the site locally, you can publish it to the internet for free.",
        "",
    ]

    if project_type == 'react_app':
        lines += [
            "### Option 1 — Vercel (easiest, recommended for React)",
            "",
            "Vercel is a free hosting platform built specifically for React apps.",
            "",
            "1. Your code is already on GitHub ✓",
            "2. Go to [https://vercel.com](https://vercel.com) and sign in with your GitHub account.",
            "3. Click **Add New Project**.",
            "4. Find this repository in the list and click **Import**.",
            "5. Vercel automatically detects it's a React project — no settings to change.",
            "6. Click **Deploy**.",
            "7. In about 60 seconds, your app is live at a URL like `https://your-project.vercel.app`.",
            "",
            "> Every time you push new code to GitHub, Vercel automatically re-deploys. No manual steps needed.",
            "",
            "---",
            "",
            "### Option 2 — GitHub Pages (also free)",
            "",
            "```bash",
            "# Install the GitHub Pages deployment tool",
            "npm install --save-dev gh-pages",
            "",
            "# Open package.json and add these two lines inside the 'scripts' section:",
            '#   "predeploy": "npm run build",',
            '#   "deploy": "gh-pages -d build"',
            "",
            "# Run the deploy command",
            "npm run deploy",
            "```",
            "",
            "Your site will be live at `https://<your-github-username>.github.io/<repo-name>/`.",
        ]

    elif needs_backend:
        lines += [
            "### Option 1 — Render (easiest, recommended — free tier available)",
            "",
            "Render is a free cloud hosting platform that runs Node.js apps.",
            "",
            "1. Your code is already on GitHub ✓",
            "2. Go to [https://render.com](https://render.com) and sign in with your GitHub account.",
            "3. Click **New +** → **Web Service**.",
            "4. Click **Connect** next to this repository.",
            "5. Fill in the following settings:",
            "",
            "   | Field | What to enter |",
            "   |-------|--------------|",
            "   | **Name** | Any name you like |",
            "   | **Environment** | `Node` |",
            "   | **Branch** | `main` |",
            "   | **Root Directory** | Leave blank |",
            "   | **Build Command** | `npm install` |",
            "   | **Start Command** | `npm start` |",
            "",
            "6. Scroll down to the **Environment Variables** section and add your secrets:",
            "",
            "   | Key | Value |",
            "   |-----|-------|",
            "   | `MONGO_URI` | Your full MongoDB Atlas connection string |",
            "   | `JWT_SECRET` | Your generated secret key |",
            "",
            "   > **Do NOT add `PORT`** — Render injects this automatically. Adding it yourself will break the app.",
            "",
            "7. Click **Create Web Service**.",
            "8. Render builds and deploys your app — this takes 2–5 minutes the first time.",
            "9. Once done, your app is live at `https://<service-name>.onrender.com`.",
            "",
            "> 💤 **Free tier note:**",
            "> On the free plan, Render pauses your service after 15 minutes of no visitors.",
            "> The first request after a pause takes about 30 seconds to wake up — this is normal.",
            "> To keep it awake 24/7, use [UptimeRobot](https://uptimerobot.com) (free) to ping your site every 10 minutes.",
            "",
            "---",
            "",
            "### Option 2 — Railway (alternative)",
            "",
            "1. Go to [https://railway.app](https://railway.app) → **New Project** → **Deploy from GitHub Repo**.",
            "2. Select this repository.",
            "3. Click the **Variables** tab and add `MONGO_URI` and `JWT_SECRET`.",
            "4. Railway automatically detects Node.js and deploys. No extra configuration needed.",
            "",
            "---",
            "",
            "### Common deployment problems and fixes",
            "",
            "| Problem | Likely cause | Fix |",
            "|---------|-------------|-----|",
            "| Site loads but login does not work | `MONGO_URI` is wrong or missing | Double-check the Atlas connection string in the Render environment variables panel |",
            "| `Cannot find module` error in logs | Packages were not installed | Make sure your Build Command is set to `npm install` |",
            "| App crashes immediately on startup | A required env variable is missing | Check the Render logs — it will tell you exactly which variable is missing |",
            "| `Error: listen EADDRINUSE` | Port conflict | Remove the `PORT` environment variable from Render — let it set it automatically |",
        ]

    else:
        lines += [
            "### Option 1 — GitHub Pages (free, instant, no setup required)",
            "",
            "Your code is already on GitHub ✓ — publishing is just a few clicks.",
            "",
            "1. Go to your repository page on GitHub.",
            "2. Click the **Settings** tab near the top of the page.",
            "3. In the left sidebar, scroll down and click **Pages**.",
            "4. Under **Branch**, select `main` from the dropdown.",
            "5. Leave the folder set to `/ (root)` and click **Save**.",
            "6. Wait about 30 seconds, then refresh the Settings → Pages page.",
            "7. A green box will appear with your live URL:",
            "   ```",
            "   https://<your-github-username>.github.io/<repo-name>/",
            "   ```",
            "8. Share that link — your site is now live and accessible to anyone.",
            "",
            "> Every time you push changes to the `main` branch, GitHub Pages automatically updates the live site.",
            "",
            "---",
            "",
            "### Option 2 — Netlify (drag & drop — even easier)",
            "",
            "1. Go to [https://netlify.com](https://netlify.com) and create a free account.",
            "2. On your Netlify dashboard, click **Add new site** → **Deploy manually**.",
            "3. Open your project folder on your computer.",
            "4. Drag the entire folder onto the Netlify upload area.",
            "5. Netlify uploads and deploys it instantly — you get a live public URL in seconds.",
            "",
            "> You can also connect Netlify to your GitHub repository so it automatically re-deploys every time you push new code.",
        ]

    return "\n".join(lines)


def _cosmetic_guide(project_type, needs_backend, needs_database, company, primary, secondary, file_list):
    css_files  = [f for f in file_list if f.endswith('.css')]
    html_files = [f for f in file_list if f.endswith('.html')]
    css_ref    = css_files[0]  if css_files  else ("App.css" if project_type == 'react_app' else "style.css")
    html_ref   = html_files[0] if html_files else ("public/index.html" if needs_backend else "index.html")

    lines = [
        "## Customising the Look & Feel",
        "",
        "You don't need to understand all the code to make this site your own.",
        "Here are the most common things people change, and exactly where to find them.",
        "",
        "> 💡 **Fastest way to rename the brand:**",
        "> In VS Code, press **Ctrl + Shift + H** (Windows) or **Cmd + Shift + H** (Mac)",
        f"> to open Find & Replace across all files. Search for `{company}` and replace it with your brand name everywhere at once.",
        "",
    ]

    if project_type == 'react_app':
        lines += [
            "### Colours",
            "",
            f"Open `{css_ref}` and look for the `:root` block near the top of the file:",
            "```css",
            ":root {",
            f"  --primary-color: {primary};   /* Main brand colour — used for buttons, highlights */",
            f"  --secondary-color: {secondary};  /* Accent colour — used for hover effects, borders */",
            "}",
            "```",
            "Change the hex colour values to anything you want. Pick colours at [coolors.co](https://coolors.co).",
            "",
            "### Text content",
            "",
            "| What to change | Where to find it |",
            "|----------------|-----------------|",
            "| Company name & tagline | Find the `<h1>` and `<p>` tags in your main component JSX file |",
            "| Navigation links | Find the `<nav>` element inside your Header component |",
            "| Footer links and text | Find the `<footer>` element in your Footer component |",
            "| Browser tab title | Open `public/index.html` → the `<title>` tag inside `<head>` |",
            "| Hero headline | Find the first large `<h1>` or `<h2>` inside a `.hero` or `.banner` section |",
            "",
            "### Fonts",
            "",
            f"Open `{css_ref}` and find the `font-family` property on the `body` selector.",
            "To use a different Google Font, add an `@import` line at the very top of the file:",
            "```css",
            "/* Add this at the very top of the CSS file */",
            "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');",
            "",
            "body {",
            "  font-family: 'Inter', sans-serif;  /* Replace 'Inter' with your chosen font name */",
            "}",
            "```",
            "Browse and pick free fonts at [fonts.google.com](https://fonts.google.com).",
        ]
    else:
        lines += [
            "### Colours",
            "",
            f"Open `{css_ref}` and look for the `:root` block near the top of the file:",
            "```css",
            ":root {",
            f"  --primary-color: {primary};   /* Main brand colour — buttons, links, highlights */",
            f"  --secondary-color: {secondary};  /* Accent colour — hover states, borders */",
            "}",
            "```",
            "Change the hex values to any colour you want. Pick colours at [coolors.co](https://coolors.co).",
            "",
            "### Text content",
            "",
            "| What to change | File to open | What to look for in that file |",
            "|----------------|-------------|------------------------------|",
            f"| Company name (`{company}`) | All `.html` files | Use Find & Replace to update it everywhere |",
            f"| Hero headline | `{html_ref}` | The `<h1>` tag inside the section with class `.hero` |",
            f"| Hero subheading / description | `{html_ref}` | The `<p>` tag directly beneath the `<h1>` |",
            f"| Navigation menu links | All `.html` files | The `<nav>` tag → the `<ul>` list items inside it |",
            f"| Footer text and links | All `.html` files | The `<footer>` tag at the bottom of each page |",
            f"| Browser tab title | All `.html` files | The `<title>` tag inside `<head>` at the top |",
            "",
            "### Fonts",
            "",
            f"Open `{css_ref}` and find `font-family` on the `body` selector.",
            "To switch to a Google Font, add this `@import` at the very top of the CSS file:",
            "```css",
            "/* Add this at the very top of the CSS file (before everything else) */",
            "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');",
            "",
            "body {",
            "  font-family: 'Inter', sans-serif;  /* Replace 'Inter' with your chosen font */",
            "}",
            "```",
            "Browse free fonts at [fonts.google.com](https://fonts.google.com) and copy the `@import` link they provide.",
            "",
            "### Images",
            "",
            f"Open `{html_ref}` and look for `<img src=\"...\">` tags.",
            "Replace the `src` value with a link to your own image or a local file path.",
            f"For background images defined in CSS, open `{css_ref}` and search for `background-image`.",
        ]

        if needs_backend:
            lines += [
                "",
                "### How long users stay logged in",
                "",
                "By default, users are automatically logged out after **7 days**.",
                "To change this, open `backend/routes/auth.js` and find this line:",
                "```javascript",
                "jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '7d' })",
                "```",
                "Change `'7d'` to `'1d'` (1 day), `'30d'` (30 days), `'1h'` (1 hour), etc.",
            ]

    return "\n".join(lines)


def _footer():
    now = datetime.datetime.now()
    return (
        f"---\n\n"
        f"*This project was generated on {now.strftime('%Y-%m-%d')} by **AI Website Generator**.*\n\n"
        f"If you get stuck, re-read the relevant section above carefully — every step is explained in plain English.\n"
        f"For further help, open an issue on the GitHub repository."
    )
