"""
WhatsApp Reminder Manager - Main Entry Point
Run this file to start the application
"""

import tkinter as tk
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from gui import WhatsAppReminderGUI

def setup_process_priority():
    """Set process priority for minimal resource usage"""
    try:
        config.set_process_priority()
    except Exception as e:
        print(f"Could not set process priority: {e}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required = {
        'selenium': 'selenium',
        'webdriver_manager': 'webdriver-manager',
        'schedule': 'schedule',
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("\n" + "="*60)
        print("ERROR: Missing required packages!")
        print("="*60)
        print("\nPlease install missing packages:")
        print(f"\npip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("pip install -r requirements.txt")
        print("="*60 + "\n")
        return False
    
    return True

def main():
    """Main application entry point"""
    
    print("\n" + "="*60)
    print(f"  {config.APP_NAME} v{config.VERSION}")
    print("="*60)
    print("\nInitializing...")
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return
    
    # Set process priority
    setup_process_priority()
    
    # Print configuration
    print(f"\nConfiguration:")
    print(f"  Database: {config.DB_PATH}")
    print(f"  Browser: {config.BROWSER} (headless={config.HEADLESS_BROWSER})")
    print(f"  Check interval: {config.CHECK_INTERVAL}s")
    print(f"  Process priority: {config.PROCESS_PRIORITY}")
    
    # Create root window
    root = tk.Tk()
    
    # Create application
    try:
        app = WhatsAppReminderGUI(root)
        
        print("\nApplication started successfully!")
        print("\nTips:")
        print("  - First time? Scan QR code when prompted")
        print("  - Add contacts in Contacts tab")
        print("  - Create reminders in Reminders tab")
        print("  - Test with File -> Test Connection")
        print("  - Check Activity Log for status")
        print("\n" + "="*60 + "\n")
        
        # Start GUI main loop
        root.mainloop()
        
    except Exception as e:
        print(f"\nError starting application: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
    
    print("\nApplication closed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")