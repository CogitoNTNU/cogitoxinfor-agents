'use client';

// Check if we're on the client side
const isClient = typeof window !== 'undefined';

// Match message types with backend exactly as defined in backend.py
export const MESSAGE_TYPES = {
  SEND_QUERY: "SEND_QUERY",
  SESSION_UPDATE: "SESSION_UPDATE",
  SESSION_COMPLETED: "SESSION_COMPLETED",
  ACTION_UPDATE: "ACTION_UPDATE",
  SCREENSHOT_UPDATE: "SCREENSHOT_UPDATE",
  HUMAN_INTERVENTION_REQUEST: "HUMAN_INTERVENTION_REQUEST",
  HUMAN_INTERVENTION_RESPONSE: "HUMAN_INTERVENTION_RESPONSE",
  ERROR: "ERROR"
};

// Event callbacks system - only initialize on client
const eventCallbacks = isClient ? {
  [MESSAGE_TYPES.SESSION_UPDATE]: [],
  [MESSAGE_TYPES.SESSION_COMPLETED]: [],
  [MESSAGE_TYPES.ACTION_UPDATE]: [],
  [MESSAGE_TYPES.SCREENSHOT_UPDATE]: [],
  [MESSAGE_TYPES.HUMAN_INTERVENTION_REQUEST]: [],
  [MESSAGE_TYPES.ERROR]: []
} : {};

// WebSocket connection state management
let socket = null;
let reconnectTimeout = null;
let isConnecting = false;
let wsUrl = null;

// Connect to WebSocket server - only if on client
export const connectWebSocket = (url) => {
  if (!isClient) return false;
  
  if (isConnecting || (socket && socket.readyState === WebSocket.OPEN)) {
    console.log(`Already connected or connecting to WebSocket at ${url}`);
    return true;
  }
  
  isConnecting = true;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // Connect to backend port (8000) rather than frontend port
  const wsUrl = `${protocol}//localhost:8000/ws`; 
  
  console.log(`Attempting to connect to WebSocket at ${url}`);
  
  try {
    socket = new WebSocket(url);
    
    socket.onopen = () => {
      console.log('✅ WebSocket connection established');
      isConnecting = false;
      
      // Clear any reconnect timeout
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      
      // Notify subscribers that connection is established
      triggerCallbacks(MESSAGE_TYPES.SESSION_UPDATE, { status: 'connected' });
    };
    
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // Handle the received message by triggering appropriate callbacks
        const { type, payload } = message;
        triggerCallbacks(type, payload);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      isConnecting = false;
      triggerCallbacks(MESSAGE_TYPES.ERROR, { message: 'Connection error' });
    };
    
    socket.onclose = (event) => {
      console.log('WebSocket disconnected', event);
      isConnecting = false;
      socket = null;
      
      // Notify subscribers that connection is closed
      triggerCallbacks(MESSAGE_TYPES.SESSION_UPDATE, { status: 'disconnected' });
      
      // Attempt to reconnect after delay
      reconnectTimeout = setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        if (wsUrl) connectWebSocket(wsUrl);
      }, 5000);
    };
    
    return true;
  } catch (err) {
    console.error('Failed to create WebSocket connection:', err);
    isConnecting = false;
    triggerCallbacks(MESSAGE_TYPES.ERROR, { message: 'Failed to create connection' });
    return false;
  }
};

// Register event listeners
export const on = (eventType, callback) => {
  if (!isClient) return false;
  
  if (eventCallbacks[eventType]) {
    eventCallbacks[eventType].push(callback);
    return true;
  }
  return false;
};

// Unregister event listeners
export const off = (eventType, callback) => {
  if (!isClient) return false;
  
  if (eventCallbacks[eventType]) {
    const index = eventCallbacks[eventType].indexOf(callback);
    if (index !== -1) {
      eventCallbacks[eventType].splice(index, 1);
      return true;
    }
  }
  return false;
};

// Trigger callbacks for an event
const triggerCallbacks = (eventType, payload) => {
  if (!isClient) return;
  
  if (eventCallbacks[eventType]) {
    eventCallbacks[eventType].forEach(callback => {
      try {
        callback(payload);
      } catch (err) {
        console.error(`Error in ${eventType} callback:`, err);
      }
    });
  }
};

// Send a query to the server
export const sendQuery = (query, config = {}) => {
  if (!isClient || !socket || socket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected');
    return false;
  }
  
  try {
    const message = {
      type: MESSAGE_TYPES.SEND_QUERY,
      payload: { 
        query,
        ...config
      }
    };
    
    socket.send(JSON.stringify(message));
    return true;
  } catch (err) {
    console.error('Error sending message:', err);
    return false;
  }
};

// Send a response to a human intervention request
export const sendHumanInterventionResponse = (sessionId, response) => {
  if (!isClient || !socket || socket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected');
    return false;
  }
  
  try {
    const message = {
      type: MESSAGE_TYPES.HUMAN_INTERVENTION_RESPONSE,
      payload: {
        session_id: sessionId,
        response
      }
    };
    
    socket.send(JSON.stringify(message));
    return true;
  } catch (err) {
    console.error('Error sending human intervention response:', err);
    return false;
  }
};

// Check if WebSocket is connected
export const isConnected = () => {
  if (!isClient) return false;
  return socket && socket.readyState === WebSocket.OPEN;
};

// Close WebSocket connection
export const closeConnection = () => {
  if (!isClient) return;
  
  if (socket) {
    socket.close();
    socket = null;
  }
  
  // Clear any reconnection attempts
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
};