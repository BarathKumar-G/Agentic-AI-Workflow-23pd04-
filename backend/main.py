from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.workflows import router as workflows_router
from routes.runs import router as runs_router
from dotenv import load_dotenv
import os

# Load environment variables at startup - ensure we load from the correct path
load_dotenv('.env')

# Validate required environment variables
required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Validate Unbound API key
UNBOUND_API_KEY = os.getenv("UNBOUND_API_KEY")
if not UNBOUND_API_KEY or UNBOUND_API_KEY.strip() == "":
    raise ValueError("UNBOUND_API_KEY is required and cannot be empty. Set it in your .env file.")

app = FastAPI(title="Agentic Workflow Builder", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
app.include_router(runs_router, prefix="/runs", tags=["runs"])

@app.get("/")
async def root():
    return {"message": "Agentic Workflow Builder API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)