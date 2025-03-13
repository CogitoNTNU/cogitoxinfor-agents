from playwright.sync_api import sync_playwright

def automate_shadow_dom():
    with sync_playwright() as p:
        # Start a browser (Chromium, Firefox, WebKit)
        browser = p.chromium.launch(headless=False)  # Set headless=True for silent execution
        page = browser.new_page()

        # Open the target website
        page.goto("https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3")

        # Locate the shadow host element
        shadow_host = page.locator("portal-root")  # Replace with the real selector

        # Locate an element inside shadow DOM
        theme_switcher = shadow_host.locator("css=ids-theme-switcher")
        theme_switcher.click()  # Example action

        print("Button clicked successfully!")

        # Keep browser open for debugging (optional)
        page.pause()

        browser.close()

if __name__ == "__main__":
    automate_shadow_dom()
