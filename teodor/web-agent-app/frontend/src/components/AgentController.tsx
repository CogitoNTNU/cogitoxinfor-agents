import React, { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

import { PlusCircle, Trash2, Play, Square, Info } from 'lucide-react'; // Lucide icons
import { useAgent } from '@/context/AgentContext';
import { cn } from '@/lib/utils';

// Define TOOL_CONFIGURATIONS
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

// Helper function to format arguments (copied from .jsx)
const formatArguments = (value: string, action: keyof typeof TOOL_CONFIGURATIONS, isBackspace = false): string => {
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


const AgentController: React.FC = () => {
  const { isRunning, startAgent, stopAgent } = useAgent();
  const [activeTab, setActiveTab] = useState('agent');
  const [query, setQuery] = useState('');
  const [testActions, setTestActions] = useState<{ action: keyof typeof TOOL_CONFIGURATIONS, args: string }[]>([]);
  const [humanIntervention, setHumanIntervention] = useState(true);
  const [errors, setErrors] = useState<{ [key: number]: string }>({});

  const parseArguments = (argsString: string, action: keyof typeof TOOL_CONFIGURATIONS): string[] | null => {
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

  const handleActionChange = useCallback((index: number, field: 'action' | 'args', value: string) => {
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
  }, [testActions, validateAction]);

  const handleStart = useCallback(() => {
    // Prevent starting in Test Mode if no actions are defined
    if (activeTab === 'test' && testActions.length === 0) {
      return;
    }

    const hasErrors = activeTab === 'test'
      ? testActions.length === 0 || testActions.some((action, index) => {
          const validation = validateAction(action.action, action.args);
          return !validation.isValid;
        })
      : false;

    if (hasErrors) {
      return; // Don't start if there are validation errors
    }

    const formattedActions = testActions.map(action => {
      const args = parseArguments(action.args, action.action) || []; // Corrected argument order
      return {
        action: action.action,
        args
      };
    });

    const payload = {
      testing: activeTab === 'test',
      human_intervention: humanIntervention,
      query: activeTab === 'agent' ? query : '',
      test_actions: formattedActions
    };
    startAgent(payload);
  }, [activeTab, query, testActions, humanIntervention, startAgent, validateAction, parseArguments]);

  return (
    <Card className={cn("w-full")}>
      <CardContent>
        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value)}
          className="mb-4" // Added margin bottom
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="agent">Agent Mode</TabsTrigger>
            <TabsTrigger value="test">Test Mode</TabsTrigger>
          </TabsList>
          <TabsContent value="agent">
            <div className="flex items-center space-x-2 mb-4"> {/* Replaced FormControlLabel and Box */}
              <Switch
                id="human-intervention"
                checked={humanIntervention}
                onCheckedChange={setHumanIntervention}
              />
              <Label htmlFor="human-intervention">Human Intervention</Label>
            </div>
            <Textarea
              placeholder="Enter your query here..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={4}
              className="mb-4" // Added margin bottom
            />
          </TabsContent>
          <TabsContent value="test">
            <div className="flex items-center space-x-2 mb-4"> {/* Replaced FormControlLabel and Box */}
              <Switch
                id="human-intervention-test"
                checked={humanIntervention}
                onCheckedChange={setHumanIntervention}
              />
              <Label htmlFor="human-intervention-test">Human Intervention</Label>
            </div>
            <Button
              variant="outline"
              onClick={() => setTestActions([...testActions, { action: 'NAVIGATE', args: '' }])}
              className="mb-4" // Added margin bottom
            >
              <PlusCircle className="mr-2 h-4 w-4" /> {/* Lucide icon */}
              Add Action
            </Button>

            <div className="space-y-2"> {/* Replaced Box */}
              {testActions.map((action, index) => (
                <div
                  key={index}
                  className="border rounded-md p-2 flex flex-col gap-2" // Replaced Paper and sx prop
                >
                  <div className="flex items-center gap-2"> {/* Replaced Box and sx prop */}
                    <Select
                      value={action.action}
                      onValueChange={(value: keyof typeof TOOL_CONFIGURATIONS) => handleActionChange(index, 'action', value)}
                    >
                      <SelectTrigger className="w-[120px]"> {/* Replaced sx prop */}
                        <SelectValue placeholder="Select Action" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.keys(TOOL_CONFIGURATIONS).map(act => (
                          <SelectItem key={act} value={act}>{act}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <div className="flex items-center flex-1"> {/* Replaced Box and sx prop */}
                      <Input
                        placeholder={TOOL_CONFIGURATIONS[action.action].placeholder}
                        value={action.args}
                        onChange={(e) => {
                          let value = e.target.value;
                          if (value.endsWith(' ') && !value.includes(',')) {
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
                        className={cn(errors[index] && 'border-destructive')} // Added error styling
                      />
                      <TooltipProvider> {/* Added TooltipProvider */}
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" className="ml-2"> {/* Replaced IconButton and sx prop */}
                              <Info className="h-4 w-4" /> {/* Lucide icon */}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Format: {TOOL_CONFIGURATIONS[action.action].placeholder}</p>
                            <p>Required Arguments: {TOOL_CONFIGURATIONS[action.action].args}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <Button
                      variant="ghost" // Replaced color="error" with variant="ghost" and text-destructive
                      size="icon"
                      onClick={() => {
                        const newActions = testActions.filter((_, i) => i !== index);
                        setTestActions(newActions);
                        const newErrors = {...errors};
                        delete newErrors[index];
                        setErrors(newErrors);
                      }}
                      className="text-destructive" // Added text-destructive class
                    >
                      <Trash2 className="h-4 w-4" /> {/* Lucide icon */}
                    </Button>
                  </div>
                  {errors[index] && (
                    <p className="text-destructive text-sm mt-1">{errors[index]}</p> // Added error message display
                  )}
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>


        <Button
          className="w-full" // Replaced fullWidth with w-full
          variant={isRunning ? "destructive" : "default"} // Replaced color prop with variant
          onClick={isRunning ? stopAgent : handleStart}
          disabled={
            (activeTab === 'agent' && !query.trim()) ||
            (activeTab === 'test' && (
              testActions.length === 0 ||
              Object.values(errors).some(errorMsg => errorMsg.length > 0)
            ))
          }
        >
          {isRunning ? (
            <>
              <Square className="mr-2 h-4 w-4" /> {/* Lucide icon */}
              Stop Agent
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" /> {/* Lucide icon */}
              Start Agent
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

export default AgentController;
