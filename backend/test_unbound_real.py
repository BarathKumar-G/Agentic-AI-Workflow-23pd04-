#!/usr/bin/env python3
"""
Real Unbound API test script
Tests both supported models with real API calls
"""

import asyncio
import sys
import os
sys.path.append('.')

from services.unbound_client import generate_text, SUPPORTED_MODELS
from dotenv import load_dotenv

async def test_real_unbound():
    print("🧪 Testing Real Unbound API Integration")
    print("=" * 50)
    
    # Load environment
    load_dotenv('.env')
    
    # Check API key
    api_key = os.getenv("UNBOUND_API_KEY")
    if not api_key:
        print("❌ UNBOUND_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    test_prompts = [
        "Generate a short essay about AI in 50 words.",
        "Write a simple Python function that adds two numbers."
    ]
    
    all_tests_passed = True
    
    for model in SUPPORTED_MODELS:
        print(f"\n🤖 Testing model: {model}")
        print("-" * 30)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\nTest {i}: {prompt}")
            
            try:
                response = await generate_text(prompt, model)
                
                # Validation checks
                is_mock = any(keyword in response.lower() for keyword in [
                    "mock response", "connection error", "api error", "timeout error"
                ])
                
                is_valid_length = len(response) > 20
                
                print(f"Response length: {len(response)} characters")
                print(f"Response preview: {response[:100]}...")
                
                if is_mock:
                    print("❌ FAILED: Response appears to be mock/error")
                    all_tests_passed = False
                elif not is_valid_length:
                    print("❌ FAILED: Response too short")
                    all_tests_passed = False
                else:
                    print("✅ PASSED: Real AI response received")
                    
            except Exception as e:
                print(f"❌ FAILED: Exception occurred: {e}")
                all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All Unbound API tests PASSED!")
        print("✅ Real AI responses confirmed for both models")
    else:
        print("❌ Some tests FAILED!")
        print("⚠️  Check API key, network connection, or API endpoint")
    
    return all_tests_passed

if __name__ == "__main__":
    result = asyncio.run(test_real_unbound())
    sys.exit(0 if result else 1)