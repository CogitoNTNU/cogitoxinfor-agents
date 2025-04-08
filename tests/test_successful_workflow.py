from persistent_browser import start_browser
import time

def run_test():
    # Get existing browser context
    context = start_browser()
    
    # Use existing page or create new
    pages = context.pages
    page = pages[0] if len(pages) > 0 else context.new_page()

    # Navigate to start page
    page.goto("https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b")
    time.sleep(12)
    response = page.goto("https://m3prduse1b.m3.inforcloudsuite.com/mne/ext/h5xi/?LogicalId=lid:%2F%2Finfor.m3.m3&inforCurrentLanguage=en-US&LNC=GB&inforCurrentLocale=en-US&inforTimeZone=(UTC%2B00:00)%20Dublin,%20Edinburgh,%20Lisbon,%20London&xfo=https:%2F%2Fmingle-portal.inforcloudsuite.com&inforThemeName=Light&inforThemeColor=amber&inforOSPortalVersion=2025.03.03", wait_until="networkidle")
    print("Second page status code:", response.status)
    time.sleep(5)
    # Trykk Ctrl + S for å lagre eller trigge snarvei
    page.keyboard.press("Control+S")

    # Successful interactions from log
    def input_text(element_id, text):
        print(f"Input '{text}' into {element_id}")
        page.locator(f"#{element_id}").fill(text)
        time.sleep(1)

    def click_element(element_id):
        print(f"Clicking {element_id}")
        page.locator(f"#{element_id}").click()
        time.sleep(1)

    # Test workflow based on successful log entries
    try:
        # Press Ctrl+S to open search bar
        page.keyboard.press("Control+S")
        time.sleep(2)

        # Input "OIS100" and press Enter
        page.keyboard.type("OIS100")
        page.keyboard.press("Enter")
        time.sleep(5)

        # Input fields
        input_text("OACUNO", "TEST123")
        input_text("WARLDZ", "TEST456")
        click_element("btn-next")
        click_element("standard-btn-ok")

        # Warehouse operations
        input_text("OBWHLO", "WH01")
        input_text("WBITNO", "ITEM001")
        input_text("WBSAPR", "100")
        click_element("A_00434")
        click_element("standard-btn-ok")

        # Order processing
        input_text("OBSPUN", "500")
        click_element("A_00434")
        click_element("standard-btn-ok")

        

        print("Test completed successfully")
    except Exception as e:
        print(f"Test failed: {str(e)}")

    # Close test page
    page.close()

if __name__ == '__main__':
    run_test()
