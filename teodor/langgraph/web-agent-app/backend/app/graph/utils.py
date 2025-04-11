"""
Utility functions for the web agent.
"""
import os
import base64
import asyncio
import shutil
from playwright.async_api import Page
from langchain_core.runnables import chain as chain_decorator
from .models import AgentState, BBox
from langchain_core.messages import SystemMessage

current_dir = os.path.dirname(os.path.abspath(__file__))
file = os.path.join(current_dir, "mark_page.js")

# Load the JavaScript code for annotating the page
with open(file) as f:
    # Some JavaScript we will run on each step
    # to take a screenshot of the page, select the
    # elements to annotate, and add bounding boxes
    mark_page_script = f.read()


@chain_decorator
async def mark_page(page):
    """
    Annotates the current browser page with bounding boxes for interactive elements,
    including elements inside iframes.
    """
    try:
        # DOM should definitely be loaded
        await page.wait_for_load_state("domcontentloaded")
        
        # Add a small delay to ensure JS has initialized
        await asyncio.sleep(1)
        
        # Now try to execute the JavaScript
        try:
            # Execute the JavaScript code to annotate the page
            await page.evaluate(mark_page_script)
        except Exception as e:
            print(f"Failed to evaluate mark_page_script: {e}")
            # Wait a bit and try again once
            await asyncio.sleep(2)
            await page.evaluate(mark_page_script)
            
        # Get the bounding boxes with retries
        bboxes = None
        for attempt in range(3):  # Reduced retry count but with better handling
            try:
                bboxes = await page.evaluate("markPage()")
                if bboxes:  # If we got valid data, break
                    break
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Attempt {attempt+1}: Error getting bounding boxes: {e}")
                await asyncio.sleep(2)  # Wait longer between retries
    
        # Take a screenshot of the page
        screenshot = await page.screenshot()
        
        return {
            "img": base64.b64encode(screenshot).decode(),
            "bboxes": bboxes,
        }
    except Exception as e:
        print(f"Critical error in mark_page: {e}")
        # Return minimal valid data instead of raising
        return {
            "img": "",
            "bboxes": []
        }

async def annotate(state: AgentState, config):
    """
    Annotates the current page and processes bounding boxes for both the main page and iframes.
    """
    try:
        page = config["configurable"].get("page")
        
        # Debug the URL we're annotating
        if state.DEBUG: print(f"📝 Annotating page: {page.url}")
        
        # Annotate the page and get bounding boxes
        marked_page = await mark_page.with_retry().ainvoke(page)
        if state.DEBUG: print(f"✅ Found {len(marked_page['bboxes'])} bounding boxes")

        # Set the annotated image and bounding boxes in the state
        state.img = marked_page["img"]
        state.bboxes = [
            BBox(**bbox) for bbox in marked_page["bboxes"]
        ]  # Convert bounding boxes to BBox objects

        # Check if any bounding box is of type 'iframe'
        iframe_bboxes = [bbox for bbox in marked_page["bboxes"] if bbox["type"] == "iframe"]
        for iframe_bbox in iframe_bboxes:
            src = iframe_bbox.get("src")
            if not src:
                print(f"Skipping iframe with no src: {iframe_bbox}")
                continue

            print(f"Iframe detected with src: {src}. Processing iframe...")
            try:
                # Use 'page' from config, not state.page
                iframe = await page.frame_locator(f"iframe[src='{src}']").frame()
                iframe_marked_page = await mark_page.with_retry().ainvoke(iframe)
                print(f"Found {len(iframe_marked_page['bboxes'])} iframe bounding boxes")

                # Combine iframe bounding boxes with the main page bounding boxes
                state.bboxes.extend([
                    BBox(**bbox) for bbox in iframe_marked_page["bboxes"]
                ])
            except Exception as iframe_error:
                print(f"Error processing iframe with src {src}: {iframe_error}")

    except Exception as e:
        print(f"Error in annotate: {e}")
        raise

    return state

def format_elements(state: AgentState) -> AgentState:
    """
    Formats the bounding box descriptions for the agent's prompt and updates the scratchpad.
    """
    from langchain_core.messages import SystemMessage
    
    # Create descriptions of available elements
    if state.bboxes:
        descriptions = [f"{i}: {bbox.description}" for i, bbox in enumerate(state.bboxes)]
        details = "\n".join(descriptions)
        message_content = f"Available elements on page:\n{details}"
    else:
        message_content = "No elements detected on page"
    
    # Create a standard SystemMessage that the LLM can understand
    bbox_message = SystemMessage(content=message_content)
    state.scratchpad.append(bbox_message)
    
    return state

async def update_scratchpad(state: AgentState, config) -> AgentState:
    """
    Updates scratchpad with:
    1. Current observation at the top
    2. Any warnings immediately after
    3. Previous observations in reverse chronological order
    """    
    try:
        page = config["configurable"].get("page")
        # Fix: Pass the entire JavaScript function definition instead of just the function name
        try:
            await page.evaluate("typeof unmarkPage === 'function' ? unmarkPage() : console.log('unmarkPage not defined')")
        except Exception as e:
            print(f"Warning: Failed to unmark page: {e}")
    except Exception as e:
        print(f"Warning: Failed to unmark page setup: {e}")

    # Start with an empty scratchpad
    state.scratchpad = []
    
    # 1. First add current observation
    current_observation = state.observation
    current_msg = SystemMessage(content=f"CURRENT OBSERVATION:\n{current_observation}")
    state.scratchpad.append(current_msg)
    
    # 2. Add warning for repeated failures if needed (right after current observation)
    if state.prediction:
        repeated_failures = state.check_repeated_failure(
            state.prediction.action, 
            state.prediction.args
        )
        if repeated_failures:
            repeated_count = len(repeated_failures)
            state.repeated_failures = repeated_count
            warning_msg = (
                f"⚠️ WARNING: This exact action has failed {repeated_count} "
                f"times before. Consider an alternative approach."
            )
            state.scratchpad.append(SystemMessage(content=warning_msg))
        # If we are in testing mode, remove the first test action
        if state.testing:
            state.test_actions.pop(0)
    # 3. Add history message if we have previous observations
    if state.observations and len(state.observations) > 1:
        # Get all previous observations (excluding the current one)
        previous_observations = state.observations[:-1]
        
        # Format in reverse chronological order (newest first)
        history_content = "PREVIOUS OBSERVATIONS (newest first):\n"
        for obs in reversed(previous_observations):
            history_content += obs.format() + "\n"
        
        history_msg = SystemMessage(content=history_content)
        state.scratchpad.append(history_msg)
    
    return state

import os
import base64
import uuid
from ..config import HISTORY_DIR

def get_history_dir(thread_id=None):
    """
    Get the history directory for a thread.
    
    Args:
        thread_id: Thread ID or None to use the default
        
    Returns:
        Path to the history directory
    """
    if thread_id is None:
        return HISTORY_DIR
        
    # Create thread-specific directory
    thread_dir = os.path.join(HISTORY_DIR, thread_id)
    os.makedirs(thread_dir, exist_ok=True)
    
    return thread_dir

def setup_history_folder(thread_id=None):
    """
    Setup the history folder for the current thread.
    
    Args:
        thread_id: Thread ID or None to use the default
        
    Returns:
        Path to the history directory
    """
    return get_history_dir(thread_id)

def save_image_to_history(image_base64, step_number=None, thread_id=None):
    """
    Save a base64 encoded image to the history folder with an auto-generated filename.
    Ensures immediate disk writing.
    
    Args:
        image_base64: Base64 encoded image
        step_number: Step number or identifier to use in filename (optional)
        thread_id: Thread ID to determine which folder to save in
        
    Returns:
        Path to the saved image and filename
    """
    try:
        # Handle None thread_id
        if thread_id is None:
            print("No thread_id provided, using default")
            return None
        
        # Generate filename
        if step_number is None:
            print("No step_number provided, using default")
            return None
        
        filename = f"{step_number}.png"
    
        # Get history directory
        history_dir = get_history_dir(thread_id)
        
        # Save the image with the generated filename
        image_path = os.path.join(history_dir, filename)

        # Use sync file operations with immediate flush to disk
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_base64))
            f.flush()
            os.fsync(f.fileno())  # Force write to physical storage
        
        # Verify file exists
        if os.path.exists(image_path):
            print(f"✅ Image saved successfully: {image_path}")
        else:
            print(f"⚠️ Image file not found after save attempt: {image_path}")
            
        return image_path, filename
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        # Return a default value rather than None
        return None, f"error_{thread_id}_{step_number}.png"