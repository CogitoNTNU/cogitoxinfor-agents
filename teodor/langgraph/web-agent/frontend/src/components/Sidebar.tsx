
import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from './ui/sheet';
import { Menu } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { EventTimeline } from './EventTimeline';
import { ScrollArea } from './ui/scroll-area';
import { useAgent } from '../context/AgentContext';
import { TestSettings } from './TestSettings';
import { AgentQuery } from './AgentQuery';

export const Sidebar: React.FC = () => {
  const { events } = useAgent();
  
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="fixed right-4 top-4 h-10 w-10 rounded-full p-0">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[350px] sm:w-[450px]">
        <SheetHeader>
          <SheetTitle>Agent Control Panel</SheetTitle>
        </SheetHeader>
        
        <div className="mt-4">
          <Tabs defaultValue="query" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="query">Query</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
            
            <TabsContent value="query" className="mt-4">
              <AgentQuery />
            </TabsContent>
            
            <TabsContent value="settings" className="mt-4">
              <TestSettings />
            </TabsContent>
          </Tabs>
        </div>
        
        <div className="mt-6">
          <h3 className="mb-2 font-medium">Event History</h3>
          <ScrollArea className="h-[calc(100vh-15rem)]">
            <EventTimeline events={events} />
          </ScrollArea>
        </div>
        
        <SheetFooter className="mt-auto pt-4">
          <Button variant="outline" className="w-full">Close</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};
