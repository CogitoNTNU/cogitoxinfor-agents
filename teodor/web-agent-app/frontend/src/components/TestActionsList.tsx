
import React from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Plus, Trash } from 'lucide-react';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Input } from './ui/input';

export interface TestAction {
  action: string;
  args: string[];
}

interface TestActionsListProps {
  actions: TestAction[];
  onAddAction: () => void;
  onRemoveAction: (index: number) => void;
  onUpdateAction: (index: number, action: TestAction) => void;
}

export const TestActionsList: React.FC<TestActionsListProps> = ({
  actions,
  onAddAction,
  onRemoveAction,
  onUpdateAction,
}) => {
  const actionTypes = ['NAVIGATE', 'CLICK', 'TYPE', 'WAIT', 'SCROLL', 'ANSWER'];

  const handleChangeActionType = (index: number, value: string) => {
    const updatedAction = { ...actions[index], action: value };
    onUpdateAction(index, updatedAction);
  };

  const handleChangeArgument = (index: number, argIndex: number, value: string) => {
    const updatedArgs = [...actions[index].args];
    updatedArgs[argIndex] = value;
    const updatedAction = { ...actions[index], args: updatedArgs };
    onUpdateAction(index, updatedAction);
  };

  const handleAddArgument = (index: number) => {
    const updatedArgs = [...actions[index].args, ''];
    const updatedAction = { ...actions[index], args: updatedArgs };
    onUpdateAction(index, updatedAction);
  };

  const handleRemoveArgument = (index: number, argIndex: number) => {
    const updatedArgs = actions[index].args.filter((_, i) => i !== argIndex);
    const updatedAction = { ...actions[index], args: updatedArgs };
    onUpdateAction(index, updatedAction);
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium">Test Actions</h3>
        <Button variant="outline" size="sm" onClick={onAddAction}>
          <Plus className="h-4 w-4 mr-1" />
          Add Action
        </Button>
      </div>
      
      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {actions.map((action, index) => (
          <Card key={index} className="p-3">
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <div className="flex gap-2 mb-2">
                  <Select 
                    value={action.action} 
                    onValueChange={(value) => handleChangeActionType(index, value)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      {actionTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => onRemoveAction(index)}
                    className="shrink-0"
                  >
                    <Trash className="h-4 w-4" />
                  </Button>
                </div>
                
                <div className="space-y-2">
                  {action.args.map((arg, argIndex) => (
                    <div key={argIndex} className="flex gap-2">
                      <Input
                        value={arg}
                        onChange={(e) => handleChangeArgument(index, argIndex, e.target.value)}
                        placeholder={`Argument ${argIndex + 1}`}
                        className="flex-1"
                      />
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => handleRemoveArgument(index, argIndex)}
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleAddArgument(index)}
                    className="w-full mt-1"
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add Argument
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
        
        {actions.length === 0 && (
          <div className="text-center py-4 text-muted-foreground text-sm">
            No test actions added yet
          </div>
        )}
      </div>
    </div>
  );
};
