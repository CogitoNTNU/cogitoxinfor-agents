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
  currentSessionId: null,
});

export function WebSocketProvider({ children }) {
  // State for React components
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [sessionData, setSessionData] = useState({});
  const [screenshots, setScreenshots] = useState({});
  const [bboxes, setBboxes] = useState({});
  const [actions, setActions] = useState([]);
  const [humanIntervention, setHumanIntervention] = useState(null);
  const [isClient, setIsClient] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  
  // Keep track of registered event handlers
  const eventHandlersRef = useRef([]);
  
  // Set isClient to true once component mounts (client-side only)
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  // Create a session with the backend API
  const createSession = useCallback(async (query, options = {}) => {
    try {
      const response = await fetch('/api/agent/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          testing: options.testing || false,
          test_actions: options.test_actions || null,
          human_intervention: options.human_intervention || false
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Session created:', data);
      setCurrentSessionId(data.session_id);
      
      // Initialize session data
      setSessionData(prev => ({
        ...prev,
        [data.session_id]: {
          status: 'initialized',
          query
        }
      }));
      
      return data.session_id;
    } catch (error) {
      console.error('Error creating session:', error);
      setError(`Failed to create session: ${error.message}`);
      return null;
    }
  }, []);
  
  // Function to get WebSocket URL with session ID
  const getWebSocketUrl = useCallback((sessionId) => {
    // Use environment variable if available
    if (process.env.NEXT_PUBLIC_WEBSOCKET_URL) {
      return `${process.env.NEXT_PUBLIC_WEBSOCKET_URL}/${sessionId}`;
    }
    
    // Otherwise construct based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;
    
    // Try different ports in development (nextjs typically runs on 3000, backend on 8000)
    const port = process.env.NODE_ENV === 'production' 
      ? window.location.port 
      : '8000';
      
    return `${protocol}//${hostname}:${port}/api/ws/${sessionId}`;
  }, []);
  
  // Connect to WebSocket with session ID
  const connectToSession = useCallback((sessionId) => {
    if (!isClient || !sessionId) return false;
    
    const wsUrl = getWebSocketUrl(sessionId);
    console.log(`Connecting to WebSocket with session ID ${sessionId} at: ${wsUrl}`);
    
    // Pass connection options with headers for authorization
    const connectionOptions = {
      headers: {
        'Authorization': 'Bearer client-connection', // Add appropriate auth token if needed
        'Origin': window.location.origin
      }
    };
    
    // Connect to WebSocket server with options
    return WebSocketService.connectWebSocket(wsUrl, connectionOptions);
  }, [isClient, getWebSocketUrl]);
  
  // Initialize WebSocket connection - only when we have a session ID
  useEffect(() => {
    // Skip if not client side or no session ID
    if (!isClient || !currentSessionId) return;
    
    console.log(`Setting up connection for session: ${currentSessionId}`);
    
    // Define handlers for different message types
    const handleSessionUpdate = (payload) => {
      if (payload.status === 'connected') {
        setIsConnected(true);
        setError(null);
        setReconnectAttempts(0); // Reset reconnect attempts on successful connection
      } else if (payload.status === 'disconnected') {
        setIsConnected(false);
      }
      
      // Update session data
      setSessionData(prev => ({
        ...prev,
        [currentSessionId]: {
          ...prev[currentSessionId],
          status: payload.status,
        }
      }));
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.SESSION_UPDATE, payload }]);
    };
    
    const handleSessionCompleted = (payload) => {
      setSessionData(prev => ({
        ...prev,
        [currentSessionId]: {
          ...prev[currentSessionId],
          status: 'completed',
          result: payload.result,
        }
      }));
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.SESSION_COMPLETED, payload }]);
    };
    
    const handleActionUpdate = (payload) => {
      // Add to actions list
      setActions(prev => [...prev, payload]);
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.ACTION_UPDATE, payload }]);
    };
    
    const handleScreenshotUpdate = (payload) => {
      if (payload.screenshot || payload.image_url) {
        // Add to screenshots collection if screenshot exists
        if (payload.screenshot) {
          setScreenshots(prev => ({
            ...prev,
            [currentSessionId]: {
              ...prev[currentSessionId],
              [payload.step]: payload.screenshot,
            }
          }));
        }
        
        // Store bounding boxes if available
        if (payload.bboxes) {
          setBboxes(prev => ({
            ...prev,
            [currentSessionId]: {
              ...prev[currentSessionId],
              [payload.step]: payload.bboxes
            }
          }));
        }
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
      
      setSessionData(prev => ({
        ...prev,
        [currentSessionId]: {
          ...prev[currentSessionId],
          status: 'error',
          error: payload.message,
        }
      }));
      
      // Add to messages list
      setMessages(prev => [...prev, { type: MESSAGE_TYPES.ERROR, payload }]);
    };
    
    const handleConnectionError = (errorMsg) => {
      setError(errorMsg || 'Connection error');
      setIsConnected(false);
      
      // Implement reconnection strategy with increasing delay
      const maxReconnects = 5;
      if (reconnectAttempts < maxReconnects) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // Exponential backoff up to 30s
        console.log(`Connection failed. Reconnecting in ${delay/1000} seconds...`);
        
        setTimeout(() => {
          setReconnectAttempts(prev => prev + 1);
          connectToSession(currentSessionId);
        }, delay);
      } else {
        console.error('Maximum reconnection attempts reached');
      }
    };
    
    // Register event handlers
    const handlers = [
      { type: MESSAGE_TYPES.SESSION_UPDATE, handler: handleSessionUpdate },
      { type: MESSAGE_TYPES.SESSION_COMPLETED, handler: handleSessionCompleted },
      { type: MESSAGE_TYPES.ACTION_UPDATE, handler: handleActionUpdate },
      { type: MESSAGE_TYPES.SCREENSHOT_UPDATE, handler: handleScreenshotUpdate },
      { type: MESSAGE_TYPES.HUMAN_INTERVENTION_REQUEST, handler: handleHumanIntervention },
      { type: MESSAGE_TYPES.ERROR, handler: handleError },
      { type: 'connection_error', handler: handleConnectionError },
    ];
    
    // Register all handlers
    handlers.forEach(({ type, handler }) => {
      WebSocketService.on(type, handler);
      // Store handlers for cleanup
      eventHandlersRef.current.push({ type, handler });
    });
    
    // Connect to WebSocket server 
    connectToSession(currentSessionId);
    
    // Cleanup function
    return () => {
      // Unregister all event handlers
      eventHandlersRef.current.forEach(({ type, handler }) => {
        WebSocketService.off(type, handler);
      });
      
      // Close connection
      WebSocketService.closeConnection();
    };
  }, [isClient, currentSessionId, connectToSession, reconnectAttempts]); 
  
  const sendQuery = useCallback(async (query, config = {}) => {
    if (!isClient) return false;
    
    console.log("Starting query process, current session:", currentSessionId);
    
    // First create a session if we don't have one
    if (!currentSessionId) {
      console.log("No active session, creating one first...");
      const sessionId = await createSession(query, config);
      if (!sessionId) {
        console.error("Failed to create session");
        return false;
      }
      console.log("Session created successfully:", sessionId);
      // Connection will be established by the useEffect
      return true;
    }
    
    console.log("Using existing session:", currentSessionId);
    // Otherwise, use existing session to send query
    return WebSocketService.sendQuery(query, config);
  }, [isClient, currentSessionId, createSession]);

  
  // Wrap the sendHumanInterventionResponse method
  const sendHumanInterventionResponse = useCallback((response) => {
    if (!isClient || !currentSessionId) return false;
    
    // Reset the human intervention state
    setHumanIntervention(null);
    return WebSocketService.sendHumanInterventionResponse(currentSessionId, response);
  }, [isClient, currentSessionId]);
  
  // The value provided to consumers
  const contextValue = {
    isConnected,
    messages,
    sendQuery,
    sendHumanInterventionResponse,
    error,
    sessionData,
    screenshots,
    bboxes,
    actions,
    humanIntervention,
    reconnectAttempts,
    currentSessionId,
    createSession,
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