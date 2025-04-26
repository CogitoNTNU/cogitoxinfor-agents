import asyncio
import traceback
import sys
from typing import Optional, Dict, Any, Callable
from langchain_core.messages import SystemMessage, HumanMessage
from .mcp_agent import MCPAgent
from langgraph.types import Command
import time

async def run_agent(
    query: str,
    agent: Optional[MCPAgent] = None,  # Make agent an optional parameter
    human_in_the_loop: bool = False,
    event_callback: Optional[Callable] = None,
    ui_mode: bool = False,
    response_queue: Optional[asyncio.Queue] = None
):
    """Run the agent with interrupt support for human-in-the-loop operation"""
    # Create the agent if not provided (for standalone usage)
    if agent is None:
        agent = MCPAgent()
        # Initialize agent
        await agent.initialize()
    
    agent.human_in_the_loop = human_in_the_loop
    
    # When initializing the agent
    messages = [
        SystemMessage(content="""You are a helpful browser assistant. Use the browser tools to help the user.
        
        When presenting search results:
        1. Always format them as a numbered list
        2. Include the title, URL, and brief description for each result
        3. Make sure to explicitly present all search results in your final response, don't just mention that you found them
        """),
        HumanMessage(content=query)
    ]
    initial_state = await agent.initialize_state(messages)
    thread_id = agent.config["configurable"]["thread_id"]
    try:
        final_answer = None
        steps = 0
        
        # Initial graph input
        current_input = initial_state
        last_screenshot = None
        
        while True:
                # Initialize agent
            event_stream = agent.graph.astream(current_input, config=agent.config)
            # Reset current_input for next potential interrupt
            current_input = None
            try:
                async for event in event_stream:
                    if "__interrupt__" in event:
                        interrupt_info = event["__interrupt__"][0]
                        message = interrupt_info.value

                        if ui_mode and event_callback:
                            # Send interrupt to frontend
                            await event_callback({
                                "type": "INTERRUPT",
                                "payload": {
                                    "session_id": thread_id,
                                    "message": message,
                                    "step": step_number
                                }
                            })
                            
                            # Wait for response from frontend
                            if response_queue:
                                print("Waiting for UI response...")
                                try:
                                    # Add timeout to avoid hanging indefinitely
                                    user_input = await asyncio.wait_for(response_queue.get(), timeout=120)
                                    print(f"Received UI response: {user_input}")
                                    
                                    # Create command to resume execution
                                    current_input = Command(resume=user_input)
                                    break  # Exit event loop to process command
                                except asyncio.TimeoutError:
                                    print("ERROR: Timed out waiting for user response!")
                                    # Provide a default response to avoid hanging
                                    current_input = Command(resume="approved")
                                    break
                            else:
                                raise Exception("Response queue not available")
                        else:
                            # Console mode fallback
                            user_input = input(                                    f"""
                                    Agent is requesting approval: {message}
                                    \nClick 'ENTER' to approve or provide alternative instructions, pass the element id you want to invoke: 
                                    \nInput 'exit' to stop the agent.
                                    """)
                            current_input = Command(resume=user_input)
                            break
                    #await agent.initialize()
                    
                    # Process normal event updates
                    step_number = steps + 1
                    print(f"Step {step_number}")
                    if "agent" in event:
                        steps += 1
                        agent_event = event["agent"]
                        print(f"\n--- Agent Event ---")
                        print(f"Agent Event: {agent_event}")
                        
                        # Extract messages and tool calls with enhanced structure
                        if "messages" in agent_event:
                            for message in agent_event["messages"]:
                                # Track the latest tool call for reference
                                if hasattr(message, "tool_calls") and message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        tool_name = tool_call.get("name", "unknown_tool")
                                        tool_args = tool_call.get("args", {})
                                        tool_id = tool_call.get("id", "")
                                        print(f"Tool: {tool_name}")
                                        print(f"Arguments: {tool_args}")
                                        print(f"Tool call ID: {tool_id}")
                                        
                                        # Store the latest tool call for interrupt handling
                                        last_tool_call = tool_call
                                        
                                        # Send tool call event if callback provided
                                        if event_callback:
                                            await event_callback({
                                                "type": "TOOL_CALL",
                                                "payload": {
                                                    "session_id": thread_id,
                                                    "tool": {
                                                        "name": tool_name,
                                                        "args": tool_args,
                                                        "id": tool_id
                                                    },
                                                    "step": step_number,
                                                    "timestamp": int(time.time() * 1000)
                                                }
                                            })
                                
                                # Handle regular content
                                if message.content and message.content.strip():
                                    print(f"Message: {message.content}")
                                    # Send agent message event if callback provided
                                    if event_callback:
                                        await event_callback({
                                            "type": "AGENT_MESSAGE",
                                            "payload": {
                                                "session_id": thread_id,
                                                "message": message.content,
                                                "step": step_number,
                                                "timestamp": int(time.time() * 1000)
                                            }
                                        })
                
            except Exception as e:
                print(f"Error during stream processing: {e}")
                break  # Exit on error
                
            # If we have a command to process, continue the loop; otherwise exit
            if not current_input:
                print("Processing complete - no more actions to take.")
                break
                
        print("Agent execution completed successfully.")
        
    except Exception as e:
        print(f"Error during agent execution: {str(e)}")
        raise

    
    finally:
        print("Performing agent cleanup...")
        await agent.cleanup()
        print("Agent cleanup completed")
        return final_answer

# Example usage
async def main():
    print("Starting browser agent...")
    result = await run_agent(
        "Go to google. Search for fastapi. Give me the top five results", 
                   human_in_the_loop=False)
    print(f"Agent completed with result: {result}")

if __name__ == "__main__":
    asyncio.run(main())