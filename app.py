from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import requests
from website_structures import determine_website_structure
from prompt_builder import get_structured_prompt
from github_manager import GitHubManager
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("\n" + "="*60)
    print("ERROR: GEMINI_API_KEY not found!")
    print("="*60)
    print("Please create a .env file with:")
    print("GEMINI_API_KEY=your_api_key_here")
    print("\nGet your API key from: https://makersuite.google.com/app/apikey")
    print("="*60 + "\n")
    exit(1)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✓ Gemini API configured successfully")
except Exception as e:
    print(f"\n✗ Error configuring Gemini API: {e}")
    exit(1)

def parse_files_from_response(text):
    """
    Parse AI response and extract individual files
    More robust parsing that handles various AI response formats
    """
    files = {}
    
    # Method 1: Try to parse "FILE: filename" format
    lines = text.split('\n')
    current_file = None
    in_code_block = False
    code_content = []
    
    for line in lines:
        # Check if this is a file declaration
        if 'FILE:' in line:
            # Save previous file if exists
            if current_file and code_content:
                files[current_file] = '\n'.join(code_content).strip()
            
            # Extract filename (handle various formats)
            if 'FILE:' in line:
                current_file = line.split('FILE:')[1].strip()
                # Remove any markdown or extra characters
                current_file = current_file.replace('`', '').strip()
            
            code_content = []
            in_code_block = False
        
        # Check for code block markers
        elif line.strip().startswith('```'):
            if in_code_block:
                # End of code block
                in_code_block = False
            else:
                # Start of code block (skip the ``` line itself)
                in_code_block = True
        
        # Collect code content
        elif in_code_block and current_file:
            code_content.append(line)
    
    # Save the last file
    if current_file and code_content:
        files[current_file] = '\n'.join(code_content).strip()
    
    # Method 2: If Method 1 didn't work, try extracting all code blocks
    if not files:
        import re
        # Find all code blocks
        pattern = r'```(?:html|css|javascript|js|json)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if len(matches) >= 3:
            # Assume standard order: HTML, CSS, JS
            files['index.html'] = matches[0].strip()
            files['style.css'] = matches[1].strip() if len(matches) > 1 else ''
            files['script.js'] = matches[2].strip() if len(matches) > 2 else ''
    
    return files

def get_pexels_images(keywords, per_keyword=2):
    """
    Fetch real images from Pexels API based on keywords
    Returns a list of image URLs
    """
    pexels_api_key = os.getenv('PEXELS_API_KEY')
    if not pexels_api_key:
        print("Warning: No Pexels API key found")
        return []
    
    image_urls = []
    headers = {'Authorization': pexels_api_key}
    
    for keyword in keywords:
        try:
            url = f'https://api.pexels.com/v1/search?query={keyword}&per_page={per_keyword}&orientation=landscape'
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                for photo in data.get('photos', []):
                    image_urls.append({
                        'url': photo['src']['large'],
                        'keyword': keyword,
                        'photographer': photo['photographer']
                    })
        except Exception as e:
            print(f"Error fetching images for '{keyword}': {str(e)}")
            continue
    
    return image_urls

def extract_keywords_from_description(description):
    """
    Extract relevant keywords from user's description
    """
    description_lower = description.lower()
    
    # Mapping of topics to relevant keywords
    keyword_map = {
        'coffee': ['coffee', 'cafe', 'espresso', 'latte', 'barista'],
        'restaurant': ['restaurant', 'food', 'dining', 'cuisine', 'chef'],
        'portfolio': ['office', 'workspace', 'professional', 'desk', 'modern'],
        'photography': ['camera', 'photography', 'photos', 'gallery', 'art'],
        'fitness': ['fitness', 'gym', 'workout', 'exercise', 'health'],
        'tech': ['technology', 'computer', 'coding', 'startup', 'innovation'],
        'fashion': ['fashion', 'clothing', 'style', 'boutique', 'shopping'],
        'travel': ['travel', 'vacation', 'destination', 'adventure', 'beach'],
        'food': ['food', 'cooking', 'ingredients', 'kitchen', 'recipe'],
        'shop': ['store', 'shopping', 'products', 'retail', 'display']
    }
    
    # Find matching topics
    matched_keywords = []
    for topic, keywords in keyword_map.items():
        if topic in description_lower:
            matched_keywords.extend(keywords[:3])  # Take first 3 keywords
            break
    
    # If no specific match, use general keywords
    if not matched_keywords:
        matched_keywords = ['modern', 'business', 'professional']
    
    return matched_keywords

def get_vanilla_prompt_enhanced(description, branding, social_media, contact):
    """Generate enhanced prompt for vanilla HTML/CSS/JS project with branding and contact info"""
    
    # Extract keywords and fetch real images
    keywords = extract_keywords_from_description(description)
    images = get_pexels_images(keywords, per_keyword=2)
    
    # Create image list for the prompt
    image_list = ""
    if images:
        image_list = "\n\nAVAILABLE REAL IMAGES - USE THESE EXACT URLS:\n"
        for i, img in enumerate(images, 1):
            image_list += f"{i}. {img['url']} (keyword: {img['keyword']})\n"
    
    # Build branding section
    branding_info = f"""
\nBRANDING INFORMATION:
- Company Name: {branding['company_name']}
- Tagline: {branding['tagline'] or 'Create an appropriate tagline'}
- Primary Color: {branding['primary_color']}
- Secondary Color: {branding['secondary_color']}
"""
    
    # Build social media section
    social_links = []
    if social_media['instagram']:
        social_links.append(f"Instagram: {social_media['instagram']}")
    if social_media['twitter']:
        social_links.append(f"Twitter: {social_media['twitter']}")
    if social_media['facebook']:
        social_links.append(f"Facebook: {social_media['facebook']}")
    if social_media['linkedin']:
        social_links.append(f"LinkedIn: {social_media['linkedin']}")
    if social_media['youtube']:
        social_links.append(f"YouTube: {social_media['youtube']}")
    
    social_info = ""
    if social_links:
        social_info = "\n\nSOCIAL MEDIA - INCLUDE FOOTER WITH THESE LINKS:\n" + "\n".join([f"- {link}" for link in social_links])
    
    # Build contact section
    contact_info = ""
    contact_items = []
    if contact['email']:
        contact_items.append(f"Email: {contact['email']}")
    if contact['phone']:
        contact_items.append(f"Phone: {contact['phone']}")
    if contact['address']:
        contact_items.append(f"Address: {contact['address']}")
    
    if contact_items:
        contact_info = "\n\nCONTACT INFORMATION - INCLUDE IN FOOTER/CONTACT SECTION:\n" + "\n".join([f"- {item}" for item in contact_items])
    
    prompt = f"""
Create a complete, professional website based on: {description}
{branding_info}{social_info}{contact_info}

You must output exactly 3 files in this format:

FILE: index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{branding['company_name']}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Use company name: {branding['company_name']} -->
    <!-- Use tagline: {branding['tagline'] or '[Create tagline]'} -->
    <script src="script.js"></script>
</body>
</html>
```

FILE: style.css
```css
:root {{
    --primary-color: {branding['primary_color']};
    --secondary-color: {branding['secondary_color']};
}}

body {{
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}}
```

FILE: script.js
```javascript
console.log('Website loaded');
```
""" + image_list + """

CRITICAL REQUIREMENTS:

1. BRANDING:
   - Use the exact company name: {branding['company_name']}
   - Include tagline: {branding['tagline'] or '[Create appropriate tagline]'}
   - Use primary color {branding['primary_color']} for main elements
   - Use secondary color {branding['secondary_color']} for accents

2. IMAGES:
   - Use the EXACT image URLs provided above
   - Make images responsive with CSS
   - Add proper alt text

3. SOCIAL MEDIA & CONTACT:
   - Include footer with all social media links provided
   - Add contact section with email, phone, and address if provided
   - Use appropriate icons (emoji or Unicode)

4. DESIGN:
   - Start each file with "FILE: filename"
   - Wrap code in triple backticks
   - Modern, responsive design
   - Smooth animations
"""
    
    return prompt

def get_vanilla_prompt(description):
    """Generate prompt for vanilla HTML/CSS/JS project with real images"""
    
    # Extract keywords and fetch real images
    keywords = extract_keywords_from_description(description)
    images = get_pexels_images(keywords, per_keyword=2)
    
    # Create image list for the prompt
    image_list = ""
    if images:
        image_list = "\n\nAVAILABLE REAL IMAGES - USE THESE EXACT URLS:\n"
        for i, img in enumerate(images, 1):
            image_list += f"{i}. {img['url']} (keyword: {img['keyword']})\n"
    
    # Note: Use {{ and }} to escape braces in f-strings for CSS
    prompt = f"""
Create a complete, professional website based on: {description}

You must output exactly 3 files in this format:

FILE: index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Title</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Your HTML here -->
    <script src="script.js"></script>
</body>
</html>
```

FILE: style.css
```css
body {{
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}}
```

FILE: script.js
```javascript
console.log('Website loaded');
```
""" + image_list + """

CRITICAL IMAGE REQUIREMENTS:

1. USE THE EXACT IMAGE URLS PROVIDED ABOVE
   - Copy the full URL exactly as shown
   - These are real, high-quality photos from Pexels
   - They match the website topic perfectly

2. HOW TO USE IMAGES:
   - For hero section: Use image 1 or 2
   - For gallery/cards: Use different images (3, 4, 5, etc.)
   - Example: <img src="PASTE_EXACT_URL_HERE" alt="Description">
   
3. IMAGE STYLING:
   - Make images responsive: width: 100%; height: auto;
   - Add object-fit: cover; for hero images
   - Use border-radius for modern look
   - Add box-shadow for depth

4. EXAMPLE USAGE:
```html
   <div class="hero">
     <img src="EXACT_PEXELS_URL_FROM_ABOVE" alt="Hero Image">
     <div class="hero-content">
       <h1>Welcome</h1>
     </div>
   </div>
```

5. IF YOU NEED MORE IMAGES:
   - Use CSS gradients as backgrounds
   - Add emoji icons for decoration
   - But prioritize using the provided Pexels images

ABSOLUTELY REQUIRED:
- Use the EXACT URLs provided above
- Do NOT modify or shorten the URLs
- Do NOT use placeholder.com or any other service
- Every <img> tag must use a URL from the list above

DESIGN REQUIREMENTS:
- Start each file with "FILE: filename"
- Wrap code in triple backticks
- Make it fully responsive (mobile-friendly)
- Modern, professional design
- Smooth animations and transitions
- Beautiful typography
"""
    
    return prompt
def get_react_prompt(description):
    """Generate prompt for React project with real images"""
    
    # Extract keywords and fetch real images
    keywords = extract_keywords_from_description(description)
    images = get_pexels_images(keywords, per_keyword=2)
    
    # Create image list for the prompt
    image_list = ""
    if images:
        image_list = "\n\nAVAILABLE REAL IMAGES - USE THESE EXACT URLS:\n"
        for i, img in enumerate(images, 1):
            image_list += f"{i}. {img['url']} (keyword: {img['keyword']})\n"
    
    return f"""
Create a complete React application based on: {description}

You must output files in this format:

FILE: App.jsx
```jsx
import React, {{ useState }} from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      <h1>Hello World</h1>
    </div>
  );
}}  

export default App;
```

FILE: App.css
```css
.App {{
  text-align: center;
}}
```

FILE: package.json
```json
{{
  "name": "react-app",
  "version": "0.1.0",
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }}
}}
```
{image_list}

CRITICAL IMAGE REQUIREMENTS:
- Use the EXACT Pexels URLs provided above
- Example: <img src="EXACT_URL" alt="Description" />
- Make images responsive with CSS

DESIGN REQUIREMENTS:
- Start each file with "FILE: filename"
- Wrap code in triple backticks
- Modern, responsive React components
- Use functional components with hooks
- Include proper package.json with dependencies
"""

def get_react_prompt_enhanced(description, branding, social_media, contact):
    """Generate enhanced prompt for React project with branding and contact info"""
    
    # Extract keywords and fetch real images
    keywords = extract_keywords_from_description(description)
    images = get_pexels_images(keywords, per_keyword=2)
    
    # Create image list for the prompt
    image_list = ""
    if images:
        image_list = "\n\nAVAILABLE REAL IMAGES - USE THESE EXACT URLS:\n"
        for i, img in enumerate(images, 1):
            image_list += f"{i}. {img['url']} (keyword: {img['keyword']})\n"
    
    # Build branding section
    branding_info = f"""
\nBRANDING INFORMATION:
- Company Name: {branding['company_name']}
- Tagline: {branding['tagline'] or 'Create an appropriate tagline'}
- Primary Color: {branding['primary_color']}
- Secondary Color: {branding['secondary_color']}
"""
    
    # Build social media section
    social_links = []
    if social_media['instagram']:
        social_links.append(f"Instagram: {social_media['instagram']}")
    if social_media['twitter']:
        social_links.append(f"Twitter: {social_media['twitter']}")
    if social_media['facebook']:
        social_links.append(f"Facebook: {social_media['facebook']}")
    if social_media['linkedin']:
        social_links.append(f"LinkedIn: {social_media['linkedin']}")
    if social_media['youtube']:
        social_links.append(f"YouTube: {social_media['youtube']}")
    
    social_info = ""
    if social_links:
        social_info = "\n\nSOCIAL MEDIA - INCLUDE FOOTER WITH THESE LINKS:\n" + "\n".join([f"- {link}" for link in social_links])
    
    # Build contact section
    contact_info = ""
    contact_items = []
    if contact['email']:
        contact_items.append(f"Email: {contact['email']}")
    if contact['phone']:
        contact_items.append(f"Phone: {contact['phone']}")
    if contact['address']:
        contact_items.append(f"Address: {contact['address']}")
    
    if contact_items:
        contact_info = "\n\nCONTACT INFORMATION - INCLUDE IN FOOTER/CONTACT SECTION:\n" + "\n".join([f"- {item}" for item in contact_items])
    
    return f"""
Create a complete React application based on: {description}
{branding_info}{social_info}{contact_info}

You must output files in this format:

FILE: App.jsx
```jsx
import React, {{ useState }} from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      <h1>{branding['company_name']}</h1>
      <p>{branding['tagline'] or '[Create tagline]'}</p>
    </div>
  );
}}  

export default App;
```

FILE: App.css
```css
:root {{
  --primary-color: {branding['primary_color']};
  --secondary-color: {branding['secondary_color']};
}}

.App {{
  text-align: center;
}}
```

FILE: package.json
```json
{{
  "name": "react-app",
  "version": "0.1.0",
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }}
}}
```
{image_list}

CRITICAL REQUIREMENTS:

1. BRANDING:
   - Use company name: {branding['company_name']}
   - Include tagline: {branding['tagline'] or '[Create appropriate tagline]'}
   - Use primary color {branding['primary_color']} for main elements
   - Use secondary color {branding['secondary_color']} for accents

2. IMAGES:
   - Use the EXACT Pexels URLs provided above
   - Make images responsive with CSS

3. SOCIAL MEDIA & CONTACT:
   - Include footer component with all social media links
   - Add contact section with provided information
   - Use appropriate icons

4. DESIGN:
   - Start each file with "FILE: filename"
   - Wrap code in triple backticks
   - Modern, responsive React components
   - Use functional components with hooks
"""

@app.route('/generate-website', methods=['POST'])
def generate_website():
    """
    Main endpoint to generate website files
    Expects JSON: {
        "description": "user's website description",
        "type": "vanilla" or "react"
    }
    """
    try:
        data = request.json
        
        # Validate input
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_description = data.get('description', '').strip()
        project_type = data.get('type', 'vanilla').lower()
        
        # Validate description
        if not user_description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Validate project type
        if project_type not in ['vanilla', 'react']:
            return jsonify({
                'success': False,
                'error': 'Type must be either "vanilla" or "react"'
            }), 400
        
        # Generate appropriate prompt
        if project_type == 'vanilla':
            prompt = get_vanilla_prompt(user_description)
        else:
            prompt = get_react_prompt(user_description)
        
        print(f"Generating {project_type} project for: {user_description}")
        
        # Call Gemini API
        response = model.generate_content(prompt)
        generated_text = response.text
        
        # Parse files from response
        files = parse_files_from_response(generated_text)
        
        # Validate that we got files
        if not files:
            return jsonify({
                'success': False,
                'error': 'Failed to parse files from AI response'
            }), 500
        
        print(f"Successfully generated {len(files)} files")
        
        return jsonify({
            'success': True,
            'project_type': project_type,
            'files': files,
            'file_count': len(files)
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Website Generator API is running'
    })

@app.route('/generate-and-push-to-github', methods=['POST'])
def generate_and_push_to_github():
    """
    INTELLIGENT WORKFLOW: Detect structure → Generate → Push to GitHub
    Supports: landing pages, multi-page, full-stack apps
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        user_description = data.get('description', '').strip()
        project_type = data.get('type', 'vanilla').lower()
        
        if not user_description:
            return jsonify({'success': False, 'error': 'Description is required'}), 400
        
        # Branding
        branding = {
            'company_name': data.get('company_name', 'My Company'),
            'tagline': data.get('tagline', ''),
            'primary_color': data.get('primary_color', '#667eea'),
            'secondary_color': data.get('secondary_color', '#764ba2'),
        }
        
        # Social media
        social_media = {
            'instagram': data.get('instagram', ''),
            'twitter': data.get('twitter', ''),
            'linkedin': data.get('linkedin', ''),
            'facebook': data.get('facebook', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
        }
        
        # Contact
        contact = {
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
        }
        
        print(f"\n{'='*60}")
        print(f"INTELLIGENT WEBSITE GENERATION")
        print(f"{'='*60}")
        print(f"Description: {user_description}")
        
        # STEP 0: Determine website structure intelligently
        print("\nStep 0/3: Analyzing requirements...")
        structure_info = determine_website_structure(user_description)
        
        print(f"✓ Detected: {structure_info['type'].upper()}")
        print(f"  Files to generate: {len(structure_info['files'])}")
        print(f"  Needs backend: {structure_info.get('needs_backend', False)}")
        print(f"  Needs database: {structure_info.get('needs_database', False)}")
        
        # STEP 1: Generate with intelligent structure
        print("\nStep 1/3: Generating code with AI...")
        
        if project_type == 'react':
            # For React, use existing prompt (for now)
            prompt = get_react_prompt_enhanced(user_description, branding, social_media, contact)
        else:
            # Use intelligent structured prompt
            prompt = get_structured_prompt(
                user_description,
                structure_info,
                branding,
                social_media,
                contact
            )
        
        response = model.generate_content(prompt)
        generated_text = response.text
        
        # Parse files
        files = parse_files_from_response(generated_text)
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'Failed to parse files from AI response'
            }), 500
        
        print(f"✓ Generated {len(files)} files")
        
        # Show what was generated
        print("\n  Generated files:")
        for filename in sorted(files.keys()):
            print(f"    - {filename}")
        
        # STEP 2: Push to GitHub
        print("\nStep 2/3: Pushing to GitHub...")
        github_mgr = GitHubManager()
        github_result = github_mgr.create_and_push(user_description, files)
        
        if not github_result['success']:
            return jsonify({
                'success': False,
                'error': f"GitHub error: {github_result['error']}"
            }), 500
        
        print(f"✓ Pushed to: {github_result['repo_url']}")
        
        # STEP 3: Complete!
        print("\nStep 3/3: Complete!")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'project_type': project_type,
            'structure': {
                'type': structure_info['type'],
                'description': structure_info['description'],
                'files_count': len(files),
                'has_backend': structure_info.get('needs_backend', False),
                'has_database': structure_info.get('needs_database', False)
            },
            'files': files,
            'file_count': len(files),
            'github': github_result,
            'customization': {
                'branding': branding,
                'social_media': {k: v for k, v in social_media.items() if v},
                'contact': {k: v for k, v in contact.items() if v}
            },
            'message': f'{structure_info["description"]} generated and pushed to GitHub!'
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("Available endpoints:")
    print("  POST /generate-website - Generate website files")
    print("  GET  /health - Health check")
    print("  POST /generate-and-push-to-github - Generate website and push to GitHub")
    app.run(debug=True, port=5000)