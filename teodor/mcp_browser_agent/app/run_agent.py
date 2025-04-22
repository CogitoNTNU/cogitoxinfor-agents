import asyncio
import traceback
import sys
from typing import Optional, Dict, Any, Callable
from langchain_core.messages import SystemMessage, HumanMessage
from mcp_agent import MCPAgent
from langgraph.types import Command

async def run_agent(
    query: str,
    human_in_the_loop: bool = False,
    event_callback: Optional[Callable] = None,
    ui_mode: bool = False,
    response_queue: Optional[asyncio.Queue] = None
):
    """Run the agent with interrupt support for human-in-the-loop operation"""
    # Create the agent with values stream mode for interrupt detection
    agent = MCPAgent()
    agent.human_in_the_loop = human_in_the_loop
    
    # Initialize agent
    await agent.initialize()
    
    # Create input messages
    messages = [
        SystemMessage(content="You are a helpful browser assistant. Use the browser tools to help the user."),
        HumanMessage(content=query)
    ]
    initial_state = await agent.initialize_state(messages)
    thread_id = agent.config["configurable"]["thread_id"]
    try:
        final_answer = None
        steps = []
        
        # Initial graph input
        current_input = initial_state
        
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
                        step_number = len(steps)

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
                                user_input = await response_queue.get()
                                print(f"Received UI response: {user_input}")
                                
                                # Create command to resume execution
                                current_input = Command(resume=user_input)
                                break  # Exit event loop to process command
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
                    await agent.initialize()
                    
                    # Process normal event updates
                    step_number = len(steps)
                    print(f"Step {step_number}")

                    if "agent" in event:
                        agent_event = event["agent"]
                        print(f"\n--- Agent Event ---")
                        
                        # Extract messages and tool calls
                        if "messages" in agent_event:
                            for message in agent_event["messages"]:
                                # Handle tool calls
                                if hasattr(message, "tool_calls") and message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        tool_name = tool_call.get("name", "unknown_tool")
                                        tool_args = tool_call.get("args", {})
                                        print(f"Tool: {tool_name}")
                                        print(f"Arguments: {tool_args}")
                                # Handle regular content
                                if message.content and message.content.strip():
                                    print(f"Message: {message.content}")
                        
                        # Extract prediction if available (older format)
                        pred = agent_event.get("prediction") or {}
                        action = pred.action if hasattr(pred, "action") else None
                        action_input = pred.args if hasattr(pred, "args") else None
                        
                        if action:
                            # Update steps list
                            steps.append(f"{len(steps) + 1}. {action}: {action_input}")
                            print(f"Action: {action}")
                            print(f"Action Input: {action_input}")
                            print("\n".join(steps))
                            
                            # Notify about action if callback provided
                            if event_callback:
                                action_message = {
                                    "type": "ACTION_UPDATE",
                                    "payload": {
                                        "session_id": thread_id,
                                        "action": action,
                                        "args": action_input,
                                        "step": step_number
                                    }
                                }
                                await event_callback(action_message)
                            
                            if action == "ANSWER":
                                print(f"\nFinal answer: {action_input[0]}")
                                final_answer = action_input[0]

                                if event_callback:
                                    answer_message = {
                                        "type": "FINAL_ANSWER",
                                        "payload": {
                                            "session_id": thread_id,
                                            "answer": action_input[0],
                                            "step": step_number
                                        }
                                    }
                                    await event_callback(answer_message)
                                
                                break
                
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
        "Go to bing.com and search for 'python programming'", 
                   human_in_the_loop=True)
    print(f"Agent completed with result: {result}")

if __name__ == "__main__":
    asyncio.run(main())