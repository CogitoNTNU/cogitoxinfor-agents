import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { PlayIcon, Square, Plus, MinusCircle, Info } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { v4 as uuidv4 } from 'uuid';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"


const TOOL_CONFIGURATIONS = {
  NAVIGATE: {
    args: 1,
    validator: (args: string[]) => {
      const url = args[0];
      const isValid = typeof url === 'string' && url.trim().length > 0;
      return {
        isValid,
        error: isValid ? '' : 'URL must be a non-empty string'
      };
    },
    placeholder: 'Enter URL (e.g., https://www.google.com)'
  },
  CLICK: {
    args: 1,
    validator: (args: string[]) => {
      const id = args[0];
      return {
        isValid: !isNaN(parseInt(id)),
        error: 'Element ID must be a number'
      };
    },
    placeholder: 'Enter element ID (e.g., 6)'
  },
  TYPE: {
    args: 2,
    validator: (args: string[]) => {
      const [id, text] = args;
      return {
        isValid: !isNaN(parseInt(id)) && typeof text === 'string' && text.length > 0,
        error: 'Requires element ID (number) and text to type'
      };
    },
    placeholder: 'Enter element ID, text (e.g., 6, search text)'
  },
  WAIT: {
    args: 1,
    validator: (args: string[]) => {
      const seconds = args[0];
      return {
        isValid: !isNaN(parseInt(seconds)) && parseInt(seconds) > 0,
        error: 'Wait time must be a positive number'
      };
    },
    placeholder: 'Enter seconds to wait (e.g., 2)'
  },
  SCROLL: {
    args: 2,
    validator: (args: string[]) => {
      const [target, direction] = args;
      const validDirections = ['up', 'down'];
      const isValidTarget = target.toUpperCase() === 'WINDOW' || !isNaN(parseInt(target));
      return {
        isValid: isValidTarget && validDirections.includes(direction.toLowerCase()),
        error: 'Target must be "WINDOW" or element ID, direction must be "up" or "down"'
      };
    },
    placeholder: 'Enter target (WINDOW or ID), direction (up/down)'
  }
};

const formatArguments = (value: string, action: keyof typeof TOOL_CONFIGURATIONS, isBackspace = false) => {
  const config = TOOL_CONFIGURATIONS[action];
  const values = value.split(',').map(v => v.trim()).filter(v => v !== '');
  
  // Handle backspace logic
  if (isBackspace) {
    // If text contains comma without proper spacing
    if (value.match(/,\S/)) {
      return value.slice(0, -1);
    }
    
    // If ending with comma and space
    if (value.endsWith(', ')) {
      return value.slice(0, -2);
    }
    
    // If ending with just comma
    if (value.endsWith(',')) {
      return '';  // Clear everything when the last comma is hit
    }
    
    // If we have a single value (no commas)
    if (!value.includes(',')) {
      return value.slice(0, -1);
    }
    
    // If we have multiple values, handle the last one
    const lastCommaIndex = value.lastIndexOf(',');
    if (lastCommaIndex !== -1) {
      const beforeComma = value.slice(0, lastCommaIndex + 2); // Keep comma and space
      const afterComma = value.slice(lastCommaIndex + 2);
      if (!afterComma.trim()) {
        return value.slice(0, lastCommaIndex);
      }
      return beforeComma + afterComma.slice(0, -1);
    }
  }

  return value;  // Return unmodified value for non-backspace operations
};


export const AgentControls: React.FC = () => {
  const { isRunning, runAgent, stopAgent } = useAgent(); // Changed startAgent to runAgent
  const [query, setQuery] = useState('');
  // Removed configOpen state
  const [testActions, setTestActions] = useState<Array<{ action: keyof typeof TOOL_CONFIGURATIONS, args: string }>>([]);
  const [testActionsOpen, setTestActionsOpen] = useState(true);
  const [humanIntervention, setHumanIntervention] = useState(true);
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [activeTab, setActiveTab] = useState('query');

  const parseArguments = (argsString: string, action: keyof typeof TOOL_CONFIGURATIONS) => {
    const args = argsString.split(',').map(arg => arg.trim());
    if (args.length !== TOOL_CONFIGURATIONS[action].args) {
      return null;
    }
    return args;
  };

  const validateAction = (action: keyof typeof TOOL_CONFIGURATIONS, argsString: string) => {
    const config = TOOL_CONFIGURATIONS[action];
    const args = parseArguments(argsString, action);
    
    if (!args) {
      return {
        isValid: false,
        error: `Expected ${config.args} argument(s)`
      };
    }
    
    return config.validator(args);
  };

  const handleActionChange = (index: number, field: 'action' | 'args', value: string) => {
    const updatedActions = [...testActions];
    const action = field === 'action' ? value as keyof typeof TOOL_CONFIGURATIONS : updatedActions[index].action;
    const args = field === 'args' ? value : updatedActions[index].args;
    
    updatedActions[index] = { ...updatedActions[index], [field]: value };
    setTestActions(updatedActions);

    // Validate the updated action
    const validation = validateAction(action, args);
    setErrors(prev => ({
      ...prev,
      [index]: validation.error
    }));
  };

  const handleStartAgent = async () => {
    const isTestMode = activeTab === 'test';
    if (isTestMode || query.trim()) {
      const hasErrors = isTestMode
        ? testActions.length === 0 || testActions.some((action, index) => {
            const validation = validateAction(action.action, action.args);
            return !validation.isValid;
          })
        : false;

      if (hasErrors) {
        return; // Don't start if there are validation errors
      }

      const formattedActions = testActions.map(action => {
        const args = parseArguments(action.args, action.action) || [];
        return {
          action: action.action,
          args
        };
      });

      const payload = {
        testing: isTestMode,
        human_intervention: humanIntervention,
        query: isTestMode ? '' : query.trim(),
        test_actions: isTestMode ? formattedActions : [],
      };
      await runAgent(payload); // Pass the payload object
    }
  };
  
  const handleAddTestAction = () => {
    const newIndex = testActions.length;
    setTestActions([
      ...testActions,
      {
        action: 'NAVIGATE',
        args: ''
      }
    ]);
    setErrors(prev => ({ ...prev, [newIndex]: '' })); // Initialize error for new action
  };
  
  const handleRemoveTestAction = (index: number) => {
    setTestActions(testActions.filter((_, i) => i !== index));
    setErrors(prevErrors => {
      const newErrors: Record<number, string> = {};
      Object.keys(prevErrors).forEach(key => {
        const numKey = parseInt(key);
        if (numKey !== index) {
          newErrors[numKey > index ? numKey - 1 : numKey] = prevErrors[numKey];
        }
      });
      return newErrors;
    });
  };
  
  const handleUpdateTestAction = (index: number, updatedAction: { action: keyof typeof TOOL_CONFIGURATIONS, args: string }) => {
    const newActions = [...testActions];
    newActions[index] = updatedAction;
    setTestActions(newActions);
    const validation = validateAction(updatedAction.action, updatedAction.args);
    setErrors(prev => ({
      ...prev,
      [index]: validation.error
    }));
  };
  
  return (
    <>
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>Agent Controls</span>
            {/* Removed Settings button */}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex-grow overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col px-4">
            <TabsList className="w-full grid grid-cols-2 px-1">
              <TabsTrigger value="query">Query</TabsTrigger>
              <TabsTrigger value="test">Test Settings</TabsTrigger>
            </TabsList>
            
            <TabsContent value="query" className="flex-grow pt-2 pb-4 space-y-4 overflow-auto">
              <div className="flex items-center space-x-2 px-1">
                <Input
                  placeholder="Enter your query..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isRunning || activeTab === 'test'}
                  className="flex-1"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="human-intervention"
                  checked={humanIntervention}
                  onCheckedChange={setHumanIntervention}
                  disabled={isRunning}
                />
                <Label htmlFor="human-intervention">Human Intervention</Label>
              </div>
            </TabsContent>
            
            <TabsContent value="test" className="flex-grow px-4 pt-2 pb-4 overflow-auto">
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Switch
                    id="human-intervention-settings"
                    checked={humanIntervention}
                    onCheckedChange={setHumanIntervention}
                    disabled={isRunning}
                  />
                  <Label htmlFor="human-intervention-settings">Human Intervention</Label>
                </div>
                
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
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleAddTestAction}
                      className="w-full"
                      disabled={isRunning}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Action
                    </Button>
                    <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                      {testActions.map((action, index) => (
                        <div key={index} className="flex items-center space-x-2 border rounded-md p-2">
                          <Select
                            value={action.action}
                            onValueChange={(value: keyof typeof TOOL_CONFIGURATIONS) => handleActionChange(index, 'action', value)}
                            disabled={isRunning}
                          >
                            <SelectTrigger className="w-[120px]">
                              <SelectValue placeholder="Select Action" />
                            </SelectTrigger>
                            <SelectContent>
                              {Object.keys(TOOL_CONFIGURATIONS).map(act => (
                                <SelectItem key={act} value={act}>{act}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Input
                            placeholder={TOOL_CONFIGURATIONS[action.action].placeholder}
                            value={action.args}
                            onChange={(e) => {
                              let value = e.target.value;
                              // If user hits space and we don't already have a comma
                              if (value.endsWith(' ') && !value.includes(',')) {
                                // Replace the space with a comma and space
                                value = value.trim() + ', ';
                              }
                              const formattedValue = formatArguments(value, action.action);
                              handleActionChange(index, 'args', formattedValue);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === 'Backspace' && action.args) {
                                e.preventDefault();
                                const formattedValue = formatArguments(action.args, action.action, true);
                                handleActionChange(index, 'args', formattedValue);
                              }
                            }}
                            disabled={isRunning}
                            className="flex-1"
                          />
                           <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Format: {TOOL_CONFIGURATIONS[action.action].placeholder}</p>
                                <p>Required Arguments: {TOOL_CONFIGURATIONS[action.action].args}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleRemoveTestAction(index)}
                            disabled={isRunning}
                          >
                            <MinusCircle className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      ))}
                      {testActions.map((action, index) => (
                        errors[index] && (
                          <p key={`error-${index}`} className="text-destructive text-sm mt-1">{errors[index]}</p>
                        )
                      ))}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="px-4 py-2">
          {!isRunning ? (
            <Button
              onClick={handleStartAgent}
              disabled={activeTab === 'query' && !query.trim() || isRunning || (activeTab === 'test' && (testActions.length === 0 || Object.values(errors).some(errorMsg => errorMsg.length > 0)))}
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
    </>
  );
};
