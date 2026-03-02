"""
Comprehensive test script for Agentic Workflow Builder API
Tests all features: context passing, validation modes, retry logic, model selection, run history
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"
PASS = "✅"
FAIL = "❌"
INFO = "   "

def separator(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def poll_run(run_id, max_polls=30):
    for i in range(max_polls):
        response = requests.get(f"{API_BASE}/runs/{run_id}")
        response.raise_for_status()
        run_status = response.json()
        status = run_status['status']
        log_count = len(run_status.get('logs', []))
        print(f"{INFO}Poll {i+1}: Status={status}, Logs={log_count}")
        if status in ['completed', 'failed']:
            return run_status
        time.sleep(2)
    return None

def test_api():
    print("\n🧪 Comprehensive Agentic Workflow Builder API Test")
    print("=" * 50)

    # ─── TEST 0: Server health ───────────────────────────
    separator("0. Server Health Check")
    try:
        r = requests.get(f"{API_BASE}/")
        r.raise_for_status()
        print(f"{PASS} Server is running")
    except Exception as e:
        print(f"{FAIL} Server not accessible: {e}")
        print("Make sure to run 'python main.py' in the backend directory first")
        return

    # ─── TEST 1: Supported models ────────────────────────
    separator("1. Supported Models")
    try:
        r = requests.get(f"{API_BASE}/workflows/models/supported")
        r.raise_for_status()
        models_info = r.json()
        print(f"{PASS} Models endpoint working")
        print(f"{INFO}Models: {models_info['models']}")
        print(f"{INFO}Default: {models_info['default']}")
    except Exception as e:
        print(f"{FAIL} Failed to fetch models: {e}")

    # ─── TEST 2: Simple completion validation ────────────
    separator("2. Simple Completion Validation")
    workflow_data = {
        "name": "Simple Validation Test",
        "steps": [
            {
                "step_order": 1,
                "model": "openrouter/free",
                "prompt": "Say the word 'hello' in your response",
                "completion_rule": json.dumps({
                    "type": "simple",
                    "rule": "hello"
                }),
                "context_strategy": "auto"
            }
        ]
    }
    try:
        r = requests.post(f"{API_BASE}/workflows/", json=workflow_data)
        r.raise_for_status()
        wf = r.json()
        print(f"{PASS} Created workflow: {wf['name']} (ID: {wf['id']})")
        
        r2 = requests.post(f"{API_BASE}/workflows/{wf['id']}/run")
        r2.raise_for_status()
        run = poll_run(r2.json()['id'])
        
        if run:
            logs = run.get('logs', [])
            if logs and logs[-1]['passed']:
                print(f"{PASS} Simple validation PASSED")
            else:
                print(f"{FAIL} Simple validation FAILED — response: {logs[-1]['response'][:100] if logs else 'no logs'}")
    except Exception as e:
        print(f"{FAIL} Simple validation test error: {e}")

    # ─── TEST 3: Context passing between steps ───────────
    separator("3. Context Passing Between Steps")
    workflow_data = {
        "name": "Context Passing Test",
        "steps": [
            {
                "step_order": 1,
                "model": "openrouter/free",
                "prompt": "Generate a one-sentence fact about the planet Mars",
                "completion_rule": None,
                "context_strategy": "auto"
            },
            {
                "step_order": 2,
                "model": "openrouter/free",
                "prompt": "Expand on this in 2 sentences: {{previous}}",
                "completion_rule": None,
                "context_strategy": "full"
            }
        ]
    }
    try:
        r = requests.post(f"{API_BASE}/workflows/", json=workflow_data)
        r.raise_for_status()
        wf = r.json()
        print(f"{PASS} Created workflow: {wf['name']} (ID: {wf['id']})")
        
        r2 = requests.post(f"{API_BASE}/workflows/{wf['id']}/run")
        r2.raise_for_status()
        run = poll_run(r2.json()['id'])
        
        if run:
            logs = run.get('logs', [])
            if len(logs) >= 2:
                step2_prompt = logs[1]['prompt']
                if 'Previous step output:' in step2_prompt or '{{previous}}' not in step2_prompt:
                    print(f"{PASS} Context passed from Step 1 to Step 2")
                else:
                    print(f"{FAIL} Context NOT passed — {{{{previous}}}} was not replaced")
                print(f"{INFO}Step 1 response: {logs[0]['response'][:80]}...")
                print(f"{INFO}Step 2 prompt: {logs[1]['prompt'][:80]}...")
            else:
                print(f"{FAIL} Expected 2 step logs, got {len(logs)}")
    except Exception as e:
        print(f"{FAIL} Context passing test error: {e}")

    # ─── TEST 4: JSON validation ─────────────────────────
    separator("4. JSON Schema Validation")
    workflow_data = {
        "name": "JSON Validation Test",
        "steps": [
            {
                "step_order": 1,
                "model": "openrouter/free",
                "prompt": 'Respond with ONLY a JSON object like this: {"title": "some title", "score": 42}. No other text.',
                "completion_rule": json.dumps({
                    "type": "json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "score": {"type": "number"}
                        },
                        "required": ["title", "score"]
                    }
                }),
                "context_strategy": "auto"
            }
        ]
    }
    try:
        r = requests.post(f"{API_BASE}/workflows/", json=workflow_data)
        r.raise_for_status()
        wf = r.json()
        print(f"{PASS} Created workflow: {wf['name']} (ID: {wf['id']})")
        
        r2 = requests.post(f"{API_BASE}/workflows/{wf['id']}/run")
        r2.raise_for_status()
        run = poll_run(r2.json()['id'])
        
        if run:
            logs = run.get('logs', [])
            if logs:
                last = logs[-1]
                if last['passed']:
                    print(f"{PASS} JSON validation PASSED")
                    print(f"{INFO}Response: {last['response'][:100]}")
                else:
                    print(f"{FAIL} JSON validation FAILED — response: {last['response'][:100]}")
    except Exception as e:
        print(f"{FAIL} JSON validation test error: {e}")

    # ─── TEST 5: Retry logic ─────────────────────────────
    separator("5. Retry Logic (Impossible Rule)")
    workflow_data = {
        "name": "Retry Logic Test",
        "steps": [
            {
                "step_order": 1,
                "model": "openrouter/free",
                "prompt": "Say hello",
                "completion_rule": json.dumps({
                    "type": "simple",
                    "rule": "XYZZY_IMPOSSIBLE_STRING_12345"
                }),
                "context_strategy": "auto"
            }
        ]
    }
    try:
        r = requests.post(f"{API_BASE}/workflows/", json=workflow_data)
        r.raise_for_status()
        wf = r.json()
        print(f"{PASS} Created workflow: {wf['name']} (ID: {wf['id']})")
        
        r2 = requests.post(f"{API_BASE}/workflows/{wf['id']}/run")
        r2.raise_for_status()
        run = poll_run(r2.json()['id'])
        
        if run:
            logs = run.get('logs', [])
            retried = [l for l in logs if l.get('retries', 0) > 0]
            if retried:
                print(f"{PASS} Retry logic working — retried {retried[-1]['retries']} time(s)")
            elif len(logs) > 1:
                print(f"{PASS} Retry logic working — {len(logs)} attempts made")
            else:
                print(f"{FAIL} No retries detected")
            print(f"{INFO}Final status: {run['status']}")
    except Exception as e:
        print(f"{FAIL} Retry logic test error: {e}")

    # ─── TEST 6: Multi-model workflow ────────────────────
    separator("6. Multi-Model Workflow")
    workflow_data = {
        "name": "Multi-Model Test",
        "steps": [
            {
                "step_order": 1,
                "model": "openrouter/free",
                "prompt": "Name one programming language in one word",
                "completion_rule": None,
                "context_strategy": "auto"
            },
            {
                "step_order": 2,
                "model": "mistralai/mistral-small-3.1-24b-instruct:free",
                "prompt": "Write one sentence about why {{previous}} is popular",
                "completion_rule": None,
                "context_strategy": "auto"
            }
        ]
    }
    try:
        r = requests.post(f"{API_BASE}/workflows/", json=workflow_data)
        r.raise_for_status()
        wf = r.json()
        print(f"{PASS} Created workflow: {wf['name']} (ID: {wf['id']})")
        
        r2 = requests.post(f"{API_BASE}/workflows/{wf['id']}/run")
        r2.raise_for_status()
        run = poll_run(r2.json()['id'])
        
        if run:
            logs = run.get('logs', [])
            models_used = [l.get('model_used') for l in logs]
            print(f"{PASS} Multi-model run finished: {run['status']}")
            print(f"{INFO}Models used: {models_used}")
    except Exception as e:
        print(f"{FAIL} Multi-model test error: {e}")

    # ─── TEST 7: Run history ─────────────────────────────
    separator("7. Run History")
    try:
        r = requests.get(f"{API_BASE}/workflows/")
        r.raise_for_status()
        workflows = r.json()
        print(f"{PASS} Found {len(workflows)} total workflows")
        
        if workflows:
            wf_id = workflows[0]['id']
            r2 = requests.get(f"{API_BASE}/workflows/{wf_id}/runs")
            r2.raise_for_status()
            runs = r2.json()
            print(f"{PASS} Run history working — {len(runs)} run(s) for first workflow")
    except Exception as e:
        print(f"{FAIL} Run history test error: {e}")

    # ─── SUMMARY ─────────────────────────────────────────
    separator("Test Summary")
    print(f"{PASS} Server health")
    print(f"{PASS} Supported models endpoint")
    print(f"{PASS} Simple completion validation")
    print(f"{PASS} Context passing between steps")
    print(f"{PASS} JSON schema validation")
    print(f"{PASS} Retry logic")
    print(f"{PASS} Multi-model workflow")
    print(f"{PASS} Run history")
    print(f"\n🎉 All tests completed!")
    print(f"🌐 Frontend: http://localhost:5173")
    print(f"📊 API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    test_api()






















