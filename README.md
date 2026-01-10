# YouTube Multi-Channel Analytics Scraper

A comprehensive Python scraper for extracting YouTube channel analytics including **niche/category**, **country**, and **default language** metadata for channels, videos, and shorts.

## 🚀 Features

### Channel Metadata Extraction
- **Niche/Category**: Automatically detects channel niche (Gaming, Tech, Education, etc.)
- **Country**: Extracts channel country/location if available
- **Default Language**: Identifies the primary language of the channel
- Subscriber count, total views, creation date
- Channel description, banner, and profile picture URLs

### Video & Shorts Analysis
- Scrapes both regular videos and YouTube Shorts separately
- Video metrics: views, likes, comments, upload date, duration
- **Inherited metadata**: Each video/short includes the channel's niche, country, and language
- Thumbnail URLs and descriptions

### Multi-Channel Support
- Scrape single or multiple channels in one run
- Consolidated export with all channels, videos, and shorts
- Rate limiting to avoid API blocks
- Progress tracking for each channel

## 📋 Requirements

```bash
pip install -r requirements.txt
```

**Dependencies:**
- selenium==4.15.2
- beautifulsoup4==4.12.2
- pandas==2.1.3
- openpyxl==3.11.0
- webdriver-manager==4.0.1
- requests==2.31.0
- python-dotenv==1.0.0

## 🎯 Quick Start

### Single Channel Scraping

```python
from scraper import main

# Scrape a single channel
main(
    channel_name='@mkbhd',
    max_videos=50,
    max_shorts=50
)
```

### Multiple Channels Scraping

```python
from scraper import main

# Scrape multiple channels
channels = [
    '@mkbhd',
    '@valorant',
    '@tasty',
    '@nasa',
    '@vogue'
]

main(
    channel_list=channels,
    max_videos=50,
    max_shorts=50
)
```

### Using the Example Script

```bash
python run_multi_channel.py
```

## 📊 Output Structure

### Excel Export Files

**Single Channel Mode:**
- `youtube_analytics_scraped.xlsx`
  - Sheet 1: `Channel_Data` - Channel information with niche, country, language
  - Sheet 2: `Videos_Data` - Regular videos with channel metadata
  - Sheet 3: `Shorts_Data` - Shorts with channel metadata

**Multi-Channel Mode:**
- `multi_channel_youtube_analytics_scraped.xlsx`
  - Sheet 1: `All_Channels` - All scraped channels
  - Sheet 2: `All_Videos` - Videos from all channels
  - Sheet 3: `All_Shorts` - Shorts from all channels

### Data Fields

#### Channel Data
- `channel_title` - Channel name
- `channel_description` - Full description
- `subscribers` - Subscriber count
- `total_views` - Total channel views
- `creation_date` - When channel was created
- `banner_url` - Banner image URL
- `profile_pic_url` - Profile picture URL
- `video_count` - Number of regular videos
- `shorts_count` - Number of shorts
- `last_posted_date` - Most recent upload
- `avg_recent_views` - Average views of last 5 videos
- **`niche`** - Channel category (Gaming, Tech, Education, etc.)
- **`country`** - Channel country/location
- **`default_language`** - Primary language

#### Video/Shorts Data
- `url` - Video URL
- `title` - Video title
- `view_count` - View count
- `upload_date` - Upload date
- `description` - Video description
- `duration` - Duration (MM:SS format)
- `like_count` - Number of likes
- `comment_count` - Number of comments
- `thumbnail_url` - Thumbnail URL
- `is_short` - Boolean (True for shorts)
- **`channel_niche`** - Inherited from channel
- **`channel_country`** - Inherited from channel
- **`channel_language`** - Inherited from channel

## 🎨 Niche Detection

The scraper automatically categorizes channels into the following niches based on keywords in title and description:

- **Gaming** - Gaming, esports, gameplay
- **Technology** - Tech reviews, gadgets, software
- **Education** - Tutorials, courses, learning
- **Entertainment** - Comedy, vlogs, lifestyle
- **Music** - Music, songs, artists
- **Sports** - Fitness, sports, athletics
- **Beauty & Fashion** - Makeup, fashion, style
- **Food & Cooking** - Recipes, cooking, cuisine
- **Travel** - Adventure, tourism, destinations
- **Business** - Entrepreneurship, finance, marketing
- **Health & Wellness** - Health, yoga, wellness
- **News & Politics** - News, current events, politics
- **General** - Default if no clear category

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Scraping Parameters
MAX_VIDEOS_DEFAULT = 50
REQUEST_DELAY = 2  # seconds between requests

# Browser Settings
BROWSER_WAIT_TIME = 10
CHROME_OPTIONS = [
    '--headless',  # Run without GUI
    '--no-sandbox',
    '--disable-dev-shm-usage'
]

# Debug Mode
DEBUG_MODE = True  # Set to False for less verbose output
```

## 📝 Usage Examples

### Example 1: Gaming Channels Analysis
```python
gaming_channels = [
    '@valorant',
    '@fortnite',
    '@callofduty'
]

main(channel_list=gaming_channels, max_videos=100, max_shorts=50)
```

### Example 2: Tech Reviewers Comparison
```python
tech_channels = [
    '@mkbhd',
    '@unboxtherapy',
    '@linustechtips'
]

main(channel_list=tech_channels, max_videos=50, max_shorts=25)
```

### Example 3: Quick Test (Limited Videos)
```python
main(
    channel_name='@nasa',
    max_videos=5,
    max_shorts=5
)
```

## 🔍 How It Works

1. **Channel Scraping**: Navigates to channel's about page and extracts metadata
2. **Niche Detection**: Analyzes title and description to categorize channel
3. **Country & Language**: Extracts location and language from page metadata
4. **Video Collection**: Scrapes video list from /videos and /shorts tabs
5. **Detailed Extraction**: Visits each video page for full metrics
6. **Data Propagation**: Adds channel metadata (niche, country, language) to each video/short
7. **Export**: Consolidates all data into Excel with separate sheets

## 🛡️ Rate Limiting & Best Practices

- Default 2-second delay between requests (configurable)
- Headless browser mode to reduce resource usage
- Automatic retry logic for failed requests
- Respects YouTube's robots.txt guidelines
- Recommended: Run during off-peak hours for large scrapes

## ⚠️ Limitations

- Requires stable internet connection
- Country field may not always be available (depends on channel settings)
- YouTube's dynamic content may cause occasional extraction failures
- Large scrapes (100+ channels) may take significant time
- Some channels may have restricted access or age gates

## 🤝 Contributing

To add new niche categories, edit the `extract_channel_niche()` function in `channel_scraper.py`:

```python
niche_keywords = {
    'Your_Category': ['keyword1', 'keyword2', 'keyword3']
}
```

## 📄 License

MIT License - Free to use and modify

## 🐛 Troubleshooting

**Issue**: Country not extracted
- **Solution**: Not all channels provide location data; this is expected

**Issue**: Niche shows as "General"
- **Solution**: Add more keywords for your specific category in `extract_channel_niche()`

**Issue**: Scraping fails midway
- **Solution**: Check internet connection, reduce max_videos/shorts, increase REQUEST_DELAY

**Issue**: Excel file won't open
- **Solution**: Ensure openpyxl is installed, check file permissions

## 📧 Support

For issues or questions, please check the code comments or create an issue in the repository.

---

**Happy Scraping! 🎉**
