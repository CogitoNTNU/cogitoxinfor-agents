import React, { useRef, useEffect, useState } from 'react';
import { AgentProvider } from '../context/AgentContext';
import { ConversationDrawer } from '../components/ConversationDrawer';
import { ScreenshotDisplay } from '../components/ScreenshotDisplay';
import { InterruptDialog } from '../components/InterruptDialog';
import { useAgent } from '../context/AgentContext';
import { Sidebar } from '../components/Sidebar';
import AgentController from '../components/AgentController';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ConfigModal } from '../components/ConfigModal';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '../components/ui/resizable';
import { ToolCalls, ToolResult } from '../components/ToolDisplay';
import { AIMessage, ToolMessage } from '@langchain/langgraph-sdk';
import { BrowserViewer } from "../components/BrowserViewer";
import { agentApi } from '../services/api';
import { Button } from '../components/ui/button';
import { RefreshCcw } from 'lucide-react';

const AgentApp: React.FC = () => {
  const { 
    screenshots, 
    clearScreenshots, 
    isRunning, 
    isPaused,
    finalAnswer, 
    events,
    currentAgentId,
    loadAgentHistory
  } = useAgent();
  
  const [systemStats, setSystemStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const logsScrollRef = useRef<HTMLDivElement>(null);

  // Effect to scroll logs to bottom when events change
  useEffect(() => {
    if (logsScrollRef.current) {
      logsScrollRef.current.scrollTop = logsScrollRef.current.scrollHeight;
    }
  }, [events]);
  
  // Fetch system stats periodically
  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const response = await agentApi.getSystemStats();
        setSystemStats(response.data);
      } catch (error) {
        console.error("Error fetching system stats:", error);
      }
    };
    
    fetchSystemStats();
    const intervalId = setInterval(fetchSystemStats, 30000); // Every 30 seconds
    
    return () => clearInterval(intervalId);
  }, []);
  
  // Fetch available agents
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await agentApi.listAgents();
        setAgents(response.data);
      } catch (error) {
        console.error("Error fetching agents:", error);
      }
    };
    
    fetchAgents();
  }, [isRunning, isPaused]); // Refresh when agent status changes
  
  // Load agent history when agent ID changes
  useEffect(() => {
    if (currentAgentId) {
      loadAgentHistory(currentAgentId);
    }
  }, [currentAgentId, loadAgentHistory]);
  
  return (
    <div className="container mx-auto py-6 h-[calc(100vh-3rem)]">
      <header className="text-center mb-4">
        <h1 className="text-3xl font-bold">Cogito x Infor Autotester</h1>
        <p className="text-muted-foreground">
          Visualize and interact with your web agent
        </p>
        {systemStats && (
          <div className="text-xs text-muted-foreground mt-1">
            System: CPU {systemStats.cpu_usage}% | Memory {systemStats.memory_usage}% | Active Agents: {systemStats.active_agents}
          </div>
        )}
      </header>
      
      <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-12rem)]">
        <ResizablePanel defaultSize={33} minSize={25}>
          <div className="h-full pr-2 flex flex-col">
            <div className="flex-shrink-0">
              <AgentController />
            </div>
            <Card className="mt-4 mb-8 flex-grow overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between py-2">
                <CardTitle>Logs</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => currentAgentId && loadAgentHistory(currentAgentId)}
                >
                  <RefreshCcw className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-2 h-[400px]">
                <div className="h-full overflow-y-auto" ref={logsScrollRef}>
                  {events.length > 0 ? (
                    <div className="p-4 space-y-2">
                      {events.map((event, index) => {
                        if (event.type === 'tool_code') {
                          const toolCalls = [{
                            id: event.payload.tool_call_id,
                            name: event.payload.tool_name,
                            args: event.payload.args || {},
                          }] as AIMessage['tool_calls'];
                          return <ToolCalls key={index} toolCalls={toolCalls} />;
                        } else {
                          const toolResult = {
                            type: 'tool',
                            name: event.type,
                            content: event.payload?.content ? JSON.stringify(event.payload.content, null, 2) : (event.payload ? JSON.stringify(event.payload, null, 2) : 'No payload'),
                            tool_call_id: event.payload?.tool_call_id,
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
            <Tabs defaultValue="screenshots" className="w-full flex-grow">
              <TabsList className="grid w-full grid-cols-2 items-center">
                <TabsTrigger value="screenshots">Screenshots</TabsTrigger>
                <TabsTrigger value="live-browser">Live Browser</TabsTrigger>
              </TabsList>
              <TabsContent value="screenshots" className="h-full">
                <ScreenshotDisplay 
                  screenshots={screenshots} 
                  onClearScreenshots={clearScreenshots}
                  loading={isRunning && screenshots.length === 0} 
                />
              </TabsContent>
              <TabsContent value="live-browser" className="h-full">
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
