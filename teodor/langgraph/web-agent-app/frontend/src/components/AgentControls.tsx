
import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { PlayIcon, Square, Settings } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { ConfigModal } from './ConfigModal';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { TestActionsList } from './TestActionsList';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { v4 as uuidv4 } from 'uuid';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

export const AgentControls: React.FC = () => {
  const { isRunning, isConnected, startAgent, stopAgent } = useAgent();
  const [query, setQuery] = useState('');
  const [configOpen, setConfigOpen] = useState(false);
  const [testMode, setTestMode] = useState(false);
  const [testActions, setTestActions] = useState([]);
  const [testActionsOpen, setTestActionsOpen] = useState(true);
  const [humanIntervention, setHumanIntervention] = useState(true);
  
  const handleStartAgent = async () => {
    if (testMode || query.trim()) {
      // Generate a session ID
      const sessionId = testMode ? uuidv4() : Math.random().toString(36).substring(2, 15);
      await startAgent(sessionId, query, {
        testing: testMode,
        test_actions: testMode ? testActions : undefined,
        human_intervention: humanIntervention
      });
    }
  };
  
  const handleAddTestAction = () => {
    setTestActions([
      ...testActions,
      {
        action: 'NAVIGATE',
        args: ['']
      }
    ]);
  };
  
  const handleRemoveTestAction = (index) => {
    setTestActions(testActions.filter((_, i) => i !== index));
  };
  
  const handleUpdateTestAction = (index, updatedAction) => {
    const newActions = [...testActions];
    newActions[index] = updatedAction;
    setTestActions(newActions);
  };
  
  return (
    <>
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>Agent Controls</span>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setConfigOpen(true)}
            >
              <Settings className="h-5 w-5" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex-grow overflow-hidden">
          <Tabs defaultValue="query" className="h-full flex flex-col">
            <TabsList className="w-full grid grid-cols-2 px-4 pt-2">
              <TabsTrigger value="query">Query</TabsTrigger>
              <TabsTrigger value="test">Test Settings</TabsTrigger>
            </TabsList>
            
            <TabsContent value="query" className="flex-grow px-4 pt-2 pb-4 space-y-4 overflow-auto">
              <div className="flex items-center space-x-2">
                <Input
                  placeholder="Enter your query..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isRunning}
                  className="flex-1"
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
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="human-intervention"
                  checked={humanIntervention}
                  onCheckedChange={setHumanIntervention}
                />
                <Label htmlFor="human-intervention">Human Intervention</Label>
              </div>
            </TabsContent>
            
            <TabsContent value="test" className="flex-grow px-4 pt-2 pb-4 overflow-auto">
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Switch
                    id="test-mode-settings"
                    checked={testMode}
                    onCheckedChange={setTestMode}
                  />
                  <Label htmlFor="test-mode-settings">Enable Test Mode</Label>
                </div>
                
                <div className="flex items-center space-x-2 mb-4">
                  <Switch
                    id="human-intervention-settings"
                    checked={humanIntervention}
                    onCheckedChange={setHumanIntervention}
                  />
                  <Label htmlFor="human-intervention-settings">Human Intervention</Label>
                </div>
                
                {testMode && (
                  <Collapsible
                    open={testActionsOpen}
                    onOpenChange={setTestActionsOpen}
                  >
                    <CollapsibleTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        {testActionsOpen ? "Hide Test Actions" : "Show Test Actions"}
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-2">
                      <TestActionsList
                        actions={testActions}
                        onAddAction={handleAddTestAction}
                        onRemoveAction={handleRemoveTestAction}
                        onUpdateAction={handleUpdateTestAction}
                      />
                    </CollapsibleContent>
                  </Collapsible>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="px-4 py-2">
          {!isRunning ? (
            <Button
              onClick={handleStartAgent}
              disabled={!testMode && !query.trim() || isRunning}
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
        </CardFooter>
      </Card>
      
      <ConfigModal open={configOpen} onOpenChange={setConfigOpen} />
    </>
  );
};
