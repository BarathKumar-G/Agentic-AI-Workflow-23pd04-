from fastapi import APIRouter, HTTPException
from models.schemas import Run, LogEntry
from services.supabase_client import get_run

router = APIRouter()

@router.get("/{run_id}", response_model=Run)
async def get_run_endpoint(run_id: str):
    """Get run by ID with logs"""
    try:
        run_data = get_run(run_id)
        
        # Parse logs
        logs = []
        if run_data["logs"]:
            for log_data in run_data["logs"]:
                logs.append(LogEntry(**log_data))
        
        return Run(
            id=run_data["id"],
            workflow_id=run_data["workflow_id"],
            status=run_data["status"],
            logs=logs,
            created_at=run_data["created_at"]
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=500, detail=f"Error fetching run: {str(e)}")