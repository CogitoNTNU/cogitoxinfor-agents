import asyncio
import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent, Browser, BrowserConfig, Controller, ActionResult
from langchain_openai import ChatOpenAI
from lmnr import Laminar
from playwright.async_api import BrowserContext

load_dotenv()
API_KEY = os.getenv("LMNR_PROJECT_API_KEY")
# Laminar.initialize(project_api_key=API_KEY)

llm = ChatOpenAI(model='gpt-4o')

class useBrowserOutput(BaseModel):
    id: Optional[str] = Field(..., description="The html id of the clicked element")
    text: str = Field(..., title="The text of the clicked element")

"""
Show how to use custom outputs.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

controller = Controller()


@controller.registry.action('Done with task', param_model=useBrowserOutput)
async def done(params: useBrowserOutput):
	result = ActionResult(is_done=True, extracted_content=params.model_dump_json())
	return result
    

llm_with_struct = llm.with_structured_output(schema=useBrowserOutput)

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
            click first element. Wait 2 seconds then task is completed. 
            """,
            llm=llm,
            initial_actions=[
                {'open_tab': {'url': 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'}},
            ],
            browser=browser,
            browser_context=context
        )

        with open("output.txt", "r") as file:
            task_description = "".join(file.readlines())
        
        task_description = task_description.replace("\n", " ")
    
        test_task = """
            Open burdger bar on top left and type in OIS100
        """

        m3_agent = Agent(
            task=task_description,
            llm=llm,
            browser=browser,
            initial_actions=[{'open_tab': {'url': 'https://m3prduse1b.m3.inforcloudsuite.com/mne/ext/h5xi/?LogicalId=lid:%2F%2Finfor.m3.m3&inforCurrentLanguage=en-US&LNC=GB&inforCurrentLocale=en-US&inforTimeZone=(UTC%2B00:00)%20Dublin,%20Edinburgh,%20Lisbon,%20London&xfo=https:%2F%2Fmingle-portal.inforcloudsuite.com&inforThemeName=Light&inforThemeColor=amber&inforOSPortalVersion=2025.03.03'}},
            ],
            browser_context=context
        )

        await login_agent.run()
        history = await m3_agent.run()
        result = history.final_result()
        if result:
            parsed = useBrowserOutput.model_validate_json(result)
            print('--------------------------------')
            print(f'id: {parsed.id}')
            print(f'text: {parsed.text}')
        
        input('Press Enter to close the browser...')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())  
