from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Step 0: Set up browser
driver = webdriver.Chrome()
driver.get("https://www.saucedemo.com/")
time.sleep(1)
driver.save_screenshot("step0_login_page.png")

# Step 1: Log in
driver.find_element(By.ID, "user-name").send_keys("standard_user")
driver.find_element(By.ID, "password").send_keys("secret_sauce")
driver.find_element(By.ID, "login-button").click()
time.sleep(2)
driver.save_screenshot("step1_logged_in.png")

# Step 2: Click on a product (e.g., first product title)
driver.find_element(By.CLASS_NAME, "inventory_item_name").click()
time.sleep(1)
driver.save_screenshot("step2_product_detail.png")

# Step 3: Click "Add to cart" button
driver.find_element(By.CLASS_NAME, "btn_primary").click()
time.sleep(1)
driver.save_screenshot("step3_added_to_cart.png")

# Step 4: Click on cart icon
driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
time.sleep(1)
driver.save_screenshot("step4_cart_page.png")

# Step 5: Print page title
print("Final page title:", driver.title)

# Step 6: Quit browser
driver.quit()

