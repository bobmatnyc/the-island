#!/usr/bin/env python3
"""
Test OpenRouter GPT-4.5 Integration

This script validates that the OpenRouter API key and configuration work correctly.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# Add project root to path (tests/scripts -> tests -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
env_path = PROJECT_ROOT / ".env.local"
print(f"Loading environment from: {env_path}")

if not env_path.exists():
    print(f"ERROR: .env.local not found at {env_path}")
    print("Please create .env.local with your OPENROUTER_API_KEY")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# Get configuration
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.5-preview")

if not api_key:
    print("ERROR: OPENROUTER_API_KEY not set in .env.local")
    sys.exit(1)

print(f"✅ API key loaded: {api_key[:15]}...{api_key[-4:]}")
print(f"✅ Model: {model}")
print()

# Initialize OpenRouter client
print("Initializing OpenRouter client...")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)
print("✅ Client initialized")
print()

# Test query
test_message = "Hello! Can you confirm you're GPT-4.5 and briefly describe your capabilities?"

print("Sending test query...")
print(f"Query: {test_message}")
print()

try:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Respond concisely."
            },
            {
                "role": "user",
                "content": test_message
            }
        ],
        temperature=0.7,
        max_tokens=200,
        timeout=30.0
    )

    response = completion.choices[0].message.content.strip()

    print("✅ SUCCESS! OpenRouter API is working correctly.")
    print()
    print("Response from GPT-4.5:")
    print("-" * 70)
    print(response)
    print("-" * 70)
    print()

    # Print usage info if available
    if hasattr(completion, "usage"):
        usage = completion.usage
        print("Token Usage:")
        print(f"  Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")
    print()

    print("✅ All tests passed! OpenRouter integration is ready.")

except Exception as e:
    print("❌ ERROR: Failed to connect to OpenRouter API")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e!s}")
    print()
    print("Troubleshooting:")
    print("1. Check that your API key is correct")
    print("2. Verify you have internet connectivity")
    print("3. Ensure OpenRouter service is operational")
    print("4. Check if the model is available on your OpenRouter account")
    sys.exit(1)
