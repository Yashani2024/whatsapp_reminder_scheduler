"""
WhatsApp Reminder Service - Headless Mode
Run the scheduler without GUI for true background operation
"""

import sys
import signal
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from database import DatabaseManager
from scheduler_service import SchedulerService

class ServiceOnly:
    """Headless scheduler service"""
    
    def __init__(self):
        self.running = True
        self.db = DatabaseManager()
        self.scheduler = SchedulerService(self.db, self.log_message)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log_message(self, message):
        """Log to console"""
        print(message)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\nShutting down gracefully...")
        self.running = False
    
    def run(self):
        """Run the service"""
        print("\n" + "="*60)
        print(f"  {config.APP_NAME} - Headless Service Mode")
        print("="*60)
        
        # Check if WhatsApp is setup
        is_setup = self.db.get_setting("whatsapp_setup_complete", "false")
        if is_setup == "false":
            print("\n❌ ERROR: WhatsApp not setup!")
            print("Please run the GUI first to scan QR code:")
            print("  python main.py")
            print("\nThen run this service mode.")
            return
        
        print("\n✅ WhatsApp setup complete")
        print(f"📊 Database: {config.DB_PATH}")
        print(f"🌐 Browser: {config.BROWSER} (headless={config.HEADLESS_BROWSER})")
        print(f"⏰ Check interval: {config.CHECK_INTERVAL}s")
        
        # Get stats
        stats = self.db.get_stats()
        print(f"\n📈 Statistics:")
        print(f"   Contacts: {stats['total_contacts']}")
        print(f"   Active Reminders: {stats['active_reminders']}")
        print(f"   Messages Sent: {stats['successful_messages']}/{stats['total_messages']}")
        
        print("\n" + "="*60)
        print("🚀 Starting scheduler service...")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Set process priority
        try:
            config.set_process_priority()
        except:
            pass
        
        # Start scheduler
        self.scheduler.start()
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        # Cleanup
        print("\nStopping scheduler...")
        self.scheduler.stop()
        print("✅ Service stopped cleanly\n")

def main():
    """Main entry point"""
    service = ServiceOnly()
    service.run()

if __name__ == "__main__":
    main()