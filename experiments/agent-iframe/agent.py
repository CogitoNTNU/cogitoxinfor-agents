"""
Minimal Browser‑Use agent that attaches to the Chrome instance
you started with `--remote-debugging-port=9222` and performs a
simple scroll on Wikipedia.  Keeps the window alive so MarinaBox
can continue streaming it.

Requirements:
    pip install browser-use langchain-openai

Make sure you have `OPENAI_API_KEY` set in your environment.
"""

import asyncio
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig

async def main() -> None:
    # Re‑use the existing Chrome window via CDP
    browser = Browser(config=BrowserConfig(cdp_url="http://127.0.0.1:9222"))

    agent = Agent(
        task="Open wikipedia.org and scroll a little",
        llm=ChatOpenAI(model="gpt-4o"),
        browser=browser,
    )

    await agent.run()

    # Do NOT close the browser if MarinaBox/noVNC still needs it.
    # Uncomment the next line if you want Browser‑Use to detach cleanly:
    # await browser.close()

if __name__ == "__main__":
    asyncio.run(main())