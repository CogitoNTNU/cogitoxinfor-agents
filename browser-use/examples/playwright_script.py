from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import os

# Path to your existing Chrome profile (the Default profile folder).
# NOTE: If you use "Profile 1" or another named profile, replace "Default" accordingly.
user_data_dir = "/Users/nybruker/Library/Application Support/Google/Chrome/Default"

# The URL you want to visit
target_url = (
    "https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/"
    "aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?"
    "OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26"
    "OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3"
)

def find_element_in_any_frame(page, selector, timeout=10_000):
    """
    Locates a selector in the main page or within any iframe.
    Returns a Playwright Locator if found, otherwise None.
    """
    # Try in main frame first
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return page.locator(selector)
    except PlaywrightTimeoutError:
        pass

    # If not found, try each sub-frame
    for frame in page.frames:
        if frame == page.main_frame:
            continue  # We already tried main frame
        try:
            frame.wait_for_selector(selector, timeout=timeout)
            return frame.locator(selector)
        except PlaywrightTimeoutError:
            pass

    # If still not found, return None
    return None


def run_test():
    # The path to your real Chrome installation on macOS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    with sync_playwright() as p:
        # Launch persistent context to reuse your existing Chrome profile data
        # (including cookies, sessions, etc.)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,    # Reuse your actual profile folder
            executable_path=chrome_path,    # Path to your real Chrome
            headless=False                  # Set to True if you want it hidden
        )

        # Reuse an existing page if the browser opened with one,
        # or create a new page if there are none.
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()

        # Navigate to the target URL
        page.goto(target_url)

        # Try to find OACUNO (ID="OACUNO") in main page or any iframe
        oacuno_input = find_element_in_any_frame(page, "#OACUNO", timeout=10_000)
        if not oacuno_input:
            raise Exception("Unable to locate the OACUNO element anywhere.")

        # Click and fill OACUNO
        oacuno_input.click()
        oacuno_input.fill("TST_126765")
        time.sleep(3)

        # Find and click Next button (ID="btn-next")
        next_button = find_element_in_any_frame(page, "#btn-next", timeout=10_000)
        if not next_button:
            raise Exception("Unable to locate #btn-next element anywhere.")
        next_button.click()

        time.sleep(3)

        # Close everything
        context.close()


if __name__ == "__main__":
    run_test()
