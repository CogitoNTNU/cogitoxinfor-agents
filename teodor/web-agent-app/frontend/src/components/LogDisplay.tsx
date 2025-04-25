import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { format } from 'date-fns';
import { Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogEntry {
  id: string;
  message: string;
  type: 'info' | 'action' | 'error' | 'result';
  timestamp: number;
}

interface LogDisplayProps {
  logs: LogEntry[];
  onClearLogs: () => void;
  className?: string;
}

export const LogDisplay: React.FC<LogDisplayProps> = ({ 
  logs, 
  onClearLogs,
  className 
}) => {
  // Function to format the timestamp
  const formatTimestamp = (timestamp: number) => {
    return format(new Date(timestamp), 'HH:mm:ss');
  };

  // Function to get the appropriate CSS class based on log type
  const getLogTypeClass = (type: LogEntry['type']) => {
    switch (type) {
      case 'info':
        return 'text-blue-500 dark:text-blue-400';
      case 'action':
        return 'text-purple-500 dark:text-purple-400';
      case 'error':
        return 'text-red-500 dark:text-red-400';
      case 'result':
        return 'text-green-500 dark:text-green-400';
      default:
        return '';
    }
  };

  // Function to get the log type label
  const getLogTypeLabel = (type: LogEntry['type']) => {
    switch (type) {
      case 'info':
        return 'INFO';
      case 'action':
        return 'ACTION';
      case 'error':
        return 'ERROR';
      case 'result':
        return 'RESULT';
      default:
        return String(type).toUpperCase();
    }
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Agent Logs</CardTitle>
        {logs.length > 0 && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onClearLogs}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Logs
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-4">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-[300px] border border-dashed rounded-md">
            <p className="text-muted-foreground">No logs available</p>
          </div>
        ) : (
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-2">
              {logs.map((log) => (
                <div 
                  key={log.id} 
                  className="border rounded-md p-2 text-sm"
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className={cn("font-medium", getLogTypeClass(log.type))}>
                      {getLogTypeLabel(log.type)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap break-words">{log.message}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

export default LogDisplay;
