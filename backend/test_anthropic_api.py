#!/usr/bin/env python3
"""
Test script for Anthropic API authentication
This script mimics the successful curl command exactly
"""

import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY environment variable not found")
    exit(1)

print(f"Using API key starting with: {api_key[:10]}...")
print(f"API key length: {len(api_key)}")
print(f"Full API key: {api_key}")  # For debugging only, remove after debugging

# Set up headers exactly like the successful curl command
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

# Set up payload exactly like the successful curl command
payload = {
    "model": "claude-3-haiku-20240307",
    "messages": [{"role": "user", "content": "Hello, this is a test message."}],
    "max_tokens": 50
}

# Make the request
print("Making request to Anthropic API...")
try:
    with httpx.Client() as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30.0
        )
    
    # Print response status and headers for debugging
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
    
    # Check if request was successful
    if response.status_code == 200:
        print("API request successful!")
        response_data = response.json()
        print(f"Response content: {json.dumps(response_data, indent=2)}")
    else:
        print(f"API request failed: {response.status_code}")
        print(f"Response content: {response.text}")
        
except Exception as e:
    print(f"Error making request: {str(e)}")
