import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Play, Square, Pause, PlayCircle } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { agentApi } from '../services/api';
import { v4 as uuidv4 } from 'uuid'; // You'll need to add this dependency

const AgentController: React.FC = () => {
  const { isRunning, isPaused, currentAgentId, setCurrentAgentId, runAgent } = useAgent();
  const [task, setTask] = useState('');
  const [localAgentId, setLocalAgentId] = useState('');
  
  // Generate a local agent ID if one doesn't exist
  useEffect(() => {
    if (currentAgentId) {
      setLocalAgentId(currentAgentId);
    } else {
      const newAgentId = `agent-${uuidv4().substring(0, 8)}`;
      setLocalAgentId(newAgentId);
      // If your context provides a setter:
      if (setCurrentAgentId) {
        setCurrentAgentId(newAgentId);
      }
    }
  }, [currentAgentId, setCurrentAgentId]);

  // Handle pause action
  const handlePause = async () => {
    if (!currentAgentId) return;
    try {
      await agentApi.pauseAgent(currentAgentId);
    } catch (error) {
      console.error("Error pausing agent:", error);
    }
  };
  
  // Handle resume action
  const handleResume = async () => {
    if (!currentAgentId) return;
    try {
      await agentApi.resumeAgent(currentAgentId);
    } catch (error) {
      console.error("Error resuming agent:", error);
    }
  };
  
  // Handle stop action
  const handleStop = async () => {
    if (!currentAgentId) return;
    try {
      await agentApi.stopAgent(currentAgentId);
    } catch (error) {
      console.error("Error stopping agent:", error);
    }
  };
  
  // Modified handleRun function to use the context's runAgent method
  const handleRun = async () => {
    console.log("Run button clicked", { task });
    
    if (!task.trim()) {
      console.log("Task is empty, not sending request");
      return;
    }
    
    try {
      const payload = {
        task,
        agentId: localAgentId,
        testing: false, // Assuming default value
        human_intervention: false, // Assuming default value
        query: task, // Assuming query is the same as task
        test_actions: [] // Assuming default empty array
      };
      // Use the context's runAgent method
      await runAgent(payload); // Pass the payload object
      console.log("Agent run request successful");
      setTask(''); // Clear task field after running
    } catch (error) {
      console.error("Error running agent:", error);
    }
  };

  return (
    <Card className="w-full mb-6">
      <CardContent className="pt-2 pl-2 relative">
        <Textarea
          placeholder="Enter your task here..."
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleRun();
            }
          }}
          rows={3}
          className="mb-2 border-none focus:border-none focus:ring-0 focus:outline-none resize-none"
        />
        <div className="flex items-center justify-center space-x-4">
          {!isRunning && (
            <Button onClick={handleRun} variant="ghost" className="absolute bottom-2 right-2 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center">
              <Play className="h-6 w-6" />
            </Button>
          )}
          {isRunning && !isPaused && (
            <Button onClick={handlePause} variant="ghost">
              <Pause className="h-6 w-6" />
            </Button>
          )}
          {isPaused && (
            <Button onClick={handleResume} variant="ghost">
              <PlayCircle className="h-6 w-6" />
            </Button>
          )}
          {(isRunning || isPaused) && (
            <Button onClick={handleStop} variant="ghost">
              <Square className="h-6 w-6" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AgentController;
