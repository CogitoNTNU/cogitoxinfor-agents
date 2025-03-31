import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI

load_dotenv()

def selenium_login():
    # First try connecting to existing Chrome
    print("Attempting to connect to existing Chrome browser...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Successfully connected to existing Chrome session")
        print(f"Current URL: {driver.current_url}")
        return driver
    except Exception as e:
        print(f"⚠️ Could not connect to existing Chrome: {str(e)}")
        print("Launching new Chrome browser instance...")
        
        # Fallback to new browser with exact user profile
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir=/Users/nybruker/Library/Application Support/Google/Chrome")
        options.add_argument("--profile-directory=Default")
        driver = webdriver.Chrome(options=options)
        print("✅ New Chrome browser launched")
        
        # Navigate to login page
        login_url = 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'
        driver.get(login_url)
        
        # Wait for and click account element
        account = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "my-element"))
        )
        account.click()
        time.sleep(3)  # Wait for login
        
        return driver

async def run_m3_agent(browser_instance):
    print("Starting M3 agent...")
    try:
        with open("output.txt", "r") as file:
            task_description = "".join(file.readlines())
    except FileNotFoundError:
        print("output.txt not found. Please ensure the file exists.")
        task_description = ""
        task_description = task_description.replace("\n", " ")

    llm = ChatOpenAI(model='gpt-4o')
    
    m3_agent = Agent(
        task=task_description,
        llm=llm,
        browser=browser_instance,
        initial_actions=[{
            'open_tab': {
                'url': 'https://m3prduse1b.m3.inforcloudsuite.com/mne/ext/h5xi/?LogicalId=lid:%2F%2Finfor.m3.m3&inforCurrentLanguage=en-US&LNC=GB&inforCurrentLocale=en-US&inforTimeZone=(UTC%2B00:00)%20Dublin,%20Edinburgh,%20Lisbon,%20London&xfo=https:%2F%2Fmingle-portal.inforcloudsuite.com&inforThemeName=Light&inforThemeColor=amber&inforOSPortalVersion=2025.03.03'
            }
        }]
    )

    await m3_agent.run()
    input('Press Enter to close the browser...')
    await browser_instance.close()

async def main():
    # First perform Selenium login
    driver = selenium_login()
    driver.quit()
    
    # Then start browser-use agent for M3 actions
    browser = Browser(
        config=BrowserConfig(
            chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            headless=False,
            disable_security=True
        )
    )
    
    async with await browser.new_context() as context:
        await run_m3_agent(browser)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
