"use client";
import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Button, CircularProgress } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { API_BASE_URL } from '../services/api';

const BrowserViewer = ({ sessionId, refreshInterval = 2000 }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshTimestamp, setRefreshTimestamp] = useState(Date.now());
  const [initializingBrowser, setInitializingBrowser] = useState(false);
  
  // Initialize browser on first load if needed
  useEffect(() => {
    if (!sessionId) return;
    
    const initBrowser = async () => {
      try {
        setInitializingBrowser(true);
        const res = await fetch(`${API_BASE_URL}/api/session/${sessionId}/init-browser`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!res.ok) {
          const errorData = await res.json();
          console.warn('Browser initialization non-fatal error:', errorData);
        }
        
        // Force refresh the DOM view
        setRefreshTimestamp(Date.now());
      } catch (err) {
        console.error('Error initializing browser:', err);
      } finally {
        setInitializingBrowser(false);
      }
    };
    
    // Only try to initialize once
    initBrowser();
  }, [sessionId]);
  
  // URL with timestamp to prevent caching
  const domUrl = sessionId ? 
    `${API_BASE_URL}/api/browser/${sessionId}/dom?t=${refreshTimestamp}` : 
    null;
  
  // Auto-refresh
  useEffect(() => {
    if (!sessionId) return;
    
    const intervalId = setInterval(() => {
      setRefreshTimestamp(Date.now());
    }, refreshInterval);
    
    return () => clearInterval(intervalId);
  }, [sessionId, refreshInterval]);
  
  const handleRefresh = () => {
    setLoading(true);
    setRefreshTimestamp(Date.now());
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle1">Live Browser View</Typography>
        <Button 
          startIcon={<RefreshIcon />}
          size="small"
          onClick={handleRefresh}
          disabled={!sessionId}
        >
          Refresh
        </Button>
      </Box>
      
      <Box sx={{ position: 'relative', flex: 1, border: '1px solid #ddd', borderRadius: 1, overflow: 'hidden' }}>
        {loading && (
          <Box sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            bgcolor: 'rgba(255,255,255,0.7)',
            zIndex: 2 
          }}>
            <CircularProgress size={24} />
          </Box>
        )}
        
        {!sessionId ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography color="text.secondary">Start a session to view the browser</Typography>
          </Box>
        ) : (
          <iframe 
            src={domUrl}
            style={{ 
              width: '100%', 
              height: '100%', 
              border: 'none',
            }}
            onLoad={() => setLoading(false)}
            onError={(e) => {
              setLoading(false);
              setError("Failed to load browser content");
            }}
            title="Browser View"
          />
        )}
        
        {error && (
          <Box sx={{ 
            position: 'absolute', 
            top: '50%', 
            left: 0, 
            right: 0, 
            textAlign: 'center',
            transform: 'translateY(-50%)',
            color: 'error.main',
            zIndex: 2
          }}>
            {error}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default BrowserViewer;