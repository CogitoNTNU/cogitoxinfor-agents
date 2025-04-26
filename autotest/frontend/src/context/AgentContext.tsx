import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { agentApi } from '../services/api';

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
  setCurrentAgentId: (id: string | null) => void; // Add setter for currentAgentId
  runAgent: (task: string) => Promise<void>;      // Add runAgent method
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
      return response;
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
      // Process the agent history data
      if (response.data) {
        setEvents(response.data.events || []);
        setScreenshots(response.data.screenshots || []);
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
  
  return (
    <AgentContext.Provider
      value={{
        screenshots,
        isRunning,
        isPaused,
        finalAnswer,
        events,
        currentAgentId,
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
