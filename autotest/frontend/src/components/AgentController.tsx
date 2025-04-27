import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Play, Square, Pause, PlayCircle } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { agentApi } from '@/services/api.tsx';

const AgentController: React.FC = () => {
  const { isRunning, isPaused, currentAgentId, setCurrentAgentId, runAgent } = useAgent();
  const [task, setTask] = useState('');

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
  
  const handleRun = async () => {
    if (!task.trim()) return;
    try {
      let agentId = currentAgentId;
      if (!agentId) {
        // create new agent if none selected
        const resp = await agentApi.createAgent();
        agentId = resp.data.agent_id;
        setCurrentAgentId(agentId);
      }
      // run (or re-run) the agent with the task
      await runAgent({ query: task, testing: false, human_intervention: false, test_actions: [] });
      setTask('');
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
        <div className="relative">
          {!isRunning && (
            <Button onClick={handleRun} variant="ghost" className="absolute bottom-2 right-2 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center">
              <Play className="h-6 w-6" />
            </Button>
          )}
          {isRunning && !isPaused && (
            <Button onClick={handlePause} variant="ghost" className="absolute bottom-2 right-2 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center">
              <Pause className="h-6 w-6" />
            </Button>
          )}
          {isPaused && (
            <Button onClick={handleResume} variant="ghost" className="absolute bottom-2 right-2 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center">
              <PlayCircle className="h-6 w-6" />
            </Button>
          )}
          {(isRunning || isPaused) && (
            <Button onClick={handleStop} variant="ghost" className="absolute bottom-2 right-14 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center">
              <Square className="h-6 w-6" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AgentController;
