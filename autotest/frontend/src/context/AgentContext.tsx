import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { agentApi, API_URL } from '../services/api';

// Add LogEntry interface
interface LogEntry {
  id: string; // Added id property
  timestamp: string;
  level: string;
  message: string;
  source?: string;
}

// Define interface for the payload sent to runAgent
interface AgentRunPayload {
  testing: boolean;
  human_intervention: boolean;
  query: string;
  test_actions: Array<{ action: string; args: string[] }>; // Simplified action type for now
  infor_mode?: boolean; // Added infor_mode parameter
}

// Define interface for Agent events
export interface AgentEvent {
  id: string;
  type: 'ACTION_UPDATE' | 'SCREENSHOT_UPDATE' | 'INTERRUPT' | 'FINAL_ANSWER'; // Add other event types as needed
  timestamp: Date; // Assuming timestamp is a Date object
  payload: any; // Define a more specific type based on event type if possible
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
  runAgent: (payload: AgentRunPayload) => Promise<void>; // Updated parameter type and return type
  clearScreenshots: () => void;
  loadAgentHistory: (agentId: string) => void;
  pauseAgent: () => void;
  resumeAgent: () => void;
  stopAgent: () => void;
  interruptMessage: string | null; // Add interruptMessage property
  respondToInterrupt: (response: string) => void; // Add respondToInterrupt property
  agentIds: string[]; // Added agentIds property
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
  const [interruptMessage, setInterruptMessage] = useState<string | null>(null); // Add state for interrupt message
  const [agentIds, setAgentIds] = useState<string[]>([]); // Added state for agentIds

  // Ensure that when currentAgentId changes it appears in agentIds
  useEffect(() => {
    if (currentAgentId && !agentIds.includes(currentAgentId)) {
      setAgentIds(prev => [...prev, currentAgentId]);
    }
  }, [currentAgentId, agentIds]);

  // Clear all screenshots
  const clearScreenshots = useCallback(() => {
    setScreenshots([]);
  }, []);

  // Placeholder function to respond to interrupt
  const respondToInterrupt = useCallback((response: string) => {
    console.log("Responding to interrupt with:", response);
    // TODO: Implement actual logic to send response to backend
    setInterruptMessage(null); // Clear message after responding
  }, []);
  
  // Run an agent with the current ID and given task
  const runAgent = useCallback(async (payload: AgentRunPayload) => { // Updated parameter type
    if (!currentAgentId) {
      console.error("Cannot run agent: Missing agent ID");
      return;
    }

    try {
      // Check if infor_mode is set in localStorage
      const inforMode = localStorage.getItem('inforMode') === 'true';
      
      // Add infor_mode to payload if it's not already set
      if (payload.infor_mode === undefined) {
        payload.infor_mode = inforMode;
      }
      
      console.log(`Running agent ${currentAgentId} with payload:`, payload); // Updated log
      const response = await agentApi.runAgent(currentAgentId, payload.query, payload.infor_mode); // Pass infor_mode
      console.log("Agent run response:", response);
      setIsRunning(true);
      // Don't return the response
    } catch (error) {
      console.error("Error running agent:", error);
      throw error;
    }
  }, [currentAgentId]); // Dependency array remains the same
  
  // Load agent history
  const loadAgentHistory = useCallback(async (agentId: string) => {
    // Declare agentId in scope for catch block
    const agentIdInScope = agentId; 
    try {
      console.log("Fetching agent history for:", agentIdInScope); // Added console log
      const response = await agentApi.getAgentHistory(agentIdInScope);
      console.log("Agent history response:", response.data); // Added console log
      setCurrentAgentId(agentIdInScope);
      
      if (response.data) {
        // Set all history data
        setEvents(response.data.events || []);
        
        // Handle screenshots with URLs
        const screenshotsWithUrls = response.data.steps
          ?.filter(step => step.has_screenshot)
          .map(step => ({
            step_number: step.step_number,
            url: step.screenshot_url,  // Map screenshot_url to url
            title: step.title,
            // Removed redundant screenshot_url property
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
      console.log("Caught error loading agent history for agentId:", agentIdInScope); // Added new console log
      console.error("Error loading agent history for", agentIdInScope, ":", error); // Modified console log to use agentIdInScope
    }
  }, []); // Removed agentId from dependency array
  
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
    console.log("Agent status effect running. currentAgentId:", currentAgentId); // Added console log
    if (!currentAgentId) {
      setIsRunning(false);
      setIsPaused(false);
      return;
    }
    
    const checkAgentStatus = async () => {
      try {
        console.log("Checking status for agent:", currentAgentId); // Added console log
        const response = await agentApi.getAgentStatus(currentAgentId);
        console.log("Status check response:", response.data); // Added console log
        if (response.data) {
          const { status } = response.data;
          setIsRunning(status === 'running' || status === 'paused');
          setIsPaused(status === 'paused');
          // Call loadAgentHistory here to fetch history and screenshots
          if (status === 'running' || status === 'paused' || status === 'stopped') {
             console.log("Agent status is", status, "- fetching history and screenshots"); // Added console log
             loadAgentHistory(currentAgentId);
          }
        }
      } catch (error) {
        console.error("Error checking agent status:", error);
      }
    };
    
    checkAgentStatus();
    const intervalId = setInterval(checkAgentStatus, 5000);
    
    return () => clearInterval(intervalId);
  }, [currentAgentId, loadAgentHistory]); // Added loadAgentHistory to dependency array

  // Clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Fetch latest screenshot or specific step screenshot
  const fetchLatestScreenshot = useCallback(async (stepNumber?: number) => {
    if (!currentAgentId) return null;
    
    try {
      const params = stepNumber !== undefined ? stepNumber : null;
      const response = await agentApi.getAgentScreenshot(currentAgentId, params);
      return response.data?.url || null;
    } catch (error) {
      console.error("Error fetching screenshot:", error);
      return null;
    }
  }, [currentAgentId]);


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
        interruptMessage, // Include interruptMessage in value
        respondToInterrupt, // Include respondToInterrupt in value
        agentIds, // Include agentIds in context value
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
