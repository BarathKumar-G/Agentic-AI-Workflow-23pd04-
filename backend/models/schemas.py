from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
import uuid

class StepCreate(BaseModel):
    step_order: int
    model: Optional[str] = None
    prompt: str
    completion_rule: Optional[str] = None
    context_strategy: Optional[str] = "auto"

class Step(BaseModel):
    id: str
    workflow_id: str
    step_order: int
    model: Optional[str]
    prompt: str
    completion_rule: Optional[str]
    context_strategy: Optional[str]

class WorkflowCreate(BaseModel):
    name: str
    steps: List[StepCreate]

class Workflow(BaseModel):
    id: str
    name: str
    created_at: datetime
    steps: Optional[List[Step]] = None

class LogEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    step: int
    prompt: str
    response: str
    passed: bool
    retries: int
    timestamp: datetime
    model_used: Optional[str] = None

class Run(BaseModel):
    id: str
    workflow_id: str
    status: str
    logs: Optional[List[LogEntry]] = None
    created_at: datetime

class RunCreate(BaseModel):
    pass  # No body needed for run creation