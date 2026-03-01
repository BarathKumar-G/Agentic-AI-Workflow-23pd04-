# Agentic Workflow Builder

A production-ready system for creating and executing multi-step AI workflows with intelligent validation and real-time monitoring.

## Setup & Run Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- Supabase account (free tier)

### Supabase Setup

1. Create a new Supabase project at https://supabase.com
2. Go to SQL Editor and run the following setup script:

```sql
-- Create workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create steps table
CREATE TABLE IF NOT EXISTS steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    model TEXT,
    prompt TEXT NOT NULL,
    completion_rule TEXT,
    context_strategy TEXT
);

-- Create runs table
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    logs JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS for simplicity
ALTER TABLE workflows DISABLE ROW LEVEL SECURITY;
ALTER TABLE steps DISABLE ROW LEVEL SECURITY;
ALTER TABLE runs DISABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_steps_workflow_id ON steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_steps_order ON steps(workflow_id, step_order);
CREATE INDEX IF NOT EXISTS idx_runs_workflow_id ON runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
```

3. Get your project URL and anon key from Settings > API

### Environment Variables

Create `backend/.env`:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

> Get your free API key at https://openrouter.ai/keys — no charges, all supported models are free.

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

### Backend Run Commands

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs on http://localhost:8000

### Frontend Run Commands

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

## API Documentation

### Workflows

#### Create Workflow
- **Method**: POST
- **URL**: `/workflows`
- **Request Body**:
```json
{
  "name": "Content Generator",
  "steps": [
    {
      "step_order": 1,
      "model": "google/gemini-2.0-flash-exp:free",
      "prompt": "Generate a blog topic about AI",
      "completion_rule": "{\"type\":\"simple\",\"rule\":\"AI\"}",
      "context_strategy": "auto"
    }
  ]
}
```
- **Response**:
```json
{
  "id": "uuid",
  "name": "Content Generator",
  "created_at": "2024-01-01T00:00:00Z",
  "steps": [...]
}
```
- **Description**: Creates a new workflow with specified steps and validation rules

#### Get All Workflows
- **Method**: GET
- **URL**: `/workflows`
- **Request Body**: None
- **Response**:
```json
[
  {
    "id": "uuid",
    "name": "Content Generator",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```
- **Description**: Retrieves all workflows without step details

#### Get Workflow by ID
- **Method**: GET
- **URL**: `/workflows/{workflow_id}`
- **Request Body**: None
- **Response**:
```json
{
  "id": "uuid",
  "name": "Content Generator",
  "created_at": "2024-01-01T00:00:00Z",
  "steps": [
    {
      "id": "uuid",
      "workflow_id": "uuid",
      "step_order": 1,
      "model": "google/gemini-2.0-flash-exp:free",
      "prompt": "Generate a blog topic about AI",
      "completion_rule": "{\"type\":\"simple\",\"rule\":\"AI\"}",
      "context_strategy": "auto"
    }
  ]
}
```
- **Description**: Retrieves workflow with complete step configuration

### Runs

#### Start Workflow Run
- **Method**: POST
- **URL**: `/workflows/{workflow_id}/run`
- **Request Body**: None
- **Response**:
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "pending",
  "logs": [],
  "created_at": "2024-01-01T00:00:00Z"
}
```
- **Description**: Initiates workflow execution and returns run tracking ID

#### Get Run Status
- **Method**: GET
- **URL**: `/runs/{run_id}`
- **Request Body**: None
- **Response**:
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "logs": [
    {
      "step": 1,
      "prompt": "Generate a blog topic about AI",
      "response": "The Future of AI in Healthcare",
      "passed": true,
      "retries": 0,
      "timestamp": "2024-01-01T00:00:00Z",
      "model_used": "google/gemini-2.0-flash-exp:free"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```
- **Description**: Returns current run status with execution logs

#### Get Workflow Runs
- **Method**: GET
- **URL**: `/workflows/{workflow_id}/runs`
- **Request Body**: None
- **Response**:
```json
[
  {
    "id": "uuid",
    "workflow_id": "uuid",
    "status": "completed",
    "logs": [...],
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```
- **Description**: Retrieves all runs for a specific workflow

## Usage Example Flow

### 1. Create Workflow
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blog Generator",
    "steps": [
      {
        "step_order": 1,
        "model": "google/gemini-2.0-flash-exp:free",
        "prompt": "Generate a blog topic about technology",
        "completion_rule": "{\"type\":\"simple\",\"rule\":\"technology\"}",
        "context_strategy": "auto"
      },
      {
        "step_order": 2,
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "prompt": "Write a 100-word intro for: {{previous}}",
        "completion_rule": "{\"type\":\"json\",\"schema\":{\"type\":\"object\",\"properties\":{\"intro\":{\"type\":\"string\",\"minLength\":50}}}}",
        "context_strategy": "full"
      }
    ]
  }'
```

### 2. Run Workflow
```bash
curl -X POST http://localhost:8000/workflows/{workflow_id}/run
```

### 3. Poll Run Status
```bash
curl http://localhost:8000/runs/{run_id}
```

### 4. View Logs
Check the `logs` array in the run response for detailed execution information including:
- Step-by-step execution
- AI model responses
- Validation results
- Retry attempts
- Timestamps

## Supported Models (All Free)

| Model | Provider | Strengths |
|-------|----------|-----------|
| `google/gemini-2.0-flash-exp:free` | Google | Fast, 1M context window — **default** |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta | High quality, GPT-4 level |
| `deepseek/deepseek-r1:free` | DeepSeek | Strong reasoning |
| `mistralai/mistral-small-3.1-24b-instruct:free` | Mistral | Solid all-rounder |
| `nvidia/llama-3.1-nemotron-nano-8b-v1:free` | NVIDIA | Lightweight and fast |

All models are served via [OpenRouter](https://openrouter.ai) and are completely free with no charges.

## Features

- **Free Model Selection**: 5 high-quality free models via OpenRouter — no API costs
- **Intelligent Completion Criteria**: Simple matching, JSON validation, and LLM-based judging
- **Real-time Monitoring**: 2-second polling for live execution updates
- **Context Strategies**: Auto, full, summary, and extract modes for step chaining
- **Retry Logic**: Automatic retry up to 2 times on validation failure
- **Comprehensive Logging**: Detailed execution traces with timestamps and validation results
