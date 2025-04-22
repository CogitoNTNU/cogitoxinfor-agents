"use client";

import React, { useState, useEffect, useRef, useMemo } from 'react';
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
    switch (data.type) {
      case 'SCREENSHOT_UPDATE':
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            image: `${API_BASE_URL}${data.payload.image_url}`,
            type: 'screenshot'
          }
        ]);
        break;
      case 'ACTION_UPDATE':
        setSteps(prev => [
          ...prev,
          { step: data.payload.step, action: data.payload.action, args: data.payload.args, type: 'action' }
        ]);
        break;
      case 'INTERRUPT':
        setIsWaitingForResponse(true);
        setSteps(prev => [
          ...prev,
          {
            step: data.payload.step,
            message: data.payload.message,
            type: 'interrupt',
            needsResponse: true
          }
        ]);
        break;
      case 'FINAL_ANSWER':
        setSteps(prev => [
          ...prev,
          { step: data.payload.step, answer: data.payload.answer, type: 'answer' }
        ]);
        break;
    }
  };

  const handleStartAgent = async payload => {
    try {
      const apiPayload = {
        query: payload.testing ? "" : payload.query,
        testing: payload.testing,
        human_intervention: payload.human_intervention,
        test_actions: payload.testing
          ? payload.test_actions.map(a => ({
              action: a.action,
              args: Array.isArray(a.args) ? a.args : [a.args]
            }))
          : undefined
      };
      const res = await fetch(`${API_BASE_URL}${endpoints.runAgent}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload)
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail.message || JSON.stringify(err.detail));
      }
      const data = await res.json();
      setSessionId(data.session_id);
      connectWebSocket(data.session_id);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleStopAgent = () => {
    wsRef.current?.close();
  };

  const sendInterventionResponse = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'INTERVENTION_RESPONSE',
        payload: { input: userResponse || '' }
      }));
      setUserResponse('');
      setIsWaitingForResponse(false);
      setSteps(prev =>
        prev.map(s =>
          s.type === 'interrupt' && s.needsResponse
            ? { ...s, needsResponse: false }
            : s
        )
      );
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
                          {s.type === 'interrupt' && s.needsResponse && (
                            <Box sx={{ mt: 1, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                              <Typography color="error" gutterBottom>
                                {s.message}
                              </Typography>
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
                                <Button size="small" variant="contained" color="success" onClick={() => { setUserResponse(''); sendInterventionResponse(); }} disabled={!isWaitingForResponse}>
                                  Approve
                                </Button>
                                <Button size="small" variant="contained" color="error" onClick={() => { setUserResponse('exit'); sendInterventionResponse(); }} disabled={!isWaitingForResponse}>
                                  Stop
                                </Button>
                              </Box>
                            </Box>
                          )}
                          {s.type === 'answer' && <Typography>{s.answer}</Typography>}
                        </Box>
                      </ListItem>
                    ))}
                </ScrollableList>
              </Paper>
            )}
          </Box>

          {/* Right: screenshot carousel */}
          <Box sx={{ width: '70%' }}>
            {(() => {
              const shots = steps.filter(s => s.type === 'screenshot');
              if (!shots.length) return null;
              const current = shots[screenshotIndex];
              return (
                <Paper sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Screenshot from step {current.step}
                  </Typography>
                  <StyledImage
                    src={current.image}
                    alt={`Screenshot from step ${current.step}`}
                    sx={{ width: '100%', maxHeight: 400, objectFit: 'contain', mt: 1 }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Button size="small" onClick={() => setScreenshotIndex(i => Math.max(i - 1, 0))} disabled={screenshotIndex === 0}>
                      {'<'}
                    </Button>
                    <Button size="small" onClick={() => setScreenshotIndex(i => Math.min(i + 1, shots.length - 1))} disabled={screenshotIndex === shots.length - 1}>
                      {'>'}
                    </Button>
                  </Box>
                </Paper>
              );
            })()}
          </Box>
        </Box>
      </Container>
      <Box sx={{ position: 'fixed', bottom: 16, right: 16 }}>
        <IconButton color="inherit" onClick={() => setThemeMode(m => (m === 'light' ? 'dark' : 'light'))}>
          {themeMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Box>
      </Box>
    </ThemeProvider>
  );
}
