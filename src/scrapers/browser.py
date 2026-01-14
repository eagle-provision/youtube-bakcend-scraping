"""
Browser automation module for YouTube scraping.
Handles Selenium WebDriver setup and browser interactions.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from src.config.config import (
    CHROME_OPTIONS, BROWSER_WAIT_TIME, DYNAMIC_CONTENT_WAIT, 
    SCROLL_DELAY, DEBUG_MODE
)


def setup_driver():
    """
    Initialize and configure Selenium WebDriver with Chrome.
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    
    # Add all configured options
    for option in CHROME_OPTIONS:
        if '=' in option:
            key, value = option.split('=', 1)
            options.add_argument(f'{key}={value}')
        else:
            options.add_argument(option)
    
    try:
        # Install ChromeDriver automatically matching the installed Chrome version
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        if DEBUG_MODE:
            print("[OK] WebDriver initialized successfully")
        return driver
    except Exception as e:
        print(f"[ERROR] Error initializing WebDriver: {e}")
        raise


def navigate_to_page(driver, url, max_retries=2):
    """
    Navigate to a URL and wait for page to load with retry logic.
    
    Args:
        driver: WebDriver instance
        url (str): URL to navigate to
        max_retries (int): Maximum retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Set page load timeout to 60 seconds (shorter than default 120)
    driver.set_page_load_timeout(60)
    
    for attempt in range(max_retries + 1):
        try:
            driver.get(url)
            WebDriverWait(driver, BROWSER_WAIT_TIME).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            if DEBUG_MODE:
                print(f"[OK] Navigated to: {url}")
            return True
        except Exception as e:
            if attempt < max_retries:
                if DEBUG_MODE:
                    print(f"[WARN] Navigation attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
            else:
                print(f"[ERROR] Error navigating to {url}: {e}")
                return False
    return False


def wait_for_dynamic_content(driver):
    """
    Wait for dynamic JavaScript content to load.
    
    Args:
        driver: WebDriver instance
    """
    time.sleep(DYNAMIC_CONTENT_WAIT)
    if DEBUG_MODE:
        print(f"[OK] Waited {DYNAMIC_CONTENT_WAIT}s for dynamic content")


def scroll_page(driver, pixels=500):
    """
    Scroll page to load additional content.
    
    Args:
        driver: WebDriver instance
        pixels (int): Number of pixels to scroll
    """
    try:
        driver.execute_script(f"window.scrollTo(0, {pixels});")
        time.sleep(SCROLL_DELAY)
        if DEBUG_MODE:
            print(f"[OK] Scrolled {pixels}px")
    except Exception as e:
        print(f"[ERROR] Error scrolling page: {e}")


def scroll_to_bottom(driver):
    """
    Scroll page to the bottom to load all content.
    
    Args:
        driver: WebDriver instance
    """
    try:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(SCROLL_DELAY)
        if DEBUG_MODE:
            print("[OK] Scrolled to bottom")
    except Exception as e:
        print(f"[ERROR] Error scrolling to bottom: {e}")


def find_element_safe(driver, by, value, timeout=BROWSER_WAIT_TIME):
    """
    Safely find an element with timeout.
    
    Args:
        driver: WebDriver instance
        by: By locator type
        value: Locator value
        timeout: Wait timeout in seconds
        
    Returns:
        WebElement or None: Found element or None
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except:
        return None


def find_elements_safe(driver, by, value):
    """
    Safely find multiple elements.
    
    Args:
        driver: WebDriver instance
        by: By locator type
        value: Locator value
        
    Returns:
        list: List of found elements
    """
    try:
        return driver.find_elements(by, value)
    except:
        return []
