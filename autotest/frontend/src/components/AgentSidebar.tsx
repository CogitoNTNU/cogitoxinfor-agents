import * as React from "react";
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator,
  SidebarFooter,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Plus, MessageSquare } from "lucide-react";
import { useAgent } from "../context/AgentContext";
import { agentApi } from "@/services/api.tsx";

export const AgentSidebar: React.FC = () => {
  const {
    agentIds,
    currentAgentId,
    setCurrentAgentId,
    runAgent,
  } = useAgent();

  const handleNewChat = async () => {
    const resp = await agentApi.createAgent();
    const newId = resp.data.agent_id;
    setCurrentAgentId(newId);
    // now wait for the user to enter a prompt and click Run
  };

  return (
    <Sidebar side="left" variant="sidebar" collapsible="icon">
      <SidebarHeader>
        <SidebarMenuButton asChild tooltip="New Chat">
          <button onClick={handleNewChat}>
            <Plus />
            <span>New Chat</span>
          </button>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarSeparator />
      <SidebarContent>
        <SidebarMenu>
          {agentIds.map((id, idx) => (
            <SidebarMenuItem key={`${id}-${idx}`}>
              <SidebarMenuButton
                isActive={currentAgentId === id}
                onClick={() => setCurrentAgentId(id)}
                tooltip={`Agent ${id}`}
              >
                <MessageSquare />
                <span>{id}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <SidebarTrigger />
      </SidebarFooter>
    </Sidebar>
  );
};

export default AgentSidebar;