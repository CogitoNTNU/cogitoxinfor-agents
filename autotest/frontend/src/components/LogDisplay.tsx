import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { format } from 'date-fns';
import { Trash2, Image, Code, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
// Removed useAgent import

interface LogEntry {
  id: string;
  message: string;
  level: string;
  timestamp: string;
}

interface LogDisplayProps {
  logs: LogEntry[];
  onClear: () => void;
  className?: string;
  isRunning: boolean;
  actionHistory: any[];
}

export const LogDisplay: React.FC<LogDisplayProps> = ({
  logs,
  onClear,
  className,
  isRunning, // isRunning is now a prop
  actionHistory // actionHistory is now a prop
}) => {
  // Removed useAgent hook usage
  const [activeTab, setActiveTab] = useState('logs');

  // Function to format the timestamp
  const formatTimestamp = (timestamp: string) => {
    return format(new Date(timestamp), 'HH:mm:ss');
  };

  // Function to get the appropriate CSS class based on log level
  const getLogTypeClass = (level: string) => {
    switch (level.toLowerCase()) {
      case 'info': return 'text-blue-500 dark:text-blue-400';
      case 'action': return 'text-purple-500 dark:text-purple-400';
      case 'error': return 'text-red-500 dark:text-red-400';
      case 'result': return 'text-green-500 dark:text-green-400';
      default: return '';
    }
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Agent Activity</CardTitle>
        {logs.length > 0 && (
          <Button variant="outline" size="sm" onClick={onClear}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Logs
          </Button>
        )}
      </CardHeader>
      
      <CardContent className="p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="logs" className="flex items-center">
              <Code className="h-4 w-4 mr-2" />
              Logs
            </TabsTrigger>
            <TabsTrigger value="actions" className="flex items-center">
              <Globe className="h-4 w-4 mr-2" />
              Actions
            </TabsTrigger>
            <TabsTrigger value="screenshots" className="flex items-center">
              <Image className="h-4 w-4 mr-2" />
              Screenshots
            </TabsTrigger>
          </TabsList>
          
          {/* Regular logs tab content */}
          <TabsContent value="logs">
            <ScrollArea className="h-[300px] pr-4">
              {logs.length === 0 && isRunning ? (
                 actionHistory && actionHistory.length > 0 ? ( // Keep actionHistory display if it's passed as a prop
                  <div className="space-y-2">
                    {actionHistory.map((action, idx) => (
                      <div key={idx} className="border rounded-md p-2 text-sm">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-medium text-purple-500">
                            Step {action.step_number + 1}
                          </span>
                          <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                            {action.title || 'Untitled Page'}
                          </span>
                        </div>
                        <p className="text-xs text-blue-500 mb-1 overflow-hidden text-ellipsis">
                          {action.url}
                        </p>
                        <p className="whitespace-pre-wrap break-words border-t pt-1 mt-1 text-muted-foreground">
                          Goal: {action.goal || 'Not specified'}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full border border-dashed rounded-md">
                    <p className="text-muted-foreground">Agent Running...</p>
                  </div>
                )
              ) : logs.length === 0 ? (
                <div className="flex items-center justify-center h-full border border-dashed rounded-md">
                  <p className="text-muted-foreground">No logs available</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {logs.map((log, idx) => (
                    <div key={idx} className="border rounded-md p-2 text-sm">
                      <div className="flex justify-between items-center mb-1">
                        <span className={cn("font-medium", getLogTypeClass(log.level))}>
                          {log.level.toUpperCase()}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap break-words">{log.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          {/* Actions tab showing navigation history */}
          <TabsContent value="actions">
            <ScrollArea className="h-[300px] pr-4">
              {!actionHistory || actionHistory.length === 0 ? (
                <div className="flex items-center justify-center h-full border border-dashed rounded-md">
                  <p className="text-muted-foreground">No actions recorded</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {actionHistory.map((action, idx) => (
                    <div key={idx} className="border rounded-md p-2 text-sm">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-medium text-purple-500">
                          Step {action.step_number + 1}
                        </span>
                        <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                          {action.title || 'Untitled Page'}
                        </span>
                      </div>
                      <p className="text-xs text-blue-500 mb-1 overflow-hidden text-ellipsis">
                        {action.url}
                      </p>
                      <p className="whitespace-pre-wrap break-words border-t pt-1 mt-1 text-muted-foreground">
                        Goal: {action.goal || 'Not specified'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          {/* Screenshots tab - This tab's content should be handled by ScreenshotDisplay */}
          {/* Keeping the tab trigger for now, but the content will be empty or removed later */}
           <TabsContent value="screenshots">
             {/* ScreenshotDisplay will be rendered outside of Tabs */}
           </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default LogDisplay;
