import json
import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from browser_use import Agent, SystemPrompt, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig  # <-- Added missing imports

config = BrowserContextConfig(
    wait_for_network_idle_page_load_time=6.0,
    browser_window_size={'width': 1280, 'height': 1100},
    locale='en-US',
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36',
    highlight_elements=True,
    viewport_expansion=-1,
)

browser = Browser()
context = BrowserContext(browser=browser, config=config)

class MySystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        existing_rules = super().important_rules()
        new_rules = (
            "REMEMBER the most important RULE: ALWAYS open first a new tab and go first to url "
            "https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?"
            "favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26"
            "OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3 no matter the task!!!"
        )
        return f'{existing_rules}\n{new_rules}'

async def main():
    initial_actions = [
        {
            'open_tab': {
                'url': (
                    "https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/"
                    "aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?"
                    "OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26"
                    "OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3"
                )
            }
        },
    ]
    task = (
        "wait for 10 seconds after login before you start the task Objective: Process a customer order efficiently using the Infor M3 system, following each step outlined in the document. Step 1: Enter Customer Order Header: Open ‘Customer Order. Open Toolbox (OIS300/B)’. Locate an existing order or press F14 (or click ‘New Order’)"
    )
    model = ChatOpenAI(model='gpt-4o')
    agent = Agent(
        task=task,
        llm=model,
        system_prompt_class=MySystemPrompt,
        browser=browser,
        initial_actions=initial_actions,
    )

    print(
        json.dumps(
            agent.message_manager.system_prompt.model_dump(exclude_unset=True),
            indent=4,
        )
    )

    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())
