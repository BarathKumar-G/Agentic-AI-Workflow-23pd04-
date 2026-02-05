import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime

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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(f"SUPABASE_URL and SUPABASE_KEY must be set in environment variables. Current URL: {SUPABASE_URL}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_workflow(name: str) -> Dict[str, Any]:
    """Create a new workflow"""
    result = supabase.table("workflows").insert({"name": name}).execute()
    if not result.data:
        raise Exception("Failed to create workflow")
    return result.data[0]

def create_steps(workflow_id: str, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create steps for a workflow"""
    steps_data = []
    for step in steps:
        steps_data.append({
            "workflow_id": workflow_id,
            "step_order": step["step_order"],
            "model": step.get("model"),
            "prompt": step["prompt"],
            "completion_rule": step.get("completion_rule"),
            "context_strategy": step.get("context_strategy", "auto")
        })
    
    result = supabase.table("steps").insert(steps_data).execute()
    return result.data

def get_workflows() -> List[Dict[str, Any]]:
    """Get all workflows"""
    result = supabase.table("workflows").select("*").order("created_at", desc=True).execute()
    return result.data

def get_workflow_with_steps(workflow_id: str) -> Dict[str, Any]:
    """Get workflow with its steps"""
    # Get workflow
    workflow_result = supabase.table("workflows").select("*").eq("id", workflow_id).execute()
    if not workflow_result.data:
        raise Exception("Workflow not found")
    
    workflow = workflow_result.data[0]
    
    # Get steps
    steps_result = supabase.table("steps").select("*").eq("workflow_id", workflow_id).order("step_order").execute()
    workflow["steps"] = steps_result.data
    
    return workflow

def create_run(workflow_id: str) -> Dict[str, Any]:
    """Create a new run"""
    result = supabase.table("runs").insert({
        "workflow_id": workflow_id,
        "status": "pending",
        "logs": [],
        "created_at": datetime.now().isoformat()
    }).execute()
    if not result.data:
        raise Exception("Failed to create run")
    return result.data[0]

def update_run_logs(run_id: str, logs: List[Dict[str, Any]], status: str):
    """Update run logs and status"""
    # Convert datetime objects to ISO strings
    processed_logs = []
    for log in logs:
        log_copy = log.copy()
        if isinstance(log_copy.get('timestamp'), datetime):
            log_copy['timestamp'] = log_copy['timestamp'].isoformat()
        processed_logs.append(log_copy)
    
    supabase.table("runs").update({
        "logs": processed_logs,
        "status": status
    }).eq("id", run_id).execute()

def get_run(run_id: str) -> Dict[str, Any]:
    """Get run by ID"""
    result = supabase.table("runs").select("*").eq("id", run_id).execute()
    if not result.data:
        raise Exception("Run not found")
    return result.data[0]

def get_runs_by_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """Get all runs for a workflow"""
    result = supabase.table("runs").select("*").eq("workflow_id", workflow_id).order("created_at", desc=True).execute()
    return result.data

def delete_workflow(workflow_id: str):
    """Delete workflow and cascade delete steps and runs"""
    # Delete runs first
    supabase.table("runs").delete().eq("workflow_id", workflow_id).execute()
    
    # Delete steps
    supabase.table("steps").delete().eq("workflow_id", workflow_id).execute()
    
    # Delete workflow
    result = supabase.table("workflows").delete().eq("id", workflow_id).execute()
    
    if not result.data:
        raise Exception("Workflow not found")