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
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '../components/ui/resizable';
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
    <div key={agentId} className="mb-8">
      <h3 className="font-bold mb-2">Agent {agentId}</h3>
      <LogDisplay
        logs={logs}
        isRunning={isRunning}
        actionHistory={[]} // or derive via history call
        onClear={() => {}}
      />
      <ScreenshotDisplay
        screenshots={screenshots.map((data, idx) => ({
          id: `${agentId}-${idx}`,
          url: `data:image/png;base64,${data}`
        }))}
        onClearScreenshots={() => {}}
        loading={isRunning && screenshots.length === 0}
      />
    </div>
  );
};

const AgentApp: React.FC = () => {
  const { agentIds, runAgent } = useAgent();

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
            {/* Agent Controller - unchanged */}
            <div className="flex-shrink-0 mb-4">
              {/* No props passed to AgentController as it uses useAgent */}
              <AgentController />
            </div>
            <div className="mb-4 flex-grow overflow-auto space-y-6">
              {agentIds.map(agentId => (
                <AgentPanel key={agentId} agentId={agentId} />
              ))}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

      </ResizablePanelGroup>

      {/* Removed unnecessary components */}
      {/* <ConversationDrawer /> */}
      {/* <InterruptDialog /> */}
      {/* <ConfigModal open={false} onOpenChange={() => {}} /> */}
      {/* Removed other potentially unnecessary components like Sidebar, ToolDisplay */}
    </div>
  );
};

const Index: React.FC = () => {
  return (
    <AgentProvider> {/* Wrap AgentApp with AgentProvider */}
      <AgentApp />
    </AgentProvider>
  );
};

export default Index;
