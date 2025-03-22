from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv

load_dotenv()

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

    agent = Agent(
        task="""You are executing a test of the Infor ERP software called M3.
Task: Curves can be created in ‘Period Accounting Curves. Open’ (CRS450)
to reflect the business trading pattern and then used to allocate budgets.""",
        llm=ChatOpenAI(model="gpt-4o"),
    )

    # If you intend to pass in `initial_actions`, make sure to include them:
    # agent = Agent(
    #     task="""...""",
    #     llm=ChatOpenAI(model="gpt-4o"),
    #     initial_actions=initial_actions
    # )

    result = await agent.run()
    print(result)

asyncio.run(main())
