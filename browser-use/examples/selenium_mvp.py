from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to your Chrome profile on macOS. 
user_data_dir = "/Users/nybruker/Library/Application Support/Google/Chrome/Default"

options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={user_data_dir}")
# If you use a named profile like "Profile 1", also add this:
# options.add_argument("--profile-directory=Profile 1")

driver = webdriver.Chrome(options=options)

driver.get(
    "https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/"
    "aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?"
    "OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26"
    "OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3"
)

def find_element_in_any_frame(driver, by, locator, timeout=10):
    """
    Looks for an element (By locator) in the main page and in every iframe.
    Returns the element if found, otherwise None.
    """
    wait = WebDriverWait(driver, timeout)
    
    # 1) Try to find in the top-level DOM:
    driver.switch_to.default_content()  # Ensure we’re at top level
    try:
        return wait.until(EC.element_to_be_clickable((by, locator)))
    except:
        pass
    
    # 2) If not found, loop through each iframe:
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for frame in iframes:
        driver.switch_to.default_content()  # reset to root each iteration
        driver.switch_to.frame(frame)
        try:
            return WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, locator))
            )
        except:
            # Element not in this iframe; keep going
            pass
    
    # 3) If we still haven't found it, return None
    driver.switch_to.default_content()  
    return None

# Use our helper method to attempt to find the OACUNO input
oacuno_input = find_element_in_any_frame(driver, By.ID, "OACUNO", timeout=10)


if oacuno_input:
    oacuno_input.click()
    oacuno_input.send_keys("TST_126765")
    time.sleep(3)
else:
    raise Exception("Unable to locate the OACUNO element anywhere.")


wait = WebDriverWait(driver, 2)  # wait up to 10 seconds
next_button = wait.until(
    EC.element_to_be_clickable((By.ID, "btn-next"))
)
next_button.click()

time.sleep(3)

driver.quit()
