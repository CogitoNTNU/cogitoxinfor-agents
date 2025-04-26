import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { useAgent } from '../context/AgentContext';
import { Code } from 'lucide-react'; // Using Code icon for logs

export const LogDrawer: React.FC = () => {
  const { events } = useAgent();

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="fixed bottom-4 right-4 h-10 w-10 rounded-full p-0">
          <Code className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="h-[50vh]"> {/* Adjust height as needed */}
        <SheetHeader>
          <SheetTitle>Logs</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100%-4rem)]"> {/* Adjust height to account for header */}
          {events.length > 0 ? (
            <div className="p-4 space-y-2">
              {events.map((event, index) => (
                <div key={index} className={`mb-2 p-2 border rounded ${event.type === 'tool_code' ? 'bg-blue-100 dark:bg-blue-900 border-blue-300 dark:border-blue-700' : ''}`}>
                  <p className={`font-medium ${event.type === 'tool_code' ? 'text-blue-800 dark:text-blue-200' : ''}`}>{event.type === 'tool_code' ? `Tool Call: ${event.payload.tool_name}` : event.type}</p>
                  <p className={`text-sm ${event.type === 'tool_code' ? 'text-blue-700 dark:text-blue-300' : 'text-muted-foreground'}`}>
                    {event.payload ? 
                      JSON.stringify(event.payload, null, 2) : 
                      'No payload'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-muted-foreground">
              No logs yet
            </div>
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};
