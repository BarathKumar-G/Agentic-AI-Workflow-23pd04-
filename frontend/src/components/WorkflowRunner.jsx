import React, { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import apiClient from '../api/client'

function WorkflowRunner() {
  const { id } = useParams()
  const [workflow, setWorkflow] = useState(null)
  const [run, setRun] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const pollingRef = useRef(null)

  useEffect(() => {
    loadWorkflow()
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [id])

  const loadWorkflow = async () => {
    try {
      const data = await apiClient.getWorkflow(id)
      setWorkflow(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const startRun = async () => {
    try {
      setLoading(true)
      setError(null)
      const runData = await apiClient.runWorkflow(id)
      setRun(runData)
      startPolling(runData.id)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const startPolling = (runId) => {
    // Poll every 2 seconds
    pollingRef.current = setInterval(async () => {
      try {
        const runData = await apiClient.getRun(runId)
        setRun(runData)
        
        // Stop polling if completed or failed
        if (runData.status === 'completed' || runData.status === 'failed') {
          clearInterval(pollingRef.current)
          setLoading(false)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 2000)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (error) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">Error: {error}</div>
        </div>
      </div>
    )
  }

  if (!workflow) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm">
            ← Back to Workflows
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{workflow.name}</h1>
              <p className="text-sm text-gray-500 mt-1">
                {workflow.steps?.length || 0} steps
              </p>
            </div>
            {!run && (
              <button
                onClick={startRun}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Starting...' : 'Start Run'}
              </button>
            )}
          </div>

          {run && (
            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-gray-700">Status:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(run.status)}`}>
                  {run.status.toUpperCase()}
                </span>
                {loading && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                )}
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Logs</h3>
                
                {!run.logs || run.logs.length === 0 ? (
                  <div className="text-gray-500 text-sm">Waiting for execution to start...</div>
                ) : (
                  <div className="space-y-4">
                    {run.logs.map((log, index) => (
                      <div
                        key={index}
                        className={`border rounded-lg p-4 ${
                          log.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-gray-900">Step {log.step}</span>
                            {log.retries > 0 && (
                              <span className="text-xs text-gray-500">(Retry {log.retries})</span>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            {log.model_used && (
                              <span className="text-xs text-gray-500">{log.model_used}</span>
                            )}
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                log.passed
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {log.passed ? 'PASSED' : 'FAILED'}
                            </span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">Prompt:</div>
                            <div className="text-sm text-gray-700 bg-white rounded p-2 border border-gray-200">
                              {log.prompt}
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">Response:</div>
                            <div className="text-sm text-gray-700 bg-white rounded p-2 border border-gray-200">
                              {log.response}
                            </div>
                          </div>

                          <div className="text-xs text-gray-500">
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {(run.status === 'completed' || run.status === 'failed') && (
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    onClick={() => {
                      setRun(null)
                      setLoading(false)
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Run Again
                  </button>
                  <Link
                    to={`/workflow/${id}/history`}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    View History
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default WorkflowRunner