from IPython import display
from playwright.async_api import async_playwright
import asyncio
import uuid
import base64
from graph import graph
from models import AgentState
from graph import (
    HUMAN_INTERACTION,
)

config = {
    "configurable": {
        "thread_id": str(uuid.uuid4()),
        "recursion_limit": 150,
    },
}

async def test_agent(query: str, config: dict = config):
    # Start Playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        executable_path="/usr/bin/chromium-browser",
        #executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        headless=False,  # Set to False to watch the agent navigate
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
        ],
    )

    # Open a new page
    page = await browser.new_page()

    # Navigate to Google
    await page.goto("https://www.google.com")
    await page.wait_for_selector("text=Godta alle", timeout=5000)
    await page.click("text=Godta alle") 

    # Create an initial AgentState
    state = AgentState(
        page=page,
        input=query,
        img=None,
        bboxes=[],
        prediction=None,
        scratchpad=[],
        observation=None,
        ids=[]
    )

    final_answer = None
    steps = []
        
    try:
        # Create an async iterator for the event stream
        event_iterator = graph.astream(state, config=config).__aiter__()
        
        while True:
            try:
                # Try to get next event with timeout
                event = await asyncio.wait_for(event_iterator.__anext__(), timeout=0.1)
                
                # Process regular events
                if "agent" in event:
                    print("\n--- Agent Event ---")
                    pred = event["agent"].get("prediction")
                    if pred and hasattr(pred, 'action'):
                        action = pred.action
                        action_input = pred.args
                        print(f"Action: {action}")
                        print(f"Action Input: {action_input}")
                        display.clear_output(wait=True)
                        steps.append(f"{len(steps) + 1}. {action}: {action_input}")
                        print("\n".join(steps))
                        
                        if event["agent"].get("img"):
                            display.display(display.Image(base64.b64decode(event["agent"]["img"])))
                            
                        if action == "ANSWER":
                            print(f"\nFinal answer: {action_input[0]}")
                            final_answer = action_input[0]
                            break
            
            except asyncio.TimeoutError:
                # Check if we're at human_interaction node
                snapshot = graph.get_state(config)
                
                if snapshot and hasattr(snapshot, "tasks"):
                    current_nodes = [task.name for task in snapshot.tasks]
                    
                    # If we're at the human interaction node
                    if HUMAN_INTERACTION in current_nodes:
                        print("\n===== BOUNDING BOX REVIEW =====")
                        
                        # Display image if available
                        if snapshot.values.get("img"):
                            print("Current webpage screenshot:")
                            display.display(display.Image(base64.b64decode(snapshot.values["img"])))
                        
                        # Format and display bounding boxes nicely
                        bboxes = snapshot.values.get("bboxes", [])
                        if bboxes:
                            print(f"\nFound {len(bboxes)} elements on page:")
                            for i, bbox in enumerate(bboxes):
                                print(f"\n[{i}] {bbox.type}: {bbox.text}")
                                print(f"    Position: x={bbox.x:.2f}, y={bbox.y:.2f}")
                                if bbox.id:
                                    print(f"    ID: {bbox.id}")
                                if bbox.ariaLabel:
                                    print(f"    Aria Label: {bbox.ariaLabel}")
                                print(f"    Description: {bbox.description}")
                        else:
                            print("No interactive elements detected on this page.")
                        
                        # Get user confirmation - simple yes/no
                        user_input = input("\nDo you want to proceed? (yes/no): ")
                        
                        if user_input.lower() in ("yes", "y"):
                            # Continue execution without modifying state
                            graph.update_state(config, snapshot.values, as_node=HUMAN_INTERACTION)
                        else:
                            print("Operation cancelled by user.")
                            break
            
            except StopAsyncIteration:
                # End of stream
                break

        print("Agent completed successfully.")
    finally:
        # Close the browser
        await browser.close()
        await playwright.stop()

    return final_answer

instructions = """ 
1. When pop box with  (<a/>): "informasjonskapsler" pops up. Use scroll to make it visible and click on "godta alle"
2. If you see (<a/>): "Godta alle" click on it to accept cookies.
3. Go to finn.no
3. In finn.no find the Search and search for 'BMW iX xDrive40 2022'.
4. Click on the car.
5. Find the car's specifications.
6. Give me a summary of the car's specifications and features.
"""


async def main():
    res = await test_agent(
        query=instructions,
    )
    print(f"Result: {res}")
    return res

# Run the async main function
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
