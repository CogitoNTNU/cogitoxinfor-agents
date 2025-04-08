"""
Main entry point for the web agent.
"""

import os
import asyncio
from dotenv import load_dotenv

from langgraph.types import Command
from .tools import CLICK, TYPE, SCROLL, WAIT, NAVIGATE
from .models import InputState, Prediction
from .browser import initialize_browser, close_browser

# Load environment variables
load_dotenv()

# Create a persistent directory for user data
user_data_dir = os.path.join(os.path.expanduser("~"), "playwright_user_data")
os.makedirs(user_data_dir, exist_ok=True)


import uuid
import base64
from IPython import display

from .models import InputState, Prediction
from .utils import setup_history_folder, save_image_to_history
from .graph import get_graph_with_config
from langgraph.types import Command

def get_current_thread_id(config):
    """Get the current thread ID from config"""
    return config["configurable"]["thread_id"]


async def run_agent(
    page, 
    query, 
    config=None, 
    testing=False, 
    test_actions=None, 
    human_intervention=False,
    event_callback=None  # Add this parameter to handle event notifications
):
    """
    Run the web agent with the provided page.
    
    Args:
        page: An initialized Playwright page
        query: The user query to process
        config: Configuration dictionary for the agent
        testing: Whether to run in testing mode with predefined actions
        test_actions: List of (action, args) tuples to test
        human_intervention: Whether to enable human intervention
        event_callback: Optional callback function to notify about events
        
    Returns:
        The final answer from the agent
    """
    
    thread_id = config["configurable"]["thread_id"]
    print(f"Thread ID: {thread_id}")
    history_dir = setup_history_folder(thread_id)
    
    # Prepare predictions for testing mode
    predictions = None
    if testing and test_actions:
        predictions = [
            Prediction(action=action, args=args)
            for action, args in test_actions
        ]
    
    # Set the page in config
    config["configurable"]["page"] = page
    
    print("testing into run agent: ", testing)
    # Create input state
    state = InputState(
        input=query, 
        testing=testing,
        test_actions=predictions,
        human_intervention=human_intervention,
    )

    graph = get_graph_with_config(config)
    thread_config = config["configurable"]
    config["configurable"]["page"] = page
    try:
        final_answer = None
        steps = []
        
        # Initial graph input
        current_input = state
        
        while True:
            event_stream = graph.astream(current_input, config=thread_config)
            # Reset current_input for next potential interrupt
            current_input = None
            stream_finished = False
            answer_found = False
            try:
                async for event in event_stream:
                    # Only clear output when it's NOT an interrupt event
                    if "__interrupt__" not in event:
                        display.clear_output(wait=True)            
                    
                    # Check if there's an interrupt in the event
                    if "__interrupt__" in event:
                        interrupt_info = event["__interrupt__"][0]
                        message = interrupt_info.value
                        
                        print("\n" + "=" * 50)
                        print(f"🔔 HUMAN INPUT REQUIRED:")
                        print(f"Agent is requesting approval: {message}")
                        print("=" * 50 + "\n")
                        
                        # Small delay to ensure message is visible before the input prompt appears
                        await asyncio.sleep(0.2)
                        
                        user_input = input(
                            f"""
                            Agent is requesting approval: {message}
                            \nClick 'ENTER' to approve or provide alternative instructions, pass the element id you want to invoke: 
                            \nInput 'exit' to stop the agent.
                            """
                            )
                                     
                        # Create a Command to resume execution
                        current_input = Command(resume=user_input)
                        break  # Exit the event loop to process the command
                    
                    # Process normal event updates
                    step_number = len(steps)
                    print(f"Step {step_number}")
                    if "format_elements" in event:
                        image = event["format_elements"]["img"]
                        thread_id = config["configurable"]["thread_id"]
                        
                        # Save image with auto-generated filename
                        image_path, filename = save_image_to_history(image, step_number, thread_id)
                        print(f"Screenshot saved to history: {filename}")
                        
                        # Use the callback to send notification if provided
                        if event_callback:
                            # Create image URL - ensure consistent thread_id
                            image_url = f"/api/history/{thread_id}/{step_number}"
                            print(f"Sending image URL to frontend: {image_url}")
                            
                            # Create a message for the frontend
                            await event_callback({
                                "type": "SCREENSHOT_UPDATE",
                                "payload": {
                                    "session_id": thread_id,
                                    "step": step_number,
                                    "image_url": image_url,
                                    "screenshot": image  
                                }
                            })

                    if "agent" in event:
                        pred = event["agent"].get("prediction") or {}
                        action = pred.action if hasattr(pred, "action") else None
                        action_input = pred.args if hasattr(pred, "args") else None
                        
                        if action:
                            # Update steps list
                            steps.append(f"{len(steps) + 1}. {action}: {action_input}")
                            print(f"\n--- Agent Event ---")
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
                                answer_found = True
                                break
                
                # If we've processed all events without interruption or finding an answer
                stream_finished = True
                
            except Exception as e:
                print(f"Error during stream processing: {e}")
                break  # Exit on error
            
            # If we found an answer, we're done
            if answer_found:
                break
                
            # If the stream finished normally (no interrupts) and we don't have new input to process, we're done
            if stream_finished and not current_input:
                # Check if we need to continue due to state of the graph
                state = graph.get_state(config)
                if not state or not hasattr(state, 'test_actions') or not state.test_actions:
                    print("No more actions to test, finishing.")
                    break
                    
                # If we got here, keep processing the next cycle without user interaction
                print("Continuing to next test action automatically.")
                continue
                
            # If we have a command to process, continue the loop; otherwise exit
            if not current_input:
                print("Processing complete - no more actions to take.")
                break
                
        print("Agent execution completed successfully.")
        print(f"All screenshots saved to: {history_dir}")
        
    except Exception as e:
        print(f"Error during agent execution: {str(e)}")
        raise
    return final_answer



async def test_agent(
        config=None, 
        state=None, 
        query=None, 
        testing=False, 
        test_actions=None,
        human_intervention=None,
        start_url=None
        ) -> str:
    """
    Run the web agent with the specified configuration.
    
    Args:
        config: Configuration dictionary for the agent
        state: InputState object
        query: The user query to process
        testing: Whether to run in testing mode with predefined actions
        test_actions: List of (action, args) tuples to test
        
    Returns:
        The final answer from the agent
    """
  # Debug input parameters
    print(f"DEBUG test_agent inputs:")
    print(f"  - query: {query}")
    print(f"  - config: {config}")
    print(f"  - state: {state}")
    print(f"  - testing: {testing}")
    print(f"  - test_actions: {test_actions}")
    print(f"  - human_intervention: {human_intervention}")
    
    playwright = None
    context = None
    
    try:
        # Initialize browser with state restoration
        playwright, context, page = await initialize_browser(reuse_session=True)
        
        # Run the agent with the initialized page
        return await run_agent(
            human_intervention=human_intervention,
            page=page,
            query=query,
            config=config,
            testing=testing,
            test_actions=test_actions,
        )
    finally:
        # Save state when closing browser
        #await close_browser(playwright, context)
        print("Finished.")
# In the __main__ section, fix the asyncio.run syntax
if __name__ == "__main__":
    # Sample instructions
    instructions = """
    1. When pop box with (<a/>): "informasjonskapsler" pops up. Use scroll to make it visible and click on "godta alle"
    2. If you see (<a/>): "Godta alle" click on it to accept cookies.
    3. Go to finn.no
    4. In finn.no find the Search and search for 'BMW iX xDrive40 2022'.
    5. Click on the car.
    6. Find the car's specifications.
    7. Give me a summary of the car's specifications and features.
    """
    
    # Define the sequence of actions to test
    test_actions = [
        (NAVIGATE, ['https://www.google.com']),
        (CLICK, ['6']), 
        (TYPE, ['6', 'google maps']), 
        #(WAIT, ['6']),
        (CLICK, ['24']),             
        (WAIT, ['2']),                
        #(CLICK, ['27']),
        #(WAIT, ['2']),
        #(CLICK, ['2']),               
        #(TYPE, ['2', 'BMW iX xDrive40 2022']),                  
    ]
    thread_id = str(uuid.uuid4())
    # Run the agent (fix syntax error)
    result = asyncio.run(test_agent(
        query=instructions,
        testing=True,
        test_actions=test_actions,
        human_intervention=True,
        #start_url="https://www.google.com",
        config={
            "recursion_limit": 150,
            "configurable": {
                "thread_id": thread_id,
                "page": None
            }
        }
    ))
    
    print(f"\nFinal result: {result}")