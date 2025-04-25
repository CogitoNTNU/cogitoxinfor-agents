import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

// Define API endpoints
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

const endpoints = {
  runAgent: `${API_BASE_URL}/api/agent/run`,
  websocket: (sessionId: string) => `${WS_BASE_URL}/api/ws/${sessionId}`,
  screenshot: (sessionId: string, step: number) => `${API_BASE_URL}/api/history/${sessionId}/${step}`
};

// Define types for our context
interface LogEntry {
  id: string;
  message: string;
  type: 'info' | 'action' | 'error' | 'result';
  timestamp: number;
}

interface Screenshot {
  step: number;
  image: string;
  timestamp: number;
}

interface AgentEvent {
  type: string;
  payload: any;
  session_id?: string; // Added optional session_id
  step?: number; // Added optional step
}

// Define a type for the structure of TOOL_CONFIGURATIONS
interface ToolConfiguration {
  args: number;
  validator: (args: string[]) => { isValid: boolean; error: string };
  placeholder: string;
}

// Define a type for the keys of TOOL_CONFIGURATIONS
type ToolName = 'NAVIGATE' | 'CLICK' | 'TYPE' | 'WAIT' | 'SCROLL';

interface AgentPayload {
  testing: boolean;
  human_intervention: boolean;
  query: string;
  test_actions: { action: ToolName, args: string[] }[];
}

interface AgentContextType {
  isRunning: boolean;
  logs: LogEntry[];
  screenshots: Screenshot[];
  finalAnswer: string | null;
  events: AgentEvent[];
  interruptMessage: string | null; // Added interruptMessage to context type
  respondToInterrupt: (response: string) => void; // Added respondToInterrupt to context type
  startAgent: (payload: AgentPayload) => Promise<void>;
  stopAgent: () => Promise<void>;
  clearLogs: () => void;
  clearScreenshots: () => void;
}

// Create the context with default values
const AgentContext = createContext<AgentContextType>({
  isRunning: false,
  logs: [],
  screenshots: [],
  finalAnswer: null,
  events: [],
  interruptMessage: null, // Added default value
  respondToInterrupt: () => {}, // Added default value
  startAgent: async () => {},
  stopAgent: async () => {},
  clearLogs: () => {},
  clearScreenshots: () => {},
});

// Custom hook to use the context
export const useAgent = () => useContext(AgentContext);

interface AgentProviderProps {
  children: ReactNode;
}

export const AgentProvider: React.FC<AgentProviderProps> = ({ children }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [interruptMessage, setInterruptMessage] = useState<string | null>(null); // Added interruptMessage state
  const wsRef = useRef<WebSocket | null>(null);

  // Function to add a log entry
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prevLogs => [
      ...prevLogs,
      {
        id: uuidv4(),
        message,
        type,
        timestamp: Date.now(),
      }
    ]);
  }, []);

  // Function to add a screenshot
  const addScreenshot = useCallback((image: string, step: number) => {
    setScreenshots(prevScreenshots => [
      ...prevScreenshots,
      {
        step,
        image,
        timestamp: Date.now(),
      }
    ]);
  }, []);

  // Function to send response to interrupt
  const respondToInterrupt = useCallback((response: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Find the last interrupt, agent message, or tool call event to get session_id and step
      const lastInterruptEvent = events.slice().reverse().find(event => 
        event.type === 'INTERRUPT' || event.type === 'AGENT_MESSAGE' || event.type === 'TOOL_CALL'
      );

      if (lastInterruptEvent) {
        const messageToSend = {
          type: 'INTERVENTION_RESPONSE', // Changed type to match backend expectation
          session_id: lastInterruptEvent.session_id,
          step: lastInterruptEvent.step,
          payload: { // Added payload structure
            input: response === '' ? 'approve' : response, // Send 'approve' for default action in payload.input
          },
        };
        wsRef.current.send(JSON.stringify(messageToSend));
        setInterruptMessage(null); // Close the dialog after sending response
      } else {
        console.error('Could not find a recent interrupt event to respond to.');
        // Fallback: send a generic response, though it might not be processed by backend
        wsRef.current.send(JSON.stringify({ type: 'INTERVENTION_RESPONSE', payload: { input: response } }));
        setInterruptMessage(null); // Close the dialog anyway
      }
    }
  }, [events]); // Added events to dependencies

  // Function to start the agent
  const startAgent = useCallback(async (payload: AgentPayload) => {
    if (isRunning) return;

    setIsRunning(true);
    addLog(`Starting agent with task: ${payload.query}`, 'info'); // Updated to use payload.query

    try {
      const response = await fetch(endpoints.runAgent, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Failed to start agent: ${response.statusText}`);
      }

      const data = await response.json();
      const newSessionId = data.session_id;
      setSessionId(newSessionId);
      addLog(`Agent session started with ID: ${newSessionId}`, 'info');

      // Establish WebSocket connection
      wsRef.current = new WebSocket(endpoints.websocket(newSessionId));

      wsRef.current.onopen = () => {
        addLog('WebSocket connection established', 'info');
      };

      wsRef.current.onmessage = (event) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const message = JSON.parse(event.data);
          console.log('WebSocket message received:', message); // Log received messages

          // Add all incoming messages to events
          setEvents(prevEvents => [...prevEvents, message]);

          if (message.type === 'log') {
            addLog(message.message, message.log_type);
          } else if (message.type === 'screenshot') {
            addScreenshot(message.image, message.step);
          } else if (message.type === 'status') {
            if (message.status === 'completed' || message.status === 'error') {
              setIsRunning(false);
              addLog(`Agent run ${message.status}`, message.status === 'completed' ? 'result' : 'error');
              wsRef.current?.close();
            }
          } else if (message.type === 'result') {
            setFinalAnswer(message.answer);
          } else if (message.type === 'INTERRUPT' || message.type === 'AGENT_MESSAGE' || message.type === 'TOOL_CALL') { // Handle interrupt, agent message, and tool call
            setInterruptMessage(JSON.stringify(message, null, 2)); // Display the message payload
          }
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        addLog(`WebSocket error: ${error}`, 'error');
        setIsRunning(false);
      };

      wsRef.current.onclose = (event) => {
        addLog(`WebSocket connection closed: ${event.code} - ${event.reason}`, 'info');
        setIsRunning(false); // Ensure isRunning is false on close
      };

    } catch (error) {
      addLog(`Error starting agent: ${error instanceof Error ? error.message : String(error)}`, 'error');
      setIsRunning(false);
    }
  }, [isRunning, addLog, addScreenshot, respondToInterrupt]); // Added respondToInterrupt to dependencies

  // Function to stop the agent
  const stopAgent = useCallback(async () => {
    if (!isRunning) return;

    addLog('Stopping agent...', 'info');

    // Close WebSocket connection
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    } else {
      setIsRunning(false); // If WS not open, just set isRunning to false
      addLog('Agent stopped (WebSocket not open)', 'info');
    }

    // Note: Assuming closing WebSocket is sufficient to stop backend process.
    // If a dedicated stop endpoint is needed, add fetch call here.

  }, [isRunning, addLog]);

  // Cleanup WebSocket on component unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Function to clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Function to clear screenshots
  const clearScreenshots = useCallback(() => {
    setScreenshots([]);
  }, []);

  // Create the context value
  const contextValue: AgentContextType = {
    isRunning,
    logs,
    screenshots,
    finalAnswer,
    events,
    interruptMessage, // Added to context value
    respondToInterrupt, // Added to context value
    startAgent,
    stopAgent,
    clearLogs,
    clearScreenshots,
  };

  return (
    <AgentContext.Provider value={contextValue}>
      {children}
    </AgentContext.Provider>
  );
};

export default AgentProvider;
