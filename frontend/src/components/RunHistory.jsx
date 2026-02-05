import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import apiClient from '../api/client'

function RunHistory() {
  const { id } = useParams()
  const [workflow, setWorkflow] = useState(null)
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      setLoading(true)
      const [workflowData, runsData] = await Promise.all([
        apiClient.getWorkflow(id),
        apiClient.getWorkflowRuns(id)
      ])
      setWorkflow(workflowData)
      setRuns(runsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
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

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm">
            ← Back to Workflows
          </Link>
        </div>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{workflow?.name}</h1>
          <p className="text-sm text-gray-500 mt-1">Run History</p>
        </div>

        {runs.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6 text-center">
            <div className="text-gray-500">No runs yet</div>
            <Link
              to={`/workflow/${id}/run`}
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Start First Run
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                  <h3 className="text-sm font-medium text-gray-900">All Runs</h3>
                </div>
                <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                  {runs.map((run) => (
                    <button
                      key={run.id}
                      onClick={() => setSelectedRun(run)}
                      className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                        selectedRun?.id === run.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">
                          {new Date(run.created_at).toLocaleString()}
                        </span>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                            run.status
                          )}`}
                        >
                          {run.status}
                        </span>
                      </div>
                      {run.logs && (
                        <div className="text-xs text-gray-500 mt-1">
                          {run.logs.length} log entries
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="lg:col-span-2">
              {selectedRun ? (
                <div className="bg-white shadow rounded-lg p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-medium text-gray-900">Run Details</h3>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                        selectedRun.status
                      )}`}
                    >
                      {selectedRun.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="mb-4 text-sm text-gray-500">
                    Started: {new Date(selectedRun.created_at).toLocaleString()}
                  </div>

                  {selectedRun.logs && selectedRun.logs.length > 0 ? (
                    <div className="space-y-4">
                      {selectedRun.logs.map((log, index) => (
                        <div
                          key={index}
                          className={`border rounded-lg p-4 ${
                            log.passed
                              ? 'border-green-200 bg-green-50'
                              : 'border-red-200 bg-red-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900">Step {log.step}</span>
                              {log.retries > 0 && (
                                <span className="text-xs text-gray-500">
                                  (Retry {log.retries})
                                </span>
                              )}
                            </div>
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

                          <div className="space-y-2">
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-1">
                                Prompt:
                              </div>
                              <div className="text-sm text-gray-700 bg-white rounded p-2 border border-gray-200">
                                {log.prompt}
                              </div>
                            </div>

                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-1">
                                Response:
                              </div>
                              <div className="text-sm text-gray-700 bg-white rounded p-2 border border-gray-200">
                                {log.response}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500 text-sm">No logs available</div>
                  )}
                </div>
              ) : (
                <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
                  Select a run to view details
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default RunHistory