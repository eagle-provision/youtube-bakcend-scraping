"""
Quick Start Script - YouTube Analytics Scraper
Optimized for GTX 1660 Super (6GB)

Run this script to quickly test the scraper with optimized settings.
"""

from src.scraper import main
from src.config.performance_config import print_performance_config, GPU_AVAILABLE
import torch
def quick_test():
    """
    Quick test with 1 channel, small dataset.
    Perfect for testing the scraper setup.
    """
    print("\n" + "="*70)
    print("QUICK TEST MODE - Testing scraper setup")
    print("="*70)
    
    # Clear previous output for fresh test
    import os
    output_file = 'data/processed/youtube_analytics_scraped.xlsx'
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"\n✓ Cleared previous output file for fresh test")
    
    main(
        channel_name='@mkbhd',
        max_videos=5,           # Small dataset for testing
        max_shorts=5,
        parallel_videos=True    # Test parallel video scraping
    )


def production_run():
    """
    Production-ready scraping with optimized settings for GTX 1660 Super.
    Scrapes multiple channels with balanced performance.
    """
    print("\n" + "="*70)
    print("PRODUCTION MODE - Optimized for GTX 1660 Super")
    print("="*70)
    
    # Define your target channels here
    target_channels = [
        '@mkbhd',           # Tech
        '@valorant',        # Gaming
        '@tasty',           # Food
        '@nasa'             # Science
    ]
    
    main(
        channel_list=target_channels,
        max_videos=50,          # Adjust as needed
        max_shorts=50,
        parallel=True,          # Channel-level parallelism
        parallel_videos=True,   # Video-level parallelism
        preset='balanced'       # GTX 1660 Super optimized preset
    )


def fast_run():
    """
    Fast scraping mode - maximum speed (higher detection risk).
    Use when you need results quickly.
    """
    print("\n" + "="*70)
    print("FAST MODE - Maximum Speed")
    print("="*70)
    
    target_channels = [
        '@channel1',
        '@channel2'
    ]
    
    main(
        channel_list=target_channels,
        max_videos=30,
        max_shorts=30,
        parallel=True,
        preset='fast'  # Aggressive settings
    )


def safe_run():
    """
    Safe scraping mode - minimal detection risk.
    Use for important channels or when being extra cautious.
    """
    print("\n" + "="*70)
    print("SAFE MODE - Minimal Detection Risk")
    print("="*70)
    
    target_channels = [
        '@important_channel'
    ]
    
    main(
        channel_list=target_channels,
        max_videos=100,
        max_shorts=100,
        parallel=True,
        preset='safe'  # Conservative settings
    )


if __name__ == "__main__":
    # Show system configuration
    print("\n" + "="*70)
    print("SYSTEM DETECTION")
    print("="*70)
    print(f"GPU Available: {'Yes ✓' if GPU_AVAILABLE else 'No ✗'}")
    print_performance_config()
    
    # Choose your mode:
    
    # 1. Quick test (recommended first run)
    quick_test()
    #print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")
    # 2. Production run (after successful test)
    # production_run()
    
    # 3. Fast run (when speed is priority)
    # fast_run()
    
    # 4. Safe run (when safety is priority)
    # safe_run()
    
    print("\n" + "="*70)
    print("SCRAPING COMPLETE!")
    print("="*70)
    print("Check the 'data/processed/' folder for Excel output files.")
    print("="*70 + "\n")
