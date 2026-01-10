"""
Performance Configuration for GTX 1660 Super (6GB) System
Optimized parallelization settings for YouTube scraping.
"""

import os
import multiprocessing

# ============================================================================
# SYSTEM DETECTION
# ============================================================================

# Detect available CPU cores
CPU_CORES = multiprocessing.cpu_count()
PHYSICAL_CORES = CPU_CORES // 2 if CPU_CORES > 2 else CPU_CORES

# GPU Detection (for future ML/video processing tasks)
GPU_AVAILABLE = False
GPU_MEMORY_GB = 6  # GTX 1660 Super

try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
    if GPU_AVAILABLE:
        GPU_MEMORY_GB = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[GPU] Detected: {torch.cuda.get_device_name(0)} with {GPU_MEMORY_GB:.1f}GB VRAM")
except ImportError:
    pass


# ============================================================================
# PARALLELIZATION SETTINGS - Optimized for GTX 1660 Super System
# ============================================================================

# Channel-Level Parallelism (Multiple channels scraped simultaneously)
# Each channel runs its own browser instance
# GTX 1660 Super systems typically have 16GB+ RAM and good CPU
# 3-4 concurrent Chrome instances = ~1.2GB RAM usage (safe)
MAX_CHANNEL_WORKERS = min(4, max(2, PHYSICAL_CORES - 2))

# Video Detail Scraping Parallelism (Within a single channel)
# For scraping individual video pages in parallel
# Limited by YouTube rate limiting more than system resources
MAX_VIDEO_DETAIL_WORKERS = 8

# HTML Parsing Thread Pool (CPU-bound BeautifulSoup processing)
# Can be higher since parsing is lightweight
MAX_PARSING_THREADS = min(12, CPU_CORES)

# Batch Processing Settings
VIDEO_DETAIL_BATCH_SIZE = 10  # Process videos in batches to avoid overwhelming YouTube
SHORTS_DETAIL_BATCH_SIZE = 15  # Shorts pages are lighter, can process more


# ============================================================================
# TIMING & RATE LIMITING (Anti-ban measures)
# ============================================================================

# Delays between requests (in seconds)
REQUEST_DELAY_MIN = 1.0  # Minimum delay
REQUEST_DELAY_MAX = 2.5  # Maximum delay (randomized)
CHANNEL_SWITCH_DELAY = 3.0  # Delay when switching between channels

# Browser wait times
BROWSER_STARTUP_DELAY = 2.0
PAGE_LOAD_TIMEOUT = 15
DYNAMIC_CONTENT_WAIT = 4
SCROLL_DELAY = 1.5

# Parallel scraping stagger (delay between starting workers)
WORKER_STAGGER_DELAY = 2.0


# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================

# Chrome memory limits per instance (prevents memory leaks)
CHROME_MEMORY_LIMIT_MB = 800
MAX_CONCURRENT_BROWSERS = MAX_CHANNEL_WORKERS

# Cleanup settings
BROWSER_REUSE_THRESHOLD = 50  # Restart browser after N pages
GARBAGE_COLLECT_FREQUENCY = 100  # Run GC after N items processed


# ============================================================================
# GPU ACCELERATION SETTINGS (Future Use)
# ============================================================================

# For future ML/CV tasks (thumbnail analysis, video processing, etc.)
if GPU_AVAILABLE:
    GPU_BATCH_SIZE = 32  # Optimal for GTX 1660 Super (6GB)
    GPU_INFERENCE_WORKERS = 2  # Parallel inference streams
    USE_MIXED_PRECISION = True  # FP16 for better performance
    TORCH_CUDNN_BENCHMARK = True
else:
    GPU_BATCH_SIZE = 1
    GPU_INFERENCE_WORKERS = 1
    USE_MIXED_PRECISION = False
    TORCH_CUDNN_BENCHMARK = False


# ============================================================================
# RECOMMENDED CONFIGURATIONS BY SCENARIO
# ============================================================================

PRESET_CONFIGS = {
    'fast': {
        'description': 'Maximum speed, higher YouTube detection risk',
        'max_channel_workers': min(5, MAX_CHANNEL_WORKERS + 1),
        'max_video_workers': 12,
        'request_delay': 0.5,
        'batch_size': 20
    },
    
    'balanced': {
        'description': 'Optimal speed/safety balance (RECOMMENDED)',
        'max_channel_workers': MAX_CHANNEL_WORKERS,
        'max_video_workers': MAX_VIDEO_DETAIL_WORKERS,
        'request_delay': 1.5,
        'batch_size': VIDEO_DETAIL_BATCH_SIZE
    },
    
    'safe': {
        'description': 'Conservative, minimal YouTube detection risk',
        'max_channel_workers': 2,
        'max_video_workers': 4,
        'request_delay': 3.0,
        'batch_size': 5
    },
    
    'single': {
        'description': 'No parallelism, safest for testing',
        'max_channel_workers': 1,
        'max_video_workers': 1,
        'request_delay': 2.0,
        'batch_size': 1
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_preset_config(preset_name='balanced'):
    """
    Get performance configuration by preset name.
    
    Args:
        preset_name (str): One of ['fast', 'balanced', 'safe', 'single']
        
    Returns:
        dict: Configuration dictionary
    """
    return PRESET_CONFIGS.get(preset_name, PRESET_CONFIGS['balanced'])


def print_performance_config():
    """Print current performance configuration."""
    print("\n" + "="*70)
    print("PERFORMANCE CONFIGURATION - GTX 1660 Super Optimized")
    print("="*70)
    print(f"CPU Cores:               {CPU_CORES} (Physical: {PHYSICAL_CORES})")
    print(f"GPU Available:           {GPU_AVAILABLE}")
    if GPU_AVAILABLE:
        print(f"GPU Memory:              {GPU_MEMORY_GB:.1f} GB")
    print(f"\nChannel Workers:         {MAX_CHANNEL_WORKERS} (concurrent browser instances)")
    print(f"Video Detail Workers:    {MAX_VIDEO_DETAIL_WORKERS} (per channel)")
    print(f"Parsing Threads:         {MAX_PARSING_THREADS}")
    print(f"Video Batch Size:        {VIDEO_DETAIL_BATCH_SIZE}")
    print(f"Shorts Batch Size:       {SHORTS_DETAIL_BATCH_SIZE}")
    print(f"\nRequest Delay:           {REQUEST_DELAY_MIN}-{REQUEST_DELAY_MAX}s")
    print(f"Worker Stagger:          {WORKER_STAGGER_DELAY}s")
    print("="*70 + "\n")


def get_optimal_workers(total_items, max_workers=None):
    """
    Calculate optimal number of workers for a given workload.
    
    Args:
        total_items (int): Number of items to process
        max_workers (int): Maximum workers allowed
        
    Returns:
        int: Optimal number of workers
    """
    if max_workers is None:
        max_workers = MAX_VIDEO_DETAIL_WORKERS
    
    # Don't create more workers than items
    optimal = min(total_items, max_workers)
    
    # Minimum 1 worker
    return max(1, optimal)


# ============================================================================
# EXPORT DEFAULT CONFIG
# ============================================================================

# Default configuration (can be imported directly)
DEFAULT_CONFIG = {
    'max_channel_workers': MAX_CHANNEL_WORKERS,
    'max_video_workers': MAX_VIDEO_DETAIL_WORKERS,
    'max_parsing_threads': MAX_PARSING_THREADS,
    'video_batch_size': VIDEO_DETAIL_BATCH_SIZE,
    'shorts_batch_size': SHORTS_DETAIL_BATCH_SIZE,
    'request_delay_min': REQUEST_DELAY_MIN,
    'request_delay_max': REQUEST_DELAY_MAX,
    'worker_stagger': WORKER_STAGGER_DELAY,
    'gpu_available': GPU_AVAILABLE,
    'gpu_batch_size': GPU_BATCH_SIZE if GPU_AVAILABLE else None
}


if __name__ == "__main__":
    # Print configuration when run directly
    print_performance_config()
    
    print("\nAVAILABLE PRESETS:")
    print("-" * 70)
    for name, config in PRESET_CONFIGS.items():
        print(f"\n'{name}': {config['description']}")
        print(f"  - Channel Workers: {config['max_channel_workers']}")
        print(f"  - Video Workers:   {config['max_video_workers']}")
        print(f"  - Request Delay:   {config['request_delay']}s")
        print(f"  - Batch Size:      {config['batch_size']}")
