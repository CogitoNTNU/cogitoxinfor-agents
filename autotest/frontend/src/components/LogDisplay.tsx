import React, { useState, useEffect, useRef } from 'react'; // Import useState, useEffect, and useRef
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { format } from 'date-fns';
import { Trash2, Image, Code, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const scrollAreaRef = useRef<HTMLDivElement>(null); // Ref for the scrollable area

  // Auto-scroll the log view to the bottom on new logs
  useEffect(() => {
    if (scrollAreaRef.current) {
      // If the ScrollArea wraps a viewport element, target that
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement;
      const scrollEl = viewport || scrollAreaRef.current;
      // Scroll to bottom
      scrollEl.scrollTop = scrollEl.scrollHeight;
    }
  }, [logs]);

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
        <CardContent className="p-4">
          {/* Regular logs tab content */}
            <ScrollArea className="h-[320px] pr-4" ref={scrollAreaRef}> {/* Attach ref to ScrollArea */}
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
                    <p className="text-muted-foreground">Agent waiting for task...</p>
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
      </CardContent>
    </Card>
  );
};

export default LogDisplay;
