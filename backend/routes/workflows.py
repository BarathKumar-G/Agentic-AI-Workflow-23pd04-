from fastapi import APIRouter, HTTPException
from typing import List
import traceback
from models.schemas import Workflow, WorkflowCreate, Run
from services.supabase_client import (
    create_workflow, create_steps, get_workflows, 
    get_workflow_with_steps, create_run, get_runs_by_workflow
)
from services.unbound_client import SUPPORTED_MODELS, validate_model
from services.workflow_runner import WorkflowRunner
import asyncio

router = APIRouter()

@router.delete("/{workflow_id}")
async def delete_workflow_endpoint(workflow_id: str):
    """Delete workflow and all associated data"""
    try:
        from services.supabase_client import delete_workflow
        delete_workflow(workflow_id)
        return {"message": "Workflow deleted successfully"}
    except Exception as e:
        if "not found" in str(e).lower():
            return {"message": "Workflow not found or already deleted"}
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")

@router.get("/models/supported")
async def get_supported_models():
    """Get list of supported models"""
    return {"models": SUPPORTED_MODELS, "default": "openrouter/free"}

@router.post("/", response_model=Workflow)
async def create_workflow_endpoint(workflow: WorkflowCreate):
    """Create a new workflow with steps"""
    try:
        # Validate models in steps
        for step in workflow.steps:
            if step.model and step.model not in SUPPORTED_MODELS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Model '{step.model}' not supported. Allowed models: {SUPPORTED_MODELS}"
                )
        
        # Create workflow
        workflow_data = create_workflow(workflow.name)
        workflow_id = workflow_data["id"]
        
        # Create steps with validated models
        steps_data = []
        for step in workflow.steps:
            steps_data.append({
                "step_order": step.step_order,
                "model": validate_model(step.model),
                "prompt": step.prompt,
                "completion_rule": step.completion_rule,
                "context_strategy": step.context_strategy
            })
        
        if steps_data:
            create_steps(workflow_id, steps_data)
        
        # Return created workflow with steps
        return await get_workflow_endpoint(workflow_id)
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

@router.get("/", response_model=List[Workflow])
async def get_workflows_endpoint():
    """Get all workflows"""
    try:
        workflows_data = get_workflows()
        
        workflows = []
        for row in workflows_data:
            workflows.append(Workflow(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"]
            ))
        
        return workflows
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching workflows: {str(e)}")

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow_endpoint(workflow_id: str):
    """Get workflow by ID with steps"""
    try:
        workflow_data = get_workflow_with_steps(workflow_id)
        
        from models.schemas import Step
        steps = []
        for step_row in workflow_data.get("steps", []):
            steps.append(Step(
                id=step_row["id"],
                workflow_id=step_row["workflow_id"],
                step_order=step_row["step_order"],
                model=step_row["model"],
                prompt=step_row["prompt"],
                completion_rule=step_row["completion_rule"],
                context_strategy=step_row["context_strategy"]
            ))
        
        return Workflow(
            id=workflow_data["id"],
            name=workflow_data["name"],
            created_at=workflow_data["created_at"],
            steps=steps
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Workflow not found")
        raise HTTPException(status_code=500, detail=f"Error fetching workflow: {str(e)}")

@router.post("/{workflow_id}/run", response_model=Run)
async def run_workflow_endpoint(workflow_id: str):
    """Start workflow execution"""
    try:
        # Verify workflow exists
        try:
            get_workflow_with_steps(workflow_id)
        except:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Create run record
        run_data = create_run(workflow_id)
        run_id = run_data["id"]
        
        # Start workflow execution in background
        runner = WorkflowRunner(run_id, workflow_id)
        asyncio.create_task(runner.execute())
        
        # Return run info
        return Run(
            id=run_id,
            workflow_id=workflow_id,
            status="pending",
            logs=[],
            created_at=run_data["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting workflow run: {str(e)}")

@router.get("/{workflow_id}/runs", response_model=List[Run])
async def get_workflow_runs_endpoint(workflow_id: str):
    """Get all runs for a workflow"""
    try:
        runs_data = get_runs_by_workflow(workflow_id)
        
        runs = []
        for row in runs_data:
            from models.schemas import LogEntry
            logs = []
            if row["logs"]:
                for log_data in row["logs"]:
                    logs.append(LogEntry(**log_data))
            
            runs.append(Run(
                id=row["id"],
                workflow_id=row["workflow_id"],
                status=row["status"],
                logs=logs,
                created_at=row["created_at"]
            ))
        
        return runs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching workflow runs: {str(e)}")