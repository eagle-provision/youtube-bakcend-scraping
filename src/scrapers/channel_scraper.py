"""
Data extraction module for channel information.
Handles scraping and parsing of YouTube channel data.
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import re
import time
from src.scrapers.browser import (
    setup_driver, navigate_to_page, wait_for_dynamic_content,
    scroll_page, find_element_safe, find_elements_safe
)
from src.config.config import (
    YOUTUBE_BASE_URL, CHANNEL_ABOUT_PATH, BROWSER_WAIT_TIME,
    XPATH_SUBSCRIBERS, XPATH_VIEWS, XPATH_JOINED_DATE,
    IMAGE_DOMAIN_YT3, DEBUG_MODE, DYNAMIC_CONTENT_WAIT
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
        # Try multiple methods to find subscriber count
        # Method 1: Standard XPath
        try:
            sub_elem = driver.find_element(By.XPATH, XPATH_SUBSCRIBERS)
            sub_text = sub_elem.text
            if sub_text and 'subscriber' in sub_text.lower():
                subscribers = extract_numeric_value(sub_text)
                if DEBUG_MODE:
                    print(f"  ✓ Subscribers: {subscribers:,}")
                return subscribers
        except:
            pass
        
        # Method 2: Try CSS selector
        try:
            sub_elem = driver.find_element(By.CSS_SELECTOR, 'yt-formatted-string#subscriber-count')
            sub_text = sub_elem.text
            if sub_text:
                subscribers = extract_numeric_value(sub_text)
                if DEBUG_MODE:
                    print(f"  ✓ Subscribers (CSS): {subscribers:,}")
                return subscribers
        except:
            pass
        
        # Method 3: Search in page source
        page_source = driver.page_source
        match = re.search(r'"subscriberCountText":{"simpleText":"([^"]+)"', page_source)
        if match:
            sub_text = match.group(1)
            subscribers = extract_numeric_value(sub_text)
            if DEBUG_MODE:
                print(f"  ✓ Subscribers (JSON): {subscribers:,}")
            return subscribers
        
        if DEBUG_MODE:
            print(f"  ⚠ Could not extract subscriber count")
        return 0
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting subscribers: {e}")
        return 0


def extract_total_views(driver, page_source):
    """
    Extract total channel views from the about page.
    Returns int with actual total views from YouTube's about page.
    """
    try:
        # Navigate to about page where total views are displayed
        current_url = driver.current_url
        
        # Parse the channel handle/ID from current URL
        if '/@' in current_url:
            # Format: https://www.youtube.com/@channelname/...
            channel_handle = current_url.split('/@')[1].split('/')[0]
            about_url = f"https://www.youtube.com/@{channel_handle}/about"
        elif '/channel/' in current_url:
            # Format: https://www.youtube.com/channel/CHANNEL_ID/...
            channel_id = current_url.split('/channel/')[1].split('/')[0]
            about_url = f"https://www.youtube.com/channel/{channel_id}/about"
        else:
            #logger.warning(f"Could not parse channel URL: {current_url}")
            if DEBUG_MODE:
                print(f"  ⚠ Could not parse channel URL")
            return 0
        
        # Navigate to about page
        if DEBUG_MODE:
            print(f"  → Navigating to about page for total views: {about_url}")
        driver.get(about_url)
        time.sleep(3)  # Wait for page to load
        
        about_source = driver.page_source
        
        # Method 1: Extract from JSON "viewCountText" field (most reliable)
        match = re.search(r'"viewCountText":\s*"([\d,]+)\s*views?"', about_source, re.IGNORECASE)
        if match:
            views_text = match.group(1)
            total_views = extract_numeric_value(views_text)
            if total_views > 0:
                if DEBUG_MODE:
                    print(f"  ✓ Total Views (about page - viewCountText): {total_views:,}")
                return total_views
        
        # Method 2: Extract from HTML table
        match = re.search(r'<td[^>]*>([\d,]+)\s*views?</td>', about_source, re.IGNORECASE)
        if match:
            views_text = match.group(1)
            total_views = extract_numeric_value(views_text)
            if total_views > 0:
                if DEBUG_MODE:
                    print(f"  ✓ Total Views (about page - HTML table): {total_views:,}")
                return total_views
        
        # Method 3: Look for viewCountText in metadata
        match = re.search(r'"viewCountText"[^}]*"content":\s*"([\d,]+)\s*views?"', about_source, re.IGNORECASE)
        if match:
            views_text = match.group(1)
            total_views = extract_numeric_value(views_text)
            if total_views > 0:
                if DEBUG_MODE:
                    print(f"  ✓ Total Views (about page - metadata): {total_views:,}")
                return total_views
        
        if DEBUG_MODE:
            print(f"  ⚠ Could not extract total views from about page")
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
        # Method 1: Standard XPath
        try:
            joined_elem = driver.find_element(By.XPATH, XPATH_JOINED_DATE)
            creation_date = joined_elem.text
            if DEBUG_MODE:
                print(f"  ✓ Joined date: {creation_date}")
            return creation_date
        except:
            pass
        
        # Method 2: Search in page source
        page_source = driver.page_source
        match = re.search(r'Joined\s+([^<]+)', page_source)
        if match:
            creation_date = f"Joined {match.group(1)}"
            if DEBUG_MODE:
                print(f"  ✓ Joined date (source): {creation_date}")
            return creation_date
        
        if DEBUG_MODE:
            print(f"  ⚠ Could not extract joined date")
        return ""
        
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


def extract_channel_id_and_url(channel_name, page_source):
    """
    Extract channel ID and construct full channel URL.
    
    Args:
        channel_name (str): Channel handle (e.g., '@vobane')
        page_source (str): Page HTML source
        
    Returns:
        tuple: (channel_id, channel_url)
    """
    try:
        # Extract channel ID from page source
        # Method 1: Look for channelId in JSON
        match = re.search(r'"channelId":"([^"]+)"', page_source)
        if match:
            channel_id = match.group(1)
            if DEBUG_MODE:
                print(f"  ✓ Channel ID: {channel_id}")
        else:
            # Method 2: Look for externalId
            match = re.search(r'"externalId":"([^"]+)"', page_source)
            if match:
                channel_id = match.group(1)
                if DEBUG_MODE:
                    print(f"  ✓ Channel ID (externalId): {channel_id}")
            else:
                channel_id = ""
                if DEBUG_MODE:
                    print(f"  ⚠ Could not extract channel ID")
        
        # Construct channel URL
        # Prefer handle format, fallback to ID format
        if channel_name.startswith('@'):
            channel_url = f"{YOUTUBE_BASE_URL}/{channel_name}"
        elif channel_id:
            channel_url = f"{YOUTUBE_BASE_URL}/channel/{channel_id}"
        else:
            channel_url = ""
        
        if DEBUG_MODE and channel_url:
            print(f"  ✓ Channel URL: {channel_url}")
        
        return channel_id, channel_url
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error extracting channel ID/URL: {e}")
        return "", ""


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


def extract_monetization_status(driver, page_source):
    """
    Placeholder for monetization status detection.
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        str: Placeholder status
    """
    return "To be determined"


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
        
        # Extract channel ID and URL first
        channel_id, channel_url = extract_channel_id_and_url(channel_name, page_source)
        
        subscribers = extract_subscribers(driver)
        total_views = extract_total_views(driver, page_source)
        description = extract_description(driver, page_source)
        creation_date = extract_joined_date(driver)
        banner_url, profile_pic_url = extract_images(page_source)
        country = extract_channel_country(driver, page_source)
        language = extract_channel_language(page_source)
        monetization_status = extract_monetization_status(driver, page_source)
        
        # Get current scrape date
        from datetime import datetime
        scrape_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create channel data with proper structure per PDF
        channel_data = {
            # Static fields
            'channel_id': channel_id,
            'channel_url': channel_url,
            'channel_handle': channel_name,
            'channel_title': channel_name.lstrip('@'),
            'channel_description': description,
            'creation_date': creation_date,
            'banner_url': banner_url,
            'profile_pic_url': profile_pic_url,
            'country': country,
            'default_language': language,
            'monetization_status': monetization_status,
            
            # Evolving fields (to be updated daily)
            'scrape_date': scrape_date,
            'subscribers': subscribers,
            'total_views': total_views,
            'video_count': 0,  # To be filled by video scraping
            'shorts_count': 0,  # To be filled by video scraping
            'total_content_count': 0,  # To be filled by video scraping
            'last_posted_date': '',  # To be filled by video scraping
            'daily_subscriber_change': 0,  # Computed from previous day
            'daily_views_change': 0,  # Computed from previous day
            'growth_rate': 0.0  # Computed from previous day
        }
        
        print(f"  ✓ Channel: {channel_name}")
        print(f"  ✓ Channel ID: {channel_id if channel_id else 'Not found'}")
        print(f"  ✓ Subscribers: {subscribers:,}")
        print(f"  ✓ Total Views: {total_views:,}")
        print(f"  ✓ Country: {country if country else 'Not specified'}")
        print(f"  ✓ Language: {language if language else 'Not specified'}")
        
        return channel_data
    
    except Exception as e:
        print(f"✗ Error in get_channel_data: {e}")
        return None
    finally:
        driver.quit()
