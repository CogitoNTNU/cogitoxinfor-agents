
import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { TestActionsList, TestAction } from './TestActionsList';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';

export const TestSettings: React.FC = () => {
  const [testActions, setTestActions] = useState<TestAction[]>([]);
  const [testActionsOpen, setTestActionsOpen] = useState(true);
  const [humanIntervention, setHumanIntervention] = useState(true);
  
  // Make testActions and humanIntervention available globally
  useEffect(() => {
    window.testActions = testActions;
    window.humanIntervention = humanIntervention;
  }, [testActions, humanIntervention]);
  
  const handleAddTestAction = () => {
    setTestActions([...testActions, { action: 'NAVIGATE', args: [''] }]);
  };
  
  const handleRemoveTestAction = (index: number) => {
    setTestActions(testActions.filter((_, i) => i !== index));
  };
  
  const handleUpdateTestAction = (index: number, updatedAction: TestAction) => {
    const newActions = [...testActions];
    newActions[index] = updatedAction;
    setTestActions(newActions);
  };
  
  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center space-x-2">
        <Switch 
          id="human-intervention" 
          checked={humanIntervention}
          onCheckedChange={setHumanIntervention}
        />
        <Label htmlFor="human-intervention">Human Intervention</Label>
      </div>
      
      <div>
        <Collapsible open={testActionsOpen} onOpenChange={setTestActionsOpen}>
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
      </div>
    </Card>
  );
};
