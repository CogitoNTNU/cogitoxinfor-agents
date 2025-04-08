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
  [MESSAGE_TYPES.ERROR]: [],
  'connection_error': [] // Add this to handle connection errors
} : {};

// WebSocket connection state management
let socket = null;
let reconnectTimeout = null;
let isConnecting = false;
let wsUrl = null;

// Connect to WebSocket server
export function connectWebSocket(url, options = {}) {
  try {
    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected, closing existing connection');
      socket.close();
    }
    
    socket = new WebSocket(url);
    wsUrl = url; // Store URL for potential reconnects
    
    // Set timeout for initial connection
    const connectionTimeout = setTimeout(() => {
      if (socket && socket.readyState !== WebSocket.OPEN) {
        console.error('WebSocket connection timed out');
        socket.close();
        // Trigger connection error callbacks
        if (eventCallbacks['connection_error']) {
          eventCallbacks['connection_error'].forEach(handler => 
            handler('Connection timeout - verify backend server is running')
          );
        }
      }
    }, 5000); // 5 second timeout

    socket.onopen = () => {
      console.log('WebSocket connection established');
      if (options.headers) {
        // Send headers as a message if needed
        const authMessage = { type: 'auth', headers: options.headers };
        socket.send(JSON.stringify(authMessage));
      }
      eventCallbacks[MESSAGE_TYPES.SESSION_UPDATE]?.forEach(handler => 
        handler({ status: 'connected' })
      );
    };
    
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Received message:', message);
        
        if (message.type && eventCallbacks[message.type]) {
          eventCallbacks[message.type].forEach(handler => handler(message.payload || {}));
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (eventCallbacks['connection_error']) {
        eventCallbacks['connection_error'].forEach(handler => handler('Connection error'));
      }
    };
    
    socket.onclose = (event) => {
      console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
      if (!event.wasClean) {
        if (eventCallbacks['connection_error']) {
          eventCallbacks['connection_error'].forEach(handler => 
            handler(`Connection closed unexpectedly: ${event.code}`)
          );
        }
      } else {
        eventCallbacks[MESSAGE_TYPES.SESSION_UPDATE]?.forEach(handler => 
          handler({ status: 'disconnected' })
        );
      }
    };
    
    return true;
  } catch (error) {
    console.error('Failed to connect to WebSocket:', error);
    return false;
  }
}

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