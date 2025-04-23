"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  CssBaseline,
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Switch,
  FormControlLabel,
  List,
  ListItem
} from '@mui/material';
import { styled } from '@mui/material/styles';
import IconButton from '@mui/material/IconButton';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import BrowserViewer from './components/BrowserViewer';
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
  // Theme mode state
  const [themeMode, setThemeMode] = useState('light');
  const theme = useMemo(
    () => createTheme({ palette: { mode: themeMode } }),
    [themeMode]
  );

  // Agent session state
  const [sessionId, setSessionId] = useState(null);
  const [steps, setSteps] = useState([]);
  const [connected, setConnected] = useState(false);
  const [userResponse, setUserResponse] = useState('');
  const wsRef = useRef(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [screenshotIndex, setScreenshotIndex] = useState(0);
  const [viewTab, setViewTab] = useState(0);
  const [activeToolExecution, setActiveToolExecution] = useState(null);

  // WebSocket connection
  const connectWebSocket = sid => {
    const ws = new WebSocket(`${WS_BASE_URL}${endpoints.websocket(sid)}`);
    ws.onopen = () => setConnected(true);
    ws.onerror = () => {
      setConnected(false);
      setIsWaitingForResponse(false);
    };
    ws.onclose = () => {
      setConnected(false);
      setIsWaitingForResponse(false);
    };
    ws.onmessage = e => handleWebSocketMessage(JSON.parse(e.data));
    wsRef.current = ws;
  };

  const handleWebSocketMessage = data => {
    console.log('Received websocket message:', data);
    
    switch (data.type) {
      case 'SCREENSHOT_UPDATE':
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            // Handle both direct base64 data and URL paths
            image: `data:image/png;base64,${data.payload.image_data}`,
            type: 'screenshot',
            timestamp: data.payload.timestamp || Date.now()
          }
        ]);
        
        // Auto-switch to screenshots tab when a new one arrives
        if (viewTab !== 0) setViewTab(0); 
        break;
        
      case 'ACTION_UPDATE':
        setSteps(prev => [
          ...prev,
          { 
            step: data.payload.step, 
            action: data.payload.action, 
            args: data.payload.args, 
            type: 'action' 
          }
        ]);
        
        // Clear active tool execution
        setActiveToolExecution(null);
        break;
        
      case 'INTERRUPT':
        setIsWaitingForResponse(true);
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            message: data.payload.message,
            type: 'interrupt',
            needsResponse: true,
            tool: data.payload.tool // Include structured tool info
          }
        ]);
        
        // Auto-switch to progress tab to show the prompt
        setViewTab(0);
        break;
        
      case 'FINAL_ANSWER':
        setSteps(prev => [
          ...prev,
          { 
            step: data.payload.step, 
            answer: data.payload.answer, 
            type: 'answer' 
          }
        ]);
        break;
        
      case 'TOOL_CALL':
        // Store tool call in steps to track agent actions
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            tool: data.payload.tool.name,
            args: data.payload.tool.args,
            type: 'tool_call'
          }
        ]);
        
        // Set active tool execution for visual indicator
        setActiveToolExecution({
          tool: data.payload.tool.name,
          args: data.payload.tool.args,
          step: data.payload.step,
          timestamp: data.payload.timestamp
        });
        
        // Auto-switch to browser view for better visibility of tool actions
        if (data.payload.tool.name.startsWith('browser_') && viewTab !== 0) {
          setViewTab(0); // Switch to browser tab on browser actions
        }
        break;
        
      case 'AGENT_MESSAGE':
        // Add agent messages to the progress
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            message: data.payload.message,
            type: 'agent_message'
          }
        ]);
        break;
        
      case 'COMPLETED':
        setIsWaitingForResponse(false);
        setConnected(false); // Mark session as completed
        
        // Add a status message to the steps
        setSteps(prev => [
          ...prev,
          { 
            step: prev.length, 
            type: 'status',
            status: 'completed',
            timestamp: Date.now()
          }
        ]);
        
        // If there's an answer, add it too
        if (data.payload.answer) {
          setSteps(prev => [
            ...prev,
            { step: prev.length, answer: data.payload.answer, type: 'answer' }
          ]);
        }
        break;
        
      case 'ERROR':
        setIsWaitingForResponse(false);
        setConnected(false);
        alert(`Error: ${data.payload.message}`);
        break;
    }
  };

  // Auto-connect on page load
  useEffect(() => {
    const storedSessionId = localStorage.getItem('webAgentSessionId');
    const reconnect = async () => {
      if (storedSessionId) {
        try {
          // Check if session still exists on server
          const response = await fetch(`${API_BASE_URL}/api/session/${storedSessionId}/status`);
          if (response.ok) {
            const data = await response.json();
            if (data.status === "active") {
              setSessionId(storedSessionId);
              connectWebSocket(storedSessionId);
              return;
            }
          }
        } catch (err) {
          console.error("Error checking stored session:", err);
        }
        
        // Session not available, create a new one
        createEmptySession();
      } else {
        // No stored session, create a new one
        createEmptySession();
      }
    };
    
    reconnect();
  }, []);

  // Create a session without starting the agent execution
  const createEmptySession = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_browser_only: true })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail?.message || JSON.stringify(err.detail));
      }
      
      const data = await res.json();
      setSessionId(data.session_id);
      
      // Store session ID for reconnection
      localStorage.setItem('webAgentSessionId', data.session_id);
      
      // Connect to WebSocket for status updates
      connectWebSocket(data.session_id);
    } catch (err) {
      console.error("Error creating empty session:", err);
    }
  }, []);

  const handleStartAgent = async payload => {
    try {
      // If we already have a session, use it
      const apiPayload = {
        query: payload.testing ? "" : payload.query,
        testing: payload.testing,
        human_intervention: payload.human_intervention,
        test_actions: payload.testing
          ? payload.test_actions.map(a => ({
              action: a.action,
              args: Array.isArray(a.args) ? a.args : [a.args]
            }))
          : undefined,
        session_id: sessionId // Pass the existing session ID
      };
      
      const res = await fetch(`${API_BASE_URL}${endpoints.runAgent}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload)
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail?.message || JSON.stringify(err.detail));
      }
      
      // Reset steps for new execution
      setSteps([]);
      
      // If session changed (unlikely), update it
      const data = await res.json();
      if (data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem('webAgentSessionId', data.session_id);
        connectWebSocket(data.session_id);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleStopAgent = () => {
    wsRef.current?.close();
  };

  const resetSession = useCallback(async () => {
    // Close current WebSocket
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Remove stored session
    localStorage.removeItem('webAgentSessionId');
    setSessionId(null);
    setSteps([]);
    setConnected(false);
    
    // Create a new session
    await createEmptySession();
  }, [createEmptySession]);

  const sendInterventionResponse = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Get the latest interrupt step to find what we're responding to
      const interruptStep = [...steps].reverse().find(s => s.type === 'interrupt' && s.needsResponse);
      
      // Send response to the server
      wsRef.current.send(JSON.stringify({
        type: 'INTERVENTION_RESPONSE',
        payload: { 
          input: userResponse || '',
          step: interruptStep?.step,
          // Include info about what tool/action we're responding to
          tool: interruptStep?.tool
        }
      }));
      
      // Reset UI state
      setUserResponse('');
      setIsWaitingForResponse(false);
      setSteps(prev =>
        prev.map(s =>
          s.type === 'interrupt' && s.needsResponse
            ? { ...s, needsResponse: false }
            : s
        )
      );
      
      // If we're showing a tool call interrupt, auto-switch to browser view
      // to see the results of the approved action
      if (interruptStep?.tool?.name?.startsWith('browser_')) {
        setViewTab(0); // Switch to browser tab
      }
    }
  };

  useEffect(() => {
    const shots = steps.filter(s => s.type === 'screenshot');
    if (shots.length) setScreenshotIndex(shots.length - 1);
  }, [steps]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ bgcolor: 'background.default', color: 'text.primary', minHeight: '100vh' }}>
      <Container disableGutters maxWidth="lg" sx={{ py: 4, px: 0 }}>
        <Typography variant="h4" gutterBottom>
          Web Agent Interface
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
          {/* Left: controls and progress */}
          <Box sx={{ width: '60%' }}>
            <AgentController onStart={handleStartAgent} onStop={handleStopAgent} isRunning={connected} />
            {steps.some(s => s.type !== 'screenshot') && (
              <Paper sx={{ p: 1, mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Session Progress
                </Typography>
                <ScrollableList>
                  {steps
                    .filter(s => s.type !== 'screenshot')
                    .map((s, i) => (
                      <ListItem key={i} divider>
                        <Box sx={{ width: '100%' }}>
                          <Typography variant="subtitle2">Step {s.step}</Typography>
                          
                          {s.type === 'action' && (
                            <Typography>
                              Action: {s.action}<br />
                              Args: {JSON.stringify(s.args)}
                            </Typography>
                          )}
                          
                          {s.type === 'tool_call' && (
                            <Box sx={{ mt: 1, p: 1, bgcolor: 'info.light', borderRadius: 1, opacity: 0.9 }}>
                              <Typography variant="body2" fontWeight="medium">
                                Tool Call: <strong>{s.tool}</strong>
                              </Typography>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9rem' }}>
                                Args: {JSON.stringify(s.args, null, 2)}
                              </Typography>
                            </Box>
                          )}
                          
                          {s.type === 'agent_message' && (
                            <Box sx={{ mt: 1, p: 1.5, bgcolor: 'success.light', borderRadius: 1 }}>
                              <Typography sx={{ whiteSpace: 'pre-wrap' }}>{s.message}</Typography>
                            </Box>
                          )}
                          
                          {s.type === 'interrupt' && (
                            <Box sx={{ mt: 1, p: 2, bgcolor: s.needsResponse ? 'warning.light' : 'warning.light', 
                                        borderRadius: 1, opacity: s.needsResponse ? 1 : 0.8 }}>
                              <Typography color={s.needsResponse ? "error" : "inherit"} gutterBottom>
                                {s.message}
                              </Typography>
                              
                              {s.needsResponse && (
                                <>
                                  <TextField
                                    fullWidth
                                    size="small"
                                    placeholder="Type instructions or press Enter to approve"
                                    value={userResponse}
                                    onChange={e => setUserResponse(e.target.value)}
                                    onKeyPress={e => { if (e.key === 'Enter') sendInterventionResponse(); }}
                                    disabled={!isWaitingForResponse}
                                    sx={{ mt: 1 }}
                                  />
                                  <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                                    <Button size="small" variant="contained" color="success" 
                                            onClick={() => { setUserResponse(''); sendInterventionResponse(); }} 
                                            disabled={!isWaitingForResponse}>
                                      Approve
                                    </Button>
                                    <Button size="small" variant="contained" color="error" 
                                            onClick={() => { setUserResponse('exit'); sendInterventionResponse(); }} 
                                            disabled={!isWaitingForResponse}>
                                      Stop
                                    </Button>
                                  </Box>
                                </>
                              )}
                            </Box>
                          )}
                          
                          {s.type === 'answer' && (
                            <Box sx={{ mt: 1, p: 1.5, bgcolor: 'primary.light', borderRadius: 1 }}>
                              <Typography sx={{ whiteSpace: 'pre-wrap' }}>{s.answer}</Typography>
                            </Box>
                          )}
                          
                          {/* Support for COMPLETED status message */}
                          {s.type === 'status' && (
                            <Box sx={{ mt: 1, p: 1, borderRadius: 1, bgcolor: 'background.paper', 
                                       border: '1px dashed', borderColor: 'divider' }}>
                              <Typography variant="body2" color="text.secondary" align="center">
                                {s.status === 'completed' ? 'Session completed' : s.status}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </ListItem>
                    ))}
                </ScrollableList>
              </Paper>
            )}
          </Box>

          {/* Right: Browser view and screenshots */}
          <Box sx={{ width: '70%' }}>
            <Paper sx={{ p: 2 }}>
              <Tabs 
                value={viewTab} 
                onChange={(e, newValue) => setViewTab(newValue)}
                sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
              >
                <Tab label="Screenshots" />
                <Tab label="Live Browser" />
              </Tabs>
              
              {/* Tab 1: Screenshot History */}
              {viewTab === 0 && (() => {
                const shots = steps.filter(s => s.type === 'screenshot');
                if (!shots.length) return (
                  <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Typography color="text.secondary">No screenshots available</Typography>
                  </Box>
                );
                
                const current = shots[screenshotIndex];
                return (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Screenshot from step {current.step}
                    </Typography>
                    <StyledImage
                      src={current.image}
                      alt={`Screenshot from step ${current.step}`}
                      sx={{ width: '100%', maxHeight: 400, objectFit: 'contain', mt: 1 }}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                      <Button 
                        size="small" 
                        onClick={() => setScreenshotIndex(i => Math.max(i - 1, 0))} 
                        disabled={screenshotIndex === 0}
                      >
                        {'<'}
                      </Button>
                      <Typography variant="caption">
                        {screenshotIndex + 1} of {shots.length}
                      </Typography>
                      <Button 
                        size="small" 
                        onClick={() => setScreenshotIndex(i => Math.min(i + 1, shots.length - 1))} 
                        disabled={screenshotIndex === shots.length - 1}
                      >
                        {'>'}
                      </Button>
                    </Box>
                  </Box>
                );
              })()}

              {/* Tab 2: Live Browser View */}
              {viewTab === 1 && (
                <Box sx={{ height: 450 }}>
                  <BrowserViewer sessionId={sessionId} refreshInterval={3000} />
                </Box>
              )}
            </Paper>
          </Box>
        </Box>
      </Container>
      <Box sx={{ position: 'fixed', bottom: 16, right: 16, display: 'flex', gap: 1 }}>
        <Button 
          variant="contained" 
          color="secondary" 
          size="small" 
          onClick={resetSession}
          disabled={!sessionId}
        >
          Reset Browser
        </Button>
        <IconButton color="inherit" onClick={() => setThemeMode(m => (m === 'light' ? 'dark' : 'light'))}>
          {themeMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Box>
      </Box>
    </ThemeProvider>
  );
}
