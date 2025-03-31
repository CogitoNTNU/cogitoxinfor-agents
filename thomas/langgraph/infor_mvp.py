import asyncio
import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel

from browser_use import Agent, Browser, BrowserConfig, Controller, ActionResult
from langchain_openai import ChatOpenAI
from lmnr import Laminar
from playwright.async_api import BrowserContext
load_dotenv()
API_KEY = os.getenv("LMNR_PROJECT_API_KEY")
Laminar.initialize(project_api_key=API_KEY)
import os
print("Current working directory:", os.getcwd())
print("Directory contents:", os.listdir(os.getcwd()))

llm = ChatOpenAI(model='gpt-4o')
#llm = OpenAI(
  #  api_key=os.getenv("OPENROUTER_API_KEY"),
  #  openai_api_base="https://openrouter.ai/api/v1",
 #   model_name="google/gemini-2.5-pro-exp-03-25:free",
    # You can set additional parameters if needed
#)

browser = Browser(
    config=BrowserConfig(
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        headless=False,
        disable_security=True
    )
)

async def main():
    async with await browser.new_context() as context:
        login_agent = Agent(
            task="""
            Click the first account. After button clicked, wait 3 seconds. Task is now completed.
            """,
            llm=llm,
            initial_actions=[
                {'open_tab': {'url': 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'}},
            ],
            browser=browser,
            browser_context=context
        )

        try:
            with open("output.txt", "r") as file:
                task_description = "".join(file.readlines())
        except FileNotFoundError:
            print("output.txt not found. Please ensure the file exists.")
            task_description = ""
            task_description = task_description.replace("\n", " ")
            

        m3_agent = Agent(
            task=task_description,
            llm=llm,
            browser=browser,
            initial_actions=[{'open_tab': {'url': 'https://m3prduse1b.m3.inforcloudsuite.com/mne/ext/h5xi/?LogicalId=lid:%2F%2Finfor.m3.m3&inforCurrentLanguage=en-US&LNC=GB&inforCurrentLocale=en-US&inforTimeZone=(UTC%2B00:00)%20Dublin,%20Edinburgh,%20Lisbon,%20London&xfo=https:%2F%2Fmingle-portal.inforcloudsuite.com&inforThemeName=Light&inforThemeColor=amber&inforOSPortalVersion=2025.03.03'}},
            ],
            browser_context=context
        )

        await login_agent.run()
        await m3_agent.run()
        
        input('Press Enter to close the browser...')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())  
