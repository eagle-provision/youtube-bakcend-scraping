"""
Data extraction module for video information.
Handles scraping and parsing of video data from YouTube.
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import re
import time
from src.scrapers.browser import (
    setup_driver, navigate_to_page, wait_for_dynamic_content,
    scroll_page, scroll_to_bottom, find_elements_safe
)
from src.config.config import (
    YOUTUBE_BASE_URL, CHANNEL_VIDEOS_PATH, CHANNEL_SHORTS_PATH, BROWSER_WAIT_TIME,
    REQUEST_DELAY, DEBUG_MODE
)
from src.scrapers.channel_scraper import extract_numeric_value


def calculate_total_views_from_pages(channel_url):
    """
    Calculate total channel views by scrolling through Videos and Shorts tabs
    and summing up all view counts from thumbnails.
    This is much faster than scraping detailed data for every video.
    
    Args:
        channel_url (str): Channel URL
        
    Returns:
        tuple: (total_videos_found, total_shorts_found, total_video_views, total_shorts_views, total_views)
    """
    print("\n  Calculating total views by scrolling through content pages...")
    
    # Calculate video views
    video_count, video_views = _get_all_view_counts_from_tab(channel_url, CHANNEL_VIDEOS_PATH, "Videos")
    
    # Calculate shorts views
    shorts_count, shorts_views = _get_all_view_counts_from_tab(channel_url, CHANNEL_SHORTS_PATH, "Shorts")
    
    total_views = video_views + shorts_views
    
    print(f"  ✓ Total channel views calculated: {total_views:,}")
    print(f"    - Videos: {video_count} videos with {video_views:,} views")
    print(f"    - Shorts: {shorts_count} shorts with {shorts_views:,} views")
    
    return video_count, shorts_count, video_views, shorts_views, total_views


def _get_all_view_counts_from_tab(channel_url, tab_path, tab_name):
    """
    Scroll through a tab (Videos or Shorts) and extract all view counts.
    
    Args:
        channel_url (str): Channel URL
        tab_path (str): Tab path (/videos or /shorts)
        tab_name (str): Tab name for logging
        
    Returns:
        tuple: (item_count, total_views)
    """
    driver = setup_driver()
    
    try:
        tab_url = f'{channel_url}{tab_path}'
        if not navigate_to_page(driver, tab_url, max_retries=2):
            print(f"    ✗ Failed to navigate to {tab_name} tab after retries")
            return 0, 0
        
        wait_for_dynamic_content(driver)
        
        # Scroll to load all content
        # Keep scrolling until no new content loads
        previous_count = 0
        no_change_count = 0
        max_scrolls = 50  # Safety limit
        
        for i in range(max_scrolls):
            scroll_to_bottom(driver)
            time.sleep(1.5)
            
            # Check if new content loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            current_count = len(soup.find_all('ytd-rich-item-renderer'))
            
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= 3:  # Stop if no new content after 3 scrolls
                    break
            else:
                no_change_count = 0
            
            previous_count = current_count
            
            if DEBUG_MODE and i % 5 == 0:
                print(f"    Scrolling {tab_name} tab... found {current_count} items")
        
        # Extract all view counts from the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Get all items (this is the actual count we found during scrolling)
        all_items = soup.find_all('ytd-rich-item-renderer')
        actual_item_count = len(all_items)
        
        # Debug: Sample HTML from first item
        if DEBUG_MODE and tab_name == "Shorts":
            if all_items:
                print(f"\n    DEBUG: Sample {tab_name} HTML structure:")
                for i, item in enumerate(all_items[:1], 1):
                    print(f"    Sample {i} text: {item.get_text(separator=' ', strip=True)[:200]}...")
        
        # Extract view counts item by item (most reliable method)
        view_counts = []
        for idx, item in enumerate(all_items):
            item_html = str(item)
            item_text = item.get_text(separator=' ', strip=True)
            view_count = 0
            
            # Try multiple extraction methods for each item
            # Method 1: yt-core-attributed-string (primary for shorts)
            if not view_count:
                view_span = item.find('span', class_='yt-core-attributed-string')
                if view_span:
                    text = view_span.get_text(strip=True)
                    if 'view' in text.lower():
                        view_count = extract_numeric_value(text)
            
            # Method 2: inline-metadata-item (primary for videos)
            if not view_count:
                metadata = item.find('span', class_='inline-metadata-item')
                if metadata:
                    text = metadata.get_text(strip=True)
                    if 'view' in text.lower():
                        view_count = extract_numeric_value(text)
            
            # Method 3: metadata-line div
            if not view_count:
                meta_line = item.find('div', id='metadata-line')
                if meta_line:
                    text = meta_line.get_text(strip=True)
                    matches = re.findall(r'([\d.]+[KMB]?)\s*views?', text, re.IGNORECASE)
                    if matches:
                        view_count = extract_numeric_value(matches[0])
            
            # Method 4: Regex search in item text
            if not view_count:
                # Look for patterns like "11K views" or "1,234 views"
                matches = re.findall(r'([\d,]+\.?\d*[KMB]?)\s*views?', item_text, re.IGNORECASE)
                if matches:
                    view_count = extract_numeric_value(matches[0])
            
            # Method 5: aria-label attribute
            if not view_count:
                elements_with_aria = item.find_all(attrs={'aria-label': True})
                for elem in elements_with_aria:
                    aria_text = elem.get('aria-label', '')
                    matches = re.findall(r'([\d,]+\.?\d*[KMB]?)\s*views?', aria_text, re.IGNORECASE)
                    if matches:
                        view_count = extract_numeric_value(matches[0])
                        break
            
            # Method 6: Search in JSON embedded in HTML
            if not view_count:
                json_matches = re.findall(r'"viewCountText".*?"simpleText":\s*"([^"]+)"', item_html)
                for match in json_matches:
                    if 'view' in match.lower():
                        view_count = extract_numeric_value(match)
                        break
            
            if view_count > 0:
                view_counts.append(view_count)
        
        if DEBUG_MODE and tab_name == "Shorts":
            print(f"    Extracted view counts from {len(view_counts)}/{actual_item_count} items")
            if len(view_counts) < actual_item_count:
                print(f"    WARNING: Missing view counts for {actual_item_count - len(view_counts)} items")
        
        total_views = sum(view_counts)
        
        print(f"    ✓ {tab_name}: Found {actual_item_count} items with total {total_views:,} views")
        
        return actual_item_count, total_views
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ✗ Error calculating {tab_name} views: {e}")
        return 0, 0
    finally:
        driver.quit()


def get_total_videos_count(channel_url):
    """
    Get the actual total number of videos from the channel's Videos tab.
    
    Args:
        channel_url (str): Channel URL
        
    Returns:
        int: Total number of videos on the channel
    """
    driver = setup_driver()
    
    try:
        videos_url = f'{channel_url}{CHANNEL_VIDEOS_PATH}'
        if not navigate_to_page(driver, videos_url):
            return 0
        
        wait_for_dynamic_content(driver)
        
        # Method 1: Look for the tab count (e.g., "Videos 150")
        try:
            # Find the Videos tab element that shows the count
            tabs = driver.find_elements(By.CSS_SELECTOR, 'yt-tab-shape')
            for tab in tabs:
                text = tab.text.strip()
                if 'video' in text.lower() and not 'short' in text.lower():
                    # Extract number from text like "Videos 150"
                    count = extract_numeric_value(text)
                    if count > 0:
                        if DEBUG_MODE:
                            print(f"  ✓ Total videos count from tab: {count:,}")
                        return count
        except:
            pass
        
        # Method 2: Count from page source JSON
        page_source = driver.page_source
        match = re.search(r'"videosCountText":{"runs":\[{"text":"([^"]+)"', page_source)
        if match:
            count_text = match.group(1)
            count = extract_numeric_value(count_text)
            if count > 0:
                if DEBUG_MODE:
                    print(f"  ✓ Total videos count from JSON: {count:,}")
                return count
        
        # Method 3: Scroll and count all elements (fallback)
        # Keep scrolling until no new content loads
        previous_count = 0
        no_change_count = 0
        max_scrolls = 100  # Safety limit
        
        for i in range(max_scrolls):
            scroll_to_bottom(driver)
            time.sleep(1.5)
            
            # Check if new content loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            video_elements = soup.find_all('ytd-rich-item-renderer')
            current_count = len(video_elements)
            
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= 3:  # Stop if no new content after 3 scrolls
                    break
            else:
                no_change_count = 0
            
            previous_count = current_count
            
            if DEBUG_MODE and i % 10 == 0 and i > 0:
                print(f"    Scrolling videos... found {current_count} items")
        
        count = previous_count
        
        if DEBUG_MODE:
            print(f"  ✓ Total videos count from elements: {count:,}")
        
        return count
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error getting total videos count: {e}")
        return 0
    finally:
        driver.quit()


def get_total_shorts_count(channel_url):
    """
    Get the actual total number of shorts from the channel's Shorts tab.
    
    Args:
        channel_url (str): Channel URL
        
    Returns:
        int: Total number of shorts on the channel
    """
    driver = setup_driver()
    
    try:
        shorts_url = f'{channel_url}{CHANNEL_SHORTS_PATH}'
        if not navigate_to_page(driver, shorts_url):
            return 0
        
        wait_for_dynamic_content(driver)
        
        # Method 1: Look for the tab count (e.g., "Shorts 45")
        try:
            # Find the Shorts tab element that shows the count
            tabs = driver.find_elements(By.CSS_SELECTOR, 'yt-tab-shape')
            for tab in tabs:
                text = tab.text.strip()
                if 'short' in text.lower():
                    # Extract number from text like "Shorts 45"
                    count = extract_numeric_value(text)
                    if count > 0:
                        if DEBUG_MODE:
                            print(f"  ✓ Total shorts count from tab: {count:,}")
                        return count
        except:
            pass
        
        # Method 2: Count from page source JSON
        page_source = driver.page_source
        match = re.search(r'"shortsCountText":{"runs":\[{"text":"([^"]+)"', page_source)
        if match:
            count_text = match.group(1)
            count = extract_numeric_value(count_text)
            if count > 0:
                if DEBUG_MODE:
                    print(f"  ✓ Total shorts count from JSON: {count:,}")
                return count
        
        # Method 3: Scroll and count all elements (fallback)
        # Keep scrolling until no new content loads
        previous_count = 0
        no_change_count = 0
        max_scrolls = 200  # Higher limit for shorts since there can be many more
        
        for i in range(max_scrolls):
            scroll_to_bottom(driver)
            time.sleep(1.5)
            
            # Check if new content loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            shorts_elements = soup.find_all('ytd-rich-item-renderer')
            current_count = len(shorts_elements)
            
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= 3:  # Stop if no new content after 3 scrolls
                    break
            else:
                no_change_count = 0
            
            previous_count = current_count
            
            if DEBUG_MODE and i % 10 == 0 and i > 0:
                print(f"    Scrolling shorts... found {current_count} items")
        
        count = previous_count
        
        if DEBUG_MODE:
            print(f"  ✓ Total shorts count from elements: {count:,}")
        
        return count
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"  ✗ Error getting total shorts count: {e}")
        return 0
    finally:
        driver.quit()


def get_video_links(channel_url, max_videos=50, total_videos_count=None):
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
                
                # Extract video ID from URL
                video_id_match = re.search(r'v=([A-Za-z0-9_-]+)', video_url)
                video_id = video_id_match.group(1) if video_id_match else ""
                
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
                    'video_id': video_id,
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


def get_shorts_links(channel_url, max_shorts=50, total_shorts_count=None):
    """
    Scrape shorts from the dedicated channel shorts tab.
    
    Args:
        channel_url (str): Channel URL
        max_shorts (int): Maximum shorts to scrape
        total_shorts_count (int): Actual total shorts on channel (if known)
        
    Returns:
        list: List of shorts objects with basic info
    """
    driver = setup_driver()
    
    try:
        print(f"\n  Fetching shorts list from dedicated tab...")
        
        # If we know the total count, adjust our target
        if total_shorts_count:
            target_count = min(max_shorts, total_shorts_count)
            print(f"  Target: {target_count} shorts (total on channel: {total_shorts_count})")
        else:
            target_count = max_shorts
        
        shorts_url = f'{channel_url}{CHANNEL_SHORTS_PATH}'
        if not navigate_to_page(driver, shorts_url):
            print("  ⚠ Could not navigate to shorts tab")
            return []
        
        wait_for_dynamic_content(driver)
        
        # Scroll to load more shorts - adjust scrolls based on target
        # Estimate: ~30 shorts loaded per page, so scroll enough times
        scroll_count = max(5, (target_count // 30) + 2)
        scroll_count = min(scroll_count, 15)  # Cap at 15 scrolls
        
        for i in range(scroll_count):
            scroll_to_bottom(driver)
            time.sleep(1)
            
            # Check if we've loaded enough
            if i > 0 and i % 3 == 0:
                soup_check = BeautifulSoup(driver.page_source, 'html.parser')
                loaded_links = soup_check.find_all('a', href=re.compile(r'/shorts/'))
                loaded = len(set(link.get('href', '') for link in loaded_links))
                if loaded >= target_count:
                    if DEBUG_MODE:
                        print(f"  Loaded {loaded} shorts, stopping scroll")
                    break
        
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
                    'video_id': shorts_href.split('/shorts/')[-1].split('?')[0],  # Extract video ID from URL
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
