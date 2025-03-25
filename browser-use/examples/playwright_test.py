from playwright.sync_api import sync_playwright
import os

def run(playwright):
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    # Point this to your real Chrome profile folder
    user_data_dir = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Default"
    )
    
    # Launch in non-headless mode (so you actually see the Chrome window)
    context = playwright.chromium.launch_persistent_context(
        channel="chrome",                 # Tells Playwright to use Chrome (not the bundled Chromium)
        executable_path=chrome_path,      # Path to your real Chrome
        user_data_dir=user_data_dir,      # Re-uses your existing Chrome profile data
        headless=False
    )
    page = context.new_page()
    page.goto("https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Customer%20Order.%20Open%26OIS100%20Customer%20Order.%20Open")
    input("Press Enter to close...")  # Let you see the page
    context.close()

with sync_playwright() as p:
    run(p)
