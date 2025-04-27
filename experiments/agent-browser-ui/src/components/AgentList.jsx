import React from 'react';
import { 
  List, ListItem, ListItemText, ListItemIcon, 
  Chip, Box, Button, TextField, Typography 
} from '@mui/material';
import ComputerIcon from '@mui/icons-material/Computer';
import { agentApi } from '../services/api';
import { useState } from 'react';

function AgentList({ agents, selectedAgentId, onAgentSelect }) {
  const [newAgentId, setNewAgentId] = useState('');
  const [newAgentTask, setNewAgentTask] = useState('');

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'paused': return 'warning';
      case 'stopped': return 'error';
      default: return 'default';
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgentId || !newAgentTask) return;
    
    try {
      await agentApi.runAgent(newAgentId, newAgentTask);
      setNewAgentId('');
      setNewAgentTask('');
    } catch (error) {
      console.error("Error creating agent:", error);
    }
  };

  return (
    <Box>
      <List dense>
        {Object.entries(agents).map(([agentId, agentData]) => (
          <ListItem 
            key={agentId}
            selected={selectedAgentId === agentId}
            onClick={() => onAgentSelect(agentId)}
            button
          >
            <ListItemIcon>
              <ComputerIcon />
            </ListItemIcon>
            <ListItemText 
              primary={agentId} 
              secondary={agentData.task?.substring(0, 30) + '...'}
            />
            <Chip 
              label={agentData.status} 
              color={getStatusColor(agentData.status)} 
              size="small" 
            />
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ mt: 2, p: 1, borderTop: '1px solid #eee' }}>
        <Typography variant="subtitle2" gutterBottom>
          Create New Agent
        </Typography>
        <TextField
          label="Agent ID"
          value={newAgentId}
          onChange={(e) => setNewAgentId(e.target.value)}
          fullWidth
          margin="dense"
          size="small"
        />
        <TextField
          label="Task"
          value={newAgentTask}
          onChange={(e) => setNewAgentTask(e.target.value)}
          fullWidth
          margin="dense"
          size="small"
          multiline
          rows={2}
        />
        <Button 
          variant="contained" 
          onClick={handleCreateAgent}
          fullWidth
          sx={{ mt: 1 }}
        >
          Create & Run
        </Button>
      </Box>
    </Box>
  );
}

export default AgentList;