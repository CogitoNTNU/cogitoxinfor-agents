
import React from 'react';
import { AgentProvider } from '../context/AgentContext';
import { ConversationDrawer } from '../components/ConversationDrawer';
import { ScreenshotDisplay } from '../components/ScreenshotDisplay';
import { InterruptDialog } from '../components/InterruptDialog';
import { useAgent } from '../context/AgentContext';
import { Sidebar } from '../components/Sidebar';
import { AgentControls } from '../components/AgentControls';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ConfigModal } from '../components/ConfigModal';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '../components/ui/resizable';

const AgentApp: React.FC = () => {
  const { currentScreenshot, currentStep, isRunning, finalAnswer, events } = useAgent();
  
  return (
    <div className="container mx-auto py-6 h-[calc(100vh-3rem)]">
      <header className="text-center mb-4">
        <h1 className="text-3xl font-bold">Event Agent UI</h1>
        <p className="text-muted-foreground">
          Visualize and interact with your web agent
        </p>
      </header>
      
      <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-12rem)]">
        <ResizablePanel defaultSize={33} minSize={25}>
          <div className="h-full pr-2">
            <AgentControls />
          </div>
        </ResizablePanel>
        
        <ResizableHandle withHandle />
        
        <ResizablePanel defaultSize={67}>
          <div className="h-full pl-2 flex flex-col gap-4">
            <ScreenshotDisplay 
              imageUrl={currentScreenshot} 
              step={currentStep}
              loading={isRunning && !currentScreenshot} 
            />
            
            {finalAnswer && (
              <div className="mt-2 p-4 bg-agent-answer/10 border border-agent-answer/30 rounded-md">
                <h3 className="font-medium mb-2">Final Answer:</h3>
                <p className="text-sm">{finalAnswer}</p>
              </div>
            )}
            
            <Card className="flex-grow overflow-hidden">
              <CardHeader>
                <CardTitle>Event History & Actions</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Tabs defaultValue="events" className="h-full">
                  <TabsList className="px-4 pt-2">
                    <TabsTrigger value="events">Events</TabsTrigger>
                    <TabsTrigger value="actions">Actions</TabsTrigger>
                  </TabsList>
                  <TabsContent value="events" className="h-[calc(100%-3rem)]">
                    <ScrollArea className="h-full">
                      {events.length > 0 ? (
                        <div className="p-4">
                          {events.map((event, index) => (
                            <div key={index} className="mb-2 p-2 border rounded">
                              <p className="font-medium">{event.type}</p>
                              <p className="text-sm text-muted-foreground">
                                {event.payload ? 
                                  JSON.stringify(event.payload) : 
                                  'No payload'}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-muted-foreground">
                          No events yet
                        </div>
                      )}
                    </ScrollArea>
                  </TabsContent>
                  <TabsContent value="actions" className="h-[calc(100%-3rem)]">
                    <ScrollArea className="h-full">
                      {window.testActions && window.testActions.length > 0 ? (
                        <div className="p-4">
                          {window.testActions.map((action, index) => (
                            <div key={index} className="mb-2 p-2 border rounded">
                              <p className="font-medium">{action.action}</p>
                              <p className="text-sm text-muted-foreground">{action.args.join(', ')}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-muted-foreground">
                          No actions configured
                        </div>
                      )}
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
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
