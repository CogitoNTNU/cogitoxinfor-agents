import asyncio
import platform
from typing import Dict, Literal

#Tools
# Constants for action types
from models import (
    AgentState,
    Observation,
    CLICK,
    TYPE,
    SCROLL,
    WAIT,
    GOBACK,
    GOOGLE,
    APPROVE,
)

# Helper function to create structured observations from tool execution
def create_observation(action: str, status: str, details: str) -> str:
    """
    Creates a structured observation object.
    
    Args:
        action: The action performed (e.g., "click", "type")
        status: Status indicator ("success", "warning", "error")
        details: Detailed information about the action
    
    Returns:
        Formatted observation string
    """
    return Observation(step=0, action=action, status=status, details=details).format()

async def click(state: AgentState, name: str = CLICK):
    """
    Simulates a mouse click on a bounding box identified by its label.
    """
    try:
        page = state.page
        click_args = state.prediction.args
        print("Click args: ", click_args)
        
        # Validate arguments
        if click_args is None or len(click_args) != 1:
            # Create a structured observation
            obs = create_observation(
                name, 
                "error",
                f"Invalid arguments: expected 1 argument (box ID), got {click_args}"
            )
            state.observation = obs
            return state
            
        bbox_id = int(click_args[0])
        print("Bbox ID clicked: ", bbox_id)
        
        # Find target element
        try:
            bbox = state.bboxes[bbox_id]
            print("Bbox: ", bbox)
            state.ids.append(bbox_id)
        except IndexError:
            obs = create_observation(
                name,
                "error",
                f"No bounding box found with ID {bbox_id}"
            )
            state.observation = obs
            return state
            
        # Perform action
        x, y = bbox.x, bbox.y
        await page.mouse.click(x, y)
        
        # Create success observation with element details
        element_type = bbox.type
        element_text = bbox.text[:30] + "..." if len(bbox.text) > 30 else bbox.text
        obs = create_observation(
            name,
            "success",
            f"Element {bbox_id} ({element_type}: '{element_text}')"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            name,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in click: {e}")
        
    return state


async def scroll(state: AgentState, name: str = SCROLL):
    """
    Simulates scrolling within the webpage or a specific element.
    """
    try:
        page = state.page
        scroll_args = state.prediction.args
        
        # Validate arguments
        if scroll_args is None or len(scroll_args) != 2:
            obs = create_observation(
                name, 
                "error",
                f"Invalid arguments: expected 2 arguments (target, direction), got {scroll_args}"
            )
            state.observation = obs
            return state
            
        target, direction = scroll_args

        # Handle window scrolling
        if target.upper() == "WINDOW":
            scroll_amount = 500
            scroll_direction = -scroll_amount if direction.lower() == "up" else scroll_amount
            await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
            
            obs = create_observation(
                name,
                "success",
                f"Window scrolled {direction.lower()}"
            )
        else:
            # Handle element scrolling
            scroll_amount = 200
            try:
                target_id = int(target)
                bbox = state.bboxes[target_id]
                x, y = bbox.x, bbox.y
                await page.mouse.move(x, y)
                scroll_direction = -scroll_amount if direction.lower() == "up" else scroll_amount
                await page.mouse.wheel(0, scroll_direction)
                
                obs = create_observation(
                    name,
                    "success",
                    f"Element {target_id} ({bbox.type}) scrolled {direction.lower()}"
                )
            except (ValueError, IndexError):
                obs = create_observation(
                    name,
                    "error",
                    f"Invalid target: {target} is not 'WINDOW' or a valid box ID"
                )
                state.observation = obs
                return state
        
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            name,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in scroll: {e}")
        
    return state


async def type_text(state: AgentState, name: str = TYPE):
    """
    Simulates typing text into an input field identified by a bounding box label.
    """
    try:
        page = state.page
        type_args = state.prediction.args
        
        # Validate arguments
        if type_args is None or len(type_args) != 2:
            obs = create_observation(
                name, 
                "error",
                f"Invalid arguments: expected 2 arguments (box ID, text), got {type_args}"
            )
            state.observation = obs
            return state
            
        bbox_id = int(type_args[0])
        text_content = type_args[1]
        
        # Find target element
        try:
            bbox = state.bboxes[bbox_id]
        except IndexError:
            obs = create_observation(
                name,
                "error",
                f"No bounding box found with ID {bbox_id}"
            )
            state.observation = obs
            return state
            
        # Perform action
        x, y = bbox.x, bbox.y
        await page.mouse.click(x, y)
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await page.keyboard.press("Backspace")
        await page.keyboard.type(text_content)
        await page.keyboard.press("Enter")
        
        # Create success observation
        safe_text = text_content[:15] + "..." if len(text_content) > 15 else text_content
        obs = create_observation(
            name,
            "success",
            f"Text '{safe_text}' in element {bbox_id} ({bbox.type})"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            name,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in type_text: {e}")
        
    return state


async def wait(state: AgentState, name: str = WAIT):
    """
    Simulates a wait action for a fixed duration.
    """
    try:
        sleep_time = 5
        await asyncio.sleep(sleep_time)
        
        # Create structured observation
        obs = create_observation(
            name,
            "success",
            f"Waited for {sleep_time} seconds"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            name,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in wait: {e}")
        
    return state


async def go_back(state: AgentState, name: str = GOBACK):
    """
    Simulates navigating back to the previous page in the browser.
    """
    try:
        page = state.page
        await page.go_back()
        current_url = page.url
        
        obs = create_observation(
            GOBACK,
            "success",
            f"Navigated back to {current_url}"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            GOBACK,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in go_back: {e}")
        
    return state


async def to_google(state: AgentState, name: str = GOOGLE):
    """
    Simulates navigating to the Google homepage.
    """
    try:
        page = state.page
        await page.goto("https://www.google.com/")
        
        obs = create_observation(
            GOOGLE,
            "success",
            "Navigated to Google homepage"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            GOOGLE,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in to_google: {e}")
        
    return state


async def approve_info_box(state: AgentState, name: str = APPROVE):
    """
    Simulates clicking the 'Approve' button in a Google information box.
    """
    try:
        page = state.page
        approve_args = state.prediction.args
        
        # Validate arguments
        if approve_args is None or len(approve_args) != 1:
            obs = create_observation(
                APPROVE, 
                "error",
                f"Invalid arguments: expected 1 argument (box ID), got {approve_args}"
            )
            state.observation = obs
            return state
            
        bbox_id = int(approve_args[0])
        
        # Find target element
        try:
            bbox = state.bboxes[bbox_id]
            print("Bbox: ", bbox)
        except IndexError:
            obs = create_observation(
                APPROVE,
                "error",
                f"No bounding box found with ID {bbox_id}"
            )
            state.observation = obs
            return state
            
        # Perform action
        x, y = bbox.x, bbox.y
        await page.mouse.click(x, y)
        
        # Create success observation
        element_type = bbox.type
        element_text = bbox.text[:30] + "..." if len(bbox.text) > 30 else bbox.text
        obs = create_observation(
            APPROVE,
            "success",
            f"Approved element {bbox_id} ({element_type}: '{element_text}')"
        )
        state.observation = obs
        
    except Exception as e:
        obs = create_observation(
            APPROVE,
            "error",
            f"Exception: {str(e)}"
        )
        state.observation = obs
        print(f"Error in approve_info_box: {e}")
        
    return state

def execute_action(state: AgentState) -> AgentState:
    """Execute the predicted action with error handling and repetition detection"""
    action = state.prediction.action
    args = state.prediction.args
    
    # Check for repeated failures
    repeated_failures = state.check_repeated_failure(action, args)
    if repeated_failures:
        repeated_count = len(repeated_failures)
        warning_msg = f"WARNING: This exact action has failed {repeated_count} times before. Consider an alternative approach."
        state.add_observation("repeat_warning", "warning", warning_msg)
    
    try:
        # Execute the action...
        result = "Success result"
        state.add_observation(action, "success", result)
    except Exception as e:
        error_msg = str(e)
        state.add_observation(action, "error", error_msg)
    
    return state
