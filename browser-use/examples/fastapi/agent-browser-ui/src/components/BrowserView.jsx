import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, CircularProgress, Button, 
  Slider, IconButton, Paper, Stack 
} from '@mui/material';
import { 
  SkipPrevious, SkipNext, Refresh, 
  PlayArrow, Pause
} from '@mui/icons-material';
import { agentApi } from '../services/api';

function BrowserView({ agentId }) {
  const [status, setStatus] = useState(null);
  const [screenshot, setScreenshot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState({ step_count: 0, steps: [] });
  const [currentStep, setCurrentStep] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1000); // ms between steps

  // Fetch agent status and history
  useEffect(() => {
    if (!agentId) return;
    
    const fetchData = async () => {
      try {
        const [statusResponse, historyResponse] = await Promise.all([
          agentApi.getAgentStatus(agentId),
          agentApi.getAgentHistory(agentId)
        ]);
        
        setStatus(statusResponse.data.status);
        setHistory(historyResponse.data);
        
        // If there's history, set current step to latest by default
        if (historyResponse.data.step_count > 0) {
          setCurrentStep(historyResponse.data.step_count - 1);
        }
      } catch (error) {
        console.error("Error fetching agent data:", error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000);
    
    return () => clearInterval(interval);
  }, [agentId]);

  const [screenshotUrl, setScreenshotUrl] = useState(null);

  // Update the useEffect that loads screenshots
  useEffect(() => {
    if (!agentId || currentStep === null) return;
    
    const loadScreenshot = async () => {
      setIsLoading(true);
      try {
        // Check if we already have a URL for this step in history
        if (history.steps && 
            history.steps[currentStep] && 
            history.steps[currentStep].screenshot_url) {
          // Use the direct file URL
          setScreenshotUrl(history.steps[currentStep].screenshot_url);
          setScreenshot(null); // Clear base64 data
        } else {
          // Fall back to API method with base64 data
          const isLatestStep = currentStep === history.step_count - 1;
          const response = await agentApi.getAgentScreenshot(
            agentId, 
            status === 'running' && isLatestStep ? null : currentStep
          );
          
          if (response.data.screenshot) {
            setScreenshot(response.data.screenshot);
            setScreenshotUrl(null);
          }
        }
      } catch (error) {
        console.error("Error loading screenshot:", error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadScreenshot();
    
    // Rest of the effect remains the same...
  }, [agentId, currentStep, status, history.step_count]);
  

  // Handle auto-playback of history
  useEffect(() => {
    if (!isPlaying || history.step_count === 0) return;
    
    const playbackInterval = setInterval(() => {
      setCurrentStep(prevStep => {
        const nextStep = prevStep + 1;
        // Stop playing if we reach the end
        if (nextStep >= history.step_count - 1) {
          setIsPlaying(false);
        }
        return nextStep < history.step_count ? nextStep : prevStep;
      });
    }, playbackSpeed);
    
    return () => clearInterval(playbackInterval);
  }, [isPlaying, history.step_count, playbackSpeed]);

  const handlePrevious = () => {
    setCurrentStep(prevStep => Math.max(0, prevStep - 1));
  };

  const handleNext = () => {
    setCurrentStep(prevStep => Math.min(history.step_count - 1, prevStep + 1));
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  const handleRefresh = async () => {
    if (!agentId) return;
    setIsLoading(true);
    
    try {
      // For running agents, get fresh data
      if (status === 'running') {
        const [historyResponse, screenshotResponse] = await Promise.all([
          agentApi.getAgentHistory(agentId),
          agentApi.getAgentScreenshot(agentId)
        ]);
        
        setHistory(historyResponse.data);
        setScreenshot(screenshotResponse.data.screenshot);
        setCurrentStep(historyResponse.data.step_count - 1);
      } 
      // For other agents, just refresh the current step
      else if (currentStep !== null) {
        const response = await agentApi.getAgentScreenshot(agentId, currentStep);
        setScreenshot(response.data.screenshot);
      }
    } catch (error) {
      console.error("Error refreshing:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!agentId) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography variant="body1">Select an agent to view its browser</Typography>
      </Box>
    );
  }

  const currentStepInfo = currentStep !== null && currentStep < history.steps.length 
    ? history.steps[currentStep] 
    : null;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6">
          Browser View: {agentId} {status && `(${status})`}
        </Typography>
        
        <Button 
          size="small"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>
      
      {/* Browser content display */}
      <Paper 
        sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          position: 'relative',
          overflow: 'hidden',
          bgcolor: '#f5f5f5',
          mb: 1
        }}
      >
        {isLoading && (
          <CircularProgress 
            size={20} 
            sx={{ position: 'absolute', top: 10, right: 10 }} 
          />
        )}
        
        {screenshotUrl ? (
            <img 
                src={screenshotUrl} 
                alt="Browser screenshot"
                style={{ 
                maxHeight: '100%', 
                maxWidth: '100%', 
                objectFit: 'contain' 
                }}
            />
            ) : screenshot ? (
            <img 
                src={`data:image/png;base64,${screenshot}`} 
                alt="Browser screenshot"
                style={{ 
                maxHeight: '100%', 
                maxWidth: '100%', 
                objectFit: 'contain' 
                }}
            />
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            {status === 'paused' && <Typography>Agent is paused</Typography>}
            {status === 'stopped' && <Typography>Agent is stopped</Typography>}
            {status === 'running' && <Typography>Waiting for screenshot...</Typography>}
            {!status && <CircularProgress size={20} />}
          </Box>
        )}
      </Paper>
      
      {/* Step information */}
      {currentStepInfo && (
        <Paper sx={{ p: 1, mb: 1, bgcolor: '#f0f9ff' }}>
          <Typography variant="subtitle2" gutterBottom>
            {currentStepInfo.title || 'No title'} - {currentStepInfo.url}
          </Typography>
          <Typography variant="body2">
            Goal: {currentStepInfo.goal || 'No goal available'}
          </Typography>
        </Paper>
      )}
      
      {/* Playback controls */}
      {history.step_count > 0 && (
        <Stack direction="row" spacing={1} alignItems="center">
          <IconButton onClick={handlePrevious} disabled={currentStep === 0}>
            <SkipPrevious />
          </IconButton>
          
          <IconButton onClick={togglePlayback}>
            {isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
          
          <IconButton onClick={handleNext} disabled={currentStep === history.step_count - 1}>
            <SkipNext />
          </IconButton>
          
          <Typography variant="caption" sx={{ minWidth: 60 }}>
            {(currentStep !== null ? currentStep + 1 : 0)}/{history.step_count}
          </Typography>
          
          <Slider
            size="small"
            min={0}
            max={Math.max(0, history.step_count - 1)}
            value={currentStep !== null ? currentStep : 0}
            onChange={(_, value) => setCurrentStep(value)}
            disabled={history.step_count <= 1}
            sx={{ flex: 1, maxWidth: '50%' }}
          />
        </Stack>
      )}
    </Box>
  );
}

export default BrowserView;