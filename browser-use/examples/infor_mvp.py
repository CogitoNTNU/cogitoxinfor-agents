import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import ChatOpenAI
from browser_use import Agent, SystemPrompt, Browser, BrowserConfig

browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        disable_security=True

        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)

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
        "Objective: Process a customer order efficiently using the Infor M3 system, following each step outlined in the document. Step 1: Enter Customer Order Header: Open ‘Customer Order. Open Toolbox (OIS300/B)’. Locate an existing order or press F14 (or click ‘New Order’)"
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
