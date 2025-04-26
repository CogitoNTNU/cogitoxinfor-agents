import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { agentApi } from '../services/api';

// Add LogEntry interface
interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  source?: string;
}

interface AgentContextProps {
  children: React.ReactNode;
}

interface AgentContextType {
  screenshots: any[];
  isRunning: boolean;
  isPaused: boolean;
  finalAnswer: string | null;
  events: any[];
  currentAgentId: string | null;
  actionHistory: any[];
  logs: LogEntry[];
  clearLogs: () => void;
  fetchLatestScreenshot: (stepNumber?: number) => Promise<string | null>;
  setCurrentAgentId: (id: string | null) => void; // Add setter for currentAgentId
  runAgent: (task: string) => Promise<any>;      // Changed return type to any
  clearScreenshots: () => void;
  loadAgentHistory: (agentId: string) => void;
  pauseAgent: () => void;
  resumeAgent: () => void;
  stopAgent: () => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export const AgentProvider: React.FC<AgentContextProps> = ({ children }) => {
  const [screenshots, setScreenshots] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null);
  const [actionHistory, setActionHistory] = useState<any[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logEventSource, setLogEventSource] = useState<EventSource | null>(null);

  // Clear all screenshots
  const clearScreenshots = useCallback(() => {
    setScreenshots([]);
  }, []);
  
  // Run an agent with the current ID and given task
  const runAgent = useCallback(async (task: string) => {
    if (!currentAgentId || !task.trim()) {
      console.error("Cannot run agent: Missing agent ID or task");
      return;
    }
    
    try {
      console.log(`Running agent ${currentAgentId} with task: ${task}`);
      const response = await agentApi.runAgent(currentAgentId, task);
      console.log("Agent run response:", response);
      setIsRunning(true);
      // Don't return the response
    } catch (error) {
      console.error("Error running agent:", error);
      throw error;
    }
  }, [currentAgentId]);
  
  // Load agent history
  const loadAgentHistory = useCallback(async (agentId: string) => {
    try {
      const response = await agentApi.getAgentHistory(agentId);
      setCurrentAgentId(agentId);
      
      if (response.data) {
        // Set all history data
        setEvents(response.data.events || []);
        
        // Handle screenshots with URLs
        const screenshotsWithUrls = response.data.steps
          ?.filter(step => step.has_screenshot)
          .map(step => ({
            step_number: step.step_number,
            url: step.url,
            title: step.title,
            screenshot_url: step.screenshot_url,  // Use saved URL from backend
            goal: step.goal
          })) || [];
          
        setScreenshots(screenshotsWithUrls);
        
        setActionHistory(response.data.steps?.map(step => ({
          step_number: step.step_number,
          goal: step.goal,
          url: step.url,
          title: step.title
        })) || []);
        
        setFinalAnswer(response.data.final_answer || null);
      }
    } catch (error) {
      console.error("Error loading agent history:", error);
    }
  }, []);
  
  // Pause the agent
  const pauseAgent = useCallback(async () => {
    if (!currentAgentId) return;
    
    try {
      await agentApi.pauseAgent(currentAgentId);
      setIsPaused(true);
    } catch (error) {
      console.error("Error pausing agent:", error);
    }
  }, [currentAgentId]);
  
  // Resume the agent
  const resumeAgent = useCallback(async () => {
    if (!currentAgentId) return;
    
    try {
      await agentApi.resumeAgent(currentAgentId);
      setIsPaused(false);
    } catch (error) {
      console.error("Error resuming agent:", error);
    }
  }, [currentAgentId]);
  
  // Stop the agent
  const stopAgent = useCallback(async () => {
    if (!currentAgentId) return;
    
    try {
      await agentApi.stopAgent(currentAgentId);
      setIsRunning(false);
      setIsPaused(false);
    } catch (error) {
      console.error("Error stopping agent:", error);
    }
  }, [currentAgentId]);
  
  // Check agent status when currentAgentId changes
  useEffect(() => {
    if (!currentAgentId) {
      setIsRunning(false);
      setIsPaused(false);
      return;
    }
    
    const checkAgentStatus = async () => {
      try {
        const response = await agentApi.getAgentStatus(currentAgentId);
        if (response.data) {
          const { status } = response.data;
          setIsRunning(status === 'running' || status === 'paused');
          setIsPaused(status === 'paused');
        }
      } catch (error) {
        console.error("Error checking agent status:", error);
      }
    };
    
    checkAgentStatus();
    const intervalId = setInterval(checkAgentStatus, 5000);
    
    return () => clearInterval(intervalId);
  }, [currentAgentId]);

  // Clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Fetch latest screenshot or specific step screenshot
  const fetchLatestScreenshot = useCallback(async (stepNumber?: number) => {
    if (!currentAgentId) return null;
    
    try {
      const params = stepNumber !== undefined ? { step: stepNumber } : {};
      const response = await agentApi.getAgentScreenshot(currentAgentId, params);
      return response.data?.screenshot || null;
    } catch (error) {
      console.error("Error fetching screenshot:", error);
      return null;
    }
  }, [currentAgentId]);

  // Connect to logs SSE endpoint when agent starts running
  useEffect(() => {
    if (isRunning && currentAgentId) {
      // Close existing connection if any
      if (logEventSource) {
        logEventSource.close();
      }
      
      // Connect to logs endpoint
      const eventSource = new EventSource(`${agentApi.getBaseUrl()}/logs`);
      
      eventSource.onmessage = (event) => {
        try {
          const logEntry = JSON.parse(event.data);
          setLogs(prevLogs => [...prevLogs, logEntry]);
        } catch (error) {
          console.error("Error parsing log data:", error);
        }
      };
      
      eventSource.onerror = () => {
        console.error("SSE connection error");
        eventSource.close();
      };
      
      setLogEventSource(eventSource);
      
      return () => {
        eventSource.close();
        setLogEventSource(null);
      };
    }
    
    // Clean up connection when agent stops
    if (!isRunning && logEventSource) {
      logEventSource.close();
      setLogEventSource(null);
    }
  }, [isRunning, currentAgentId]);

  return (
    <AgentContext.Provider
      value={{
        screenshots,
        isRunning,
        isPaused,
        finalAnswer,
        events,
        currentAgentId,
        actionHistory,
        logs,
        clearLogs,
        fetchLatestScreenshot,
        setCurrentAgentId,  // Expose the setter
        runAgent,           // Expose the run method
        clearScreenshots,
        loadAgentHistory,
        pauseAgent,
        resumeAgent,
        stopAgent,
      }}
    >
      {children}
    </AgentContext.Provider>
  );
};

export const useAgent = (): AgentContextType => {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
};
