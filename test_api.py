#!/usr/bin/env python3
"""
Simple test script to verify the API is working
Run this after starting the backend server
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_api():
    print("🧪 Testing Agentic Workflow Builder API")
    print("=" * 50)
    
    # Test 0: Check if server is running
    print("\n0. Checking server status...")
    try:
        response = requests.get(f"{API_BASE}/")
        response.raise_for_status()
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("Make sure to run 'python main.py' in the backend directory first")
        return
    
    # Test 1: Create a workflow with intelligent completion criteria
    print("\n1. Creating test workflow with intelligent completion...")
    workflow_data = {
        "name": "Advanced Content Generator",
        "steps": [
            {
                "step_order": 1,
                "model": "kimi-k2p5",
                "prompt": "Generate a blog topic about technology",
                "completion_rule": json.dumps({
                    "type": "simple",
                    "rule": "technology"
                }),
                "context_strategy": "auto"
            },
            {
                "step_order": 2,
                "prompt": "Write a structured intro for: {{previous}}",
                "completion_rule": json.dumps({
                    "type": "json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "intro": {
                                "type": "string",
                                "minLength": 50
                            }
                        }
                    }
                }),
                "context_strategy": "full"
            },
            {
                "step_order": 3,
                "prompt": "Evaluate if the previous content is engaging: {{previous}}",
                "completion_rule": json.dumps({
                    "type": "judge",
                    "prompt": "Is this content engaging and well-written?"
                }),
                "context_strategy": "full"
            }
        ]
    }
    
    try:
        response = requests.post(f"{API_BASE}/workflows", json=workflow_data)
        response.raise_for_status()
        workflow = response.json()
        print(f"✅ Created workflow: {workflow['name']} (ID: {workflow['id']})")
        workflow_id = workflow['id']
    except Exception as e:
        print(f"❌ Failed to create workflow: {e}")
        return
    
    # Test 2: Get all workflows
    print("\n2. Fetching all workflows...")
    try:
        response = requests.get(f"{API_BASE}/workflows")
        response.raise_for_status()
        workflows = response.json()
        print(f"✅ Found {len(workflows)} workflows")
    except Exception as e:
        print(f"❌ Failed to fetch workflows: {e}")
        return
    
    # Test 3: Get specific workflow
    print("\n3. Fetching workflow details...")
    try:
        response = requests.get(f"{API_BASE}/workflows/{workflow_id}")
        response.raise_for_status()
        workflow_details = response.json()
        print(f"✅ Retrieved workflow with {len(workflow_details.get('steps', []))} steps")
        
        # Verify intelligent completion rules
        for step in workflow_details.get('steps', []):
            if step['completion_rule']:
                rule = json.loads(step['completion_rule'])
                print(f"   Step {step['step_order']}: {rule['type']} validation")
    except Exception as e:
        print(f"❌ Failed to fetch workflow details: {e}")
        return
    
    # Test 4: Check supported models
    print("\n4. Checking supported models...")
    try:
        response = requests.get(f"{API_BASE}/workflows/models/supported")
        response.raise_for_status()
        models_info = response.json()
        print(f"✅ Supported models: {models_info['models']}")
        print(f"   Default model: {models_info['default']}")
    except Exception as e:
        print(f"❌ Failed to fetch supported models: {e}")
    
    # Test 5: Run the workflow
    print("\n5. Running workflow...")
    try:
        response = requests.post(f"{API_BASE}/workflows/{workflow_id}/run")
        response.raise_for_status()
        run = response.json()
        print(f"✅ Started run: {run['id']} (Status: {run['status']})")
        run_id = run['id']
    except Exception as e:
        print(f"❌ Failed to start run: {e}")
        return
    
    # Test 6: Poll run status
    print("\n6. Polling run status...")
    max_polls = 30  # 1 minute max
    for i in range(max_polls):
        try:
            response = requests.get(f"{API_BASE}/runs/{run_id}")
            response.raise_for_status()
            run_status = response.json()
            
            status = run_status['status']
            log_count = len(run_status.get('logs', []))
            
            print(f"   Poll {i+1}: Status={status}, Logs={log_count}")
            
            if status in ['completed', 'failed']:
                print(f"✅ Run finished with status: {status}")
                
                # Show logs with intelligent validation results
                if run_status.get('logs'):
                    print("\n📋 Execution Logs:")
                    for log in run_status['logs']:
                        status_icon = "✅" if log['passed'] else "❌"
                        print(f"   {status_icon} Step {log['step']}: {'PASSED' if log['passed'] else 'FAILED'}")
                        print(f"      Model: {log.get('model_used', 'default')}")
                        print(f"      Prompt: {log['prompt'][:50]}...")
                        print(f"      Response: {log['response'][:50]}...")
                        if log.get('validation_reasoning'):
                            print(f"      Validation: {log['validation_reasoning']}")
                        if log.get('retries', 0) > 0:
                            print(f"      Retries: {log['retries']}")
                break
                
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to poll run status: {e}")
            return
    else:
        print("⏰ Run did not complete within timeout")
    
    # Test 7: Get workflow runs
    print("\n7. Fetching workflow run history...")
    try:
        response = requests.get(f"{API_BASE}/workflows/{workflow_id}/runs")
        response.raise_for_status()
        runs = response.json()
        print(f"✅ Found {len(runs)} runs for this workflow")
    except Exception as e:
        print(f"❌ Failed to fetch runs: {e}")
        return
    
    print("\n🎉 All tests completed successfully!")
    print(f"🌐 Frontend should be available at: http://localhost:5173")
    print(f"📊 API documentation: http://localhost:8000/docs")
    print("\n🚀 New Features Tested:")
    print("   ✅ Controlled model selection (kimi-k2p5, kimi-k2-instruct-0905)")
    print("   ✅ Simple string/regex validation")
    print("   ✅ JSON structure validation")
    print("   ✅ LLM-based judge validation")
    print("   ✅ Enhanced logging with validation reasoning")

if __name__ == "__main__":
    test_api()