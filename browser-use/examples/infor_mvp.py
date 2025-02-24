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
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)

class MySystemPrompt(SystemPrompt):
	def important_rules(self) -> str:
		existing_rules = super().important_rules()
		new_rules = 'REMEMBER the most important RULE: ALWAYS open first a new tab and go first to url https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3 no matter the task!!!'
		return f'{existing_rules}\n{new_rules}'

		# other methods can be overridden as well (not recommended)


async def main():
	task = "Objective: Process a customer order efficiently using the Infor M3 system, following each step outlined in the document. Step 1: Enter Customer Order Header: Open ‘Customer Order. Open Toolbox (OIS300/B)’. Locate an existing order or press F14 (or click ‘New Order’) to create a new order. Ensure key fields are entered: Customer which is TST_126765 (ordering organization), Requested delivery date which is 25/02/21, Customer order type. Additional details will populate automatically (payer, delivery address, etc.). Verify and modify these as needed. If the customer is unknown, press F4 to browse and search for the customer. For season-controlled orders, enter the project number (season code) on panel OIS100/E. Use F4 to browse available seasons. If the order belongs to a specialty category, ensure the ‘Your Reference 1’ field is completed on panel OIS100/G. Step 2: Perform Credit Check: The system automatically performs a credit check upon order entry or amendment. If credit limits are exceeded, a warning and a stop code are issued. Follow the ‘Managing Credit Checks’ process to handle stopped orders. Step 3: Enter Customer Order Lines: Open ‘Customer Order Lines (OIS101/B)’. Enter item details: Item code (can be customer’s item code or EAN-code), Quantity, Unit of measure, Sales price. The system retrieves additional information (pricing, discounts, promotions). For fashion orders, if a style code is entered, use the ‘Matrix Entry (CRS207/B)’ to specify SKU quantities. Ensure totals match for both size and color. Verify stock availability for urgent replenishment orders. Step 4: Enter Matrix (if applicable): Open ‘Full-screen Entry - Matrix. Open (CRS207/B)’. Enter ordered quantities for SKUs. Confirm entries by pressing Enter. Step 5: Review the Customer Order: Open ‘Customer Order. Simulate Totals (OIS110/E)’ to view a summary of the order values. Verify net goods value, sales tax, discounts, and charges. Confirm the creation of a shipment using ‘Shipment. Open Toolbox (DRS100/B)’. Additional Guidelines and Tips: Use Quick Order Copy: Create a new order by copying an existing one from OIS100 or OIS300 using option 33. Lost Sales Handling: If a line cannot be fulfilled due to stock unavailability, record the lost sale using ‘Customer Order. Enter Lost Sales (OSS450)’. Charge Management: To add line charges, open ‘Order Line Charge (CRS275)’ and follow steps to connect predefined charges. Formatting Rules for Customer Order Numbers: Validate the customer’s order number format based on rules defined in ‘Formatting Rules. Define (CMS085)’. Negative Header or Line Charges: Ensure that negative charges are only applied when permitted by the ‘CO Type’ settings in ‘OIS010/F’. Order Completion: Ensure all steps are completed without errors. Close the order entry session, confirming that the status and documentation match the requirements. System and Setup Notes: Refer to the IPC preconfigured data documentation for specific setups, such as sorting orders and dispatch policies. Ensure all warehouse and route configurations align with the customer’s delivery requirements. Enable automated processes for ATP (Available-to-Promise) checks, if applicable."
	model = ChatOpenAI(model='gpt-4o')
	agent = Agent(task=task, 
        llm=model, 
        system_prompt_class=MySystemPrompt,
        browser = browser
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
