import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Play, Square, Pause, PlayCircle } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { agentApi } from '../services/api';
import { v4 as uuidv4 } from 'uuid'; // You'll need to add this dependency

const AgentController: React.FC = () => {
  const { isRunning, isPaused, currentAgentId, setCurrentAgentId, runAgent } = useAgent();
  const [activeTab, setActiveTab] = useState('agent');
  const [task, setTask] = useState('');
  const [humanIntervention, setHumanIntervention] = useState(true);
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
      // Use the context's runAgent method
      await runAgent(task);
      console.log("Agent run request successful");
      setTask(''); // Clear task field after running
    } catch (error) {
      console.error("Error running agent:", error);
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value)}
          className="mb-4"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="agent">Agent Mode</TabsTrigger>
            <TabsTrigger value="control">Agent Controls</TabsTrigger>
          </TabsList>
          
          <TabsContent value="agent">
            <div className="flex items-center space-x-2 mb-4">
              <Switch
                id="human-intervention"
                checked={humanIntervention}
                onCheckedChange={setHumanIntervention}
              />
              <Label htmlFor="human-intervention">Human Intervention</Label>
            </div>
            <Textarea
              placeholder="Enter your task for the agent here..."
              value={task}
              onChange={(e) => setTask(e.target.value)}
              rows={4}
              className="mb-4"
            />
            
            <Button
              className="w-full"
              variant={isRunning ? "destructive" : "default"}
              onClick={isRunning ? handleStop : handleRun}
              disabled={isRunning || !task.trim()}
            >
              {isRunning ? (
                <>
                  <Square className="mr-2 h-4 w-4" />
                  Stop Agent
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Agent
                </>
              )}
            </Button>
          </TabsContent>
          
          <TabsContent value="control">
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground mb-2">
                Control the currently running agent:
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={handlePause}
                  disabled={!isRunning || isPaused || !currentAgentId}
                >
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </Button>
                
                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={handleResume}
                  disabled={!isPaused || !currentAgentId}
                >
                  <PlayCircle className="mr-2 h-4 w-4" />
                  Resume
                </Button>
                
                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={handleStop}
                  disabled={(!isRunning && !isPaused) || !currentAgentId}
                  color="destructive"
                >
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              </div>
              
              {currentAgentId ? (
                <div className="text-xs text-center mt-2">
                  Current Agent ID: <code>{currentAgentId}</code>
                </div>
              ) : (
                <div className="text-xs text-center mt-2 text-muted-foreground">
                  No agent currently running
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AgentController;
