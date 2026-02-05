import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import WorkflowList from './components/WorkflowList'
import WorkflowCreator from './components/WorkflowCreator'
import WorkflowRunner from './components/WorkflowRunner'
import RunHistory from './components/RunHistory'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/" className="text-xl font-bold text-gray-900">
                  Agentic Workflow Builder
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Workflows
                </Link>
                <Link
                  to="/create"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Create Workflow
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<WorkflowList />} />
            <Route path="/create" element={<WorkflowCreator />} />
            <Route path="/workflow/:id" element={<WorkflowRunner />} />
            <Route path="/run/:id" element={<WorkflowRunner />} />
            <Route path="/workflow/:id/run" element={<WorkflowRunner />} />
            <Route path="/history/:id" element={<RunHistory />} />
            <Route path="/workflow/:id/history" element={<RunHistory />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App