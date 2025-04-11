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

# Update BROWSER_TYPES with persistent config
BROWSER_TYPES = {
    "chrome": {
        "executable_path": "/usr/bin/google-chrome",
        "default_port": 9223,
        "launch_args": ['--no-sandbox', '--disable-blink-features=AutomationControlled']
    },
    "personal_chrome": {
        "executable_path": None,  # Will use system default
        "default_port": 9223,
        "launch_args": ['--no-sandbox', '--disable-blink-features=AutomationControlled'],
        "persistent": True  # Add persistent flag
    }
}

class BrowserConfig:
    def __init__(
        self,
        browser_type: str = "personal_chrome",
        host: str = "localhost",
        port: Optional[int] = None,
        user_data_dir: Optional[str] = None,
        headless: bool = False,
        use_cdp: bool = False,
        custom_args: Optional[list] = None,
        persistent: bool = True
    ):
        self.browser_type = browser_type.lower()
        self.host = host
        self.browser_config = BROWSER_TYPES.get(self.browser_type, BROWSER_TYPES["chrome"])
        self.port = port or self.browser_config["default_port"]
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.use_cdp = use_cdp
        self.custom_args = custom_args or []
        self.persistent = persistent
        
    @property
    def launch_args(self) -> list:
        """Get the combined launch arguments for the browser."""
        args = self.browser_config["launch_args"].copy()
        if self.port:
            args.append(f'--remote-debugging-port={self.port}')
        args.extend(self.custom_args)
        return args


async def initialize_browser(
    start_url: Optional[str] = None,
    reuse_session: bool = True,
    config: Optional[BrowserConfig] = None
) -> Tuple[Any, Any, Any]:
    global _browser_instance
    
    if config is None:
        config = BrowserConfig()
    
    if reuse_session and _browser_instance["is_active"]:
        if all(_browser_instance.values()):
            return (_browser_instance["playwright"],
                    _browser_instance["context"],
                    _browser_instance["page"])
    
    playwright = await async_playwright().start()
    try:
        if config.persistent:
            # Launch persistent context
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=config.user_data_dir,
                headless=config.headless,
                args=config.launch_args
            )
            # Get first page or create new one
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
        else:
            # Regular browser launch
            browser = await playwright.chromium.launch(
                headless=config.headless,
                args=config.launch_args
            )
            context = await browser.new_context(
                user_data_dir=config.user_data_dir
            )
            page = await context.new_page()
        
        if start_url:
            await page.goto(start_url)
            
        _browser_instance.update({
            "playwright": playwright,
            "browser": None if config.persistent else browser,
            "context": context,
            "page": page,
            "is_active": True
        })
        
        return playwright, context, page
        
    except Exception as e:
        await playwright.stop()
        raise RuntimeError(f"Failed to initialize browser: {str(e)}") from e


async def close_browser(force: bool = False):
    """
    Close the browser and clean up resources.
    
    Args:
        force: If True, clean up all resources. If False, only clean up non-persistent sessions.
    """
    global _browser_instance

    try:
        if not _browser_instance["is_active"]:
            print("No active browser session to close.")
            return

        # Get the current context and playwright instance
        context = _browser_instance["context"]
        playwright = _browser_instance["playwright"]
        browser = _browser_instance["browser"]

        if force:
            # Close everything regardless of persistence
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
                
            _browser_instance.update({
                "playwright": None,
                "browser": None,
                "context": None,
                "page": None,
                "is_active": False
            })
            print("Browser session forcefully closed and all resources cleaned up.")
        else:
            # Only close non-persistent sessions
            if browser:  # Non-persistent session
                await context.close()
                await browser.close()
                await playwright.stop()
                
                _browser_instance.update({
                    "playwright": None,
                    "browser": None,
                    "context": None,
                    "page": None,
                    "is_active": False
                })
                print("Non-persistent browser session closed.")
            else:  # Persistent session
                # Just mark as inactive but keep the session
                _browser_instance.update({
                    "playwright": playwright,
                    "browser": None,
                    "context": context,
                    "page": None,
                    "is_active": False
                })
                print("Persistent browser session marked as inactive. Browser remains open.")

    except Exception as e:
        print(f"Error while closing browser: {str(e)}")
        # Ensure we reset the state even if there's an error
        _browser_instance.update({
            "playwright": None,
            "browser": None,
            "context": None,
            "page": None,
            "is_active": False
        })
        raise