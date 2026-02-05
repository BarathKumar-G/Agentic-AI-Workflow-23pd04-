const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_URL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body)
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const error = await response.text()
        throw new Error(`API Error: ${response.status} - ${error}`)
      }

      return response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Workflows
  async getWorkflows() {
    return this.request('/workflows')
  }

  async getWorkflow(id) {
    return this.request(`/workflows/${id}`)
  }

  async createWorkflow(workflow) {
    return this.request('/workflows', {
      method: 'POST',
      body: workflow,
    })
  }

  async runWorkflow(id) {
    return this.request(`/workflows/${id}/run`, {
      method: 'POST',
    })
  }

  async getWorkflowRuns(id) {
    return this.request(`/workflows/${id}/runs`)
  }

  async deleteWorkflow(id) {
    return this.request(`/workflows/${id}`, {
      method: 'DELETE',
    })
  }

  // Runs
  async getRun(id) {
    return this.request(`/runs/${id}`)
  }
}

export default new ApiClient()