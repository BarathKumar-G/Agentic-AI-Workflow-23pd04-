# Agentic Workflow Builder

A hackathon MVP for creating and executing multi-step AI workflows with real-time execution tracking.

## What This Does

- Create multi-step AI workflows with configurable prompts, models, and validation rules
- Execute workflows with automatic context passing between steps
- Real-time execution monitoring with detailed logs
- View workflow run history

## Prerequisites

- Python 3.9+
- Node.js 16+
- Supabase account (free tier works)

## Setup

### 1. Supabase Setup

Create a new Supabase project and run this SQL:

```sql
-- Create workflows table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create steps table
CREATE TABLE steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    model TEXT,
    prompt TEXT NOT NULL,
    completion_rule TEXT,
    context_strategy TEXT
);

-- Create runs table
CREATE TABLE runs (
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
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "SUPABASE_URL=your_supabase_url" > .env
echo "SUPABASE_KEY=your_supabase_anon_key" >> .env
echo "UNBOUND_API_KEY=your_unbound_key_optional" >> .env

# Run server
python main.py
```

Backend runs on http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run dev server
npm run dev
```

Frontend runs on http://localhost:5173

## API Examples

### Create Workflow
```bash
POST http://localhost:8000/workflows
Content-Type: application/json

{
  "name": "Content Generator",
  "steps": [
    {
      "step_order": 1,
      "model": "gpt-4",
      "prompt": "Generate a blog topic about AI",
      "completion_rule": "AI",
      "context_strategy": "auto"
    },
    {
      "step_order": 2,
      "prompt": "Write a 100-word intro for: {{previous}}",
      "completion_rule": "\\d{2,}",
      "context_strategy": "full"
    }
  ]
}
```

### Get All Workflows
```bash
GET http://localhost:8000/workflows
```

### Get Workflow by ID
```bash
GET http://localhost:8000/workflows/{workflow_id}
```

### Run Workflow
```bash
POST http://localhost:8000/workflows/{workflow_id}/run
```

### Get Run Status
```bash
GET http://localhost:8000/runs/{run_id}
```

### Get Workflow Runs
```bash
GET http://localhost:8000/workflows/{workflow_id}/runs
```

## Architecture

- **Backend**: FastAPI with modular services for workflow execution
- **Frontend**: React + Vite + Tailwind with 2-second polling for live updates
- **Database**: Supabase Postgres with simple schema
- **Execution**: Sequential step processing with context injection and validation
