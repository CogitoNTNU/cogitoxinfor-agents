from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI
from lmnr import Laminar
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()
API_KEY=os.getenv("LMNR_PROJECT_API_KEY")
print(API_KEY)


# this line auto-instruments Browser Use and any browser you use (local or remote)
Laminar.initialize(project_api_key=API_KEY)



# Configure the browser to connect to your Chrome instance
browser = Browser(
    config=BrowserConfig(
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'

        headless=False,
        disable_security=True
    )
)

# Create the agent with your configured browser
agent = Agent(
        task="""
        step1: open the following link:"
        https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Customer%20Order.%20Open%26OIS100%20Customer%20Order.%20Open&LogicalId=lid://infor.m3.m3
        step 2: wait 20 seconds
        step 3: type 'sometext' in the customer field.
        step 4: press 'next' button
        """,
    llm=ChatOpenAI(model='gpt-4o'),
    browser=browser,
    use_vision=True
)

async def main():
    await agent.run()

    input('Press Enter to close the browser...')
    await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
