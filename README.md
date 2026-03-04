# YouTube Analytics Backend

A high-performance, cost-effective YouTube channel analytics scraper built for large-scale data collection.

## Project Overview

This backend system is designed to:
- Discover and ingest hundreds of thousands to millions of YouTube channels
- Track daily metrics for performance analysis
- Separate and analyze long-form videos vs Shorts
- Extract detailed engagement metrics
- Export data in a structured 3-part format for advanced analysis

## Data Structure (Per PDF Specification)

The system organizes data into 3 distinct parts:

### 1. Static Data (Channel-level, rarely changes)
- Channel ID, URL, handle
- Description, creation date
- Banner/profile images
- Country, language
- Monetization status

### 2. Evolving Data (Channel-level, updated daily)
- Subscriber count (daily snapshots)
- Total views (daily snapshots)
- Video and shorts counts
- Last posted date
- Growth metrics (computed from historical snapshots)

### 3. Video Data (Video-level)
- Video ID, URL, title, description
- View count, likes, comments
- Upload date, duration
- Thumbnail URL
- Content type (short vs long-form)

## Excel Output Structure

Data is exported to Excel with **4 sheets**:
1. **Static_Data** - Channel static information
2. **Evolving_Data** - Daily metric snapshots for tracking changes
3. **Videos_Data** - Long-form videos (>60 seconds)
4. **Shorts_Data** - Short-form videos (<60 seconds)

This structure enables:
- Daily tracking and trend analysis
- Separate analysis of Shorts vs long-form content
- Historical comparison and growth rate calculation
- Easy integration with data analysis tools

## Quick Start

### Test with a Single Channel

To test the scraper with the client's channel (@vobane):

```bash
python test_vobane.py
```

This will:
- Extract channel data (ID, URL, subscribers, views, etc.)
- Scrape up to 20 long-form videos + 20 shorts
- Validate all required fields per PDF specification
- Show detailed extraction summary
- Save to Excel with proper 4-sheet structure

### General Usage

```python
from src.scraper import scrape_channel, save_results

# Scrape a channel
channel_data, videos, shorts = scrape_channel(
    channel_name='@channelname',
    max_videos=50,
    max_shorts=50,
    parallel_videos=True
)

# Save to Excel
save_results(channel_data, videos, shorts)
```

## Key Features

### Accuracy
- **Channel ID extraction** from multiple sources (JSON, URL patterns)
- **Precise view counts** using maximum values from multiple elements
- **Reliable content separation** between long-form and shorts
- **Exact video counts** by content type

### Structure
- **3-part data model** aligned with PDF specification
- **Daily tracking** via separate evolving data sheet
- **Proper linking** using channel_id across all sheets
- **Clean separation** of static vs dynamic data

### Performance
- **Parallel video scraping** for faster execution
- **Optimized for GTX 1660 Super** GPU
- **Configurable presets** (fast, balanced, safe modes)
- **Efficient browser automation** with Selenium

### Completeness
All required fields per PDF:
- ✓ Channel ID and URL
- ✓ Channel handle and title
- ✓ Creation/activation date
- ✓ Subscriber and view counts
- ✓ Video and shorts counts
- ✓ Video IDs for all content
- ✓ Engagement metrics (likes, comments)
- ✓ Monetization status (placeholder)

## Data Validation

The test script validates:
1. All required static fields are present
2. All required evolving fields are captured
3. Video IDs are extracted correctly
4. Content is properly categorized (video vs short)
5. Engagement metrics are included
6. Excel output has correct 4-sheet structure

## Project Structure

```
youtube-analytics-backend/
├── src/
│   ├── scraper.py              # Main orchestration
│   ├── config/
│   │   ├── config.py           # Data structure definitions
│   │   └── performance_config.py
│   ├── scrapers/
│   │   ├── channel_scraper.py  # Channel data extraction
│   │   ├── video_scraper.py    # Video/shorts extraction
│   │   └── parallel_video_scraper.py
│   └── utils/
│       └── data_processor.py   # Data processing & Excel export
├── test_vobane.py              # Validation test script
├── quick_start.py              # Quick test with presets
└── CHANGES_SUMMARY.md          # Detailed changes documentation
```

## Testing & Validation

### Run POC Test

```bash
python test_vobane.py
```

Expected output:
- Channel extraction summary
- Video/shorts counts and samples
- Field validation results
- Excel file path and size
- Detailed extraction report

### Verify Output

Check the Excel file at:
```
data/processed/youtube_analytics_scraped.xlsx
```

Verify:
1. **Static_Data sheet** - Channel info with all required fields
2. **Evolving_Data sheet** - Daily metrics snapshot
3. **Videos_Data sheet** - Long-form videos only
4. **Shorts_Data sheet** - Short-form videos only

## Requirements

- Python 3.8+
- Selenium WebDriver
- Chrome/Chromium browser
- Required packages: `pip install -r requirements.txt`

## Performance Configuration

The system auto-detects your GPU and adjusts settings:
- **GTX 1660 Super optimized** - Balanced preset by default
- **Fast mode** - Maximum speed (higher detection risk)
- **Safe mode** - Minimal detection risk
- **Custom configuration** - Adjust workers, delays, batch sizes

## Cost Efficiency

- **No expensive proxy services** needed
- **In-house scraping** like Algrow, TubeLab, NextLev
- **Optimized resource usage** for GPU/CPU
- **Parallel processing** for faster scraping

## Next Steps

1. **Validate POC** - Run test_vobane.py and verify output
2. **Check accuracy** - Compare scraped data with actual YouTube data
3. **Review structure** - Confirm 4-sheet Excel matches requirements
4. **Provide feedback** - Report any missing/incorrect data
5. **Scale testing** - Test with multiple channels if needed

## Documentation

- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - Detailed technical changes
- [PDF Specification](Developer_Document.pdf) - Original requirements

## Support

For issues or questions:
1. Check CHANGES_SUMMARY.md for technical details.
2. Verify Excel output structure.
3. Review test_vobane.py validation results.
4. Report specific accuracy concerns with examples.

