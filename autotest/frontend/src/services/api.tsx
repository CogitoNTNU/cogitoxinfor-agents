import axios from 'axios';

export const API_URL = 'http://localhost:8000';

export const agentApi = {
  // Create and run an agent
  runAgent: (agentId: string, task: string) => 
    axios.post(`${API_URL}/agent/run`, { agent_id: agentId, task }),
  
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

  // Stream real-time logs and screenshots via Server-Sent Events
  streamAgentEvents: (): EventSource => new EventSource(`${API_URL}/logs`),
};
