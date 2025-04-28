import React, { useRef, useEffect, useState } from 'react';
import { AgentProvider, useAgent } from '../context/AgentContext'; // Re-import AgentProvider and import useAgent
import { ScreenshotDisplay } from '../components/ScreenshotDisplay';
import { LogDisplay } from '../components/LogDisplay';
import { useAgentStream } from '../hooks/useAgentStream';
import { agentApi } from '../services/api';
import AgentController from '../components/AgentController';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'; // Keep Card components for layout
import AgentSidebar from '../components/AgentSidebar';
import { SidebarProvider, useSidebar, SIDEBAR_WIDTH, SIDEBAR_WIDTH_ICON } from "@/components/ui/sidebar"; // Import useSidebar and width constants
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"; // Import Tabs components
import { Button } from '../components/ui/button'; // Keep Button for Clear Logs/Screenshots
import { RefreshCcw } from 'lucide-react'; // Keep Refresh icon
import TestGenerator from '../components/TestGenerator'; // Import the new component

interface AgentPanelProps {
  agentId: string;
}

const AgentPanel: React.FC<AgentPanelProps> = ({ agentId }) => {
  const { logs, screenshots, isRunning } = useAgentStream(agentId);

  return (
    <div className="flex flex-1 ml-12">
      {/* Left: logs and chat */}
      <div className="w-1/3 flex flex-col h-full pr-4">
        <h3 className="font-bold mb-2">Log</h3>
        <div className="flex-1 overflow-visible mb-4">
          <LogDisplay
            logs={logs}
            isRunning={isRunning}
            actionHistory={[]}
            onClear={() => {}}
          />
        </div>
        <div className="flex-shrink-0">
          <AgentController />
        </div>
      </div>
      {/* Right: screenshots */}
      <div className="w-2/3 flex flex-col h-full pl-4">
        <h3 className="font-bold mb-2">Screenshots</h3>
        <div className="flex-1 overflow-visible">
          <ScreenshotDisplay
            screenshots={screenshots} // Pass screenshots directly
            onClearScreenshots={() => {}}
            loading={isRunning && screenshots.length === 0}
          />
        </div>
      </div>
    </div>
  );
};

const AgentApp: React.FC = () => {
  const { currentAgentId } = useAgent();
  const { state, isMobile } = useSidebar(); // Use the useSidebar hook

  // Calculate left padding based on sidebar state

  return (
    <div className="container mx-auto py-6 h-[calc(100vh-3rem)] flex flex-col">
      <header className="text-center mb-4">
        <h1 className="text-3xl font-bold">AI-Powered Test Automation 🤖</h1>
        <p className="text-muted-foreground">
           Our agent browses your site, figures out the flows, and generates ready-to-run web tests.              </p>

      </header>
      <div className="flex flex-1 overflow-hidden"> {/* Main flex container */}
        <AgentSidebar /> {/* Sidebar remains outside tabs */}
          <Tabs defaultValue="execution" className="w-full h-full flex flex-col"> {/* Tabs take full width of content area */}
            <TabsList className="grid w-auto grid-cols-2 justify-center mx-auto"> {/* TabsList centered within Tabs */}
              <TabsTrigger value="execution">Site Exploration</TabsTrigger>
              <TabsTrigger value="test-generation">Test Generation</TabsTrigger>
            </TabsList>

            <TabsContent value="execution" className="flex-1 overflow-auto"> {/* Execution Tab Content */}
              {currentAgentId ? (
                <AgentPanel agentId={currentAgentId} />
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  Select or create a chat
                </div>
              )}
            </TabsContent>

            <TabsContent value="test-generation" className="flex-1 overflow-auto"> {/* Test Generation Tab Content */}
              <TestGenerator />
            </TabsContent>
          </Tabs>
        </div>
        <p className="text-center text-muted-foreground" >⚡ Powered by Cogito × Infor ⚡</p>
      </div>
  );
};

const Index: React.FC = () => {
  return (
    <AgentProvider> {/* Wrap AgentApp with AgentProvider */}
      <SidebarProvider>
        <AgentApp />
      </SidebarProvider>
    </AgentProvider>
  );
};

export default Index;
