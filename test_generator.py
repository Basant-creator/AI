import requests
import json
import subprocess
import time
import sys

API_URL = 'http://localhost:5000'
server_process = None

def start_server():
    """Start the Flask server in the background"""
    global server_process
    print("Starting Flask server...")
    try:
        server_process = subprocess.Popen(
            [sys.executable, 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait for server to start
        time.sleep(3)
        print("✓ Server started (PID: {})".format(server_process.pid))
        return True
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        return False

def stop_server():
    """Stop the Flask server"""
    global server_process
    if server_process:
        print("\nStopping Flask server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✓ Server stopped")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("✓ Server stopped (forced)")

def test_health():
    """Test if server is running"""
    print("\n" + "="*60)
    print("TESTING SERVER HEALTH")
    print("="*60)
    try:
        response = requests.get(f'{API_URL}/health')
        print("✓ Server is running!")
        print("Response:", response.json())
    except Exception as e:
        print("✗ Server is not running!")
        print("Error:", str(e))
        print("\nMake sure to run 'python app.py' first!")
        return False
    return True

def test_vanilla_generation():
    """Test vanilla HTML/CSS/JS generation"""
    print("\n" + "="*60)
    print("TESTING VANILLA PROJECT GENERATION")
    print("="*60)
    
    payload = {
        'description': 'Create a simple todo list app with add, delete, and mark as complete features',
        'type': 'vanilla'
    }
    
    print(f"Sending request: {payload['description']}")
    print("Waiting for AI response (this may take 10-30 seconds)...")
    
    try:
        response = requests.post(f'{API_URL}/generate-website', json=payload)
        result = response.json()
        
        if result['success']:
            print(f"\n✓ Successfully generated {result['file_count']} files")
            print(f"✓ Project type: {result['project_type']}")
            print("\nGenerated files:")
            for filename in result['files'].keys():
                print(f"  - {filename} ({len(result['files'][filename])} characters)")
            
            # Show preview of index.html
            if 'index.html' in result['files']:
                print(f"\nPreview of index.html (first 400 characters):")
                print("-" * 60)
                print(result['files']['index.html'][:400] + "...")
                print("-" * 60)
        else:
            print(f"\n✗ Error: {result['error']}")
    
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")

def test_react_generation():
    """Test React project generation"""
    print("\n" + "="*60)
    print("TESTING REACT PROJECT GENERATION")
    print("="*60)
    
    payload = {
        'description': 'Create a weather app that shows current weather with a nice UI',
        'type': 'react'
    }
    
    print(f"Sending request: {payload['description']}")
    print("Waiting for AI response (this may take 10-30 seconds)...")
    
    try:
        response = requests.post(f'{API_URL}/generate-website', json=payload)
        result = response.json()
        
        if result['success']:
            print(f"\n✓ Successfully generated {result['file_count']} files")
            print(f"✓ Project type: {result['project_type']}")
            print("\nGenerated files:")
            for filename in result['files'].keys():
                print(f"  - {filename} ({len(result['files'][filename])} characters)")
            
            # Show package.json if exists
            if 'package.json' in result['files']:
                print("\npackage.json content:")
                print("-" * 60)
                print(result['files']['package.json'])
                print("-" * 60)
        else:
            print(f"\n✗ Error: {result['error']}")
    
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")

def save_generated_files_test():
    """Generate and save files to disk"""
    print("\n" + "="*60)
    print("GENERATE AND SAVE FILES TEST")
    print("="*60)
    
    payload = {
        'description': 'Create a simple landing page for a coffee shop',
        'type': 'vanilla'
    }
    
    print(f"Generating: {payload['description']}")
    
    try:
        response = requests.post(f'{API_URL}/generate-website', json=payload)
        result = response.json()
        
        if result['success']:
            import os
            
            # Create output directory
            output_dir = 'test_output'
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"\nSaving {result['file_count']} files to '{output_dir}/' folder...")
            
            for filename, content in result['files'].items():
                filepath = os.path.join(output_dir, filename)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ Saved: {filepath}")
            
            print(f"\n✓ All files saved! Check the '{output_dir}' folder")
            print(f"✓ You can open index.html in a browser to see the website")
        else:
            print(f"\n✗ Error: {result['error']}")
    
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")
def test_github_push():
    """Test complete workflow: Generate and push to GitHub"""
    print("\n" + "="*60)
    print("TEST: GENERATE AND PUSH TO GITHUB")
    print("="*60)
    
    payload = {
        'description': 'Create a modern landing page for a coffee shop with menu',
        'type': 'vanilla'
    }
    
    print(f"Sending request: {payload['description']}")
    print("This will:")
    print("  1. Generate website with AI")
    print("  2. Create GitHub repository")
    print("  3. Push all files to GitHub")
    print("\nWaiting for response (may take 30-60 seconds)...\n")
    
    try:
        response = requests.post(f'{API_URL}/generate-and-push-to-github', json=payload)
        result = response.json()
        
        if result['success']:
            print(f"\n{'='*60}")
            print("SUCCESS! ✓")
            print(f"{'='*60}")
            print(f"\nProject Type: {result['project_type']}")
            print(f"Files Generated: {result['file_count']}")
            
            print(f"\nGenerated Files:")
            for filename in result['files'].keys():
                print(f"  - {filename}")
            
            print(f"\nGitHub Repository:")
            print(f"  Name: {result['github']['repo_name']}")
            print(f"  Owner: {result['github']['username']}")
            print(f"  URL: {result['github']['repo_url']}")
            
            print(f"\n{'='*60}")
            print("🎉 Your website is now on GitHub!")
            print(f"Visit: {result['github']['repo_url']}")
            print(f"{'='*60}\n")
        else:
            print(f"\n✗ Error: {result['error']}")
    
    except Exception as e:
        print(f"\n✗ Request failed: {str(e)}")
def test_customized_generation():
    """Test generation with full customization - branding and social media"""
    print("\n" + "="*60)
    print("TEST: CUSTOMIZED WEBSITE WITH BRANDING & SOCIAL MEDIA")
    print("="*60)
    
    payload = {
        'description': 'Create a modern landing page for a coffee shop with menu and about section',
        'type': 'vanilla',
        
        # Branding customization
        'company_name': 'Bean Haven Coffee',
        'tagline': 'Crafted with Love, Served with Passion ☕',
        'primary_color': '#8B4513',      # Coffee brown
        'secondary_color': '#D2691E',    # Chocolate brown
        
        # Social media
        'instagram': 'beanhavencoffee',
        'twitter': 'beanhavencafe',
        'facebook': 'beanhavencoffee',
        'linkedin': 'bean-haven-coffee',
        
        # Contact information
        'email': 'hello@beanhaven.com',
        'phone': '+1-555-BEAN-CAFE',
        'address': '123 Coffee Street',
        'city': 'Seattle',
        'state': 'WA',
        'zip': '98101',
        'country': 'USA'
    }
    
    print("\n📋 Generating customized website with:")
    print(f"   Company: {payload['company_name']}")
    print(f"   Tagline: {payload['tagline']}")
    print(f"   Primary Color: {payload['primary_color']} (Coffee Brown)")
    print(f"   Secondary Color: {payload['secondary_color']} (Chocolate)")
    print(f"   Social Media: Instagram, Twitter, Facebook, LinkedIn")
    print(f"   Contact: Email, Phone, Full Address")
    
    print("\n⏳ This may take 60-90 seconds...")
    print("   Step 1: Generating customized code with AI")
    print("   Step 2: Creating GitHub repository")
    print("   Step 3: Pushing files to GitHub\n")
    
    try:
        response = requests.post(f'{API_URL}/generate-and-push-to-github', json=payload)
        result = response.json()
        
        if result['success']:
            print(f"\n{'='*60}")
            print("✅ SUCCESS! CUSTOMIZED WEBSITE CREATED")
            print(f"{'='*60}")
            
            print(f"\n📁 Files Generated: {result['file_count']}")
            for filename in result['files'].keys():
                print(f"   - {filename}")
            
            print(f"\n🎨 Customization Applied:")
            print(f"   ✓ Company Name: {result['customization']['branding']['company_name']}")
            print(f"   ✓ Brand Colors: {result['customization']['branding']['primary_color']}, {result['customization']['branding']['secondary_color']}")
            
            if result['customization']['social_media']:
                print(f"   ✓ Social Media: {len(result['customization']['social_media'])} platforms connected")
                for platform, username in result['customization']['social_media'].items():
                    print(f"      - {platform.capitalize()}: {username}")
            
            if result['customization']['contact']:
                print(f"   ✓ Contact Info: {len(result['customization']['contact'])} fields")
            
            print(f"\n🔗 GitHub Repository:")
            print(f"   Name: {result['github']['repo_name']}")
            print(f"   Owner: {result['github']['username']}")
            print(f"   URL: {result['github']['repo_url']}")
            
            print(f"\n{'='*60}")
            print("🎉 Your customized website is now on GitHub!")
            print(f"🌐 Visit: {result['github']['repo_url']}")
            print(f"{'='*60}\n")
            
            print("💡 Next: Check the generated files to see:")
            print("   - 'Bean Haven Coffee' used throughout")
            print("   - Brown/chocolate color scheme")
            print("   - Social media links in footer")
            print("   - Contact information section\n")
            
        else:
            print(f"\n{'='*60}")
            print(f"❌ ERROR")
            print(f"{'='*60}")
            print(f"Error: {result['error']}\n")
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ REQUEST FAILED")
        print(f"{'='*60}")
        print(f"Error: {str(e)}\n")
def test_multipage_website():
    """Test multi-page website generation"""
    print("\n" + "="*60)
    print("TEST: MULTI-PAGE WEBSITE")
    print("="*60)
    
    payload = {
        'description': 'Create a professional website for a law firm with about, services, team, and contact pages',
        'type': 'vanilla',
        'company_name': 'Smith & Associates Law',
        'primary_color': '#1a1a2e',
        'secondary_color': '#16213e',
        'email': 'info@smithlaw.com',
        'phone': '+1-555-LAW-FIRM'
    }
    
    print("\n📄 Expecting multi-page structure with navigation")
    print("⏳ Generating...\n")
    
    response = requests.post(f'{API_URL}/generate-and-push-to-github', json=payload)
    result = response.json()
    
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"Structure: {result['structure']['type']}")
        print(f"Files: {result['structure']['files_count']}")
        print(f"GitHub: {result['github']['repo_url']}\n")
    else:
        print(f"\n❌ Error: {result.get('error')}")


def test_webapp_with_auth():
    """Test full-stack web app with authentication"""
    print("\n" + "="*60)
    print("TEST: WEB APP WITH AUTHENTICATION")
    print("="*60)
    
    payload = {
        'description': 'Create a task management web application with user authentication, login, signup, and dashboard where users can create and manage tasks',
        'type': 'vanilla',
        'company_name': 'TaskMaster Pro',
        'primary_color': '#6366f1',
        'secondary_color': '#8b5cf6'
    }
    
    print("\n🔐 Expecting full-stack app with:")
    print("  - Login/Signup pages")
    print("  - Protected dashboard")
    print("  - Express.js backend")
    print("  - Database schema")
    print("⏳ This may take 90-120 seconds...\n")
    
    response = requests.post(f'{API_URL}/generate-and-push-to-github', json=payload)
    result = response.json()
    
    if result['success']:
        print(f"\n✅ SUCCESS! FULL-STACK APP GENERATED")
        print(f"Structure: {result['structure']['description']}")
        print(f"Files: {result['structure']['files_count']}")
        print(f"Backend: {result['structure']['has_backend']}")
        print(f"Database: {result['structure']['has_database']}")
        print(f"\nGitHub: {result['github']['repo_url']}")
        print(f"\n💡 Check the repo - it has frontend + backend code!")
        print(f"   Follow README.md for setup instructions\n")
    else:
        print(f"\n❌ Error: {result.get('error')}")


def test_ecommerce_site():
    """Test e-commerce website generation"""
    print("\n" + "="*60)
    print("TEST: E-COMMERCE WEBSITE")
    print("="*60)
    
    payload = {
        'description': 'Create an online store for selling handmade jewelry with product catalog, shopping cart, and checkout',
        'type': 'vanilla',
        'company_name': 'Artisan Jewelry Co',
        'primary_color': '#d4af37',
        'secondary_color': '#c9a958',
        'instagram': 'artisanjewelry',
        'email': 'shop@artisanjewelry.com'
    }
    
    print("\n🛍️ Expecting e-commerce structure with:")
    print("  - Product pages")
    print("  - Shopping cart")
    print("  - Checkout flow")
    print("⏳ Generating...\n")
    
    response = requests.post(f'{API_URL}/generate-and-push-to-github', json=payload)
    result = response.json()
    
    if result['success']:
        print(f"\n✅ E-COMMERCE SITE GENERATED!")
        print(f"Files: {result['structure']['files_count']}")
        print(f"GitHub: {result['github']['repo_url']}\n")
    else:
        print(f"\n❌ Error: {result.get('error')}")
if __name__ == '__main__':
    print("="*60)
    print("AI WEBSITE GENERATOR - TEST SUITE")
    print("="*60)
    
    # First check if server is running
    if not test_health():
        exit(1)
    
    print("\n" + "="*60)
    print("Choose test to run:")
    print("1. Test Vanilla HTML/CSS/JS Generation")
    print("2. Test React Generation")
    print("3. Test Both")
    print("4. Generate and Save Files to Disk")
    print("5. Generate and Push to GitHub")
    print("6. Customized Generation")
    print("7. 🆕 Multi-Page Website")
    print("8. 🆕 Web App with Authentication")
    print("9. 🆕 E-Commerce Site")
    print("="*60)
    
    choice = input("\nEnter choice (1/2/3/4/5/6/7/8/9): ").strip()
    
    if choice == '1':
        test_vanilla_generation()
    elif choice == '2':
        test_react_generation()
    elif choice == '3':
        test_vanilla_generation()
        test_react_generation()
    elif choice == '4':
        save_generated_files_test()
    elif choice == '5':
        test_github_push()
    elif choice == '6':
        test_customized_generation()  # NEW!
    elif choice == '7':
        test_multipage_website()
    elif choice == '8':
        test_webapp_with_auth()
    elif choice == '9':
        test_ecommerce_site()
    else:
        print("Invalid choice")