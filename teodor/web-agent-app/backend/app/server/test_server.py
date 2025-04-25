import asyncio
import sys
import os


from ..mcp_agent import MCPAgent

async def test_bridge():
    print("Creating MCPAgent...")
    agent = MCPAgent()
    
    try:
        # Initialize the agent (this will start the bridge server if needed)
        print("Initializing agent...")
        await agent.initialize()
        
        # Start the interactive loop
        print("\n=== Browser Interactive Mode ===")
        print("Available commands:")
        print("- 'navigate URL' - Navigate to a specific URL")
        print("- 'screenshot' - Take a screenshot")
        print("- 'click SELECTOR' - Click on an element with the given selector")
        print("- 'type SELECTOR TEXT' - Type text into an element")
        print("- 'exit' - Exit the program")
        
        while True:
            command = input("\nEnter command: ")
            
            if command.lower() == "exit":
                print("Exiting...")
                break
                
            elif command.lower() == "screenshot":
                screenshot_tool = next((t for t in agent.tools if t.name == "browser_snapshot"), None)
                if screenshot_tool:
                    print("Taking screenshot...")
                    try:
                        # Use ainvoke for async operation
                        screenshot = await screenshot_tool.ainvoke({})
                        
                        # Process and save screenshot
                        if screenshot and "data" in screenshot:
                            # Create screenshots directory if it doesn't exist
                            screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
                            os.makedirs(screenshots_dir, exist_ok=True)
                            
                            # Generate filename with timestamp
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
                            
                            # Save the screenshot
                            import base64
                            with open(filename, "wb") as f:
                                # The data is usually base64 encoded
                                image_data = base64.b64decode(screenshot["data"].split(",")[1] 
                                                            if "," in screenshot["data"] 
                                                            else screenshot["data"])
                                f.write(image_data)
                                
                            print(f"Screenshot saved to: {filename}")
                        else:
                            print(f"Screenshot data missing or invalid: {screenshot}")
                    except Exception as e:
                        print(f"Error taking screenshot: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("Screenshot tool not found!")
            
            elif command.lower().startswith("navigate "):
                url = command[9:].strip()
                navigate_tool = next((t for t in agent.tools if t.name == "browser_navigate"), None)
                if navigate_tool:
                    print(f"Navigating to {url}...")
                    try:
                        result = await navigate_tool.ainvoke({"url": url})
                        print(f"Navigation successful: {result}")
                    except Exception as e:
                        print(f"Navigation error: {e}")
                else:
                    print("Navigation tool not found!")
            
            elif command.lower().startswith("click "):
                selector = command[6:].strip()
                click_tool = next((t for t in agent.tools if t.name == "browser_click"), None)
                if click_tool:
                    print(f"Clicking on {selector}...")
                    try:
                        result = await click_tool.ainvoke({"selector": selector})
                        print(f"Click successful: {result}")
                    except Exception as e:
                        print(f"Click error: {e}")
                else:
                    print("Click tool not found!")
            
            elif command.lower().startswith("type "):
                parts = command[5:].strip().split(' ', 1)
                if len(parts) == 2:
                    selector, text = parts
                    type_tool = next((t for t in agent.tools if t.name == "browser_type"), None)
                    if type_tool:
                        print(f"Typing '{text}' into {selector}...")
                        try:
                            result = await type_tool.ainvoke({
                                "selector": selector,
                                "text": text
                            })
                            print(f"Type successful: {result}")
                        except Exception as e:
                            print(f"Type error: {e}")
                    else:
                        print("Type tool not found!")
                else:
                    print("Invalid format. Use: type SELECTOR TEXT")
            
            else:
                print("Unknown command. Try 'navigate', 'screenshot', 'click', 'type', or 'exit'")
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up resources
        print("\nCleaning up resources...")
        await agent.cleanup()
        print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_bridge())