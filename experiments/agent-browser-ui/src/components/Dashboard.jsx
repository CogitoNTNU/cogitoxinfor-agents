import React, { useState, useEffect } from 'react';
import { Box, Container, Grid, Typography, Paper } from '@mui/material';
import AgentList from './AgentList';
import AgentControls from './AgentControls';
import BrowserView from './BrowserView';
import SystemStats from './SystemStats';
import { agentApi } from '../services/api';

function Dashboard() {
  const [agents, setAgents] = useState({});
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [systemStats, setSystemStats] = useState({});
  
  // Fetch agents and system stats periodically
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [agentsResponse, statsResponse] = await Promise.all([
          agentApi.listAgents(),
          agentApi.getSystemStats()
        ]);
        
        setAgents(agentsResponse.data);
        setSystemStats(statsResponse.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleAgentSelect = (agentId) => {
    setSelectedAgentId(agentId);
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Browser Agents Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Agents
            </Typography>
            <AgentList 
              agents={agents} 
              selectedAgentId={selectedAgentId}
              onAgentSelect={handleAgentSelect}
            />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
            <BrowserView agentId={selectedAgentId} />
          </Paper>
          
          <Box sx={{ mt: 2 }}>
            <Paper sx={{ p: 2 }}>
              <AgentControls 
                agentId={selectedAgentId}
                onAgentAction={() => {
                  // Refresh agents after action
                  agentApi.listAgents().then(res => setAgents(res.data));
                }}
              />
            </Paper>
          </Box>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <SystemStats stats={systemStats} />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;