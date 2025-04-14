"""
Browser interaction functions for the web agent, connecting to an existing browser instance.
"""
import os
# import platform # No longer needed
import asyncio # Added for sleep
from playwright.async_api import async_playwright, Error as PlaywrightError
from typing import Dict, Any, Optional, Tuple

# Global singleton to store browser instance between graph executions
_browser_instance: Dict[str, Any] = {
    "playwright": None,
    "browser": None, # Store browser object when connecting via CDP
    "context": None,
    "page": None,
    "is_active": False
}

# CDP connection endpoint
CDP_ENDPOINT = "http://localhost:9223" # Changed port to 9223

async def initialize_browser(start_url: Optional[str] = None, reuse_session: bool = True):
    """
    Connects to an existing browser instance via CDP and returns the page and context.
    Requires Chrome/Chromium to be launched with --remote-debugging-port=9222 (or the port specified in CDP_ENDPOINT).

    Args:
        start_url: URL to navigate to if a new page needs to be opened.
        reuse_session: Whether to reuse an existing connection if available.

    Returns:
        Tuple of (playwright, context, page)
    """
    global _browser_instance
    
    # Check if we have an active browser session and should reuse it
    if reuse_session and _browser_instance["is_active"]:
        print("Reusing existing browser session")
        # Ensure all components are valid before returning reuse
        if (_browser_instance["playwright"] and
            _browser_instance["context"] and
            _browser_instance["page"]):
             return (_browser_instance["playwright"],
                     _browser_instance["context"],
                     _browser_instance["page"])
        else:
             # If components are missing, mark as inactive and proceed to connect
             _browser_instance["is_active"] = False
             print("Warning: Reused session components missing, establishing new connection.")


    # Otherwise, establish a new connection
    playwright = await async_playwright().start()
    try:
        print("Waiting 2 seconds before attempting connection...")
        await asyncio.sleep(2) # Added delay
        print(f"Attempting to connect to browser at {CDP_ENDPOINT}...")
        browser = await playwright.chromium.connect_over_cdp(CDP_ENDPOINT)
        print("Successfully connected to browser.")

        # Assume the first context is the default one the user is interacting with
        if not browser.contexts:
             raise RuntimeError("No browser contexts found. Is the browser running with the correct profile?")
        context = browser.contexts[0]

        # Get the first available page (tab) or create a new one
        if context.pages:
            page = context.pages[0]
            print(f"Using existing page: {page.url}")
        else:
            print("No open pages found, creating a new one.")
            page = await context.new_page()
            if start_url:
                print(f"Navigating new page to: {start_url}")
                await page.goto(start_url)
            else:
                 # Maybe navigate to about:blank or a default page?
                 await page.goto("about:blank")


        # Store the connection details
        _browser_instance["playwright"] = playwright
        _browser_instance["browser"] = browser # Store browser
        _browser_instance["context"] = context
        _browser_instance["page"] = page
        _browser_instance["is_active"] = True

        # Handle disconnection
        browser.on("disconnected", lambda: handle_disconnect(playwright))

        return playwright, context, page

    except PlaywrightError as e:
        await playwright.stop()
        if "ECONNREFUSED" in str(e):
             # Updated error message to reflect the new default port
             raise RuntimeError(f"Connection refused at {CDP_ENDPOINT}. Is Chrome running with --remote-debugging-port=9223 (or the correct port)? Ensure ALL other Chrome instances are closed first.") from e
        raise RuntimeError(f"Failed to connect to browser via CDP: {str(e)}") from e
    except Exception as e:
        # Ensure playwright is stopped in case of other errors during setup
        if playwright and playwright.is_connected:
             await playwright.stop()
        raise RuntimeError(f"An unexpected error occurred during browser initialization: {str(e)}") from e

def handle_disconnect(playwright_instance):
    """Callback function for browser disconnection."""
    global _browser_instance
    print("Browser disconnected.")
    _browser_instance = {
        "playwright": None,
        "browser": None,
        "context": None,
        "page": None,
        "is_active": False
    }
    # We might not want to stop playwright here if other parts of the app use it
    # Consider if playwright.stop() is needed or if it should be handled elsewhere
    # asyncio.create_task(playwright_instance.stop()) # Example if stopping is desired


async def close_browser(force=False):
    """
    Close the browser and clean up resources.
    
    Args:
        force: If True, mark the session as inactive. If False, do nothing.
               Note: This function no longer actually closes the user's browser.
    """
    global _browser_instance

    if force:
        # We don't close the context or stop playwright when connected via CDP,
        # as that would affect the user's main browser instance.
        # We just mark our tracked session as inactive.
        if _browser_instance["is_active"]:
             _browser_instance["is_active"] = False
             # Optionally detach? browser.disconnect() - maybe too aggressive.
             # Resetting the state seems sufficient.
             _browser_instance = {
                 "playwright": _browser_instance["playwright"], # Keep playwright instance?
                 "browser": None,
                 "context": None,
                 "page": None,
                 "is_active": False
             }
             print("Browser session marked as inactive (CDP connection). Browser remains open.")
        else:
             print("No active browser session to mark as inactive.")

    else:
        # If not forcing, we definitely don't do anything.
        print("Browser session kept active (CDP connection).")


async def get_current_browser_session() -> Optional[Tuple]:
    """
    Get the current browser connection details if active.

    Returns:
        Tuple of (playwright, context, page) if active, None otherwise.
    """
    if _browser_instance["is_active"]:
        # Ensure all components are still valid before returning
        if (_browser_instance["playwright"] and
            _browser_instance["context"] and
            _browser_instance["page"]):
             # Check if page is still connected/valid? page.is_closed() might be useful
             # if not _browser_instance["page"].is_closed(): # Requires async check
             return (_browser_instance["playwright"],
                     _browser_instance["context"],
                     _browser_instance["page"])
        else:
             # If components are missing, mark as inactive
             _browser_instance["is_active"] = False
             print("Warning: Active session components missing, marking as inactive.")
             return None
    return None


def is_browser_active() -> bool:
    """
    Check if the browser is active.
    
    Returns:
        True if active, False otherwise
    """
    return _browser_instance["is_active"]
