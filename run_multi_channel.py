"""
Example script to run multi-channel YouTube scraper.
This script demonstrates how to scrape multiple channels with niche, country, and language metadata.
"""

from scraper import main

# Example 1: Single channel scraping
def run_single_channel():
    """Scrape a single YouTube channel."""
    print("="*60)
    print("SINGLE CHANNEL MODE")
    print("="*60)
    
    main(
        channel_name='@mkbhd',
        max_videos=10,
        max_shorts=10
    )


# Example 2: Multiple channels scraping
def run_multiple_channels():
    """Scrape multiple YouTube channels at once."""
    print("="*60)
    print("MULTI-CHANNEL MODE")
    print("="*60)
    
    # List of channels to scrape
    channels = [
        '@mkbhd',           # Tech reviewer
        '@valorant',        # Gaming
        '@tasty',           # Food & Cooking
        '@nasa',            # Science & Education
        '@vogue'            # Fashion & Beauty
    ]
    
    main(
        channel_list=channels,
        max_videos=10,      # Max videos per channel
        max_shorts=10       # Max shorts per channel
    )


# Example 3: Custom channel list
def run_custom_channels():
    """Scrape your custom list of channels."""
    
    # Customize this list with your target channels
    my_channels = [
        '@channel1',
        '@channel2',
        '@channel3'
    ]
    
    main(
        channel_list=my_channels,
        max_videos=50,      # Adjust as needed
        max_shorts=50       # Adjust as needed
    )


if __name__ == "__main__":
    # Choose which mode to run:
    
    # Option 1: Single channel
    run_single_channel()
    
    # Option 2: Multiple channels (recommended)
    #run_multiple_channels()
    
    # Option 3: Your custom channel list
    # run_custom_channels()
    
    print("\n" + "="*60)
    print("SCRAPING COMPLETE!")
    print("="*60)
    print("\nThe following data has been extracted for each channel:")
    print("  ✓ Niche/Category (auto-detected)")
    print("  ✓ Country (if available)")
    print("  ✓ Default Language")
    print("\nThis metadata is stored in:")
    print("  • Channel data (All_Channels sheet)")
    print("  • Video data (All_Videos sheet)")
    print("  • Shorts data (All_Shorts sheet)")
    print("\nOutput file: youtube_analytics_scraped.xlsx")
    print("="*60 + "\n")
