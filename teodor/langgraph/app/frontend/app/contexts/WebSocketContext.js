'use client';

import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import * as WebSocketService from '../services/websocket';
import { MESSAGE_TYPES } from '../services/websocket';

// Create context with default values
const WebSocketContext = createContext({
  isConnected: false,
  messages: [],
  sendQuery: () => false,
  sendHumanInterventionResponse: () => false,
  error: null,
  sessionData: {},
  screenshots: {},
  actions: [],
  humanIntervention: null,
});

export function WebSocketProvider({ children }) {
  // State for React components
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [sessionData, setSessionData] = useState({});
  const [screenshots, setScreenshots] = useState({});
  const [actions, setActions] = useState([]);
  const [humanIntervention, setHumanIntervention] = useState(null);
  const [isClient, setIsClient] = useState(false);
  
  // Keep track of registered event handlers
  const eventHandlersRef = useRef([]);
  
  // Set isClient to true once component mounts (client-side only)
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  // Initialize WebSocket connection - only on client side
  useEffect(() => {
    // Skip if not client side
    if (!isClient) return;
    
    // Use secure WebSocket if the page is served over HTTPS
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Connect to backend port (8000) rather than frontend port
    const wsUrl = `${protocol}//localhost:8000/ws`;
    
    console.log(`Attempting to connect to WebSocket at: ${wsUrl}`);
    
    // Define handlers for different message types
    const handleSessionUpdate = (payload) => {
      if (payload.status === 'connected') {
        setIsConnected(true);
        setError(null);
      } else if (payload.status === 'disconnected') {
        setIsConnected(false);
      }
      
      if (payload.session_id) {
        setSessionData(prev => ({
          ...prev,
          [payload.session_id]: {
            ...prev[payload.session_id],
            status: payload.status,
          }
        }));
      }
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.SESSION_UPDATE, payload }]);
    };
    
    const handleSessionCompleted = (payload) => {
      if (payload.session_id) {
        setSessionData(prev => ({
          ...prev,
          [payload.session_id]: {
            ...prev[payload.session_id],
            status: 'completed',
            result: payload.result,
          }
        }));
      }
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.SESSION_COMPLETED, payload }]);
    };
    
    const handleActionUpdate = (payload) => {
      if (payload.session_id) {
        // Add to actions list
        setActions(prev => [...prev, payload]);
      }
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.ACTION_UPDATE, payload }]);
    };
    
    const handleScreenshotUpdate = (payload) => {
      if (payload.session_id && payload.screenshot) {
        // Add to screenshots collection
        setScreenshots(prev => ({
          ...prev,
          [payload.session_id]: {
            ...prev[payload.session_id],
            [payload.step]: payload.screenshot,
          }
        }));
      }
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.SCREENSHOT_UPDATE, payload }]);
    };
    
    const handleHumanIntervention = (payload) => {
      // Store the human intervention request
      setHumanIntervention(payload);
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.HUMAN_INTERVENTION_REQUEST, payload }]);
    };
    
    const handleError = (payload) => {
      setError(payload.message || 'Unknown error');
      
      if (payload.session_id) {
        setSessionData(prev => ({
          ...prev,
          [payload.session_id]: {
            ...prev[payload.session_id],
            status: 'error',
            error: payload.message,
          }
        }));
      }
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.ERROR, payload }]);
    };
    
    // Register event handlers
    const handlers = [
      { type: MESSAGE_TYPES.SESSION_UPDATE, handler: handleSessionUpdate },
      { type: MESSAGE_TYPES.SESSION_COMPLETED, handler: handleSessionCompleted },
      { type: MESSAGE_TYPES.ACTION_UPDATE, handler: handleActionUpdate },
      { type: MESSAGE_TYPES.SCREENSHOT_UPDATE, handler: handleScreenshotUpdate },
      { type: MESSAGE_TYPES.HUMAN_INTERVENTION_REQUEST, handler: handleHumanIntervention },
      { type: MESSAGE_TYPES.ERROR, handler: handleError },
    ];
    
    // Register all handlers
    handlers.forEach(({ type, handler }) => {
      WebSocketService.on(type, handler);
      // Store handlers for cleanup
      eventHandlersRef.current.push({ type, handler });
    });
    
    // Connect to WebSocket server
    WebSocketService.connectWebSocket(wsUrl);
    
    // Cleanup function
    return () => {
      // Unregister all event handlers
      eventHandlersRef.current.forEach(({ type, handler }) => {
        WebSocketService.off(type, handler);
      });
      
      // Close connection
      WebSocketService.closeConnection();
    };
  }, [isClient]); // Only run when isClient changes to true
  
  // Wrap the sendQuery method from WebSocketService
  const sendQuery = useCallback((query, config = {}) => {
    if (!isClient) return false;
    return WebSocketService.sendQuery(query, config);
  }, [isClient]);
  
  // Wrap the sendHumanInterventionResponse method
  const sendHumanInterventionResponse = useCallback((sessionId, response) => {
    if (!isClient) return false;
    // Reset the human intervention state
    setHumanIntervention(null);
    return WebSocketService.sendHumanInterventionResponse(sessionId, response);
  }, [isClient]);
  
  // The value provided to consumers
  const contextValue = {
    isConnected,
    messages,
    sendQuery,
    sendHumanInterventionResponse,
    error,
    sessionData,
    screenshots,
    actions,
    humanIntervention,
  };
  
  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  return useContext(WebSocketContext);
}