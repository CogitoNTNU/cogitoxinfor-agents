import React, { createContext, useContext, ReactNode } from 'react';
import { useWebSocket, WebSocketEvent } from '../services/websocket';

type WebSocketContextType = {
  isConnected: boolean;
  messages: WebSocketEvent[];
  error: string | null;
  sendMessage: (type: string, payload: any) => boolean;
  sendQuery: (query: string) => boolean;
  clearMessages: () => void;
  connect: () => void;
  disconnect: () => void;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const websocket = useWebSocket();
  
  return (
    <WebSocketContext.Provider value={websocket}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};