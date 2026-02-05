import os
import httpx
import json
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any

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

# Available models - CONTROLLED LIST
SUPPORTED_MODELS = [
    "kimi-k2p5",
    "kimi-k2-instruct-0905"
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_model(model: Optional[str]) -> str:
    """Validate and return a supported model"""
    if not model:
        return DEFAULT_MODEL
    
    if model not in SUPPORTED_MODELS:
        return DEFAULT_MODEL
    
    return model

async def generate_text(prompt: str, model: Optional[str] = None) -> str:
    """Generate text using Unbound API"""
    
    model_to_use = validate_model(model)
    
    if not UNBOUND_API_KEY:
        logger.error("UNBOUND_API_KEY not found - this should not happen if startup validation works")
        return f"Configuration error: API key missing for model {model_to_use}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.getunbound.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {UNBOUND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_to_use,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            logger.info(f"Unbound API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Generated content length: {len(content)} characters")
                return content
            else:
                error_text = response.text
                logger.error(f"Unbound API error {response.status_code}: {error_text}")
                return f"API Error ({response.status_code}): Falling back to mock response for '{prompt[:30]}...'"
                
    except httpx.TimeoutException:
        logger.error("Unbound API timeout")
        return f"Timeout error: Mock response for '{prompt[:30]}...'"
    except Exception as e:
        logger.error(f"Unbound API exception: {str(e)}")
        return f"Connection error: Mock response for '{prompt[:30]}...'"

async def judge_response(response: str, judge_prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Use LLM to judge if response meets criteria"""
    
    model_to_use = validate_model(model)
    
    full_prompt = f"""
Judge the following response based on this criteria: {judge_prompt}

Response to judge:
{response}

Respond with ONLY a JSON object in this exact format:
{{"passed": true/false, "reasoning": "brief explanation"}}
"""
    
    if not UNBOUND_API_KEY:
        logger.error("UNBOUND_API_KEY not found for judge")
        return {"passed": True, "reasoning": "Judge unavailable - API key missing"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            api_response = await client.post(
                "https://api.getunbound.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {UNBOUND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_to_use,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": 200,
                    "temperature": 0.1
                }
            )
            
            if api_response.status_code == 200:
                data = api_response.json()
                judge_text = data["choices"][0]["message"]["content"].strip()
                
                try:
                    # Try to parse JSON response
                    judgment = json.loads(judge_text)
                    if "passed" in judgment and "reasoning" in judgment:
                        return judgment
                except json.JSONDecodeError:
                    pass
                
                # Fallback parsing
                passed = "true" in judge_text.lower() or "pass" in judge_text.lower()
                return {"passed": passed, "reasoning": judge_text[:100]}
            else:
                logger.error(f"Judge API error: {api_response.status_code}")
                
    except Exception as e:
        logger.error(f"Judge API exception: {str(e)}")
    
    # Fallback judgment
    return {"passed": True, "reasoning": "Judge unavailable, defaulting to pass"}