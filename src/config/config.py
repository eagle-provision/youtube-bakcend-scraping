# Configuration and Constants for YouTube Analytics Scraper

# URLs
YOUTUBE_BASE_URL = "https://www.youtube.com"
CHANNEL_ABOUT_PATH = "/about"
CHANNEL_VIDEOS_PATH = "/videos"
CHANNEL_SHORTS_PATH = "/shorts"

# Selenium Configuration
BROWSER_WAIT_TIME = 10  # seconds
DYNAMIC_CONTENT_WAIT = 5  # seconds
SCROLL_DELAY = 2  # seconds
REQUEST_DELAY = 2  # seconds between requests

# Scraping Parameters
MAX_VIDEOS_DEFAULT = 50
VIDEO_LIMIT_TEST = 1  # For testing purposes

# Chrome Options
CHROME_OPTIONS = [
    '--headless',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
]

# XPath Selectors
XPATH_SUBSCRIBERS = "//span[contains(text(), 'subscribers')]"
XPATH_VIEWS = "//span[contains(text(), 'views')]"
XPATH_JOINED_DATE = "//span[contains(text(), 'Joined')]"

# CSS Selectors
CSS_SUBSCRIBER_COUNT = 'yt-formatted-string#subscriber-count'

# Export Configuration
EXCEL_OUTPUT_FILE = 'data/processed/youtube_analytics_scraped.xlsx'
SHEET_CHANNEL_DATA = 'Channel_Data'
SHEET_VIDEOS_DATA = 'Videos_Data'

# Image Domains
IMAGE_DOMAIN_YT3 = 'yt3.googleusercontent.com'
IMAGE_DOMAIN_YT4 = 'yt4.googleusercontent.com'
IMAGE_DOMAIN_THUMBNAIL = 'i.ytimg.com'

# Data Field Definitions
CHANNEL_FIELDS = [
    'channel_title',
    'channel_description',
    'subscribers',
    'total_views',
    'creation_date',
    'banner_url',
    'profile_pic_url',
    'video_count',
    'shorts_count',
    'last_posted_date',
    'avg_recent_views',
    'niche',
    'country',
    'default_language'
]

VIDEO_FIELDS = [
    'url',
    'title',
    'view_count',
    'upload_date',
    'description',
    'duration',
    'like_count',
    'comment_count',
    'thumbnail_url',
    'is_short',
    'channel_niche',
    'channel_country',
    'channel_language'
]

# Logging
DEBUG_MODE = True
LOG_LEVEL = 'INFO'
