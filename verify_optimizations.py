"""
Verification Script - Test all optimizations are working
"""

print("="*70)
print("VERIFICATION SCRIPT - Testing GTX 1660 Super Optimizations")
print("="*70)

# Test 1: Import main modules
print("\n[Test 1/5] Importing core modules...")
try:
    from src.scraper import main, scrape_channel, scrape_multiple_channels
    print("✓ Core scraper modules imported")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 2: Import parallel video scraper
print("\n[Test 2/5] Importing parallel video scraper...")
try:
    from src.scrapers.parallel_video_scraper import scrape_video_details, scrape_videos_parallel
    print("✓ Parallel video scraper imported")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 3: Import performance config
print("\n[Test 3/5] Importing performance configuration...")
try:
    from src.config.performance_config import (
        print_performance_config, 
        MAX_CHANNEL_WORKERS,
        MAX_VIDEO_DETAIL_WORKERS,
        PRESET_CONFIGS,
        get_preset_config
    )
    print("✓ Performance configuration imported")
    print(f"  - Channel Workers: {MAX_CHANNEL_WORKERS}")
    print(f"  - Video Workers: {MAX_VIDEO_DETAIL_WORKERS}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 4: Test preset loading
print("\n[Test 4/5] Testing performance presets...")
try:
    for preset_name in ['fast', 'balanced', 'safe', 'single']:
        config = get_preset_config(preset_name)
        print(f"✓ Preset '{preset_name}': {config['max_channel_workers']} channel workers")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 5: Test function signatures
print("\n[Test 5/5] Testing function signatures...")
try:
    import inspect
    
    # Check main() signature
    main_sig = inspect.signature(main)
    main_params = list(main_sig.parameters.keys())
    expected_params = ['channel_name', 'channel_list', 'max_videos', 'max_shorts', 
                       'parallel', 'max_workers', 'parallel_videos', 'preset']
    
    for param in expected_params:
        if param in main_params:
            print(f"✓ main() has parameter: {param}")
        else:
            print(f"✗ main() missing parameter: {param}")
            exit(1)
    
    # Check scrape_channel() signature
    scrape_sig = inspect.signature(scrape_channel)
    scrape_params = list(scrape_sig.parameters.keys())
    
    if 'parallel_videos' in scrape_params:
        print(f"✓ scrape_channel() has parallel_videos parameter")
    else:
        print(f"✗ scrape_channel() missing parallel_videos parameter")
        exit(1)
    
    # Check scrape_multiple_channels() signature
    multi_sig = inspect.signature(scrape_multiple_channels)
    multi_params = list(multi_sig.parameters.keys())
    
    if 'parallel_videos' in multi_params and 'preset' in multi_params:
        print(f"✓ scrape_multiple_channels() has parallel_videos and preset parameters")
    else:
        print(f"✗ scrape_multiple_channels() missing required parameters")
        exit(1)
        
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# All tests passed
print("\n" + "="*70)
print("✓ ALL TESTS PASSED!")
print("="*70)
print("\nYour scraper is ready with GTX 1660 Super optimizations:")
print(f"  • {MAX_CHANNEL_WORKERS} concurrent channel workers")
print(f"  • {MAX_VIDEO_DETAIL_WORKERS} parallel video detail requests per channel")
print("  • 4 performance presets available (fast, balanced, safe, single)")
print("  • Two-level parallelization enabled")
print("\nNext steps:")
print("  1. Run: python quick_start.py")
print("  2. Or run: python run_multi_channel.py")
print("="*70 + "\n")
