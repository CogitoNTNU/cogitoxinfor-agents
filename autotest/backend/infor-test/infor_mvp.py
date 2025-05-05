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
#API_KEY = os.getenv("LMNR_PROJECT_API_KEY")
#Laminar.initialize(project_api_key=API_KEY)
import os
print("Current working directory:", os.getcwd())
print("Directory contents:", os.listdir(os.getcwd()))

llm = ChatOpenAI(model='gpt-4.1')
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

async def main(task):
    async with await browser.new_context() as context:
        m3_agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            initial_actions=[{'open_tab': {'url': 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'}},
                            {'open_tab': {'url': 'https://m3prduse1b.m3.inforcloudsuite.com/mne/infor?HybridCertified=1&xfo=https%3A%2F%2Fmingle-portal.inforcloudsuite.com&SupportWorkspaceFeature=0&Responsive=All&enable_health_service=true&portalV2Certified=1&LogicalId=lid%3A%2F%2Finfor.m3.m3&inforThemeName=Light&inforThemeColor=amber&inforCurrentLocale=en-US&inforCurrentLanguage=en-US&infor10WorkspaceShell=1&inforWorkspaceVersion=2025.03.03&inforOSPortalVersion=2025.03.03&inforTimeZone=(UTC%2B01%3A00)%20Dublin%2C%20Edinburgh%2C%20Lisbon%2C%20London&inforStdTimeZone=Europe%2FLondon&inforStartMode=3&inforTenantId=ICSGDENA002_DEV&inforSessionId=ICSGDENA002_DEV~6ba2f2fc-8f7b-4651-97de-06a45e5f54e7'}},
            ],
            browser_context=context,
        )

        m3_history = await m3_agent.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user.")
    finally:
        print("Script finished.")
