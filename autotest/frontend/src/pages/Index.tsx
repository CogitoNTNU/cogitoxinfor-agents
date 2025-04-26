import React, { useRef, useEffect } from 'react';
import { AgentProvider } from '../context/AgentContext';
import { ConversationDrawer } from '../components/ConversationDrawer';
import { ScreenshotDisplay } from '../components/ScreenshotDisplay';
import { InterruptDialog } from '../components/InterruptDialog';
import { useAgent } from '../context/AgentContext';
import { Sidebar } from '../components/Sidebar';
import { AgentControls } from '../components/AgentControls';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ConfigModal } from '../components/ConfigModal';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '../components/ui/resizable';
import { ToolCalls, ToolResult } from '../components/ToolDisplay'; // Import ToolCalls and ToolResult
import { AIMessage, ToolMessage } from '@langchain/langgraph-sdk'; // Import necessary types
import { BrowserViewer } from "../components/BrowserViewer";


const AgentApp: React.FC = () => {
  const { screenshots, clearScreenshots, isRunning, finalAnswer, events } = useAgent();
  const logsScrollRef = useRef<HTMLDivElement>(null); // Declare logsScrollRef

  // Effect to scroll logs to bottom when events change
  useEffect(() => {
    if (logsScrollRef.current) {
      logsScrollRef.current.scrollTop = logsScrollRef.current.scrollHeight;
    }
  }, [events]);
  
  return (
    <div className="container mx-auto py-6 h-[calc(100vh-3rem)]">
      <header className="text-center mb-4">
        <h1 className="text-3xl font-bold">Cogito x Infor Autotester</h1>
        <p className="text-muted-foreground">
          Visualize and interact with your web agent
        </p>
      </header>
      
      <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-12rem)]">
        <ResizablePanel defaultSize={33} minSize={25}>
          <div className="h-full pr-2 flex flex-col">
            <div className="flex-shrink-0">
              <AgentControls />
            </div>
            <Card className="mt-4 mb-8 flex-grow overflow-hidden">
              <CardHeader>
                <CardTitle>Logs</CardTitle>
              </CardHeader>
              <CardContent className="p-2 h-[400px]"> {/* Made logs even less tall */}
                <div className="h-full overflow-y-auto" ref={logsScrollRef}>
                  {events.length > 0 ? (
                    <div className="p-4 space-y-2">
                      {events.map((event, index) => {
                        if (event.type === 'tool_code') {
                          // Assuming 'tool_code' events have a payload structure
                          // that can be mapped to ToolCalls props.
                          // This might need adjustment based on the actual event payload structure.
                          const toolCalls = [{
                            id: event.payload.tool_call_id, // Assuming tool_call_id exists
                            name: event.payload.tool_name,
                            args: event.payload.args || {}, // Assuming args exist
                          }] as AIMessage['tool_calls'];
                          return <ToolCalls key={index} toolCalls={toolCalls} />;
                        } else {
                          // Assuming other event types represent tool results
                          // This might need adjustment based on the actual event payload structure.
                          const toolResult = {
                            type: 'tool', // Assuming type is 'tool' for ToolResult
                            name: event.type, // Using event type as tool name for now
                            content: event.payload?.content ? JSON.stringify(event.payload.content, null, 2) : (event.payload ? JSON.stringify(event.payload, null, 2) : 'No payload'), // Use payload.content if available, otherwise use the whole payload
                            tool_call_id: event.payload?.tool_call_id, // Assuming tool_call_id exists in payload
                          } as ToolMessage;
                          return <ToolResult key={index} message={toolResult} />;
                        }
                      })}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-muted-foreground">
                      No logs yet
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </ResizablePanel>
        
        <ResizableHandle withHandle />
        
        <ResizablePanel defaultSize={67}>
          <div className="h-full pl-2 flex flex-col gap-4">
            <Tabs defaultValue="screenshots" className="w-full flex-grow"> {/* Make tabs take available height */}
              <TabsList className="grid w-full grid-cols-2 items-center"> {/* Added items-center */}
                <TabsTrigger value="screenshots">Screenshots</TabsTrigger>
                <TabsTrigger value="live-browser">Live Browser</TabsTrigger>
              </TabsList>
              <TabsContent value="screenshots" className="h-full"> {/* Make content take available height */}
                <ScreenshotDisplay 
                  screenshots={screenshots} 
                  onClearScreenshots={clearScreenshots}
                  loading={isRunning && screenshots.length === 0} 
                />
              </TabsContent>
              <TabsContent value="live-browser" className="h-full"> {/* Make content take available height */}
                <Card className="h-full">
                  <CardHeader>
                    <CardTitle>Live Browser View</CardTitle>
                  </CardHeader>
                  <CardContent className="flex items-center justify-center h-[200px] border border-dashed rounded-md">
                    <BrowserViewer />
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
            
            {finalAnswer && (
              <div className="mt-2 p-4 bg-agent-answer/10 border border-agent-answer/30 rounded-md">
                <h3 className="font-medium mb-2">Final Answer:</h3>
                <p className="text-sm">{finalAnswer}</p>
              </div>
            )}
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
      
      <ConversationDrawer />
      <InterruptDialog />
      <ConfigModal open={false} onOpenChange={() => {}} />
    </div>
  );
};

const Index: React.FC = () => {
  return (
    <AgentProvider>
      <AgentApp />
    </AgentProvider>
  );
};

export default Index;
