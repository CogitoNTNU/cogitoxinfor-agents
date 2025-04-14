"""
Web interaction tools for the agent.
"""
import asyncio
import platform
import functools
from typing import Callable, List, Dict, Any, Optional, Tuple, Union

from .models import AgentState, BBox

# Constants
CLICK = "CLICK"
TYPE = "TYPE"
SCROLL = "SCROLL"
WAIT = "WAIT"
GOBACK = "GOBACK"
GOOGLE = "GOOGLE"
ANSWER = "ANSWER"
RETRY = "RETRY"
NAVIGATE = "NAVIGATE"

# Debug flag to enable detailed logging
DEBUG = True

# =============================================================================
# Utility Functions
# =============================================================================

def validate_args(state: AgentState, name: str, expected: int, args: List) -> bool:
    """Validate argument count for a tool"""
    if args is None or len(args) != expected:
        state.add_observation(
            name, 
            "error",
            f"Invalid arguments: expected {expected} argument(s), got {args}"
        )
        return False
    return True

def get_bbox(state: AgentState, name: str, bbox_id: int) -> Optional[Any]:
    """Get bounding box by ID with error handling"""
    try:
        bbox = state.bboxes[bbox_id]
        return bbox
    except IndexError:
        state.add_observation(
            name,
            "error",
            f"No bounding box found with ID {bbox_id}"
        )
        return None

async def handle_navigation(state: AgentState, page, action_func, success_message, name: str):
    """Handle possible navigation after an action with proper bounding box cleanup"""
    navigation_detected = False
    
    try:
        # Create a context manager for navigation events with a timeout
        async with page.expect_navigation(timeout=5000) as navigation_info:
            # Execute the provided action
            await action_func()
            # Wait for navigation to complete if it happens
            await navigation_info.value
            navigation_detected = True
    except Exception:
        # No navigation occurred or timeout reached
        pass
        
    # Process the result based on whether navigation happened
    if navigation_detected:
        # Clear bounding boxes when navigation happens
        if DEBUG: print(f"🚀 Navigation detected - clearing bounding boxes")
        state.bboxes = []
        state.add_observation(name, "success", f"{success_message} and navigated to new page")
    else:
        # No navigation occurred
        state.add_observation(name, "success", success_message)
        
    # Give the page a moment to stabilize
    await asyncio.sleep(1)

# =============================================================================
# Enhanced Web Tool Decorator
# =============================================================================

def web_tool(func):
    """Decorator for web tools to handle common error patterns and observation recording"""
    @functools.wraps(func)
    async def wrapper(state: AgentState, config, name: str = None):
        tool_name = name if name else func.__name__.upper()
        try:
            # Execute the tool function - this should modify state in-place
            await func(state, config, tool_name)
            # Return the observation string, not the state object
            return state.observation
        except Exception as e:
            # Handle general exceptions
            state.add_observation(tool_name, "error", f"Exception: {str(e)}")
            print(f"Error in {func.__name__}: {e}")
            # Return the error observation as a string
            return state.observation
    return wrapper

# =============================================================================
# Navigation Tools
# =============================================================================

@web_tool
async def navigate_to(state: AgentState, config, name: str = "NAVIGATE"):
    """Directly navigates to a specified URL."""
    page = config["configurable"].get("page")
    nav_args = state.prediction.args
    
    if not validate_args(state, name, 1, nav_args):
        return
        
    url = nav_args[0]
    
    # Add https:// if not present
    if not url.startswith("http"):
        url = f"https://{url}"
    
    # Clear existing bounding boxes BEFORE navigation
    if DEBUG: print(f"🧹 Clearing bounding boxes before navigation to {url}")
    state.bboxes = []
    
    try:
        # Navigate to the URL
        await page.goto(url, wait_until="domcontentloaded", timeout=10000)
        
        # Wait for the page to be fully loaded
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            print(f"Network idle wait failed but continuing: {str(e)}")
        
        # Allow time for page to fully render
        await asyncio.sleep(2)
        
        state.add_observation(name, "success", f"Successfully navigated to {url}")
    except Exception as e:
        state.add_observation(name, "error", f"Navigation failed: {str(e)}")

@web_tool
async def go_back(state: AgentState, config, name: str = GOBACK):
    """Simulates navigating back to the previous page in the browser."""
    page = config["configurable"].get("page")
    
    # Clear existing bounding boxes BEFORE navigation
    if DEBUG: print(f"🧹 Clearing bounding boxes before going back")
    state.bboxes = []
    
    await page.go_back()
    current_url = page.url
    
    state.add_observation(name, "success", f"Navigated back to {current_url}")

@web_tool
async def to_google(state: AgentState, config, name: str = GOOGLE):
    """Simulates navigating to the Google homepage."""
    page = config["configurable"].get("page")
    
    # Clear existing bounding boxes BEFORE navigation
    if DEBUG: print(f"🧹 Clearing bounding boxes before going to Google")
    state.bboxes = []
    
    await page.goto("https://www.google.com/")
    
    state.add_observation(name, "success", "Navigated to Google homepage")

# =============================================================================
# Interaction Tools
# =============================================================================

@web_tool
async def click(state: AgentState, config, name: str = CLICK):
    """Simulates a mouse click on a bounding box identified by its label."""
    page = config["configurable"].get("page")
    click_args = state.prediction.args
    
    if not validate_args(state, name, 1, click_args):
        return
        
    bbox_id = int(click_args[0])
    bbox = get_bbox(state, name, bbox_id)
    if bbox is None:
        return
    
    element_text = bbox.text[:30] + "..." if len(bbox.text) > 30 else bbox.text
    success_message = f"Clicked element {bbox_id} ({bbox.type}: '{element_text}')"
    
    # Define the click action as a callable
    click_action = lambda: page.mouse.click(bbox.x, bbox.y)
    
    # Handle the click with navigation detection
    await handle_navigation(state, page, click_action, success_message, name)

@web_tool
async def type_text(state: AgentState, config, name: str = TYPE):
    """Simulates typing text into an input field identified by a bounding box label."""
    page = config["configurable"].get("page")
    type_args = state.prediction.args
    
    if not validate_args(state, name, 2, type_args):
        return
        
    bbox_id = int(type_args[0])
    text_content = type_args[1]
    
    bbox = get_bbox(state, name, bbox_id)
    if bbox is None:
        return
    
    async def type_action():
        x, y = bbox.x, bbox.y
        await page.mouse.click(x, y)
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await page.keyboard.press("Backspace")
        await page.keyboard.type(text_content)
        
        # Only press Enter if the text ends with newline
        if "\n" in text_content:
            await page.keyboard.press("Enter")
    
    safe_text = text_content[:15] + "..." if len(text_content) > 15 else text_content
    success_message = f"Text '{safe_text}' entered in element {bbox_id} ({bbox.type})"
    
    # Handle typing with navigation detection
    await handle_navigation(state, page, type_action, success_message, name)

@web_tool
async def scroll(state: AgentState, config, name: str = SCROLL):
    """Simulates scrolling within the webpage or a specific element."""
    page = config["configurable"].get("page")
    scroll_args = state.prediction.args
    
    if not validate_args(state, name, 2, scroll_args):
        return
        
    target, direction = scroll_args
    scroll_amount = 500 if target.upper() == "WINDOW" else 200
    scroll_direction = -scroll_amount if direction.lower() == "up" else scroll_amount

    # Handle window scrolling
    if target.upper() == "WINDOW":
        await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
        state.add_observation(name, "success", f"Window scrolled {direction.lower()}")
    else:
        # Handle element scrolling
        try:
            target_id = int(target)
            bbox = get_bbox(state, name, target_id)
            if bbox is None:
                return
                
            x, y = bbox.x, bbox.y
            await page.mouse.move(x, y)
            await page.mouse.wheel(0, scroll_direction)
            
            state.add_observation(
                name,
                "success",
                f"Element {target_id} ({bbox.type}) scrolled {direction.lower()}"
            )
        except ValueError:
            state.add_observation(
                name,
                "error",
                f"Invalid target: {target} is not 'WINDOW' or a valid box ID"
            )

# =============================================================================
# Utility Tools
# =============================================================================

@web_tool
async def wait(state: AgentState, config, name: str = WAIT):
    """Simulates a wait action for a fixed duration."""
    sleep_time = 2  # Reduced wait time for better responsiveness
    await asyncio.sleep(sleep_time)
    state.add_observation(name, "success", f"Waited for {sleep_time} seconds")
