"""
Builds AI prompts for different website structures
Handles single-page, multi-page, and full-stack applications
"""

def build_file_instructions(filename):
    """Generate specific instructions for each file type"""
    
    if filename.endswith('.html'):
        if 'login' in filename or 'signup' in filename:
            return """
This is an authentication page. Include:
- Clean, modern form design
- Email and password inputs
- "Remember me" checkbox (for login)
- "Forgot password?" link (for login)
- Terms acceptance checkbox (for signup)
- Client-side validation
- Error message display area
- Loading state handling
- Redirect logic after successful auth
"""
        elif 'dashboard' in filename:
            return """
This is a protected dashboard page. Include:
- User greeting with name
- Navigation sidebar/menu
- Main content area with cards/stats
- Quick actions section
- Logout button
- Profile link
- Responsive layout
"""
        elif 'profile' in filename or 'settings' in filename:
            return """
This is a user profile/settings page. Include:
- Form to edit user information
- Password change section
- Profile picture upload (placeholder)
- Save/Cancel buttons
- Success/error messages
- Validation feedback
"""
        elif 'index' in filename:
            return """
This is the homepage. Include:
- Hero section with compelling headline
- Call-to-action buttons
- Features/benefits section
- Testimonials (if applicable)
- Footer with links and info
"""
        else:
            return """
Create a well-structured HTML page with:
- Proper semantic HTML5
- Consistent navigation
- Responsive design
- Accessibility features
"""
    
    elif filename.endswith('.css'):
        return """
Create comprehensive CSS with:
- CSS variables for colors/fonts
- Responsive breakpoints
- Modern layout (Flexbox/Grid)
- Hover effects and transitions
- Consistent spacing
- Mobile-first approach
"""
    
    elif filename.endswith('.js'):
        if 'auth' in filename and filename.endswith('.js') and 'backend' not in filename and 'routes' not in filename:
            return """
Create authentication JavaScript with:
- A single base URL constant at the very top:
    const API_BASE = window.location.origin + '/api';
  Use this for ALL fetch calls so the app works both locally and on Render without changes.
- Form validation before submitting
- fetch() calls to ${API_BASE}/auth/login and ${API_BASE}/auth/signup
- JWT token stored in localStorage after successful auth
- Redirect to dashboard after login/signup
- Redirect to login if token missing on protected pages
- User-friendly error messages shown in the DOM
- Loading / disabled button state while request is in flight
"""
        elif 'dashboard' in filename:
            return """
Create dashboard JavaScript with:
- Check if user is authenticated
- Fetch user data from API
- Handle logout
- Update UI with user info
- Redirect to login if not authenticated
"""
        else:
            return """
Create JavaScript with:
- Event listeners
- Form handling
- Smooth scrolling/animations
- Mobile menu toggle
- Any interactive features
"""
    
    elif filename == 'backend/server.js' or filename == 'server.js':
        return """
Create a production-ready Express.js server. STRICT RULES:

1. FIRST line: require('dotenv').config();
2. Use: const PORT = process.env.PORT || 5000;
3. MongoDB: mongoose.connect(process.env.MONGO_URI) — NEVER use hardcoded URIs.
4. CORS — allow all origins:
   app.use(cors({ origin: '*', methods: ['GET','POST','PUT','DELETE','OPTIONS'], allowedHeaders: ['Content-Type','Authorization'] }));
5. Static files: app.use(express.static('public'));
6. Body parsers: app.use(express.json()); app.use(express.urlencoded({ extended: true }));
7. Mount routes under /api/auth and /api/users.
8. Global error handler middleware at the bottom.
9. Startup logs:
   console.log(`Server running on port ${PORT}`);
   console.log('MongoDB connected');
10. Do NOT use nodemon — only 'node backend/server.js' in production.
"""
    
    elif 'routes' in filename:
        return """
Create Express route file with:
- Use express.Router()
- Import controller or write inline logic
- Use process.env.JWT_SECRET for JWT signing/verification (NEVER hardcode)
- Password hashing with bcryptjs (saltRounds=10)
- Return consistent JSON: { success: true/false, data: {}, message: '' }
- Proper HTTP status codes (200, 201, 400, 401, 404, 500)
- try/catch on every async handler with next(err)
- For auth routes: POST /signup, POST /login, GET /me (protected)
"""
    
    elif 'models' in filename:
        return """
Create Mongoose model with:
- Schema definition
- Field validation
- Required fields
- Default values
- Timestamps
- Methods (if needed)
"""
    
    elif filename == 'package.json':
        return """
Create package.json with:
- "main": "backend/server.js"
- Scripts MUST be exactly:
    "start": "node backend/server.js"
  Do NOT include nodemon or dev scripts.
- Dependencies: express, mongoose, bcryptjs, jsonwebtoken, dotenv, cors
- No devDependencies needed
- Proper formatting
"""
    
    elif filename == '.env.example':
        return """
Create .env.example with exactly these keys (no values for sensitive ones):
  PORT=5000
  MONGO_URI=
  JWT_SECRET=
Add a comment above each explaining what it is.
Do NOT create a real .env file.
"""
    
    elif filename == 'README.md':
        return """
Create README.md with:
- Project title and description
- Features list
- Installation instructions
- Environment setup
- How to run
- API endpoints (if backend)
- Technologies used
"""
    
    elif filename == '.gitignore':
        return """
Create a .gitignore that excludes:
  node_modules/
  .env
  *.log
  .DS_Store
  dist/
  build/
"""

    elif filename.endswith('.sql'):
        return """
Create SQL schema with:
- Table definitions
- Proper data types
- Primary keys
- Foreign keys (if needed)
- Indexes
- Sample data (optional)
"""
    
    else:
        return "Create this file with appropriate content for its purpose."


def get_structured_prompt(description, structure_info, branding, social_media, contact):
    """
    Build complete AI prompt for structured website generation
    """
    
    website_type = structure_info['type']
    files_list = structure_info['files']
    needs_backend = structure_info.get('needs_backend', False)
    needs_database = structure_info.get('needs_database', False)
    
    # Build file generation instructions
    files_section = f"You must generate exactly {len(files_list)} files:\n\n"
    
    for filename in files_list:
        files_section += f"FILE: {filename}\n"
        
        # Add specific instructions for this file
        instructions = build_file_instructions(filename)
        
        # Add code block template
        if filename.endswith('.html'):
            files_section += "```html\n"
            files_section += f"<!-- {instructions} -->\n"
            files_section += "[Your HTML code here]\n"
            files_section += "```\n\n"
        elif filename.endswith('.css'):
            files_section += "```css\n"
            files_section += f"/* {instructions} */\n"
            files_section += "[Your CSS code here]\n"
            files_section += "```\n\n"
        elif filename.endswith('.js'):
            files_section += "```javascript\n"
            files_section += f"// {instructions}\n"
            files_section += "[Your JavaScript code here]\n"
            files_section += "```\n\n"
        elif filename.endswith('.json'):
            files_section += "```json\n"
            files_section += "[Your JSON code here]\n"
            files_section += "```\n\n"
        elif filename.endswith('.md'):
            files_section += "```markdown\n"
            files_section += "[Your Markdown content here]\n"
            files_section += "```\n\n"
        elif filename.endswith('.sql'):
            files_section += "```sql\n"
            files_section += "[Your SQL code here]\n"
            files_section += "```\n\n"
        else:
            files_section += "```\n"
            files_section += "[Your code here]\n"
            files_section += "```\n\n"
    
    # Build branding section
    branding_section = f"""
BRANDING (use throughout ALL files):
- Company Name: {branding.get('company_name', 'My Company')}
- Tagline: {branding.get('tagline', 'Your tagline here')}
- Primary Color: {branding.get('primary_color', '#667eea')}
- Secondary Color: {branding.get('secondary_color', '#764ba2')}
"""
    
    # Build social media section
    social_section = ""
    if any(social_media.values()):
        social_section = "\nSOCIAL MEDIA (add to footer):\n"
        for platform, username in social_media.items():
            if username:
                if platform == 'email':
                    social_section += f"Email: {username}\n"
                elif platform == 'phone':
                    social_section += f"Phone: {username}\n"
                else:
                    social_section += f"{platform.capitalize()}: {username}\n"
    
    # Build navigation requirements
    navigation_section = ""
    if website_type != 'landing_page':
        # Get unique HTML pages
        html_pages = [f for f in files_list if f.endswith('.html')]
        page_names = []
        for page in html_pages:
            # Extract page name from path
            name = page.split('/')[-1].replace('.html', '').replace('-', ' ').title()
            if name not in ['Login', 'Signup', 'Sign Up']:  # Exclude auth pages from nav
                page_names.append((name, page))
        
        navigation_section = f"""
NAVIGATION (include on ALL pages):
Create consistent navigation with these pages:
"""
        for name, path in page_names[:5]:  # Limit to main pages
            navigation_section += f"- {name} (links to {path})\n"
        
        navigation_section += """
Navigation should:
- Be responsive (hamburger menu on mobile)
- Highlight current page
- Be consistent across all pages
- Include logo/company name
"""
    
    # Build main prompt
    prompt = f"""
Create a complete {website_type.replace('_', ' ')} based on: {description}

PROJECT TYPE: {structure_info['description']}
TOTAL FILES: {len(files_list)}

{branding_section}
{social_section}
{navigation_section}

{files_section}

CRITICAL REQUIREMENTS:

0. EXTERNAL LIBRARIES:
   - If using Font Awesome or other CDN libraries, use SIMPLE links
   - Example: <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
   - NEVER include integrity="" or crossorigin="" attributes
   - These can cause parsing issues

1. CONSISTENCY ACROSS ALL PAGES:
   - Use exact same color scheme everywhere
   - Consistent header and footer on all pages
   - Same font family and sizes
   - Unified design language

2. RESPONSIVE DESIGN:
   - Mobile-first approach
   - Breakpoints: 768px (tablet), 1024px (desktop)
   - Touch-friendly buttons on mobile
   - Readable text sizes on all devices

3. FILE ORGANIZATION:
   - Use proper relative paths
   - Link CSS: <link rel="stylesheet" href="css/style.css">
   - Link JS: <script src="js/script.js"></script>
   - For nested pages, adjust paths accordingly

4. CODE QUALITY:
   - Clean, commented code
   - Semantic HTML5
   - Modern CSS (Flexbox/Grid)
   - Vanilla JavaScript (no jQuery)
   - Accessibility (ARIA labels, alt tags)

5. EXTERNAL RESOURCES:
   - DO NOT use integrity or crossorigin attributes on CDN links
   - Use simple CDN links without hashes
   - Example: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
   - DO NOT include integrity="sha..." attributes
   - These cause issues and are not needed for this use case
"""
    
    if needs_backend:
        prompt += """
6. BACKEND — PRODUCTION RULES (Render-deployable):
   a. require('dotenv').config() MUST be the first line of backend/server.js.
   b. Port: const PORT = process.env.PORT || 5000;
   c. MongoDB: mongoose.connect(process.env.MONGO_URI) — NEVER mongodb://127.0.0.1 or any hardcoded URI.
   d. Serve frontend: app.use(express.static('public'));
   e. CORS: allow all origins (see server.js instructions).
   f. Deploy commands for Render:
      - Build command: npm install
      - Start command: npm start   (which runs: node backend/server.js)
   g. Do NOT use nodemon anywhere.
   h. Never create a real .env file — only .env.example.

7. API ENDPOINTS:
   POST /api/auth/signup  — register, return JWT
   POST /api/auth/login   — login, return JWT
   GET  /api/auth/me      — return current user (protected)
   PUT  /api/users/:id    — update user (protected)

   All responses: { "success": true/false, "data": {}, "message": "" }

8. FRONTEND API CALLS:
   All fetch() calls MUST use:
     const API_BASE = window.location.origin + '/api';
   This ensures the same code works locally (http://localhost:5000) and on Render (https://yourapp.onrender.com) without any changes.
"""
    
    if needs_database:
        prompt += """
9. DATABASE — MongoDB Atlas:
   - Use Mongoose with process.env.MONGO_URI (Atlas connection string).
   - NEVER use mongodb://127.0.0.1 or any local URI.
   - Database name should be derived from the project name (e.g. myapp-db).
   - Schemas must include: required fields, validation, timestamps: true.
   - Add indexes on frequently queried fields (e.g. email).
   - Do NOT assume the database or collections already exist.
"""
    
    prompt += """
9. IMPORTANT FORMAT:
   - Start EACH file with: FILE: path/to/filename
   - Wrap code in triple backticks with language
   - No explanations outside code blocks
   - Make it production-ready
   - Include all necessary files

10. AUTHENTICATION (if applicable):
   - JWT-based authentication
   - Password hashing with bcrypt
   - Protected routes middleware
   - Token stored in localStorage
   - Auto-redirect if not authenticated

REMEMBER:
- Every file MUST start with "FILE: filename"
- Use provided branding colors
- Make it look professional
- Add smooth animations
- Include all requested features
"""
    
    return prompt