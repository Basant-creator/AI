import os
from dotenv import load_dotenv
from google import genai

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
    client = genai.Client(api_key=api_key)
    print("\n✓ API configured successfully")
    
    # List available models
    print("\nAvailable Gemini Models:")
    for model in client.models.list():
        if 'generateContent' in model.supported_actions:
            print(f"  - {model.name}")
    
    # Try a simple generation
    print("\nTesting model...")
    response = client.models.generate_content(model='gemini-2.5-flash', contents='Say hello!')
    print(f"✓ Test successful! Response: {response.text}")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. API key doesn't have permissions")
    print("3. Outdated google-genai library")