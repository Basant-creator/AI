import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Check if API key is loaded
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
else:
    print("✗ API Key NOT found!")
    print("Make sure your .env file has: GEMINI_API_KEY=your_key_here")
    exit(1)

# Try to configure and list models
try:
    genai.configure(api_key=api_key)
    print("\n✓ API configured successfully")
    
    # List available models
    print("\nAvailable models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    # Try a simple generation
    print("\nTesting model...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say hello!")
    print(f"✓ Test successful! Response: {response.text}")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. API key doesn't have permissions")
    print("3. Outdated google-generativeai library")