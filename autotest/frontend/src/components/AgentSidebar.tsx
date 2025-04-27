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
import { useSidebar } from "@/components/ui/sidebar";

export const AgentSidebar: React.FC = () => {
  const { state } = useSidebar();
  const {
    agentIds,
    currentAgentId,
    setCurrentAgentId,
  } = useAgent();

  const handleNewChat = async () => {
    const resp = await agentApi.createAgent();
    const newId = resp.data.agent_id;
    setCurrentAgentId(newId);
    // now wait for the user to enter a prompt and click Run
  };

  return (
    <Sidebar
        side="left"
        variant="sidebar"
        collapsible="icon"
        className="w-12 hover:w-64 transition-all duration-200 ease-in-out"
      >
      <SidebarHeader>
        <SidebarMenuButton asChild tooltip="New Chat">
          <button onClick={handleNewChat}>
            <Plus />
            <span>New Chat</span>
          </button>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarSeparator className="mb-2"/>
      <SidebarContent>
        <SidebarMenu>
          {agentIds.map((id, idx) => (
            <SidebarMenuItem key={`${id}-${idx}`}
              className="mx-2">
              <SidebarMenuButton
                isActive={currentAgentId === id}
                onClick={() => setCurrentAgentId(id)}
                tooltip={`Agent ${id}`}
              >
                <MessageSquare />
                <span className={state === "collapsed" ? "hidden" : ""}>{id}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  );
};

export default AgentSidebar;
