
import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { PlayIcon, Square } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { v4 as uuidv4 } from 'uuid';

export const AgentQuery: React.FC = () => {
  const { isRunning, startAgent, stopAgent } = useAgent();
  const [query, setQuery] = useState('');
  const [testMode, setTestMode] = useState(false);
  
  const handleStartAgent = async () => {
    if ((query.trim() || testMode)) {
      const sessionId = testMode ? uuidv4() : Math.random().toString(36).substring(2, 15);
      await startAgent(sessionId, query, {
        testing: testMode,
        // These will be passed from the TestSettings component
        test_actions: testMode ? window.testActions || [] : undefined,
        human_intervention: window.humanIntervention !== undefined ? window.humanIntervention : true
      });
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
    </Card>
  );
};
