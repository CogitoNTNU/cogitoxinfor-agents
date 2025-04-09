
import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from './ui/sheet';
import { Button } from './ui/button';
import { MessageSquare, Settings, Layers, History } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { EventTimeline } from './EventTimeline';
import { Switch } from './ui/switch';
import { Label } from './ui/label';

export const ConversationDrawer: React.FC = () => {
  const { events } = useAgent();
  const [darkMode, setDarkMode] = React.useState(false);

  // Toggle dark mode function (just a placeholder for now)
  const toggleDarkMode = (checked: boolean) => {
    setDarkMode(checked);
    // Implementation would go here
  };
  
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="fixed left-4 top-4 h-10 w-10 rounded-full p-0">
          <Layers className="h-5 w-5" />
          {events.length > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-primary text-white text-xs flex items-center justify-center">
              {events.length}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[350px] sm:w-[450px]">
        <SheetHeader>
          <SheetTitle>Conversation & User Settings</SheetTitle>
        </SheetHeader>
        
        <Tabs defaultValue="conversations" className="flex-1 mt-4">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="conversations">Conversations</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="conversations" className="flex-1 mt-4">
            <div className="space-y-4">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <History className="h-4 w-4" />
                Conversation History
              </h3>
              <ScrollArea className="h-[calc(100vh-15rem)]">
                {events.length > 0 ? (
                  <EventTimeline events={events} />
                ) : (
                  <div className="text-center p-4 text-muted-foreground">
                    No conversations yet
                  </div>
                )}
              </ScrollArea>
            </div>
          </TabsContent>
          
          <TabsContent value="settings" className="flex-1 mt-4">
            <div className="space-y-6">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Settings className="h-4 w-4" />
                User Settings
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="dark-mode">Dark Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Toggle between light and dark theme
                    </p>
                  </div>
                  <Switch 
                    id="dark-mode" 
                    checked={darkMode}
                    onCheckedChange={toggleDarkMode}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="notifications">Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable desktop notifications
                    </p>
                  </div>
                  <Switch id="notifications" />
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
        
        <SheetFooter className="mt-auto pt-4">
          <Button variant="outline" className="w-full">Close</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};
