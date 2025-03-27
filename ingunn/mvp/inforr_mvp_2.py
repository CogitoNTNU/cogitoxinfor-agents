import asyncio
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Add project root to path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent, Browser, BrowserConfig, Controller, ActionResult
from langchain_openai import ChatOpenAI
from playwright.async_api import BrowserContext

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("LMNR_PROJECT_API_KEY")

# Initialize LLM
llm = ChatOpenAI(model='gpt-4o')

# ─────────────────────────────────────────────
# 📦 Step 1: Define Output Model
# ─────────────────────────────────────────────

class ElementInfo(BaseModel):
    tag_name: str = Field(..., title="The tag name of the element")
    element_id: Optional[str] = Field(None, title="The id attribute of the element")
    name: Optional[str] = Field(None, title="The name attribute of the element")

class useBrowserOutput(BaseModel):
    elements: List[ElementInfo]

# ─────────────────────────────────────────────
# 🔧 Step 2: Create Controller and Register Action
# ─────────────────────────────────────────────

controller = Controller()

@controller.registry.action('Done with task', param_model=useBrowserOutput)
async def done(params: useBrowserOutput):
    return ActionResult(is_done=True, extracted_content=params.model_dump_json())

# ─────────────────────────────────────────────
# 🌐 Step 3: Setup Browser
# ─────────────────────────────────────────────

browser = Browser(
    config=BrowserConfig(
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        # Windows example: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        headless=False,
        disable_security=True
    )
)

# ─────────────────────────────────────────────
# 🚀 Step 4: Main Logic
# ─────────────────────────────────────────────

async def main():
    async with await browser.new_context() as context:
        # Optional login step
        login_agent = Agent(
            task="When logged in task is completed.",
            llm=llm,
            initial_actions=[
                {'open_tab': {'url': 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'}},  # Change this URL to your target
                {"click_element": {"index": 1}}  # Optional
            ],
            browser=browser,
            browser_context=context
        )

        # 📜 Task: Extract element attributes
        task_description = """
        Go to the current page and extract all <button> and <input> elements.
        For each element, return:
        - the tag name (e.g. "button" or "input")
        - the html id attribute (if present)
        - the name attribute (if present)
        Return the results as a JSON objects with fields: tag_name, element_id, and name.
        """

        m3_agent = Agent(
            task=task_description,
            llm=llm,
            browser=browser,
            browser_context=context
        )

        await login_agent.run()  # Optional
        history = await m3_agent.run()

        result = history.final_result()
        if result:
            parsed = useBrowserOutput.model_validate_json(result)
            for element in parsed.elements:
                print('\n--------------------------------')
                print(f'Tag Name:  {element.tag_name}')
                print(f'ID:        {element.element_id}')
                print(f'Name:      {element.name}')
        else:
            print("❌ No result received from the agent.")

        input('Press Enter to close the browser...')
        await browser.close()

# ─────────────────────────────────────────────
# 🏁 Run
# ─────────────────────────────────────────────

if __name__ == '__main__':
    asyncio.run(main())
