import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

def setup_driver():
    """Sets up Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_channel_data(channel_name):
    """Scrapes channel data from the about page."""
    driver = setup_driver()
    try:
        about_url = f'https://www.youtube.com/{channel_name}/about'
        driver.get(about_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  # Wait for dynamic content to load
        
        # Scroll down to load more content
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        # Try to wait for subscriber count
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'yt-formatted-string#subscriber-count')) > 0
            )
        except:
            pass  # Continue even if not found
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract subscribers
        subscribers = 0
        try:
            sub_elem = driver.find_element(By.XPATH, "//span[contains(text(), 'subscribers')]")
            sub_text = sub_elem.text
            print(f"Subscriber element text: '{sub_text}'")
            match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)', sub_text)
            if match:
                sub_str = match.group(1)
                print(f"Found subscriber text: {sub_str}")
                if 'K' in sub_str:
                    subscribers = int(float(sub_str.replace('K', '')) * 1000)
                elif 'M' in sub_str:
                    subscribers = int(float(sub_str.replace('M', '')) * 1000000)
                elif 'B' in sub_str:
                    subscribers = int(float(sub_str.replace('B', '')) * 1000000000)
                else:
                    subscribers = int(sub_str.replace(',', ''))
        except Exception as e:
            print(f"Error finding subscribers: {e}")
        
        # Extract total views - look for multiple elements as "X views" appears multiple times
        total_views = 0
        try:
            views_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'views')]")
            # Get all view counts and use the largest one (usually the total channel views)
            view_counts = []
            for views_elem in views_elements:
                views_text = views_elem.text
                match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)', views_text)
                if match:
                    views_str = match.group(1)
                    if 'K' in views_str:
                        count = int(float(views_str.replace('K', '')) * 1000)
                    elif 'M' in views_str:
                        count = int(float(views_str.replace('M', '')) * 1000000)
                    elif 'B' in views_str:
                        count = int(float(views_str.replace('B', '')) * 1000000000)
                    else:
                        count = int(views_str.replace(',', ''))
                    view_counts.append(count)
            if view_counts:
                total_views = max(view_counts)  # Get the largest view count
                print(f"Found views: {total_views}")
        except Exception as e:
            print(f"Error finding views: {e}")
        
        # Extract description - try to get full text from the about section
        description = ""
        try:
            page_source = driver.page_source
            
            # First, try to extract from the About section header/intro
            # The channel description is usually at the top of the about page
            import re as regex
            
            # Look for descriptions that contain "A 5v5 character-based"
            match = regex.search(r'"description":\s*"(A 5v5[^"\\]*(?:\\.[^"\\]*)*)"', page_source)
            if match:
                description = match.group(1)
                description = description.replace('\\n', '\n').replace('\\"', '"')
            
            # If not found, search for any structured description in the initial page data
            if not description or len(description) < 50:
                match = regex.search(r'"description":\s*"([^"\\]{80,}(?:\\.[^"\\]*)*)"', page_source[:8000])
                if match:
                    full_text = match.group(1)
                    # Filter to likely channel descriptions (not video transcripts)
                    if 'character-based' in full_text or 'tactical shooter' in full_text:
                        description = full_text
                        description = description.replace('\\n', '\n').replace('\\"', '"')
            
            # Fallback approach
            if not description or len(description) < 80:
                # Look for the description in meta tags
                desc_elem = soup.select_one('meta[name="description"]')
                if desc_elem:
                    description = desc_elem.get('content', '')
            
            print(f"Description: {description[:100]}...")
        except Exception as e:
            print(f"Error extracting description: {e}")
        
        # Extract joined date
        creation_date = ""
        try:
            joined_elem = driver.find_element(By.XPATH, "//span[contains(text(), 'Joined')]")
            creation_date = joined_elem.text
            print(f"Joined date: '{creation_date}'")
        except:
            print("Joined date not found")
        
        # Extract banner URL and profile picture
        banner_url = ""
        profile_pic_url = ""
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Look for images in specific sections
            all_imgs = soup.find_all('img')
            
            # Get all yt3 images (first is banner, subsequent might be profile)
            yt3_images = []
            
            for img in all_imgs:
                src = img.get('src', '')
                
                # Collect yt3 images
                if 'yt3.googleusercontent.com' in src and src not in yt3_images:
                    yt3_images.append(src)
            
            # The first yt3 image is the banner
            if len(yt3_images) > 0:
                banner_url = yt3_images[0]
                print(f"Banner found: {banner_url[:80]}...")
            
            # The second yt3 image (if exists) or look for different pattern for profile pic
            if len(yt3_images) > 1:
                profile_pic_url = yt3_images[1]
                print(f"Profile pic found: {profile_pic_url[:80]}...")
            
        except Exception as e:
            print(f"Error extracting images: {e}")
        
        return {
            'channel_title': channel_name,
            'channel_description': description,
            'subscribers': subscribers,
            'total_views': total_views,
            'creation_date': creation_date,
            'banner_url': banner_url,
            'profile_pic_url': profile_pic_url
        }
    finally:
        driver.quit()

def get_video_links(channel_url, max_videos=50):
    """Fetches video links and basic data from the channel's video page using Selenium."""
    driver = setup_driver()
    
    try:
        driver.get(channel_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "contents"))
        )
        # Scroll to load more videos
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        videos = []
        video_elements = soup.find_all('ytd-rich-item-renderer')
        for video in video_elements[:max_videos]:
            link_tag = video.find('a', href=re.compile(r'/watch\?v='))
            if link_tag:
                video_url = f"https://www.youtube.com{link_tag['href']}"
                title_tag = video.find('yt-formatted-string', {'id': 'video-title'})
                title = title_tag.text.strip() if title_tag else "No Title"
                
                metadata = video.find_all('span', {'class': 'inline-metadata-item'})
                views = 0
                upload_date = ""
                if len(metadata) >= 2:
                    views_text = metadata[0].text.strip()
                    match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)', views_text)
                    if match:
                        view_str = match.group(1)
                        if 'K' in view_str:
                            views = int(float(view_str.replace('K', '')) * 1000)
                        elif 'M' in view_str:
                            views = int(float(view_str.replace('M', '')) * 1000000)
                        elif 'B' in view_str:
                            views = int(float(view_str.replace('B', '')) * 1000000000)
                        else:
                            views = int(view_str.replace(',', ''))
                    upload_date = metadata[1].text.strip()
                
                videos.append({
                    'url': video_url,
                    'title': title,
                    'view_count': views,
                    'upload_date': upload_date
                })
        
        return videos
    finally:
        driver.quit()

def get_detailed_video_data(video_url):
    """Scrapes detailed data from a video page."""
    driver = setup_driver()
    try:
        driver.get(video_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  # Wait for dynamic content to load
        
        # Scroll to reveal like/comment buttons
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Description - extract full text from the video description element
        description = ""
        try:
            # The full description is usually in a collapsible element
            # Try to expand it first by looking for the description text
            desc_elem = soup.select_one('yt-formatted-string#description')
            
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # If not found, try other common selectors
            if not description:
                # Look for description-text class
                desc_elem = soup.select_one('div#description-inner')
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
            
            # Try to get from the page source JSON if visible
            if not description or len(description) < 50:
                # Search in page source for description content
                import re as regex
                page_source = driver.page_source
                # Look for description in JSON format
                match = regex.search(r'"description":{"simpleText":"([^"]+)"', page_source)
                if match:
                    description = match.group(1)
                    # Unescape JSON special characters
                    description = description.replace('\\n', '\n').replace('\\"', '"')
            
            # Fallback to meta tag
            if not description or len(description) < 50:
                desc_elem = soup.select_one('meta[name="description"]')
                if desc_elem:
                    description = desc_elem.get('content', '')
        except Exception as e:
            print(f"Note: Error extracting full description - {type(e).__name__}")
        
        # Duration - extract from meta tag (in seconds format PT...)
        duration = ""
        duration_seconds = 0
        try:
            dur_elem = soup.select_one('meta[itemprop="duration"]')
            if dur_elem:
                duration = dur_elem.get('content', '')
                # Convert PT format to seconds
                if duration.startswith('PT'):
                    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                    if match:
                        hours = int(match.group(1)) if match.group(1) else 0
                        minutes = int(match.group(2)) if match.group(2) else 0
                        seconds = int(match.group(3)) if match.group(3) else 0
                        duration_seconds = hours * 3600 + minutes * 60 + seconds
                        duration = f"{duration_seconds}"
        except Exception as e:
            print(f"Error extracting duration: {e}")
        
        # Likes - use Selenium to find the button by looking at page
        like_count = 0
        try:
            # Try to find the like button using different strategies
            like_buttons = driver.find_elements(By.XPATH, "//button[@aria-label]")
            for btn in like_buttons:
                aria_label = btn.get_attribute('aria-label')
                if aria_label and 'like' in aria_label.lower():
                    match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)', aria_label)
                    if match:
                        like_text = match.group(1)
                        if 'K' in like_text:
                            like_count = int(float(like_text.replace('K', '')) * 1000)
                        elif 'M' in like_text:
                            like_count = int(float(like_text.replace('M', '')) * 1000000)
                        elif 'B' in like_text:
                            like_count = int(float(like_text.replace('B', '')) * 1000000000)
                        else:
                            like_count = int(like_text.replace(',', ''))
                        if like_count > 0:
                            break
        except Exception as e:
            print(f"Note: Like count not found - {type(e).__name__}")
        
        # Comments - check page source for comment count
        comment_count = 0
        try:
            # Scroll to comments section
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            
            # Try to find comment count in the page source
            page_source = driver.page_source
            if '"commentCount":"' in page_source:
                match = re.search(r'"commentCount":"([\d]+)"', page_source)
                if match:
                    comment_count = int(match.group(1))
            
            # Fallback: try to find in the comments section header
            if comment_count == 0:
                comment_headers = driver.find_elements(By.XPATH, "//*[@id='comments']//h2")
                for header in comment_headers:
                    header_text = header.text.strip()
                    if 'comment' in header_text.lower():
                        match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)', header_text)
                        if match:
                            comm_text = match.group(1)
                            if 'K' in comm_text:
                                comment_count = int(float(comm_text.replace('K', '')) * 1000)
                            elif 'M' in comm_text:
                                comment_count = int(float(comm_text.replace('M', '')) * 1000000)
                            elif 'B' in comm_text:
                                comment_count = int(float(comm_text.replace('B', '')) * 1000000000)
                            else:
                                comment_count = int(comm_text.replace(',', ''))
                            break
        except Exception as e:
            print(f"Note: Comment count error - {type(e).__name__}")
        
        # Thumbnail URL
        thumbnail_url = ""
        try:
            thumb_elem = soup.select_one('meta[property="og:image"]')
            if thumb_elem:
                thumbnail_url = thumb_elem.get('content', '')
        except Exception as e:
            print(f"Error extracting thumbnail: {e}")
        
        return {
            'description': description,
            'duration': duration,
            'like_count': like_count,
            'comment_count': comment_count,
            'thumbnail_url': thumbnail_url
        }
    finally:
        driver.quit()


def scrape_channel(channel_name):
    """Scrapes channel and video data using scraping."""
    print(f"Fetching data for channel: {channel_name}")
    
    # Get channel data
    channel_data = get_channel_data(channel_name)
    if not channel_data:
        print("Failed to get channel data")
        return None, []
    
    print(f"Channel: {channel_data['channel_title']}")
    print(f"Subscribers: {channel_data['subscribers']}")
    print(f"Total Views: {channel_data['total_views']}")
    
    # Get basic video list
    channel_url = f'https://www.youtube.com/{channel_name}/videos'
    basic_videos = get_video_links(channel_url, max_videos=50)  # Limit to max videos
    
    videos = []
    for i, basic_video in enumerate(basic_videos):
        print(f"Processing video {i+1}/{len(basic_videos)}: {basic_video['title'][:50]}...")
        
        # Get detailed data
        detailed_data = get_detailed_video_data(basic_video['url'])
        
        # Combine data
        video_data = {**basic_video, **detailed_data}
        
        # Determine if short (rough estimate)
        is_short = '#shorts' in video_data['title'].lower() or (video_data['duration'] and 'PT' in video_data['duration'] and video_data['duration'].startswith('PT') and len(video_data['duration']) < 6)
        video_data['is_short'] = is_short
        
        videos.append(video_data)
        
        time.sleep(2)  # Delay between requests
    
    # Update channel data with calculated metrics
    if videos:
        channel_data['video_count'] = len(videos)  # Approximate
        channel_data['shorts_count'] = sum(1 for v in videos if v['is_short'])
        channel_data['last_posted_date'] = max(v['upload_date'] for v in videos if v['upload_date'])
        recent_videos = sorted(videos, key=lambda x: x.get('upload_date', ''), reverse=True)[:5]
        channel_data['avg_recent_views'] = sum(v['view_count'] for v in recent_videos) / len(recent_videos) if recent_videos else 0
    
    print(f"Videos processed: {len(videos)}")
    print(f"Shorts count: {channel_data.get('shorts_count', 0)}")
    
    return channel_data, videos

if __name__ == "__main__":
    # Replace 'channel_name' with the desired channel's name
    channel_name = '@NetworkChuck'
    
    channel_data, videos = scrape_channel(channel_name)
    
    if channel_data and videos:
        # Save to Excel with multiple sheets
        excel_file = 'youtube_analytics_scraped.xlsx'
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Channel data sheet
            pd.DataFrame([channel_data]).to_excel(writer, sheet_name='Channel_Data', index=False)
            # Videos data sheet
            pd.DataFrame(videos).to_excel(writer, sheet_name='Videos_Data', index=False)
        
        print(f"Saved channel data and {len(videos)} videos to {excel_file}")
    else:
        print("Failed to fetch data.")
