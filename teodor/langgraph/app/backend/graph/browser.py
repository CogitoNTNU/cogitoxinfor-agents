"""
Browser interaction functions for the web agent.
"""
import os
from playwright.async_api import async_playwright

async def initialize_browser(start_url="https://www.google.com", user_data_dir=None, headless=False):
    """
    Initialize a browser session and return the page and context.
    
    Args:
        start_url: URL to navigate to after initialization
        user_data_dir: Directory for user data persistence
        headless: Whether to run in headless mode
        
    Returns:
        Tuple of (playwright, context, page)
    """
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
        
        return playwright, context, page
    except Exception as e:
        await playwright.stop()
        raise RuntimeError(f"Failed to initialize browser: {str(e)}") from e


async def close_browser(playwright, context):
    """
    Close the browser and clean up resources.
    """
    if context:
        await context.close()
    if playwright:
        await playwright.stop()