"""
Data extraction module for channel information.
Handles scraping and parsing of YouTube channel data.
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import re
import time
from browser import (
    setup_driver, navigate_to_page, wait_for_dynamic_content,
    scroll_page, find_element_safe, find_elements_safe
)
from config import (
    YOUTUBE_BASE_URL, CHANNEL_ABOUT_PATH, BROWSER_WAIT_TIME,
    XPATH_SUBSCRIBERS, XPATH_VIEWS, XPATH_JOINED_DATE,
    IMAGE_DOMAIN_YT3, DEBUG_MODE
)


def extract_numeric_value(text, default=0):
    """
    Convert text with K/M/B suffixes or spelled out numbers to numeric value.
    Handles: "100K", "1.5M", "20.7m", "100 thousand", "1 million", etc.
    
    Args:
        text (str): Text containing number with optional K/M/B suffix or spelled out
        default: Default value if parsing fails
        
    Returns:
        int: Numeric value
    """
    try:
        # First check for spelled out multipliers
        if 'million' in text.lower():
            match = re.search(r'([\d,]+(?:\.\d+)?)', text)
            if match:
                num = match.group(1).replace(',', '')
                return int(float(num) * 1000000)
        elif 'thousand' in text.lower():
            match = re.search(r'([\d,]+(?:\.\d+)?)', text)
            if match:
                num = match.group(1).replace(',', '')
                return int(float(num) * 1000)
        elif 'billion' in text.lower():
            match = re.search(r'([\d,]+(?:\.\d+)?)', text)
            if match:
                num = match.group(1).replace(',', '')
                return int(float(num) * 1000000000)
        
        # Then check for K/M/B suffixes (case insensitive)
        match = re.search(r'([\d,]+(?:\.\d+)?)\s*([KMBkmb])?', text)
        if not match:
            return default
        
        num_str = match.group(1).replace(',', '')  # Remove commas first
        suffix = match.group(2)
        
        if suffix:
            suffix = suffix.upper()
            if suffix == 'K':
                return int(float(num_str) * 1000)
            elif suffix == 'M':
                return int(float(num_str) * 1000000)
            elif suffix == 'B':
                return int(float(num_str) * 1000000000)
        
        return int(float(num_str))
    except Exception as e:
        if DEBUG_MODE:
            print(f"✗ Error parsing numeric value '{text}': {e}")
        return default


def extract_subscribers(driver):
    """
    Extract subscriber count from channel about page.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        int: Subscriber count
    """
    try:
        sub_elem = driver.find_element(By.XPATH, XPATH_SUBSCRIBERS)
        sub_text = sub_elem.text
        if DEBUG_MODE:
            print(f"  Subscriber element text: '{sub_text}'")
        
        subscribers = extract_numeric_value(sub_text)
        if DEBUG_MODE:
            print(f"  ✓ Subscribers: {subscribers:,}")
        return subscribers
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting subscribers: {e}")
        return 0


def extract_total_views(driver):
    """
    Extract total channel views (maximum of all view count elements).
    
    Args:
        driver: WebDriver instance
        
    Returns:
        int: Total views count
    """
    try:
        views_elements = driver.find_elements(By.XPATH, XPATH_VIEWS)
        view_counts = []
        
        for views_elem in views_elements:
            views_text = views_elem.text
            count = extract_numeric_value(views_text)
            if count > 0:
                view_counts.append(count)
        
        if view_counts:
            total_views = max(view_counts)
            if DEBUG_MODE:
                print(f"  ✓ Total Views: {total_views:,}")
            return total_views
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting total views: {e}")
        return 0


def extract_description(driver, page_source):
    """
    Extract channel description (full text, not truncated).
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        str: Channel description
    """
    try:
        # Try to extract from page JSON first
        match = re.search(
            r'"description":\s*"(A 5v5[^"\\]*(?:\\.[^"\\]*)*)"',
            page_source
        )
        if match:
            description = match.group(1)
            description = description.replace('\\n', '\n').replace('\\"', '"')
            if DEBUG_MODE:
                print(f"  ✓ Description extracted (from JSON, {len(description)} chars)")
            return description
        
        # Fallback to meta tag
        soup = BeautifulSoup(page_source, 'html.parser')
        desc_elem = soup.select_one('meta[name="description"]')
        if desc_elem:
            description = desc_elem.get('content', '')
            if DEBUG_MODE:
                print(f"  ✓ Description extracted (from meta, {len(description)} chars)")
            return description
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting description: {e}")
        return ""


def extract_joined_date(driver):
    """
    Extract channel creation/joined date.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        str: Joined date string
    """
    try:
        joined_elem = driver.find_element(By.XPATH, XPATH_JOINED_DATE)
        creation_date = joined_elem.text
        if DEBUG_MODE:
            print(f"  ✓ Joined date: {creation_date}")
        return creation_date
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting joined date: {e}")
        return ""


def extract_images(page_source):
    """
    Extract banner and profile picture URLs from channel page.
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        tuple: (banner_url, profile_pic_url)
    """
    banner_url = ""
    profile_pic_url = ""
    
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        all_imgs = soup.find_all('img')
        
        # Collect yt3 images (first = banner, second = profile)
        yt3_images = []
        
        for img in all_imgs:
            src = img.get('src', '')
            
            if IMAGE_DOMAIN_YT3 in src and src not in yt3_images:
                yt3_images.append(src)
        
        # First yt3 image is banner
        if len(yt3_images) > 0:
            banner_url = yt3_images[0]
            if DEBUG_MODE:
                print(f"  ✓ Banner URL extracted")
        
        # Second yt3 image is profile pic
        if len(yt3_images) > 1:
            profile_pic_url = yt3_images[1]
            if DEBUG_MODE:
                print(f"  ✓ Profile picture URL extracted")
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting images: {e}")
    
    return banner_url, profile_pic_url


def extract_channel_country(driver, page_source):
    """
    Extract channel country from the about page.
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        str: Country name or empty string
    """
    try:
        # Try to find country in page text elements
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for country info in the details section
        detail_rows = soup.find_all('tr', class_='description-item')
        for row in detail_rows:
            text = row.get_text(strip=True)
            if 'country' in text.lower() or 'location' in text.lower():
                # Extract the value part
                cells = row.find_all('td')
                if len(cells) > 1:
                    country = cells[1].get_text(strip=True)
                    if DEBUG_MODE:
                        print(f"  ✓ Country: {country}")
                    return country
        
        # Alternative: search in page source for country metadata
        match = re.search(r'"country":\s*"([^"]+)"', page_source)
        if match:
            country = match.group(1)
            if DEBUG_MODE:
                print(f"  ✓ Country (from JSON): {country}")
            return country
        
        # Try XPath to find country element
        try:
            country_elements = driver.find_elements(By.XPATH, "//yt-formatted-string[contains(text(), 'United') or contains(text(), 'India') or contains(text(), 'Canada') or contains(text(), 'Australia') or contains(text(), 'Brazil')]")
            if country_elements:
                country = country_elements[0].text.strip()
                if DEBUG_MODE:
                    print(f"  ✓ Country (from element): {country}")
                return country
        except:
            pass
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting country: {e}")
        return ""


def extract_channel_language(page_source):
    """
    Extract default channel language.
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        str: Language code or name
    """
    try:
        # Try to find language in meta tags
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Check html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            language = html_tag.get('lang')
            if DEBUG_MODE:
                print(f"  ✓ Language: {language}")
            return language
        
        # Check og:locale meta tag
        og_locale = soup.find('meta', property='og:locale')
        if og_locale and og_locale.get('content'):
            language = og_locale.get('content')
            if DEBUG_MODE:
                print(f"  ✓ Language (og:locale): {language}")
            return language
        
        # Search in JSON data
        match = re.search(r'"defaultLanguage":\s*"([^"]+)"', page_source)
        if match:
            language = match.group(1)
            if DEBUG_MODE:
                print(f"  ✓ Language (from JSON): {language}")
            return language
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting language: {e}")
        return ""


def extract_channel_niche(channel_data, page_source):
    """
    Determine channel niche/category based on description and keywords.
    
    Args:
        channel_data (dict): Channel data with description
        page_source (str): Page HTML source
        
    Returns:
        str: Channel niche/category
    """
    try:
        description = channel_data.get('channel_description', '').lower()
        title = channel_data.get('channel_title', '').lower()
        combined_text = f"{title} {description}"
        
        # Try to find explicit category in page source
        match = re.search(r'"category":\s*"([^"]+)"', page_source)
        if match:
            category = match.group(1)
            if DEBUG_MODE:
                print(f"  ✓ Niche (from category): {category}")
            return category
        
        # Define niche keywords
        niche_keywords = {
            'Gaming': ['gaming', 'game', 'valorant', 'fortnite', 'minecraft', 'esports', 'gameplay', 'gamer', 'ps5', 'xbox', 'steam'],
            'Education': ['education', 'tutorial', 'learn', 'course', 'teaching', 'lesson', 'study', 'academic', 'school'],
            'Entertainment': ['entertainment', 'comedy', 'funny', 'vlogs', 'vlog', 'lifestyle', 'daily life', 'entertainment'],
            'Technology': ['tech', 'technology', 'gadget', 'review', 'unboxing', 'software', 'hardware', 'coding', 'programming'],
            'Music': ['music', 'song', 'artist', 'band', 'album', 'musician', 'singer', 'beats', 'audio'],
            'Sports': ['sports', 'fitness', 'workout', 'training', 'athlete', 'football', 'basketball', 'soccer', 'gym'],
            'Beauty & Fashion': ['beauty', 'makeup', 'fashion', 'style', 'clothing', 'cosmetics', 'skincare', 'hair'],
            'Food & Cooking': ['food', 'cooking', 'recipe', 'chef', 'kitchen', 'baking', 'cuisine', 'restaurant'],
            'Travel': ['travel', 'adventure', 'explore', 'tourism', 'destination', 'vacation', 'journey', 'trip'],
            'Business': ['business', 'entrepreneur', 'startup', 'finance', 'investing', 'marketing', 'sales'],
            'Health & Wellness': ['health', 'wellness', 'yoga', 'meditation', 'mental health', 'therapy', 'healthcare'],
            'News & Politics': ['news', 'politics', 'current events', 'journalism', 'media', 'political'],
        }
        
        # Score each niche based on keyword matches
        niche_scores = {}
        for niche, keywords in niche_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                niche_scores[niche] = score
        
        # Return highest scoring niche
        if niche_scores:
            best_niche = max(niche_scores, key=niche_scores.get)
            if DEBUG_MODE:
                print(f"  ✓ Niche (detected): {best_niche}")
            return best_niche
        
        return "General"
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting niche: {e}")
        return "General"


def get_channel_data(channel_name):
    """
    Scrape complete channel data from YouTube.
    
    Args:
        channel_name (str): YouTube channel name (e.g., '@valorant')
        
    Returns:
        dict: Channel data with all metrics
    """
    driver = setup_driver()
    
    try:
        print(f"\nFetching data for channel: {channel_name}")
        
        # Navigate to about page
        about_url = f'{YOUTUBE_BASE_URL}/{channel_name}{CHANNEL_ABOUT_PATH}'
        if not navigate_to_page(driver, about_url):
            return None
        
        # Wait for dynamic content
        wait_for_dynamic_content(driver)
        
        # Scroll to load content
        scroll_page(driver, 500)
        
        # Get page source for parsing
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract all metrics
        print("  Extracting channel metrics...")
        subscribers = extract_subscribers(driver)
        total_views = extract_total_views(driver)
        description = extract_description(driver, page_source)
        creation_date = extract_joined_date(driver)
        banner_url, profile_pic_url = extract_images(page_source)
        
        # Create initial channel data for niche extraction
        channel_data = {
            'channel_title': channel_name,
            'channel_description': description,
            'subscribers': subscribers,
            'total_views': total_views,
            'creation_date': creation_date,
            'banner_url': banner_url,
            'profile_pic_url': profile_pic_url,
            'video_count': 0,  # To be filled by video scraping
            'shorts_count': 0,  # To be filled by video scraping
            'last_posted_date': '',  # To be filled by video scraping
            'avg_recent_views': 0  # To be filled by video scraping
        }
        
        # Extract new metadata fields
        country = extract_channel_country(driver, page_source)
        language = extract_channel_language(page_source)
        niche = extract_channel_niche(channel_data, page_source)
        
        # Add new fields to channel data
        channel_data['country'] = country
        channel_data['default_language'] = language
        channel_data['niche'] = niche
        
        print(f"  ✓ Channel: {channel_name}")
        print(f"  ✓ Subscribers: {subscribers:,}")
        print(f"  ✓ Total Views: {total_views:,}")
        print(f"  ✓ Niche: {niche}")
        print(f"  ✓ Country: {country if country else 'Not specified'}")
        print(f"  ✓ Language: {language if language else 'Not specified'}")
        
        return channel_data
    
    except Exception as e:
        print(f"✗ Error in get_channel_data: {e}")
        return None
    finally:
        driver.quit()
