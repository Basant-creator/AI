from flask import Flask, request, jsonify
from google import genai
import os
from dotenv import load_dotenv
import re
import requests
import base64
import hashlib
import datetime
from functools import wraps
import bcrypt
import jwt
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from cryptography.fernet import Fernet, InvalidToken
from website_structures import determine_website_structure, get_structure_by_type
from prompt_builder import get_structured_prompt
from github_manager import GitHubManager
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'change-this-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DAYS = int(os.getenv('JWT_EXP_DAYS', '7'))


def _build_fernet():
    """Create a Fernet instance from TOKEN_ENCRYPTION_KEY if configured."""
    raw_key = os.getenv('TOKEN_ENCRYPTION_KEY', '').strip()
    if not raw_key:
        return None

    try:
        return Fernet(raw_key.encode('utf-8'))
    except Exception:
        # Allow a human-readable secret by deterministically deriving a valid Fernet key.
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode('utf-8')).digest())
        return Fernet(derived)


fernet = _build_fernet()


def _strip_mongodb_credentials(uri):
    """Remove inline credentials from a MongoDB URI, keeping host/query intact."""
    if '://' not in uri:
        return uri

    scheme, rest = uri.split('://', 1)
    if '@' in rest:
        rest = rest.rsplit('@', 1)[1]
    return f"{scheme}://{rest}"


mongo_uri = os.getenv('MONGODB_URI', '').strip()
mongo_db_name = os.getenv('MONGODB_DB_NAME', 'ai_website_generator')
mongo_username = os.getenv('MONGODB_USER', '').strip()
mongo_password = os.getenv('MONGODB_PASSWORD')
mongo_auth_db = os.getenv('MONGODB_AUTH_DB', 'admin').strip()
mongo_client = None
users_collection = None

if mongo_uri:
    try:
        mongo_client_args = {
            'serverSelectionTimeoutMS': 5000,
        }
        connection_uri = mongo_uri

        # Prefer separate credentials when provided so raw special characters in
        # password (like @) can stay untouched in env vars.
        if mongo_username and mongo_password:
            connection_uri = _strip_mongodb_credentials(mongo_uri)
            mongo_client_args.update({
                'username': mongo_username,
                'password': mongo_password,
                'authSource': mongo_auth_db,
            })

        mongo_client = MongoClient(connection_uri, **mongo_client_args)
        mongo_client.admin.command('ping')
        db = mongo_client[mongo_db_name]
        users_collection = db['users']
        users_collection.create_index('username_lower', unique=True)
        users_collection.create_index('email_lower', unique=True)
        print(f"✓ MongoDB connected ({mongo_db_name})")
    except Exception as e:
        print(f"⚠ MongoDB connection failed: {e}")
        users_collection = None
else:
    print("⚠ MONGODB_URI not set. Auth and saved token features are disabled.")

if not fernet:
    print("⚠ TOKEN_ENCRYPTION_KEY not set. GitHub token encryption features are disabled.")


def _require_auth_dependencies():
    if users_collection is None:
        return False, jsonify({'success': False, 'error': 'Database is not configured'}), 503
    if fernet is None:
        return False, jsonify({'success': False, 'error': 'Token encryption is not configured'}), 503
    return True, None, None


def _hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def _encrypt_token(token):
    return fernet.encrypt(token.encode('utf-8')).decode('utf-8')


def _decrypt_token(encrypted_token):
    return fernet.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')


def _create_session_token(user_doc):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'sub': str(user_doc['_id']),
        'username': user_doc['username'],
        'iat': now,
        'exp': now + datetime.timedelta(days=JWT_EXP_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _extract_bearer_token():
    auth_header = request.headers.get('Authorization', '').strip()
    if not auth_header.lower().startswith('bearer '):
        return None
    token = auth_header[7:].strip()
    return token or None


def _get_current_user(optional=False):
    if users_collection is None:
        if optional:
            return None, None
        return None, ('Database is not configured', 503)

    token = _extract_bearer_token()
    if not token:
        if optional:
            return None, None
        return None, ('Missing bearer token', 401)

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('sub')
        if not user_id:
            return None, ('Invalid session token', 401)

        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return None, ('User not found', 401)

        return user, None
    except jwt.ExpiredSignatureError:
        return None, ('Session expired. Please login again.', 401)
    except jwt.InvalidTokenError:
        return None, ('Invalid session token', 401)
    except Exception:
        return None, ('Failed to authenticate user', 401)


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user, error = _get_current_user(optional=False)
        if error:
            message, status = error
            return jsonify({'success': False, 'error': message}), status
        return func(user, *args, **kwargs)

    return wrapper


def _build_user_response(user_doc):
    history = user_doc.get('generation_history', [])
    return {
        'id': str(user_doc['_id']),
        'username': user_doc.get('username', ''),
        'gmail': user_doc.get('email', ''),
        'has_github_token': bool(user_doc.get('github_token_encrypted')),
        'generation_count': len(history),
        'token_last_updated_at': user_doc.get('token_last_updated_at'),
        'created_at': user_doc.get('created_at'),
        'updated_at': user_doc.get('updated_at'),
    }


@app.route('/auth/signup', methods=['POST'])
def signup():
    """Create a user account with encrypted GitHub token."""
    ok, error_response, status = _require_auth_dependencies()
    if not ok:
        return error_response, status

    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        email = data.get('gmail', '').strip() or data.get('email', '').strip()
        password = data.get('password', '')
        github_token = data.get('github_token', '').strip()

        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        if not email:
            return jsonify({'success': False, 'error': 'Gmail is required'}), 400
        if '@' not in email:
            return jsonify({'success': False, 'error': 'Please provide a valid Gmail'}), 400
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        if not github_token:
            return jsonify({'success': False, 'error': 'GitHub access token is required'}), 400

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_doc = {
            'username': username,
            'username_lower': username.lower(),
            'email': email,
            'email_lower': email.lower(),
            'password_hash': _hash_password(password),
            'github_token_encrypted': _encrypt_token(github_token),
            'generation_history': [],
            'token_last_updated_at': now,
            'created_at': now,
            'updated_at': now,
        }

        result = users_collection.insert_one(user_doc)
        created = users_collection.find_one({'_id': result.inserted_id})
        session_token = _create_session_token(created)

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'token': session_token,
            'user': _build_user_response(created)
        }), 201

    except DuplicateKeyError:
        return jsonify({'success': False, 'error': 'Username or Gmail already exists'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and issue JWT session token."""
    if users_collection is None:
        return jsonify({'success': False, 'error': 'Database is not configured'}), 503

    try:
        data = request.json or {}
        identifier = data.get('username', '').strip() or data.get('gmail', '').strip() or data.get('email', '').strip()
        password = data.get('password', '')

        if not identifier or not password:
            return jsonify({'success': False, 'error': 'Credentials are required'}), 400

        user = users_collection.find_one({
            '$or': [
                {'username_lower': identifier.lower()},
                {'email_lower': identifier.lower()},
            ]
        })

        if not user or not _verify_password(password, user.get('password_hash', '')):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        token = _create_session_token(user)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': _build_user_response(user)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/auth/me', methods=['GET'])
@require_auth
def get_me(current_user):
    """Get authenticated user's profile (safe fields only)."""
    return jsonify({
        'success': True,
        'user': _build_user_response(current_user)
    })


@app.route('/auth/profile', methods=['GET'])
@require_auth
def get_profile(current_user):
    """Get authenticated user's profile plus generation history."""
    history = current_user.get('generation_history', [])
    # Keep most recent entries first.
    history_sorted = sorted(history, key=lambda x: x.get('created_at', ''), reverse=True)

    return jsonify({
        'success': True,
        'user': _build_user_response(current_user),
        'history': history_sorted,
    })


@app.route('/auth/github-token', methods=['PUT'])
@require_auth
def update_github_token(current_user):
    """Allow users to rotate/change their encrypted GitHub token any time."""
    ok, error_response, status = _require_auth_dependencies()
    if not ok:
        return error_response, status

    try:
        data = request.json or {}
        github_token = data.get('github_token', '').strip()
        if not github_token:
            return jsonify({'success': False, 'error': 'GitHub access token is required'}), 400

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        users_collection.update_one(
            {'_id': current_user['_id']},
            {
                '$set': {
                    'github_token_encrypted': _encrypt_token(github_token),
                    'token_last_updated_at': now,
                    'updated_at': now,
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'GitHub token updated successfully',
            'token_last_updated_at': now
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    client = genai.Client(api_key=api_key)
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
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
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
        
        # Check if user selected a specific template
        requested_type = data.get('website_type', '').strip().lower()
        if requested_type:
            # Use user-selected template
            structure_info = get_structure_by_type(requested_type)
            if structure_info:
                print(f"✓ Using user-selected template: {structure_info['type'].upper()}")
            else:
                # Fall back to auto-detection if template is invalid
                print(f"⚠ Unknown template '{requested_type}', auto-detecting...")
                structure_info = determine_website_structure(user_description)
                print(f"✓ Detected: {structure_info['type'].upper()}")
        else:
            # Auto-detect based on description
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
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
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
        
        # Resolve GitHub token source: request payload > authenticated user's saved token.
        payload_token = data.get('github_token', '').strip()
        save_token = bool(data.get('save_token', False))
        token_source = None
        resolved_token = None

        current_user, auth_error = _get_current_user(optional=True)
        if auth_error:
            message, status = auth_error
            return jsonify({'success': False, 'error': message}), status

        if payload_token:
            resolved_token = payload_token
            token_source = 'request'
        elif current_user and current_user.get('github_token_encrypted'):
            if fernet is None:
                return jsonify({'success': False, 'error': 'Token encryption is not configured'}), 503
            try:
                resolved_token = _decrypt_token(current_user['github_token_encrypted'])
                token_source = 'saved-user-token'
            except InvalidToken:
                return jsonify({'success': False, 'error': 'Stored GitHub token is unreadable. Please update your token.'}), 500

        if not resolved_token:
            return jsonify({
                'success': False,
                'error': 'GitHub access token is required. Provide github_token in the request or save one to your account.'
            }), 400

        # Optionally persist a newly provided token for authenticated users.
        if payload_token and current_user and save_token:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            users_collection.update_one(
                {'_id': current_user['_id']},
                {
                    '$set': {
                        'github_token_encrypted': _encrypt_token(payload_token),
                        'token_last_updated_at': now,
                        'updated_at': now,
                    }
                }
            )

        # STEP 2: Push to GitHub
        print("\nStep 2/3: Pushing to GitHub...")
        github_mgr = GitHubManager(token=resolved_token)
        github_result = github_mgr.create_and_push(
            user_description,
            files,
            branding=branding,
            structure_info=structure_info,
        )
        
        if not github_result['success']:
            return jsonify({
                'success': False,
                'error': f"GitHub error: {github_result['error']}"
            }), 500

        if current_user and users_collection is not None:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            history_entry = {
                'created_at': now,
                'description': user_description,
                'project_type': project_type,
                'repo_name': github_result.get('repo_name', ''),
                'repo_url': github_result.get('repo_url', ''),
                'file_count': len(files),
                'structure_type': structure_info.get('type', ''),
            }
            users_collection.update_one(
                {'_id': current_user['_id']},
                {
                    '$set': {'updated_at': now},
                    '$push': {
                        'generation_history': {
                            '$each': [history_entry],
                            '$slice': -30,
                        }
                    }
                }
            )
        
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
            'auth': {
                'authenticated': bool(current_user),
                'github_token_source': token_source,
                'token_saved': bool(payload_token and current_user and save_token)
            },
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
    print("  GET  /auth/profile - Authenticated profile with generation history")
    print("  POST /generate-and-push-to-github - Generate website and push to GitHub")
    app.run(debug=True, port=5000)