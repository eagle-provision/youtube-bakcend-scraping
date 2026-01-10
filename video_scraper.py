"""
Data extraction module for video information.
Handles scraping and parsing of video data from YouTube.
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import re
import time
from browser import (
    setup_driver, navigate_to_page, wait_for_dynamic_content,
    scroll_page, scroll_to_bottom, find_elements_safe
)
from config import (
    YOUTUBE_BASE_URL, CHANNEL_VIDEOS_PATH, CHANNEL_SHORTS_PATH, BROWSER_WAIT_TIME,
    REQUEST_DELAY, DEBUG_MODE
)
from channel_scraper import extract_numeric_value


def get_video_links(channel_url, max_videos=50):
    """
    Scrape video list and basic metadata from channel videos page.
    
    Args:
        channel_url (str): Channel URL
        max_videos (int): Maximum videos to scrape
        
    Returns:
        list: List of video objects with basic info
    """
    driver = setup_driver()
    
    try:
        print(f"\n  Fetching video list...")
        
        videos_url = f'{channel_url}{CHANNEL_VIDEOS_PATH}'
        if not navigate_to_page(driver, videos_url):
            return []
        
        wait_for_dynamic_content(driver)
        
        # Scroll to load more videos
        for _ in range(5):
            scroll_to_bottom(driver)
            time.sleep(1)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        videos = []
        video_elements = soup.find_all('ytd-rich-item-renderer')
        
        print(f"  Found {len(video_elements)} video elements")
        
        for video in video_elements[:max_videos]:
            try:
                # Extract URL
                link_tag = video.find('a', href=re.compile(r'/watch\?v='))
                if not link_tag:
                    continue
                
                video_url = f"{YOUTUBE_BASE_URL}{link_tag['href']}"
                
                # Extract title
                title_tag = video.find('yt-formatted-string', {'id': 'video-title'})
                title = title_tag.text.strip() if title_tag else "No Title"
                
                # Check if it's a short (usually indicated by "Shorts" badge or URL pattern)
                is_short_badge = 'shorts' in video_url.lower()
                
                # Extract view count and upload date
                metadata = video.find_all('span', {'class': 'inline-metadata-item'})
                views = 0
                upload_date = ""
                
                if len(metadata) >= 2:
                    views_text = metadata[0].text.strip()
                    views = extract_numeric_value(views_text)
                    upload_date = metadata[1].text.strip()
                
                videos.append({
                    'url': video_url,
                    'title': title,
                    'view_count': views,
                    'upload_date': upload_date,
                    'is_short': is_short_badge  # Initial detection based on URL
                })
                
            except Exception as e:
                if DEBUG_MODE:
                    print(f"    ✗ Error parsing video: {e}")
                continue
        
        if DEBUG_MODE:
            print(f"  ✓ Extracted {len(videos)} videos from list")
        
        return videos
    
    except Exception as e:
        print(f"  ✗ Error in get_video_links: {e}")
        return []
    finally:
        driver.quit()


def get_shorts_links(channel_url, max_shorts=50):
    """
    Scrape shorts from the dedicated channel shorts tab.
    
    Args:
        channel_url (str): Channel URL
        max_shorts (int): Maximum shorts to scrape
        
    Returns:
        list: List of shorts objects with basic info
    """
    driver = setup_driver()
    
    try:
        print(f"\n  Fetching shorts list from dedicated tab...")
        
        shorts_url = f'{channel_url}{CHANNEL_SHORTS_PATH}'
        if not navigate_to_page(driver, shorts_url):
            print("  ⚠ Could not navigate to shorts tab")
            return []
        
        wait_for_dynamic_content(driver)
        
        # Scroll to load more shorts
        for _ in range(5):
            scroll_to_bottom(driver)
            time.sleep(1)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Strategy: Create a map of shorts URLs to their best title
        shorts_map = {}  # URL -> {title, views, upload_date}
        
        # Find ALL links that contain /shorts/
        all_links = soup.find_all('a', href=re.compile(r'/shorts/'))
        
        print(f"  Found {len(all_links)} short links")
        
        # Process all links to build map of unique shorts with best titles
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Get title from link text or title attribute
            text = link.get_text(strip=True)
            title_attr = link.get('title', '')
            title = title_attr if title_attr else text
            
            # Store unique shorts, preferring links with titles
            if href not in shorts_map:
                shorts_map[href] = {'title': title, 'views': 0, 'upload_date': ''}
            elif title and not shorts_map[href]['title']:
                # Update if we find a better title
                shorts_map[href]['title'] = title
        
        # Now build final shorts list with limited results
        shorts = []
        for shorts_href, data in list(shorts_map.items())[:max_shorts]:
            try:
                video_url = f"{YOUTUBE_BASE_URL}{shorts_href}"
                title = data['title'] if data['title'] else "No Title"
                
                # Try to find view count and upload date from the page
                # Look for any short element containing this URL
                for link in all_links:
                    if link.get('href') == shorts_href:
                        # Get parent element to search for metadata
                        parent = link.parent
                        while parent and parent.name != 'ytd-rich-item-renderer':
                            parent = parent.parent
                        
                        if parent:
                            # Extract view count from text
                            text_content = parent.get_text(strip=True)
                            views_match = re.search(r'([\d.]+[KMB]?)\s*views', text_content)
                            if views_match:
                                data['views'] = extract_numeric_value(views_match.group(1))
                            
                            # Try to extract upload date
                            metadata = parent.find_all('span', {'class': 'inline-metadata-item'})
                            if len(metadata) >= 2:
                                data['upload_date'] = metadata[1].text.strip()
                        break
                
                shorts.append({
                    'url': video_url,
                    'title': title,
                    'view_count': data['views'],
                    'upload_date': data['upload_date'],
                    'is_short': True  # Explicitly mark as short since it came from shorts tab
                })
                
            except Exception as e:
                if DEBUG_MODE:
                    print(f"    ✗ Error processing short {shorts_href}: {e}")
                continue
        
        if DEBUG_MODE:
            print(f"  ✓ Extracted {len(shorts)} unique shorts from tab")
        
        return shorts
    
    except Exception as e:
        print(f"  ✗ Error in get_shorts_links: {e}")
        return []
    finally:
        driver.quit()


def duration_to_seconds(duration_str):
    """
    Convert ISO 8601 duration format (PT3M29S) to seconds.
    
    Args:
        duration_str (str): Duration in PT format
        
    Returns:
        int: Duration in seconds
    """
    try:
        if not duration_str or not duration_str.startswith('PT'):
            return 0
        
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error converting duration: {e}")
        return 0


def extract_video_description(driver, page_source):
    """
    Extract full video description.
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        str: Video description
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try to extract from JSON in page source
        match = re.search(r'"description":{"simpleText":"([^"]+)"', page_source)
        if match:
            description = match.group(1)
            description = description.replace('\\n', '\n').replace('\\"', '"')
            return description
        
        # Try to find in page elements
        desc_elem = soup.select_one('yt-formatted-string#description')
        if desc_elem:
            return desc_elem.get_text(strip=True)
        
        # Fallback to meta tag
        desc_elem = soup.select_one('meta[name="description"]')
        if desc_elem:
            return desc_elem.get('content', '')
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting description: {e}")
        return ""


def extract_video_duration(page_source):
    """
    Extract video duration in seconds.
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        str: Duration as string (in seconds)
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        dur_elem = soup.select_one('meta[itemprop="duration"]')
        
        if dur_elem:
            duration = dur_elem.get('content', '')
            seconds = duration_to_seconds(duration)
            return str(seconds)
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting duration: {e}")
        return ""


def extract_video_likes(driver):
    """
    Extract video like count.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        int: Like count
    """
    try:
        like_buttons = driver.find_elements(By.XPATH, "//button[@aria-label]")
        
        for btn in like_buttons:
            aria_label = btn.get_attribute('aria-label')
            if aria_label and 'like' in aria_label.lower():
                return extract_numeric_value(aria_label)
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting likes: {e}")
        return 0


def extract_video_comments(driver, page_source):
    """
    Extract video comment count.
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        int: Comment count
    """
    try:
        # Try to find in page source JSON
        match = re.search(r'"commentCount":"([\d]+)"', page_source)
        if match:
            return int(match.group(1))
        
        # Try to find in page elements
        comment_headers = driver.find_elements(By.XPATH, "//*[@id='comments']//h2")
        for header in comment_headers:
            header_text = header.text.strip()
            if 'comment' in header_text.lower():
                return extract_numeric_value(header_text)
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting comments: {e}")
        return 0


def extract_video_thumbnail(page_source):
    """
    Extract video thumbnail URL.
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        str: Thumbnail URL
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        thumb_elem = soup.select_one('meta[property="og:image"]')
        
        if thumb_elem:
            return thumb_elem.get('content', '')
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting thumbnail: {e}")
        return ""


# Shorts-specific extraction functions
def extract_shorts_description(driver, page_source):
    """
    Extract description from shorts page.
    For shorts, the title IS the description (they don't have separate descriptions).
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        str: Shorts description (the video title)
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # For shorts, use the title as description
        # Pattern 1: Look for title in videoDetails
        match = re.search(r'"videoDetails":{[^}]*?"title":"([^"]*)"', page_source)
        if match:
            title = match.group(1)
            title = title.replace('\\n', '\n').replace('\\"', '"')
            return title
        
        # Pattern 2: Try OG title meta tag
        title_elem = soup.select_one('meta[property="og:title"]')
        if title_elem:
            return title_elem.get('content', '')
        
        # Pattern 3: Try regular title tag
        title_elem = soup.select_one('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove " - YouTube" suffix if present
            if ' - YouTube' in title_text:
                title_text = title_text.replace(' - YouTube', '')
            return title_text
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts description: {e}")
        return ""


def extract_shorts_duration(page_source):
    """
    Extract shorts duration (usually very short, under 60 seconds).
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        str: Duration in seconds
    """
    try:
        # Shorts typically have duration in meta tags
        soup = BeautifulSoup(page_source, 'html.parser')
        dur_elem = soup.select_one('meta[itemprop="duration"]')
        
        if dur_elem:
            duration = dur_elem.get('content', '')
            seconds = duration_to_seconds(duration)
            return str(seconds)
        
        # Search in JSON for lengthSeconds
        match = re.search(r'"lengthSeconds":"?(\d+)"?', page_source)
        if match:
            return match.group(1)
        
        # Search for videoDetails.lengthSeconds
        match = re.search(r'"videoDetails":{[^}]*?"lengthSeconds":"(\d+)"', page_source)
        if match:
            return match.group(1)
        
        return "0"
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts duration: {e}")
        return "0"
        return "0"


def extract_shorts_likes(driver):
    """
    Extract like count from shorts page.
    Shorts like buttons show count in aria-label (e.g., "100 thousand likes").
    
    Args:
        driver: WebDriver instance
        
    Returns:
        int: Like count
    """
    try:
        # Find all buttons with aria-label
        like_buttons = driver.find_elements(By.XPATH, "//button[@aria-label]")
        
        for btn in like_buttons:
            aria_label = btn.get_attribute('aria-label')
            if aria_label and ('like' in aria_label.lower()):
                # Extract count from aria-label
                # Handles: "100 thousand likes", "100 thousand other people", etc.
                count = extract_numeric_value(aria_label)
                if count > 0:
                    return count
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts likes: {e}")
        return 0


def extract_shorts_comments(driver, page_source):
    """
    Extract comment count from shorts page.
    Looks for comment button with count (e.g., "View 551 comments").
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        int: Comment count
    """
    try:
        # Try to find comment count in page source JSON
        # Pattern 1: commentCount field
        match = re.search(r'"commentCount":"?(\d+)"?', page_source)
        if match:
            return int(match.group(1))
        
        # Pattern 2: engagementMetrics comment count
        match = re.search(r'"engagementMetrics":{[^}]*?"commentCount":{[^}]*?"simpleText":"(\d+)', page_source)
        if match:
            return int(match.group(1))
        
        # Try to find comment button in UI
        comment_buttons = driver.find_elements(By.XPATH, "//button[@aria-label]")
        for btn in comment_buttons:
            aria_label = btn.get_attribute('aria-label')
            if aria_label and 'comment' in aria_label.lower():
                count = extract_numeric_value(aria_label)
                if count > 0:
                    return count
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts comments: {e}")
        return 0


def extract_shorts_views(driver, page_source):
    """
    Extract view count from shorts page.
    
    Args:
        driver: WebDriver instance
        page_source (str): Page HTML source
        
    Returns:
        int: View count
    """
    try:
        # Try to find view count in JSON data
        match = re.search(r'"viewCount":{"simpleText":"([^"]+)"', page_source)
        if match:
            views_text = match.group(1)
            return extract_numeric_value(views_text)
        
        # Alternative pattern
        match = re.search(r'"viewCount":"([^"]+)"', page_source)
        if match:
            views_text = match.group(1)
            return extract_numeric_value(views_text)
        
        # Look for view count in text elements
        try:
            view_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'views')]")
            for elem in view_elements:
                text = elem.text.strip()
                if 'views' in text.lower():
                    return extract_numeric_value(text)
        except:
            pass
        
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts views: {e}")
        return 0


def extract_shorts_thumbnail(page_source):
    """
    Extract thumbnail URL from shorts page.
    
    Args:
        page_source (str): Page HTML source
        
    Returns:
        str: Thumbnail URL
    """
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try og:image meta tag
        thumb_elem = soup.select_one('meta[property="og:image"]')
        if thumb_elem:
            return thumb_elem.get('content', '')
        
        # Try twitter:image meta tag
        thumb_elem = soup.select_one('meta[property="twitter:image"]')
        if thumb_elem:
            return thumb_elem.get('content', '')
        
        return ""
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error extracting shorts thumbnail: {e}")
        return ""


def get_detailed_video_data(video_url):
    """
    Scrape detailed data from individual video page.
    Handles both regular videos (/watch?v=) and shorts (/shorts/).
    
    Args:
        video_url (str): YouTube video URL
        
    Returns:
        dict: Detailed video data
    """
    driver = setup_driver()
    
    try:
        if not navigate_to_page(driver, video_url):
            return {}
        
        wait_for_dynamic_content(driver)
        scroll_page(driver, 500)
        scroll_to_bottom(driver)
        time.sleep(1)
        
        page_source = driver.page_source
        
        # Check if this is a short or regular video
        is_short = '/shorts/' in video_url.lower()
        
        if is_short:
            # Extract data specifically for shorts
            description = extract_shorts_description(driver, page_source)
            duration = extract_shorts_duration(page_source)
            like_count = extract_shorts_likes(driver)
            comment_count = extract_shorts_comments(driver, page_source)
            thumbnail_url = extract_shorts_thumbnail(page_source)
            view_count = extract_shorts_views(driver, page_source)
            
            # Extract upload date for shorts
            upload_date = ""
            date_match = re.search(r'"uploadDate":"([^"]+)"', page_source)
            if date_match:
                upload_date = date_match.group(1)
        else:
            # Extract data for regular videos
            description = extract_video_description(driver, page_source)
            duration = extract_video_duration(page_source)
            like_count = extract_video_likes(driver)
            comment_count = extract_video_comments(driver, page_source)
            thumbnail_url = extract_video_thumbnail(page_source)
            
            # Extract upload date for regular videos
            upload_date = ""
            date_match = re.search(r'"uploadDate":"([^"]+)"', page_source)
            if date_match:
                upload_date = date_match.group(1)
        
        detailed_data = {
            'description': description,
            'duration': duration,
            'like_count': like_count,
            'comment_count': comment_count,
            'thumbnail_url': thumbnail_url,
            'upload_date': upload_date
        }
        
        # Add view_count for shorts (regular videos get it from list page)
        if is_short:
            detailed_data['view_count'] = view_count
        
        return detailed_data
    
    except Exception as e:
        print(f"  ✗ Error in get_detailed_video_data: {e}")
        return {}
    finally:
        driver.quit()
