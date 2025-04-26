import React, { useState } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { PlayIcon, Square } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { v4 as uuidv4 } from 'uuid';
import { agentApi } from '../services/api';

export const AgentQuery: React.FC = () => {
  const { isRunning, stopAgent, currentAgentId, loadAgentHistory } = useAgent();
  const [query, setQuery] = useState('');
  const [testMode, setTestMode] = useState(false);
  
  const handleStartAgent = async () => {
    if (!query.trim() && !testMode) return;
    
    try {
      // Generate a new agent ID if one doesn't exist
      const agentId = currentAgentId || uuidv4();
      
      // Call the API to run the agent with the query
      const response = await agentApi.runAgent(agentId, query);
      
      // If we get a response with a new agent ID, load its history
      if (response.data && response.data.agent_id) {
        loadAgentHistory(response.data.agent_id);
      }
      
      // Clear the query after running
      setQuery('');
    } catch (error) {
      console.error("Error running agent:", error);
    }
  };
  
  return (
    <Card className="p-4 space-y-4">
      <div>
        <Label htmlFor="query-input" className="mb-2 block">Enter your query</Label>
        <Textarea
          id="query-input"
          placeholder="Enter your query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isRunning}
          className="min-h-24"
        />
      </div>
      
      <div className="flex items-center space-x-2">
        <Switch 
          id="test-mode" 
          checked={testMode}
          onCheckedChange={setTestMode}
        />
        <Label htmlFor="test-mode">Test Mode</Label>
      </div>
      
      {testMode && (
        <div className="text-sm text-muted-foreground">
          In test mode, the agent will use predefined test actions instead of natural language processing.
        </div>
      )}
      
      <div>
        {!isRunning ? (
          <Button 
            onClick={handleStartAgent}
            disabled={(!query.trim() && !testMode) || isRunning}
            className="w-full"
          >
            <PlayIcon className="mr-2 h-4 w-4" />
            Start Agent
          </Button>
        ) : (
          <Button 
            onClick={stopAgent}
            variant="destructive"
            className="w-full"
          >
            <Square className="mr-2 h-4 w-4" />
            Stop Agent
          </Button>
        )}
      </div>
      
      {currentAgentId && (
        <div className="text-xs text-center text-muted-foreground">
          Current Agent ID: <code>{currentAgentId}</code>
        </div>
      )}
    </Card>
  );
};
