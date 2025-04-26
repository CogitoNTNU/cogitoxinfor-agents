import React, { useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useAgent } from '../context/AgentContext';
import { Code, Search, Terminal, ArrowRight } from 'lucide-react';

export const LogDrawer: React.FC = () => {
  const { events, actionHistory } = useAgent();
  const [activeTab, setActiveTab] = useState('events');
  
  // Function to determine event type display
  const getEventTypeDisplay = (type: string) => {
    switch (type) {
      case 'tool_code':
        return { label: 'Tool Call', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', icon: <Code className="h-3 w-3 mr-1" /> };
      case 'action':
        return { label: 'Action', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200', icon: <ArrowRight className="h-3 w-3 mr-1" /> };
      case 'extract':
        return { label: 'Extract', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', icon: <Search className="h-3 w-3 mr-1" /> };
      case 'error':
        return { label: 'Error', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: null };
      default:
        return { label: type, color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200', icon: <Terminal className="h-3 w-3 mr-1" /> };
    }
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="fixed bottom-4 right-4 h-10 w-10 rounded-full p-0">
          <Code className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="h-[80vh]">
        <SheetHeader>
          <SheetTitle>Agent Activity Log</SheetTitle>
        </SheetHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="events">Events</TabsTrigger>
            <TabsTrigger value="model">Model Actions</TabsTrigger>
          </TabsList>
          
          <TabsContent value="events" className="mt-4">
            <ScrollArea className="h-[calc(80vh-120px)]">
              {events.length > 0 ? (
                <div className="space-y-3">
                  {events.map((event, index) => {
                    const { label, color, icon } = getEventTypeDisplay(event.type);
                    return (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline" className={`${color} flex items-center`}>
                            {icon} {label}
                          </Badge>
                          {event.timestamp && (
                            <span className="text-xs text-muted-foreground">
                              {new Date(event.timestamp).toLocaleTimeString()}
                            </span>
                          )}
                        </div>
                        
                        {event.type === 'tool_code' && event.payload?.tool_name && (
                          <div className="text-sm font-medium mb-1">{event.payload.tool_name}</div>
                        )}
                        
                        {event.payload && (
                          <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-40">
                            {typeof event.payload === 'string' 
                              ? event.payload
                              : JSON.stringify(event.payload, null, 2)
                            }
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No events recorded yet
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="model" className="mt-4">
            <ScrollArea className="h-[calc(80vh-120px)]">
              {actionHistory && actionHistory.length > 0 ? (
                <div className="space-y-3">
                  {actionHistory.map((action, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className="bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                          Step {action.step_number + 1}
                        </Badge>
                      </div>
                      
                      <div className="mb-2">
                        <div className="text-sm font-medium">Goal:</div>
                        <div className="text-sm">{action.goal || 'No goal specified'}</div>
                      </div>
                      
                      <div>
                        <div className="text-xs text-muted-foreground">Page:</div>
                        <div className="text-xs truncate">{action.title || 'Untitled'}</div>
                        <div className="text-xs text-blue-500 truncate">{action.url}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No model actions recorded yet
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
};

export default LogDrawer;
