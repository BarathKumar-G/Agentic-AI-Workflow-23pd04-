import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.supabase_client import (
    get_workflow_with_steps, 
    update_run_logs
)
from services.unbound_client import generate_text, judge_response, validate_model

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
                # Validate and set model
                model = validate_model(step.get("model"))
                
                # Inject context into prompt
                prompt = self._inject_context(
                    step["prompt"], 
                    previous_output, 
                    step.get("context_strategy", "auto")
                )
                
                # Call LLM
                response = await generate_text(prompt, model)
                
                # Validate response using intelligent completion criteria
                validation_result = await self._validate_response_intelligent(
                    response, 
                    step.get("completion_rule"),
                    model
                )
                
                passed = validation_result["passed"]
                reasoning = validation_result.get("reasoning", "")
                
                # Log the attempt
                log_entry = {
                    "step": step["step_order"],
                    "prompt": prompt,
                    "response": response,
                    "passed": passed,
                    "retries": retry,
                    "timestamp": datetime.now(),
                    "model_used": model,
                    "validation_reasoning": reasoning
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
                    "model_used": step.get("model"),
                    "validation_reasoning": f"Execution error: {str(e)}"
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
    
    async def _validate_response_intelligent(self, response: str, completion_rule: Optional[str], model: str) -> Dict[str, Any]:
        """Intelligent validation using multiple modes"""
        if not completion_rule:
            return {"passed": True, "reasoning": "No validation rule specified"}
        
        try:
            # Try to parse as JSON completion rule
            rule_data = json.loads(completion_rule)
            rule_type = rule_data.get("type", "simple")
            
            if rule_type == "simple":
                # Mode A: Simple string/regex match
                rule_value = rule_data.get("rule", "")
                return self._validate_simple(response, rule_value)
                
            elif rule_type == "json":
                # Mode B: JSON structure validation
                schema = rule_data.get("schema", {})
                return self._validate_json_structure(response, schema)
                
            elif rule_type == "judge":
                # Mode C: LLM-based judge
                judge_prompt = rule_data.get("prompt", "")
                return await self._validate_with_judge(response, judge_prompt, model)
                
        except json.JSONDecodeError:
            # Fallback to simple string match for backward compatibility
            return self._validate_simple(response, completion_rule)
        
        return {"passed": False, "reasoning": "Invalid completion rule format"}
    
    def _validate_simple(self, response: str, rule: str) -> Dict[str, Any]:
        """Mode A: Simple string or regex validation"""
        if not rule:
            return {"passed": True, "reasoning": "No rule specified"}
        
        try:
            # Try as regex first
            if re.search(rule, response, re.IGNORECASE):
                return {"passed": True, "reasoning": f"Regex pattern '{rule}' matched"}
        except re.error:
            # Fall back to substring match
            if rule.lower() in response.lower():
                return {"passed": True, "reasoning": f"Substring '{rule}' found"}
        
        return {"passed": False, "reasoning": f"Pattern '{rule}' not found in response"}
    
    def _validate_json_structure(self, response: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Mode B: JSON structure validation"""
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed_json = json.loads(json_str)
                
                # Basic schema validation
                if self._validate_json_schema(parsed_json, schema):
                    return {"passed": True, "reasoning": "JSON structure matches schema"}
                else:
                    return {"passed": False, "reasoning": "JSON structure does not match schema"}
            else:
                return {"passed": False, "reasoning": "No valid JSON found in response"}
                
        except json.JSONDecodeError:
            return {"passed": False, "reasoning": "Invalid JSON format in response"}
    
    def _validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Basic JSON schema validation"""
        schema_type = schema.get("type")
        
        if schema_type == "object" and isinstance(data, dict):
            properties = schema.get("properties", {})
            for prop, prop_schema in properties.items():
                if prop in data:
                    if not self._validate_json_schema(data[prop], prop_schema):
                        return False
            return True
            
        elif schema_type == "string" and isinstance(data, str):
            min_length = schema.get("minLength", 0)
            max_length = schema.get("maxLength", float('inf'))
            return min_length <= len(data) <= max_length
            
        elif schema_type == "number" and isinstance(data, (int, float)):
            return True
            
        elif schema_type == "array" and isinstance(data, list):
            return True
            
        return False
    
    async def _validate_with_judge(self, response: str, judge_prompt: str, model: str) -> Dict[str, Any]:
        """Mode C: LLM-based validation"""
        if not judge_prompt:
            return {"passed": False, "reasoning": "No judge prompt specified"}
        
        try:
            judgment = await judge_response(response, judge_prompt, model)
            return {
                "passed": judgment.get("passed", False),
                "reasoning": f"Judge: {judgment.get('reasoning', 'No reasoning provided')}"
            }
        except Exception as e:
            return {"passed": False, "reasoning": f"Judge error: {str(e)}"}
    
    async def _save_logs(self):
        """Save current logs to database"""
        update_run_logs(self.run_id, self.logs, "running")
    
    async def _update_run_status(self, status: str):
        """Update run status in database"""
        update_run_logs(self.run_id, self.logs, status)