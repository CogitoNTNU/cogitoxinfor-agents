"""
Browser interaction functions for the web agent.
"""
import os
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional, Tuple

# Global singleton to store browser instance between graph executions
_browser_instance: Dict[str, Any] = {
    "playwright": None,
    "context": None,
    "page": None,
    "is_active": False
}

async def initialize_browser(start_url="https://www.google.com", user_data_dir=None, 
                            headless=False, reuse_session=True):
    """
    Initialize a browser session and return the page and context.
    
    Args:
        start_url: URL to navigate to after initialization
        user_data_dir: Directory for user data persistence
        headless: Whether to run in headless mode
        reuse_session: Whether to reuse an existing session if available
        
    Returns:
        Tuple of (playwright, context, page)
    """
    global _browser_instance
    
    # Check if we have an active browser session and should reuse it
    if reuse_session and _browser_instance["is_active"]:
        print("Reusing existing browser session")
        return (_browser_instance["playwright"], 
                _browser_instance["context"], 
                _browser_instance["page"])
    
    # Otherwise create a new session
    if user_data_dir is None:
        user_data_dir = os.path.join(os.path.expanduser("~"), "playwright_user_data")
        os.makedirs(user_data_dir, exist_ok=True)
        
    # Start Playwright
    playwright = await async_playwright().start()
    try:
        # Create a persistent context
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
        )

        # Get the default page
        page = context.pages[0]
        
        # Navigate to the start URL
        if start_url:
            await page.goto(start_url)
            
        # Store the browser instance
        _browser_instance["playwright"] = playwright
        _browser_instance["context"] = context
        _browser_instance["page"] = page
        _browser_instance["is_active"] = True
        
        return playwright, context, page
    except Exception as e:
        await playwright.stop()
        raise RuntimeError(f"Failed to initialize browser: {str(e)}") from e


async def close_browser(force=False):
    """
    Close the browser and clean up resources.
    
    Args:
        force: If True, always close the browser; if False, keep it running
              for future graph executions
    """
    global _browser_instance
    
    if force:
        if _browser_instance["context"]:
            await _browser_instance["context"].close()
        if _browser_instance["playwright"]:
            await _browser_instance["playwright"].stop()
        
        # Reset the browser instance
        _browser_instance = {
            "playwright": None,
            "context": None,
            "page": None,
            "is_active": False
        }
        print("Browser session closed")
    else:
        print("Browser session kept alive for future interactions")


async def get_current_browser_session() -> Optional[Tuple]:
    """
    Get the current browser session if active.
    
    Returns:
        Tuple of (playwright, context, page) if active, None otherwise
    """
    if _browser_instance["is_active"]:
        return (_browser_instance["playwright"], 
                _browser_instance["context"], 
                _browser_instance["page"])
    return None


def is_browser_active() -> bool:
    """
    Check if the browser is active.
    
    Returns:
        True if active, False otherwise
    """
    return _browser_instance["is_active"]