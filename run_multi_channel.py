"""
Example script to run multi-channel YouTube scraper.
This script demonstrates how to scrape multiple channels with niche, country, and language metadata.
Optimized for GTX 1660 Super (6GB) and similar mid-range systems.
"""

from src.scraper import main
from src.config.performance_config import print_performance_config, PRESET_CONFIGS

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


# Example 2: Multiple channels scraping (PARALLEL - FAST! - Optimized for GTX 1660 Super)
def run_multiple_channels_parallel():
    """Scrape multiple YouTube channels in parallel for faster processing."""
    print("="*60)
    print("MULTI-CHANNEL MODE - PARALLEL (GTX 1660 Super Optimized)")
    print("="*60)
    
    # List of channels to scrape
    channels = [
        '@mkbhd',           # Tech reviewer
        '@valorant',        # Gaming
        '@nasa',            # Science & Education
        '@vogue'            # Fashion & Beauty
    ]
    
    main(
        channel_list=channels,
        max_videos=10,          # Max videos per channel
        max_shorts=10,          # Max shorts per channel
        parallel=True,          # Enable parallel channel scraping
        max_workers=None,       # Auto-detect from config (4 for GTX 1660 Super systems)
        parallel_videos=True,   # Enable parallel video detail scraping (NEW!)
        preset='balanced'       # Use balanced preset (safe & fast)
    )


# Example 3: FAST mode - Maximum speed (higher detection risk)
def run_multiple_channels_fast():
    """Scrape multiple channels using FAST preset - optimized for speed."""
    print("="*60)
    print("MULTI-CHANNEL MODE - FAST PRESET")
    print("="*60)
    
    channels = [
        '@mkbhd',
        '@valorant',
        '@tasty'
    ]
    
    main(
        channel_list=channels,
        max_videos=20,
        max_shorts=20,
        parallel=True,
        preset='fast'  # Aggressive parallelization
    )


# Example 4: SAFE mode - Conservative settings (minimal detection risk)
def run_multiple_channels_safe():
    """Scrape multiple channels using SAFE preset - minimal YouTube detection."""
    print("="*60)
    print("MULTI-CHANNEL MODE - SAFE PRESET")
    print("="*60)
    
    channels = [
        '@mkbhd',
        '@valorant'
    ]
    
    main(
        channel_list=channels,
        max_videos=10,
        max_shorts=10,
        parallel=True,
        preset='safe'  # Conservative settings
    )


# Example 5: Multiple channels scraping (SEQUENTIAL - SAFEST)
def run_multiple_channels_sequential():
    """Scrape multiple YouTube channels one by one (slower but safer)."""
    print("="*60)
    print("MULTI-CHANNEL MODE - SEQUENTIAL")
    print("="*60)
    
    # List of channels to scrape
    channels = [
        '@mkbhd',           # Tech reviewer
        '@valorant',        # Gaming
        '@tasty'            # Food & Cooking
    ]
    
    main(
        channel_list=channels,
        max_videos=10,      # Max videos per channel
        max_shorts=10,      # Max shorts per channel
        parallel=False,     # Disable parallel (sequential mode)
        parallel_videos=False  # Also disable parallel video scraping
    )


# Example 6: Custom channel list
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
        max_shorts=50,      # Adjust as needed
        parallel=True,      # Use parallel mode for speed
        preset='balanced'   # Recommended preset
    )


# Example 7: Show performance configuration
def show_performance_info():
    """Display current performance configuration."""
    print("\n")
    print("="*70)
    print("PERFORMANCE PRESETS AVAILABLE")
    print("="*70)
    
    for name, config in PRESET_CONFIGS.items():
        print(f"\n'{name}' preset:")
        print(f"  Description: {config['description']}")
        print(f"  Channel Workers: {config['max_channel_workers']}")
        print(f"  Video Workers: {config['max_video_workers']}")
        print(f"  Request Delay: {config['request_delay']}s")
        print(f"  Batch Size: {config['batch_size']}")
    
    print("\n")
    print_performance_config()


if __name__ == "__main__":
    # Show performance configuration first
    show_performance_info()
    
    # Choose which mode to run:
    
    # Option 1: Single channel
    # run_single_channel()
    
    # Option 2: Multiple channels - PARALLEL BALANCED (RECOMMENDED for GTX 1660 Super)
    run_multiple_channels_parallel()
    
    # Option 3: Multiple channels - FAST (Maximum speed)
    # run_multiple_channels_fast()
    
    # Option 4: Multiple channels - SAFE (Conservative)
    # run_multiple_channels_safe()
    
    # Option 5: Multiple channels - SEQUENTIAL (safest, slower)
    # run_multiple_channels_sequential()
    
    # Option 4: Your custom channel list
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
