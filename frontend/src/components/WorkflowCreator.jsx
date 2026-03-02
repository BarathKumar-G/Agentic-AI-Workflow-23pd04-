import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'

const SUPPORTED_MODELS = [
  'openrouter/free',
  'meta-llama/llama-3.3-70b-instruct:free',
  'deepseek/deepseek-r1:free',
  'mistralai/mistral-small-3.1-24b-instruct:free',
  'google/gemma-3-27b-it:free',
]
const CONTEXT_STRATEGIES = ['auto', 'full', 'summary', 'extract']

function WorkflowCreator() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [steps, setSteps] = useState([
    {
      step_order: 1,
      model: '',
      prompt: '',
      completion_type: 'any',
      completion_rule: '',
      context_strategy: 'auto'
    }
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const addStep = () => {
    setSteps([
      ...steps,
      {
        step_order: steps.length + 1,
        model: '',
        prompt: '',
        completion_type: 'any',
        completion_rule: '',
        context_strategy: 'auto'
      }
    ])
  }

  const removeStep = (index) => {
    if (steps.length > 1) {
      const newSteps = steps.filter((_, i) => i !== index)
      newSteps.forEach((step, i) => {
        step.step_order = i + 1
      })
      setSteps(newSteps)
    }
  }

  const updateStep = (index, field, value) => {
    const newSteps = [...steps]
    newSteps[index][field] = value
    
    if (field === 'completion_type') {
      newSteps[index].completion_rule = ''
    }
    
    setSteps(newSteps)
  }

  const buildCompletionRule = (step) => {
    if (step.completion_type === 'any') {
      return null
    } else if (step.completion_type === 'simple') {
      return JSON.stringify({
        type: 'simple',
        rule: step.completion_rule
      })
    } else if (step.completion_type === 'json') {
      try {
        const schema = JSON.parse(step.completion_rule || '{}')
        return JSON.stringify({
          type: 'json',
          schema: schema
        })
      } catch (e) {
        return JSON.stringify({
          type: 'json',
          schema: {}
        })
      }
    } else if (step.completion_type === 'judge') {
      return JSON.stringify({
        type: 'judge',
        prompt: step.completion_rule
      })
    }
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!name.trim()) {
      setError('Workflow name is required')
      return
    }

    if (steps.some(step => !step.prompt.trim())) {
      setError('All steps must have a prompt')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const workflow = {
        name: name.trim(),
        steps: steps.map(step => ({
          step_order: step.step_order,
          model: step.model || null,
          prompt: step.prompt.trim(),
          completion_rule: buildCompletionRule(step),
          context_strategy: step.context_strategy
        }))
      }

      await apiClient.createWorkflow(workflow)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderCompletionRuleInput = (step, index) => {
    if (step.completion_type === 'any') {
      return (
        <p className="text-sm text-gray-500 mt-1">
          Any response will be accepted
        </p>
      )
    } else if (step.completion_type === 'simple') {
      return (
        <div>
          <input
            type="text"
            value={step.completion_rule}
            onChange={(e) => updateStep(index, 'completion_rule', e.target.value)}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="String to match or regex pattern"
          />
          <p className="mt-1 text-xs text-gray-500">
              Use substring matching or regex patterns (e.g., AI or {'\\d{2,}'})
          </p>
        </div>
      )
    } else if (step.completion_type === 'json') {
      return (
        <div>
          <textarea
            value={step.completion_rule}
            onChange={(e) => updateStep(index, 'completion_rule', e.target.value)}
            rows={4}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder='JSON schema example: {"type":"object","properties":{"title":{"type":"string"}}}'
          />
          <p className="mt-1 text-xs text-gray-500">
            JSON schema to validate response structure
          </p>
        </div>
      )
    } else if (step.completion_type === 'judge') {
      return (
        <div>
          <textarea
            value={step.completion_rule}
            onChange={(e) => updateStep(index, 'completion_rule', e.target.value)}
            rows={2}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Does this response contain a valid Python function?"
          />
          <p className="mt-1 text-xs text-gray-500">
            AI judge will evaluate the response based on this criteria
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Create Workflow
            </h1>
          </div>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Workflow Name
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter workflow name"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Steps</h3>
              <button
                type="button"
                onClick={addStep}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Add Step
              </button>
            </div>

            <div className="mt-4 space-y-6">
              {steps.map((step, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-md font-medium text-gray-900">
                      Step {step.step_order}
                    </h4>
                    {steps.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeStep(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Model
                      </label>
                      <select
                        value={step.model}
                        onChange={(e) => updateStep(index, 'model', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      >
                        <option value="">Use default model (kimi-k2p5)</option>
                        {SUPPORTED_MODELS.map(model => (
                          <option key={model} value={model}>{model}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Context Strategy
                      </label>
                      <select
                        value={step.context_strategy}
                        onChange={(e) => updateStep(index, 'context_strategy', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      >
                        {CONTEXT_STRATEGIES.map(strategy => (
                          <option key={strategy} value={strategy}>
                            {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Prompt *
                    </label>
                    <textarea
                      value={step.prompt}
                      onChange={(e) => updateStep(index, 'prompt', e.target.value)}
                      rows={3}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Enter the prompt for this step. Use {{previous}} to reference previous step output."
                      required
                    />
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Completion Type
                    </label>
                    <select
                      value={step.completion_type}
                      onChange={(e) => updateStep(index, 'completion_type', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="any">Any response</option>
                      <option value="simple">String / Regex match</option>
                      <option value="json">JSON structure validation</option>
                      <option value="judge">LLM judge prompt</option>
                    </select>
                  </div>

                  {step.completion_type !== 'any' && (
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700">
                        Completion Rule
                      </label>
                      {renderCompletionRuleInput(step, index)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Workflow'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default WorkflowCreator