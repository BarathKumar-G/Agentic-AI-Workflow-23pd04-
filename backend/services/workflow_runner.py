import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.supabase_client import (
    get_workflow_with_steps, 
    update_run_logs
)
from services.unbound_client import generate_text

class WorkflowRunner:
    def __init__(self, run_id: str, workflow_id: str):
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.logs: List[Dict[str, Any]] = []
    
    async def execute(self) -> bool:
        """Execute workflow and return success status"""
        try:
            # Update run status to running
            await self._update_run_status("running")
            
            # Get workflow with steps
            workflow_data = get_workflow_with_steps(self.workflow_id)
            steps = workflow_data.get("steps", [])
            
            if not steps:
                await self._update_run_status("failed")
                return False
            
            # Sort steps by step_order
            steps.sort(key=lambda x: x["step_order"])
            
            # Execute steps sequentially
            previous_output = ""
            
            for step in steps:
                success = await self._execute_step(step, previous_output)
                if not success:
                    await self._update_run_status("failed")
                    return False
                
                # Get the output from the last log entry for context
                if self.logs:
                    previous_output = self.logs[-1]["response"]
            
            # Mark as completed
            await self._update_run_status("completed")
            return True
            
        except Exception as e:
            await self._update_run_status("failed")
            return False
    
    async def _execute_step(self, step: Dict[str, Any], previous_output: str) -> bool:
        """Execute a single step with retries"""
        max_retries = 2
        
        for retry in range(max_retries + 1):
            try:
                # Inject context into prompt
                prompt = self._inject_context(
                    step["prompt"], 
                    previous_output, 
                    step.get("context_strategy", "auto")
                )
                
                # Call LLM
                response = await generate_text(prompt, step.get("model"))
                
                # Validate response
                passed = self._validate_response(response, step.get("completion_rule"))
                
                # Log the attempt
                log_entry = {
                    "step": step["step_order"],
                    "prompt": prompt,
                    "response": response,
                    "passed": passed,
                    "retries": retry,
                    "timestamp": datetime.now(),
                    "model_used": step.get("model")
                }
                
                self.logs.append(log_entry)
                await self._save_logs()
                
                if passed:
                    return True
                
                if retry == max_retries:
                    return False
                    
            except Exception as e:
                log_entry = {
                    "step": step["step_order"],
                    "prompt": step["prompt"],
                    "response": f"Error: {str(e)}",
                    "passed": False,
                    "retries": retry,
                    "timestamp": datetime.now(),
                    "model_used": step.get("model")
                }
                
                self.logs.append(log_entry)
                await self._save_logs()
                
                if retry == max_retries:
                    return False
        
        return False
    
    def _inject_context(self, prompt: str, previous_output: str, strategy: Optional[str]) -> str:
        """Inject context from previous step based on strategy"""
        if not previous_output or not strategy:
            return prompt
        
        context = previous_output
        
        if strategy == "summary" and len(previous_output) > 200:
            # Simple summarization - take first 100 chars
            context = previous_output[:100] + "..."
        elif strategy == "extract":
            # Try to extract structured content (JSON, lists, etc.)
            try:
                # Look for JSON
                if "{" in previous_output and "}" in previous_output:
                    start = previous_output.find("{")
                    end = previous_output.rfind("}") + 1
                    context = previous_output[start:end]
                # Look for lists
                elif "•" in previous_output or "-" in previous_output:
                    lines = previous_output.split("\n")
                    context = "\n".join([line for line in lines if "•" in line or line.strip().startswith("-")])
            except:
                pass  # Fall back to full context
        elif strategy == "auto":
            # Auto-detect: if long text, summarize; if structured, extract
            if len(previous_output) > 300:
                context = previous_output[:150] + "..."
            elif any(char in previous_output for char in ["{", "[", "•", "-"]):
                # Looks structured, keep as is
                pass
        
        # Replace placeholder in prompt
        return prompt.replace("{{previous}}", context)
    
    def _validate_response(self, response: str, completion_rule: Optional[str]) -> bool:
        """Validate response against completion rule"""
        if not completion_rule:
            return True
        
        try:
            # Try as regex first
            if re.search(completion_rule, response, re.IGNORECASE):
                return True
        except re.error:
            # Fall back to substring match
            if completion_rule.lower() in response.lower():
                return True
        
        return False
    
    async def _save_logs(self):
        """Save current logs to database"""
        update_run_logs(self.run_id, self.logs, "running")
    
    async def _update_run_status(self, status: str):
        """Update run status in database"""
        update_run_logs(self.run_id, self.logs, status)