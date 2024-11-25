import logging
import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configure Logging
logging.basicConfig(
    filename="adfly_automation_with_proxy.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Proxy List
proxy_list = [
    "http://username:password@proxy1:port",
    "http://username:password@proxy2:port",
    "http://username:password@proxy3:port",
]

# Generate a random MAC address
def generate_random_mac():
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(random.randint(0, 255) for _ in range(5))

# Change MAC address
def change_mac_address(interface="eth0"):
    new_mac = generate_random_mac()
    try:
        subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
        subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", new_mac], check=True)
        subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)
        logging.info(f"MAC address changed to {new_mac} on interface {interface}")
        return True
    except Exception as e:
        logging.error(f"Failed to change MAC address: {e}")
        return False

# Set up Selenium WebDriver with Proxy
def get_driver_with_proxy(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server={proxy}")
    driver = webdriver.Chrome(options=options)
    return driver

# Handle AdFly link
def handle_adfly(adfly_url, proxy):
    """
    Handles an AdFly URL using the given proxy.
    
    Parameters:
    adfly_url (str): The AdFly URL to process.
    proxy (str): Proxy address for the session.
    
    Returns:
    str: The final destination URL or an error message.
    """
    driver = None
    try:
        logging.info(f"Starting AdFly handler for URL: {adfly_url} using proxy: {proxy}")
        driver = get_driver_with_proxy(proxy)
        driver.get(adfly_url)

        # Wait for the AdFly page to load
        logging.info("Waiting for the AdFly timer to appear...")
        try:
            ad_timer = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "timer"))  # Replace ID if different
            )
            logging.info("Ad timer detected. Waiting for completion...")
        except TimeoutException:
            logging.warning("Ad timer not found. Either no ad or site error.")
            return "Ad timer not found. Check AdFly site or URL."

        # Wait for the Skip Ad button to appear
        try:
            skip_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "skip_button"))  # Replace ID if necessary
            )
            logging.info("Skip Ad button detected. Waiting 3 seconds before skipping...")
            time.sleep(3)  # Wait before skipping
            skip_button.click()
            logging.info("Skip Ad button clicked.")
        except TimeoutException:
            logging.error("Skip Ad button did not appear. Watching full ad or exiting.")
            return "Skip Ad button not found. Full ad watched."

        # Wait for the destination page to load
        logging.info("Waiting for the destination page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        final_url = driver.current_url
        logging.info(f"Destination page loaded successfully: {final_url}")
        return final_url

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return f"Error: {str(e)}"

    finally:
        if driver:
            driver.quit()
            logging.info("Browser session closed.")

# Main script to handle multiple AdFly URLs
if __name__ == "__main__":
    adfly_links = [
        "https://www.adfly.com/sample1",  # Replace with actual AdFly URLs
        "https://www.adfly.com/sample2",
        "https://www.adfly.com/sample3"
    ]

    results = {}
    for link in adfly_links:
        # Rotate MAC address
        logging.info("Changing MAC address...")
        if not change_mac_address(interface="eth0"):
            logging.warning("MAC address change failed. Continuing with the current MAC.")

        # Rotate Proxy
        proxy = random.choice(proxy_list)
        logging.info(f"Using proxy: {proxy}")

        # Process the AdFly link
        logging.info(f"Processing AdFly link: {link}")
        result = handle_adfly(link, proxy)
        results[link] = result
        print(f"Result for {link}: {result}")

    logging.info("AdFly automation with proxy and MAC rotation complete.")
    print("Processing completed. Check 'adfly_automation_with_proxy.log' for details.")
