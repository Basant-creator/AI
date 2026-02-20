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
        if 'auth' in filename:
            return """
Create authentication JavaScript with:
- Form validation
- API calls to backend
- Token storage (localStorage)
- Redirect after login/signup
- Error handling
- Loading states
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
    
    elif filename == 'server.js':
        return """
Create Express.js server with:
- Express setup and middleware
- CORS configuration
- Body parser
- Routes import
- Database connection
- Error handling
- Port configuration
- Start server
"""
    
    elif 'routes' in filename:
        return """
Create Express routes with:
- Route definitions
- Request validation
- Business logic
- Error handling
- Response formatting
- Status codes
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
- Project name and version
- Dependencies: express, mongoose, bcrypt, jsonwebtoken, dotenv, cors
- Scripts: start, dev (nodemon)
- Proper formatting
"""
    
    elif filename == '.env.example':
        return """
Create .env.example with:
- PORT=5000
- MONGODB_URI=mongodb://localhost:27017/dbname
- JWT_SECRET=your_jwt_secret_here
- Comments explaining each variable
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
6. BACKEND IMPLEMENTATION:
   - Express.js framework
   - RESTful API structure
   - Proper error handling
   - Input validation
   - Security best practices (helmet, cors)
   - Environment variables for sensitive data

7. API ENDPOINTS (example structure):
   POST /api/auth/signup - Register new user
   POST /api/auth/login - Login user
   GET /api/auth/me - Get current user
   PUT /api/users/:id - Update user
   
   All responses should use JSON format:
   { "success": true/false, "data": {}, "message": "" }
"""
    
    if needs_database:
        prompt += """
8. DATABASE:
   - MongoDB with Mongoose
   - Clear schema definitions
   - Validation rules
   - Indexes on frequently queried fields
   - Timestamps (createdAt, updatedAt)
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