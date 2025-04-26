import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const agentApi = {
  // Create and run an agent
  runAgent: (agentId, task) => 
    axios.post(`${API_URL}/agent/run`, { agent_id: agentId, task }),
  
  // Get agent status
  getAgentStatus: (agentId) => 
    axios.get(`${API_URL}/agent/${agentId}/status`),
  
  // Control agents
  pauseAgent: (agentId) => 
    axios.post(`${API_URL}/agent/${agentId}/pause`),
  
  resumeAgent: (agentId) => 
    axios.post(`${API_URL}/agent/${agentId}/resume`),
  
  stopAgent: (agentId) => 
    axios.post(`${API_URL}/agent/${agentId}/stop`),
  
  // Get all agents
  listAgents: () => 
    axios.get(`${API_URL}/agents`),
  
  // System statistics
  getSystemStats: () => 
    axios.get(`${API_URL}/system/stats`),
  
  // Get screenshot for a specific step (or latest if step is not provided)
  getAgentScreenshot: (agentId, step = null) => {
    const stepParam = step !== null ? `?step=${step}` : '';
    return axios.get(`${API_URL}/agent/${agentId}/screenshot${stepParam}`);
  },
  
  // Get agent history information
  getAgentHistory: (agentId) => 
    axios.get(`${API_URL}/agent/${agentId}/history`)
};