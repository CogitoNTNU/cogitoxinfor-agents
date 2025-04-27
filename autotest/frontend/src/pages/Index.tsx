import React, { useRef, useEffect, useState } from 'react';
import { AgentProvider, useAgent } from '../context/AgentContext'; // Re-import AgentProvider and import useAgent
import { ScreenshotDisplay } from '../components/ScreenshotDisplay';
import { LogDisplay } from '../components/LogDisplay';
// Removed InterruptDialog import
import { useAgentStream } from '../hooks/useAgentStream';
import { agentApi } from '../services/api';
import AgentController from '../components/AgentController';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'; // Keep Card components for layout
// Removed ConfigModal import
import AgentSidebar from '../components/AgentSidebar';
import { SidebarProvider } from "@/components/ui/sidebar";
// Removed Tabs, TabsContent, TabsList, TabsTrigger imports
// Removed ToolCalls, ToolResult imports
import { Button } from '../components/ui/button'; // Keep Button for Clear Logs/Screenshots
import { RefreshCcw } from 'lucide-react'; // Keep Refresh icon

interface AgentPanelProps {
  agentId: string;
}

const AgentPanel: React.FC<AgentPanelProps> = ({ agentId }) => {
  const { logs, screenshots, isRunning } = useAgentStream(agentId);

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left: logs and chat */}
      <div className="w-1/3 flex flex-col h-full pr-4">
        <h3 className="font-bold mb-2">Log</h3>
        <div className="flex-1 overflow-auto mb-4">
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

  return (
    <div className="container mx-auto py-6 h-[calc(100vh-3rem)] flex flex-col">
      <header className="text-center mb-4">
        <h1 className="text-3xl font-bold">Cogito x Infor Autotester</h1>
        <p className="text-muted-foreground">
          Visualize and interact with your web agent
        </p>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <AgentSidebar />
        <div className="flex-1 flex flex-col overflow-auto pl-4">
          <div className="flex-1 overflow-auto">
            {currentAgentId ? (
              <AgentPanel agentId={currentAgentId} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                Select or create a chat
              </div>
            )}
          </div>
        </div>
      </div>
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
