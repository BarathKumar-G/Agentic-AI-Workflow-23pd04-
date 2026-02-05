import os
import httpx
from dotenv import load_dotenv
from typing import Optional

# Load environment variables - try multiple paths
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # backend/.env
    '.env',  # root .env
    'backend/.env'  # from root
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
else:
    load_dotenv()  # fallback to default behavior

UNBOUND_API_KEY = os.getenv("UNBOUND_API_KEY")
DEFAULT_MODEL = "kimi-k2p5"

# Available models
SUPPORTED_MODELS = [
    "kimi-k2p5",
    "kimi-k2-instruct-0905"
]

async def generate_text(prompt: str, model: Optional[str] = None) -> str:
    """Generate text using Unbound API or return mock response"""
    
    model_to_use = model or DEFAULT_MODEL
    
    # Validate model
    if model_to_use not in SUPPORTED_MODELS:
        model_to_use = DEFAULT_MODEL
    
    if not UNBOUND_API_KEY:
        # Return deterministic mock response for demo
        mock_responses = {
            "blog topic": "The Future of AI in Healthcare: Transforming Patient Care Through Innovation",
            "intro": "Artificial intelligence is revolutionizing healthcare by enabling faster diagnoses, personalized treatments, and improved patient outcomes. From machine learning algorithms that detect diseases early to AI-powered surgical robots, technology is transforming how medical professionals deliver care. This transformation promises to make healthcare more accessible, efficient, and effective for patients worldwide, creating unprecedented opportunities for better health outcomes.",
            "summary": "This content discusses AI's transformative impact on healthcare, covering diagnosis improvements, treatment personalization, and enhanced patient care delivery.",
            "analysis": "The text demonstrates strong technical understanding with practical applications and clear benefits outlined for healthcare transformation.",
            "generate": f"Generated content for: {prompt[:30]}... This is a mock response demonstrating the workflow execution with model {model_to_use}."
        }
        
        # Simple keyword matching for demo
        prompt_lower = prompt.lower()
        for key, response in mock_responses.items():
            if key in prompt_lower:
                return response
        
        return f"Mock response for prompt: {prompt[:50]}... (using model: {model_to_use})"
    
    # Real Unbound API call
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.getunbound.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {UNBOUND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_to_use,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                # Fallback to mock on API error
                return f"API Error ({response.status_code}), using mock: Generated content for '{prompt[:30]}...'"
                
    except Exception as e:
        # Fallback to mock on any error
        return f"Connection error, using mock: Generated content for '{prompt[:30]}...'"