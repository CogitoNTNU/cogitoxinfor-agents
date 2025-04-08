from playwright.sync_api import sync_playwright
import time

# Globale variabler for å holde på playwright og context
playwright = None
context = None

def start_browser():
    global playwright, context
    if playwright is None:
        playwright = sync_playwright().start()
    if context is None:
        user_data_dir = '/Users/nybruker/Library/Application Support/Google/Chrome'
        executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=executable_path,
            headless=False,
            no_viewport=True,  # Bruk systemets native viewport
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
    return context

def stop_browser():
    global playwright, context
    if context:
        context.close()
        context = None
    if playwright:
        playwright.stop()
        playwright = None

if __name__ == '__main__':
    # Dette skriptet skal kjøres først for å logge inn.
    context = start_browser()
    page = context.new_page()
    page.goto("https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b")
    input("Logg inn manuelt og trykk Enter for å starte testene...")
    print("Browser er nå logget inn og vil forbli åpen...")
    input("Trykk Enter for å avslutte (skriptet stopper da browseren lukkes)...")
    stop_browser()