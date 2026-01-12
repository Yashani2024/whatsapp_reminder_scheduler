"""
Configuration settings for WhatsApp Reminder Manager
Edit these settings to customize behavior
"""

import os
from pathlib import Path

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

APP_NAME = "WhatsApp Reminder Manager"
VERSION = "1.0.0"

# Base directory
BASE_DIR = Path(__file__).parent

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

# Local SQLite database path
DB_PATH = BASE_DIR / "whatsapp_reminders.db"

# =============================================================================
# BROWSER SETTINGS (Optimized for Gaming PC)
# =============================================================================

# Use headless browser (no visible window, less resources)
# For FIRST TIME SETUP: Set to False to see browser window
# After setup complete: Set to True for background operation
HEADLESS_BROWSER = True

# Browser choice: 'chrome' or 'firefox' or 'edge'
BROWSER = 'chrome'

# Browser arguments for minimal resource usage
BROWSER_ARGS = [
    '--headless=new',  # New headless mode (fixes crashes)
    '--disable-gpu',  # Disable GPU for less resource use
    '--no-sandbox',  # Required for some systems
    '--disable-dev-shm-usage',  # Overcome limited resource problems
    '--disable-extensions',  # No extensions
    '--disable-images',  # Don't load images (faster, less memory)
    '--blink-settings=imagesEnabled=false',  # Another way to disable images
    '--window-size=1920,1080',  # Set window size
    '--log-level=3',  # Minimize logging
    '--remote-debugging-port=9222',  # Helps with debugging
]

# Wait times (in seconds)
WHATSAPP_LOAD_TIME = 20  # Time to wait for WhatsApp Web to load
MESSAGE_SEND_DELAY = 3   # Delay after sending message
TAB_CLOSE_DELAY = 2      # Delay before closing tab

# Keep browser session alive (faster subsequent sends)
KEEP_BROWSER_ALIVE = True
BROWSER_TIMEOUT = 300  # Close browser after 5 minutes of inactivity

# =============================================================================
# SCHEDULER SETTINGS
# =============================================================================

# How often to check for due reminders (seconds)
CHECK_INTERVAL = 30

# Check for missed reminders on startup
CHECK_MISSED_ON_STARTUP = True

# Time window to check for missed reminders (hours)
MISSED_REMINDER_WINDOW = 24

# =============================================================================
# SYSTEM TRAY SETTINGS
# =============================================================================

# Enable system tray icon (requires pillow and pystray)
ENABLE_SYSTEM_TRAY = True  # Set to True if you install pillow and pystray

# Start minimized to tray
START_MINIMIZED = False

# =============================================================================
# AUTO-START SETTINGS
# =============================================================================

# Enable auto-start on system boot
AUTO_START_ENABLED = False  # Set to True to enable

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

# Log file path
LOG_FILE = BASE_DIR / "whatsapp_manager.log"

# Enable file logging
ENABLE_FILE_LOGGING = True

# Log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_LEVEL = 'INFO'

# Maximum log file size (MB)
MAX_LOG_SIZE = 10

# Number of backup log files to keep
LOG_BACKUP_COUNT = 3

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Process priority: 'low', 'below_normal', 'normal', 'above_normal', 'high'
# Set to 'low' or 'below_normal' for gaming
PROCESS_PRIORITY = 'below_normal'

# Maximum memory usage (MB) - restart if exceeded
MAX_MEMORY_MB = 500

# Check memory usage interval (seconds)
MEMORY_CHECK_INTERVAL = 300

# =============================================================================
# WHATSAPP SETTINGS
# =============================================================================

# WhatsApp Web URL
WHATSAPP_WEB_URL = "https://web.whatsapp.com"

# Message format
MESSAGE_PREFIX = ""  # Add prefix to all messages (e.g., "[BOT]")
MESSAGE_SUFFIX = ""  # Add suffix to all messages

# Retry settings
MAX_SEND_RETRIES = 3
RETRY_DELAY = 10  # seconds between retries

# =============================================================================
# VALIDATION
# =============================================================================

def validate_phone_number(phone):
    """
    Validate phone number format
    Must start with + and country code
    """
    if not phone.startswith('+'):
        return False, "Phone must start with + and country code"
    
    if len(phone) < 10:
        return False, "Phone number too short"
    
    # Remove + and check if rest is numeric
    if not phone[1:].replace(' ', '').isdigit():
        return False, "Phone must contain only numbers after +"
    
    return True, "Valid"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_browser_options():
    """Get browser options based on settings"""
    from selenium import webdriver
    
    if BROWSER == 'chrome':
        from selenium.webdriver.chrome.options import Options
        options = Options()
    elif BROWSER == 'firefox':
        from selenium.webdriver.firefox.options import Options
        options = Options()
    elif BROWSER == 'edge':
        from selenium.webdriver.edge.options import Options
        options = Options()
    else:
        raise ValueError(f"Unsupported browser: {BROWSER}")
    
    # Always add these stability arguments
    stability_args = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--window-size=1920,1080',
        '--log-level=3',
        '--remote-debugging-port=9222',
    ]
    
    for arg in stability_args:
        options.add_argument(arg)
    
    # Only add headless-specific arguments if headless mode is enabled
    if HEADLESS_BROWSER:
        options.add_argument('--headless=new')
        options.add_argument('--disable-images')
        options.add_argument('--blink-settings=imagesEnabled=false')
    
    # Add user data directory to keep session
    user_data_dir = BASE_DIR / "browser_data"
    user_data_dir.mkdir(exist_ok=True)
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    return options

def set_process_priority():
    """Set process priority for minimal resource usage"""
    try:
        import psutil
        import os
        
        p = psutil.Process(os.getpid())
        
        priority_map = {
            'low': psutil.IDLE_PRIORITY_CLASS,
            'below_normal': psutil.BELOW_NORMAL_PRIORITY_CLASS,
            'normal': psutil.NORMAL_PRIORITY_CLASS,
            'above_normal': psutil.ABOVE_NORMAL_PRIORITY_CLASS,
            'high': psutil.HIGH_PRIORITY_CLASS,
        }
        
        if PROCESS_PRIORITY in priority_map:
            p.nice(priority_map[PROCESS_PRIORITY])
            print(f"Process priority set to: {PROCESS_PRIORITY}")
    except ImportError:
        print("psutil not installed - skipping process priority setting")
    except Exception as e:
        print(f"Could not set process priority: {e}")

# =============================================================================
# CONSTANTS
# =============================================================================

FREQUENCIES = ["Once", "Daily", "Weekdays", "Weekly", "Monthly", "Yearly"]

STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

MESSAGE_STATUS_SENT = "sent"
MESSAGE_STATUS_FAILED = "failed"
MESSAGE_STATUS_PENDING = "pending"