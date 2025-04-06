import { useEffect, useState, useCallback, useRef } from 'react';

// Event types for WebSocket messages
export type WebSocketEvent = {
  type: string;
  payload: any;
};

// Message types
export const MESSAGE_TYPES = {
  SEND_QUERY: 'SEND_QUERY',
  SESSION_UPDATE: 'SESSION_UPDATE',
  SESSION_COMPLETED: 'SESSION_COMPLETED',
  ERROR: 'ERROR',
};

// Use secure WebSocket connection
const SOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(SOCKET_URL);
      
      socket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        
        // Clear any reconnection timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      socket.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data);
          setMessages(prev => [...prev, data]);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      socket.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect after 3 seconds
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };

      socket.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      socketRef.current = socket;
    } catch (err) {
      console.error('Failed to connect to WebSocket:', err);
      setError('Failed to connect to WebSocket server');
      
      // Attempt to reconnect after 3 seconds
      if (!reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    }
  }, []);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Send message to WebSocket server
  const sendMessage = useCallback((type: string, payload: any) => {
    if (socketRef.current && isConnected) {
      const message: WebSocketEvent = { type, payload };
      socketRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, [isConnected]);

  // Send a query to the server
  const sendQuery = useCallback((query: string) => {
    return sendMessage(MESSAGE_TYPES.SEND_QUERY, { query });
  }, [sendMessage]);

  // Clear received messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Connect on component mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    messages,
    error,
    sendMessage,
    sendQuery,
    clearMessages,
    connect,
    disconnect,
  };
};