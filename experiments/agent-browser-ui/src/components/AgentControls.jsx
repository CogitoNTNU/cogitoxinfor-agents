import React, { useState } from 'react';
import { 
  Box, Button, TextField, Typography, 
  ButtonGroup, Paper, Divider 
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import { agentApi } from '../services/api';

function AgentControls({ agentId, onAgentAction }) {
  const [task, setTask] = useState('');
  
  const handlePause = async () => {
    if (!agentId) return;
    try {
      await agentApi.pauseAgent(agentId);
      if (onAgentAction) onAgentAction();
    } catch (error) {
      console.error("Error pausing agent:", error);
    }
  };
  
  const handleResume = async () => {
    if (!agentId) return;
    try {
      await agentApi.resumeAgent(agentId);
      if (onAgentAction) onAgentAction();
    } catch (error) {
      console.error("Error resuming agent:", error);
    }
  };
  
  const handleStop = async () => {
    if (!agentId) return;
    try {
      await agentApi.stopAgent(agentId);
      if (onAgentAction) onAgentAction();
    } catch (error) {
      console.error("Error stopping agent:", error);
    }
  };
  
  const handleRun = async () => {
    if (!agentId || !task) return;
    try {
      await agentApi.runAgent(agentId, task);
      if (onAgentAction) onAgentAction();
    } catch (error) {
      console.error("Error running agent:", error);
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Agent Controls
      </Typography>
      
      {agentId ? (
        <>
          <ButtonGroup variant="contained" sx={{ mb: 2 }}>
            <Button 
              startIcon={<PauseIcon />}
              onClick={handlePause}
              color="warning"
            >
              Pause
            </Button>
            <Button 
              startIcon={<PlayArrowIcon />}
              onClick={handleResume}
              color="success"
            >
              Resume
            </Button>
            <Button 
              startIcon={<StopIcon />}
              onClick={handleStop}
              color="error"
            >
              Stop
            </Button>
          </ButtonGroup>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Run New Task with Selected Agent
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <TextField
              label="New Task"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              fullWidth
              multiline
              rows={2}
              size="small"
            />
            <Button 
              variant="contained"
              onClick={handleRun}
              sx={{ mt: 0.5 }}
            >
              Run
            </Button>
          </Box>
        </>
      ) : (
        <Typography>Select an agent to control</Typography>
      )}
    </Box>
  );
}

export default AgentControls;