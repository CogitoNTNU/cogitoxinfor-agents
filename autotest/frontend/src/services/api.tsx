import axios from 'axios';

export const API_URL = 'http://localhost:8000';

export const agentApi = {
  // Create a new agent
  createAgent: () =>
    axios.post(`${API_URL}/agent`),

  // Run an existing agent
  runAgent: (agentId: string, query: string) =>
    axios.post(`${API_URL}/agent/${agentId}/run`, { query }),
  
  // Get agent status
  getAgentStatus: (agentId: string) => 
    axios.get(`${API_URL}/agent/${agentId}/status`),
  
  // Control agents
  pauseAgent: (agentId: string) => 
    axios.post(`${API_URL}/agent/${agentId}/pause`),
  
  resumeAgent: (agentId: string) => 
    axios.post(`${API_URL}/agent/${agentId}/resume`),
  
  stopAgent: (agentId: string) => 
    axios.post(`${API_URL}/agent/${agentId}/stop`),
  
  // Get all agents
  listAgents: () => 
    axios.get(`${API_URL}/agents`),
  
  // System statistics
  getSystemStats: () => 
    axios.get(`${API_URL}/system/stats`),
  
  // Get screenshot for a specific step (or latest if step is not provided)
  getAgentScreenshot: (agentId: string, step: number | null = null) => {
    const stepParam = step !== null ? `?step=${step}` : '';
    return axios.get(`${API_URL}/agent/${agentId}/screenshot${stepParam}`);
  },
  
  // Get agent history information
  getAgentHistory: (agentId: string) => 
    axios.get(`${API_URL}/agent/${agentId}/history`),

  // Stream real-time logs and screenshots for a specific agent via SSE
  streamAgentEvents: (agentId: string): EventSource =>
    new EventSource(`${API_URL}/agent/${agentId}/stream`),
};
