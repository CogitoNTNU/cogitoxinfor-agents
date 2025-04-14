"use client";

import { useState, useEffect, useRef } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  Paper,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AgentController from './components/AgentController';
import { API_BASE_URL, WS_BASE_URL, endpoints } from './services/api';

const StyledImage = styled('img')({
  width: '100%',
  height: 'auto',
  borderRadius: '4px'
});

const ScrollableList = styled(List)({
  maxHeight: '300px',
  overflow: 'auto'
});

export default function WebAgent() {
  const [mode, setMode] = useState('agent'); // 'agent' or 'test'
  const [query, setQuery] = useState('');
  const [humanIntervention, setHumanIntervention] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [steps, setSteps] = useState([]);
  const [connected, setConnected] = useState(false);
  const [userResponse, setUserResponse] = useState('');
  const wsRef = useRef(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  
  
  const connectWebSocket = (sid) => {
    console.log('Connecting WebSocket with session ID:', sid);
    const ws = new WebSocket(`${WS_BASE_URL}${endpoints.websocket(sid)}`);
    
    ws.onopen = () => {
      console.log('WebSocket Connected');
      setConnected(true);
    };
  
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
      setIsWaitingForResponse(false);
    };
  
    ws.onclose = () => {
      console.log('WebSocket Disconnected');
      setConnected(false);
      setIsWaitingForResponse(false);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    wsRef.current = ws;
  };

  const handleWebSocketMessage = (data) => {
    console.log('Received WebSocket message:', data);
    
    switch(data.type) {
      case 'SCREENSHOT_UPDATE':
        const { 
          step, 
          image_url 
        } = data.payload;
        
        setSteps(prev => [...prev, {
          step,
          // Prepend API_BASE_URL to the image_url
          image: `${API_BASE_URL}${image_url}`,
          type: 'screenshot'
        }]);
        break;
  
        case 'ACTION_UPDATE':
          const { action, args } = data.payload;
          setSteps(prev => [...prev, {
            step: data.payload.step,
            action,
            args,
            type: 'action'
          }]);
          break;

        case 'INTERRUPT':
          console.log('Received interrupt request:', data.payload);
          setIsWaitingForResponse(true);
          setSteps(prev => [...prev, {
            step: data.payload.step,
            message: data.payload.message,
            type: 'interrupt',
            needsResponse: true
          }]);
          break;

      case 'FINAL_ANSWER':
        setSteps(prev => [...prev, {
          step: data.payload.step,
          answer: data.payload.answer,
          type: 'answer'
        }]);
        break;
    }
  };

  const handleStartAgent = async (payload) => {
    try {
      // Transform payload to match backend expectations
      const apiPayload = {
        query: payload.testing ? "" : payload.query,
        testing: payload.testing,
        human_intervention: payload.human_intervention,
        test_actions: payload.testing ? payload.test_actions.map(action => ({
          action: action.action,
          args: [action.args] // Ensure args is an array
        })) : undefined
      };

      const response = await fetch(`${API_BASE_URL}${endpoints.runAgent}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start agent');
      }

      const data = await response.json();
      if (data.session_id) {
        setSessionId(data.session_id);
        connectWebSocket(data.session_id);
      } else {
        throw new Error('No session ID received');
      }
    } catch (error) {
      console.error('Failed to start agent:', error);
      alert(`Error: ${error.message}`);
    }
  };

  const handleStopAgent = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  const sendInterventionResponse = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('Sending intervention response:', userResponse);
      
      const message = {
        type: 'INTERVENTION_RESPONSE',
        payload: {
          input: userResponse || ''
        }
      };
  
      try {
        wsRef.current.send(JSON.stringify(message));
        console.log('Intervention response sent successfully');
        setUserResponse('');
        setIsWaitingForResponse(false);
        
        // Update step status
        setSteps(prev => prev.map(step => 
          step.type === 'interrupt' && step.needsResponse 
            ? { ...step, needsResponse: false }
            : step
        ));
      } catch (error) {
        console.error('Failed to send intervention response:', error);
        alert('Failed to send response to agent');
      }
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Web Agent Interface
        </Typography>

      <AgentController
        onStart={handleStartAgent}
        onStop={handleStopAgent}
        isRunning={connected}
      />

        {steps.length > 0 && (
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Session Progress
            </Typography>
            <ScrollableList>
              {steps.map((step, index) => (
                <ListItem key={index} divider>
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="subtitle2">
                      Step {step.step}
                    </Typography>
                    
              {step.type === 'screenshot' && (
              <Box>
                {step.image ? (
                  <>
                    <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                      Screenshot from step {step.step}
                    </Typography>
                    <StyledImage 
                      src={step.image}
                      alt={`Screenshot from step ${step.step}`}
                      onError={(e) => {
                        console.error('Image failed to load:', {
                          step: step.step,
                          url: step.image,
                          sessionId: sessionId
                        });
                        e.target.onerror = null;
                        e.target.src = '/placeholder-image.png';  // Use a local placeholder
                      }}
                      sx={{
                        maxWidth: '100%',
                        maxHeight: '400px',
                        objectFit: 'contain',
                        mt: 1,
                        mb: 2,
                        border: '1px solid #e0e0e0',
                        borderRadius: 1,
                        boxShadow: 1
                      }}
                    />
                  </>
                ) : (
                  <Typography color="text.secondary" sx={{ mt: 1 }}>
                    No screenshot available
                  </Typography>
                )}
              </Box>
            )}

                    {step.type === 'action' && (
                      <Typography>
                        Action: {step.action}<br/>
                        Args: {JSON.stringify(step.args)}
                      </Typography>
                    )}
            
                {step.action && (
                  <Typography>
                    Action: {step.action}<br/>
                    Args: {JSON.stringify(step.args)}
                  </Typography>
                )}

                {step.type === 'interrupt' && step.needsResponse && (
                  <Box sx={{ mt: 1, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                    <Typography color="error" gutterBottom>
                      {step.message}
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Press Enter to approve or type alternative instructions"
                      value={userResponse}
                      onChange={(e) => setUserResponse(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          sendInterventionResponse();
                        }
                      }}
                      sx={{ mt: 1 }}
                      disabled={!isWaitingForResponse}
                    />
                    <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                      <Button 
                        size="small"
                        variant="contained"
                        color="success"
                        onClick={() => {
                          setUserResponse('');
                          sendInterventionResponse();
                        }}
                        disabled={!isWaitingForResponse}
                      >
                        Approve
                      </Button>
                      <Button 
                        size="small"
                        variant="contained"
                        color="error"
                        onClick={() => {
                          setUserResponse('exit');
                          sendInterventionResponse();
                        }}
                        disabled={!isWaitingForResponse}
                      >
                        Stop Agent
                      </Button>
                    </Box>
                  </Box>
                )}
                  </Box>
                </ListItem>
              ))}
            </ScrollableList>
          </Paper>
        )}
      </Box>
    </Container>
  );
}