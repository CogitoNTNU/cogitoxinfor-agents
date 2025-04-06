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

async def run_agent(
    page, 
    query, 
    config=None, 
    testing=False, 
    test_actions=None, 
    human_intervention=False
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
        
    Returns:
        The final answer from the agent
    """

    # Setup history folder
    history_dir = setup_history_folder()
    
    # Prepare predictions for testing mode
    predictions = None
    if testing and test_actions:
        predictions = [
            Prediction(action=action, args=args)
            for action, args in test_actions
        ]
    
    # Create or update config
    if config is None:
        config = {
            "recursion_limit": 150,
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "page": None  # Will be set below
            }
        }
    elif "configurable" not in config:
        config["configurable"] = {"thread_id": str(uuid.uuid4())}
    
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
                            \nClick 'ENTER' to approve or provide alternative instructions, pass the element id you want to invoke: """
                            )
                                     
                        # Create a Command to resume execution
                        current_input = Command(resume=user_input)
                        break  # Exit the event loop to process the command
                    
                    # Process normal event updates
                    step_number = len(steps)
                    if "format_elements" in event:
                        image = event["format_elements"]["img"]
                        # Update only the image using the display ID
                        display.display(display.Image(base64.b64decode(image)))
                        # Save image with step number
                        save_image_to_history(image, "webpage.png", step_number)

                    if "agent" in event:
                        pred = event["agent"].get("prediction") or {}
                        action = pred.action if hasattr(pred, "action") else None
                        action_input = pred.args if hasattr(pred, "args") else None
                        
                        if action:
                            action_message = {
                                "type": "ACTION_UPDATE",
                                "action": action,
                                "args": action_input,
                                "step": len(steps)
                            }
                            # Add to steps and display updated text
                            steps.append(f"{len(steps) + 1}. {action}: {action_input}")
                            print(f"\n--- Agent Event ---")
                            print(f"Action: {action}")
                            print(f"Action Input: {action_input}")
                            print("\n".join(steps))
                            
                            if action == "ANSWER":
                                # Save final screenshot with special name
                                if "format_elements" in event and "img" in event["format_elements"]:
                                    save_image_to_history(event["format_elements"]["img"], "final_webpage.png")
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
        human_intervention=None
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
    
    # Extract query from state if provided
    if query is None and state is not None:
        query = state.input
        print(f"DEBUG: Extracted query from state: {query}")
    
    if query is None:
        print("DEBUG: ERROR - No query provided!")
        raise ValueError("Either query or state with input must be provided")
    
    # Process test_actions from state if available
    effective_test_actions = test_actions
    effective_testing = testing
    
    if state is not None:
        # Debug state values
        print(f"DEBUG state properties:")
        print(f"  - state.testing: {state.testing}")
        print(f"  - state.test_actions: {state.test_actions}")
        print(f"  - state.human_intervention: {state.human_intervention}")
        
        # If test_actions not provided directly but in state, use those
        if not effective_test_actions and state.test_actions:
            print(f"DEBUG: Using test_actions from state")
            effective_test_actions = [(pred.action, pred.args) for pred in state.test_actions]
        
        # If testing not provided directly but in state, use state value
        if not effective_testing and state.testing:
            effective_testing = state.testing
            print(f"DEBUG: Using testing flag from state: {effective_testing}")
    
    # Final debug of resolved parameters
    print(f"DEBUG resolved parameters:")
    print(f"  - query: {query}")
    print(f"  - effective_testing: {effective_testing}")
    print(f"  - effective_test_actions: {effective_test_actions}")
    print(f"  - human_intervention: {human_intervention}")
    
    playwright = None
    context = None
    
    try:
        # Initialize browser
        playwright, context, page = await initialize_browser()
        
        # Run the agent with the initialized page
        return await run_agent(
            human_intervention=human_intervention,
            page=page,
            query=query,
            config=config,
            testing=testing,
            test_actions=test_actions or (state and state.test_actions),
        )
    finally:
        # Clean up browser resources
        await close_browser(playwright, context)


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
        (CLICK, ['6']), 
        (TYPE, ['6', 'google maps']), 
        #(WAIT, ['6']),
        (CLICK, ['21']),             
        #(WAIT, ['2']),                
        #(CLICK, ['27']),
        #(WAIT, ['2']),
        #(CLICK, ['2']),               
        #(TYPE, ['2', 'BMW iX xDrive40 2022']),                  
    ]
    
    # Run the agent (fix syntax error)
    result = asyncio.run(test_agent(
        query=instructions,
        testing=True,
        test_actions=test_actions,
        human_intervention=True,
    ))
    
    print(f"\nFinal result: {result}")