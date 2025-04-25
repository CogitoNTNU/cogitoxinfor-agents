from datetime import datetime, timedelta
from playwright.sync_api import expect, Page
import pytest

@pytest.fixture(scope="module")
def authenticated_page(page: Page):
    # Add authentication logic here
    yield page

def test_infor_m3_workflow(page, request):
    # Check for required environment variables
    if not os.getenv('INFOR_USERNAME') or not os.getenv('INFOR_PASSWORD'):
        pytest.skip("INFOR_USERNAME and INFOR_PASSWORD environment variables required")
    # Configure test with retries and screenshots
    page.set_default_timeout(10000)
    
    def take_screenshot(name):
        page.screenshot(path=f"screenshots/{request.node.name}_{name}.png", full_page=True)
    
    # Take initial screenshot
    take_screenshot("start")
    # Calculate today's date + 2 days in yy/mm/dd format
    delivery_date = (datetime.now() + timedelta(days=2)).strftime('%y/%m/%d')
    
    # Step 1: Open first URL
    page.goto('https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b')
    page.wait_for_timeout(5000)  # Wait 5 seconds
    
    # Step 2: Open second URL
    page.goto('https://m3prduse1b.m3.inforcloudsuite.com/mne/infor?HybridCertified=1&xfo=https%3A%2F%2Fmingle-portal.inforcloudsuite.com&SupportWorkspaceFeature=0&Responsive=All&enable_health_service=true&portalV2Certified=1&LogicalId=lid%3A%2F%2Finfor.m3.m3&inforThemeName=Light&inforThemeColor=amber&inforCurrentLocale=en-US&inforCurrentLanguage=en-US&infor10WorkspaceShell=1&inforWorkspaceVersion=2025.03.03&inforOSPortalVersion=2025.03.03&inforTimeZone=(UTC%2B01%3A00)%20Dublin%2C%20Edinburgh%2C%20Lisbon%2C%20London&inforStdTimeZone=Europe%2FLondon&inforStartMode=3&inforTenantId=ICSGDENA002_DEV&inforSessionId=ICSGDENA002_DEV~6ba2f2fc-8f7b-4651-97de-06a45e5f54e7')
    
    # Press Ctrl+S to open search bar
    page.keyboard.press('Control+S')
    
    # Search for OIS100
    search_input = page.locator('[data-testid="global-search-input"]')
    expect(search_input).to_be_visible()
    search_input.fill('OIS100')
    search_input.press('Enter')
    
    # Enter customer number with retry logic
    customer_field = page.locator('[data-testid="customer-field"]')
    expect(customer_field).to_be_visible()
    customer_field.fill('1337', timeout=5000)
    
    # Enter delivery date
    delivery_field = page.locator('input[name="deliveryDate"]')
    delivery_field.fill(delivery_date)
    delivery_field.press('Enter')
    
    # Handle confirmation alert
    page.on('dialog', lambda dialog: dialog.accept())
    
    # Press Next three times to reach Panel G
    for _ in range(3):
        next_button = page.locator('button:has-text("Next")')
        next_button.click()
    
    # Enter customer order info
    order_field = page.locator('input[name="customerOrder"]')
    order_field.fill('ABC123')
    ie_field = page.locator('input[name="ie"]')
    ie_field.fill('IE1')

    # Press Next 2 times to reach Panel B1
    for _ in range(2):
        next_button = page.locator('button:has-text("Next")')
        next_button.click()

    # Enter item details
    item_field = page.locator('input[name="item"]')
    item_field.fill('11040')
    qty_field = page.locator('input[name="orderQty"]')
    qty_field.fill('2')
    price_field = page.locator('input[name="salesPrice"]')
    price_field.fill('10')
    add_button = page.locator('button:has-text("Add")')
    add_button.click()

    # Verify Panel E opens
    panel_e = page.locator('div.panel-e')
    expect(panel_e).to_be_visible()

    # Press Next
    next_button = page.locator('button:has-text("Next")')
    next_button.click()

    # Verify order status is 22
    status = page.locator('span.status')
    expect(status).to_have_text('22')

    # Save order number (would need to extract from UI)
    order_number = '0010007876'  # This would normally be extracted from the page

    # Close program (OIS101)
    close_button = page.locator('button:has-text("Close")')
    close_button.click()

    # Press Ctrl+S and search for OIS300
    page.keyboard.press('Control+S')
    search_input = page.locator('input[type="search"]')
    search_input.fill('OIS300')
    search_input.press('Enter')

    # Search for the order number
    order_search = page.locator('input[name="orderSearch"]')
    order_search.fill(order_number)
    order_search.press('Enter')

    # Verify order appears and status is 22
    order_row = page.locator(f'tr:has-text("{order_number}")')
    expect(order_row).to_be_visible()
    status_cell = order_row.locator('td.status')
    expect(status_cell).to_have_text('22')

    # Right-click and select Delivery Toolbox (Ctrl+43)
    order_row.click(button='right')
    delivery_option = page.locator('li:has-text("Delivery toolbox +43")')
    delivery_option.click()

    # Verify MWS410 appears
    mws410 = page.locator('div.mws410')
    expect(mws410).to_be_visible()

    # Right-click and select Picking list (Ctrl+11)
    order_row.click(button='right')
    picking_option = page.locator('li:has-text("Picking list Ctrl+11")')
    picking_option.click()

    # Verify MWS420 appears with status 40
    mws420 = page.locator('div.mws420')
    expect(mws420).to_be_visible()
    status_40 = mws420.locator('span.status:has-text("40")')
    expect(status_40).to_be_visible()

    # Right-click and select Confirm issues
    order_row.click(button='right')
    confirm_option = page.locator('li:has-text("Confirm issues")')
    confirm_option.click()

    # Press "flagged compl" and next through warnings
    flagged_button = page.locator('button:has-text("flagged compl")')
    flagged_button.click()
    for _ in range(2):
        next_button = page.locator('button:has-text("Next")')
        next_button.click()

    # Verify status updated to 90
    status_90 = mws420.locator('span.status:has-text("90")')
    expect(status_90).to_be_visible()

    # Press back until OIS300
    while not page.url().contains('OIS300'):
        back_button = page.locator('button:has-text("Back")')
        back_button.click()

    # Verify order status updated to 66
    status_66 = order_row.locator('td.status:has-text("66")')
    expect(status_66).to_be_visible()
