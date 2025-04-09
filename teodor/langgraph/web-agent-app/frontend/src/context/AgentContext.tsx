
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { websocketService } from '../services/websocketService';
import { toast } from "sonner";
import { TestAction } from '../components/TestActionsList';

export interface AgentEvent {
  id: string;
  type: 'SCREENSHOT_UPDATE' | 'ACTION_UPDATE' | 'INTERRUPT' | 'FINAL_ANSWER';
  payload: any;
  timestamp: Date;
}

interface AgentConfig {
  testing?: boolean;
  test_actions?: TestAction[];
  human_intervention?: boolean;
}

interface AgentContextType {
  events: AgentEvent[];
  isConnected: boolean;
  isRunning: boolean;
  sessionId: string | null;
  screenshots: Record<number, string>;
  currentScreenshot: string | null;
  currentStep: number;
  finalAnswer: string | null;
  interruptMessage: string | null;
  startAgent: (sessionId: string, query: string, config?: AgentConfig) => Promise<void>;
  stopAgent: () => void;
  respondToInterrupt: (input: string) => void;
  resetSession: () => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export const AgentProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [screenshots, setScreenshots] = useState<Record<number, string>>({});
  const [currentScreenshot, setCurrentScreenshot] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [interruptMessage, setInterruptMessage] = useState<string | null>(null);

  useEffect(() => {
    const removeListener = websocketService.onMessage((data) => {
      const newEvent: AgentEvent = {
        id: Date.now().toString(),
        type: data.type,
        payload: data.payload,
        timestamp: new Date()
      };
      
      setEvents(prev => [...prev, newEvent]);
      
      switch (data.type) {
        case 'SCREENSHOT_UPDATE':
          const imageUrl = data.payload.image_url;
          const step = data.payload.step;
          
          setScreenshots(prev => ({ ...prev, [step]: imageUrl }));
          setCurrentScreenshot(imageUrl);
          setCurrentStep(step);
          break;
        
        case 'ACTION_UPDATE':
          setCurrentStep(data.payload.step);
          toast.info(`Action: ${data.payload.action}`);
          break;
        
        case 'INTERRUPT':
          setInterruptMessage(data.payload.message);
          toast.warning("Agent needs input", {
            description: data.payload.message
          });
          break;
        
        case 'FINAL_ANSWER':
          setFinalAnswer(data.payload.answer);
          setIsRunning(false);
          toast.success("Agent completed task", {
            description: "Final answer received"
          });
          break;
          
        default:
          break;
      }
    });
    
    return () => removeListener();
  }, []);

  const startAgent = async (
    newSessionId: string, 
    query: string, 
    config?: AgentConfig
  ) => {
    resetSession();
    
    try {
      // 1. First call the API to create a session
      const response = await fetch('http://localhost:8000/api/agent/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          testing: config?.testing || false,
          human_intervention: config?.human_intervention !== undefined ? config.human_intervention : true,
          test_actions: config?.test_actions || []
        })
      });
      
      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }
      
      // 2. Get session ID from response
      const data = await response.json();
      const sessionId = data.session_id;
      
      // 3. Now connect to WebSocket with this session ID
      setSessionId(sessionId);
      const connected = await websocketService.connect(sessionId);
      
      if (connected) {
        setIsConnected(true);
        setIsRunning(true);
        
        toast.info("Agent started", {
          description: "Connected and running"
        });
      } else {
        toast.error("Connection failed", {
          description: "Could not connect to agent"
        });
      }
    } catch (error) {
      console.error("Error starting agent:", error);
      toast.error("Failed to start agent", {
        description: error.message || "An unexpected error occurred"
      });
    }
  };

  const stopAgent = () => {
    websocketService.disconnect();
    setIsRunning(false);
    setIsConnected(false);
    toast.info("Agent stopped");
  };

  const respondToInterrupt = (input: string) => {
    websocketService.respondToInterrupt(input);
    setInterruptMessage(null);
    toast.info("Response sent", {
      description: input || "Default approval"
    });
  };

  const resetSession = () => {
    setEvents([]);
    setScreenshots({});
    setCurrentScreenshot(null);
    setCurrentStep(0);
    setFinalAnswer(null);
    setInterruptMessage(null);
  };

  return (
    <AgentContext.Provider value={{
      events,
      isConnected,
      isRunning,
      sessionId,
      screenshots,
      currentScreenshot,
      currentStep,
      finalAnswer,
      interruptMessage,
      startAgent,
      stopAgent,
      respondToInterrupt,
      resetSession
    }}>
      {children}
    </AgentContext.Provider>
  );
};

export const useAgent = () => {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
};
