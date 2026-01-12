"""
Scheduler Service - Background reminder checking
Runs independently and processes due reminders
"""

import schedule
import threading
import time
from datetime import datetime, timedelta
import calendar
import logging
import config
from database import DatabaseManager
from whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

class SchedulerService:
    """Manages scheduled reminders"""
    
    def __init__(self, db_manager, whatsapp_service, log_callback=None):  # ✅ FIXED: Added log_callback parameter
        """Initialize scheduler service"""
        self.db = db_manager
        self.whatsapp = whatsapp_service
        self.log_callback = log_callback  # ✅ FIXED: Store log_callback
        self.is_running = False
        self.scheduler_thread = None
    
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        logger.info(message)
        if self.log_callback:  # ✅ FIXED: Send to GUI callback
            self.log_callback(log_msg)
    
    def get_valid_day_for_month(self, year, month, desired_day):
        """
        Get valid day for a given month/year
        If desired_day doesn't exist (e.g., Feb 31), return last day of month
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            desired_day: Desired day (1-31)
        
        Returns:
            Valid day for that month (1-31)
        """
        # Get number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Return the minimum of desired_day and days_in_month
        return min(desired_day, days_in_month)
    
    def check_due_reminders(self):
        """Check and process due reminders"""
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_day = current_time.weekday()  # 0=Monday, 6=Sunday
        current_date = current_time.day  # Day of month (1-31)
        current_month = current_time.month  # Month (1-12)
        current_year = current_time.year
        
        # Get all active reminders
        reminders = self.db.get_active_reminders()
        
        for reminder in reminders:
            reminder_id = reminder['id']
            contact_name = reminder['contact_name']
            phone = reminder['phone']
            message = reminder['message']
            schedule_time = reminder['schedule_time']
            frequency = reminder['frequency']
            last_sent = reminder['last_sent']
            schedule_day = reminder.get('schedule_day')  # For Monthly/Yearly
            schedule_month = reminder.get('schedule_month')  # For Yearly
            
            # Parse schedule time
            try:
                schedule_hour, schedule_minute = map(int, schedule_time.split(':'))
            except:
                logger.error(f"Invalid schedule time format for reminder {reminder_id}: {schedule_time}")
                continue
            
            # Check if time matches (within 1 minute window)
            time_matches = (
                schedule_hour == current_hour and
                abs(schedule_minute - current_minute) <= 1
            )
            
            if not time_matches:
                continue
            
            # Check if already sent recently (within last 5 minutes to avoid duplicates)
            if last_sent:
                try:
                    last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                    time_since_sent = (current_time - last_sent_dt).total_seconds()
                    
                    if time_since_sent < 300:  # 5 minutes
                        continue
                except:
                    pass  # If parsing fails, proceed with check
            
            # Check frequency and determine if should send
            should_send = False
            
            if frequency == "Once":
                # Only send if never sent before
                if not last_sent:
                    should_send = True
            
            elif frequency == "Daily":
                # Send every day at the scheduled time
                should_send = True
            
            elif frequency == "Weekdays":
                # Monday=0 to Friday=4
                if current_day <= 4:
                    should_send = True
            
            elif frequency == "Weekly":
                # Check if a week has passed since last sent
                if not last_sent:
                    should_send = True
                else:
                    try:
                        last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                        days_since = (current_time - last_sent_dt).days
                        if days_since >= 7:
                            should_send = True
                    except:
                        should_send = True  # If error, allow send
            
            elif frequency == "Monthly":
                # Check if current day matches schedule_day
                if schedule_day is None:
                    logger.warning(f"Monthly reminder {reminder_id} missing schedule_day")
                    continue
                
                # Get valid day for current month (handles Feb 31 -> Feb 28/29, etc.)
                valid_day = self.get_valid_day_for_month(current_year, current_month, schedule_day)
                
                if current_date == valid_day:
                    # Check if already sent this month
                    if not last_sent:
                        should_send = True
                    else:
                        try:
                            last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                            # Check if last sent was in a different month or year
                            if (last_sent_dt.month != current_month or 
                                last_sent_dt.year != current_year):
                                should_send = True
                        except:
                            should_send = True  # If error, allow send
            
            elif frequency == "Yearly":
                # Check if current month and day match schedule
                if schedule_month is None or schedule_day is None:
                    logger.warning(f"Yearly reminder {reminder_id} missing schedule_month or schedule_day")
                    continue
                
                # Check if current month matches
                if current_month == schedule_month:
                    # Get valid day for this month/year (handles Feb 29 on non-leap years)
                    valid_day = self.get_valid_day_for_month(current_year, current_month, schedule_day)
                    
                    if current_date == valid_day:
                        # Check if already sent this year
                        if not last_sent:
                            should_send = True
                        else:
                            try:
                                last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                                # Check if last sent was in a different year
                                if last_sent_dt.year != current_year:
                                    should_send = True
                            except:
                                should_send = True  # If error, allow send
            
            # Send if due
            if should_send:
                self.process_reminder(reminder_id, contact_name, phone, message, frequency)
    
    def process_reminder(self, reminder_id, name, phone, message, frequency):
        """Process and send a single reminder"""
        self.log(f"📤 Processing reminder #{reminder_id} for {name} ({frequency})")
        
        # Send message with retry
        success, error = self.whatsapp.send_message_with_retry(phone, message)
        
        if success:
            # Update last sent time
            self.db.update_last_sent(reminder_id)
            self.log(f"✅ Reminder sent successfully to {name}")
        else:
            self.log(f"❌ Failed to send reminder to {name}: {error}")
    
    def check_missed_reminders(self):
        """Check and send missed reminders from past window"""
        if not config.CHECK_MISSED_ON_STARTUP:
            return
        
        self.log("🔍 Checking for missed reminders...")
        
        now = datetime.now()
        window_start = now - timedelta(hours=config.MISSED_REMINDER_WINDOW)
        
        reminders = self.db.get_active_reminders()
        missed_count = 0
        
        for reminder in reminders:
            reminder_id = reminder['id']
            contact_name = reminder['contact_name']
            phone = reminder['phone']
            message = reminder['message']
            schedule_time = reminder['schedule_time']
            frequency = reminder['frequency']
            last_sent = reminder['last_sent']
            schedule_day = reminder.get('schedule_day')
            schedule_month = reminder.get('schedule_month')
            
            # Parse schedule time
            try:
                hour, minute = map(int, schedule_time.split(':'))
            except:
                continue
            
            # Check different frequencies
            should_have_sent = []
            
            if frequency == "Once":
                scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if window_start < scheduled_dt < now:
                    should_have_sent.append(scheduled_dt)
            
            elif frequency == "Daily":
                # Check each day in window
                check_date = window_start
                while check_date < now:
                    scheduled_dt = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if window_start < scheduled_dt < now:
                        should_have_sent.append(scheduled_dt)
                    check_date += timedelta(days=1)
            
            elif frequency == "Weekdays":
                # Check weekdays only
                check_date = window_start
                while check_date < now:
                    if check_date.weekday() <= 4:  # Monday to Friday
                        scheduled_dt = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if window_start < scheduled_dt < now:
                            should_have_sent.append(scheduled_dt)
                    check_date += timedelta(days=1)
            
            elif frequency == "Weekly":
                # Check if weekly reminder was missed
                if last_sent:
                    try:
                        last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                        # If more than 7 days ago and within window
                        if (now - last_sent_dt).days >= 7 and last_sent_dt > window_start:
                            next_due = last_sent_dt + timedelta(days=7)
                            next_due = next_due.replace(hour=hour, minute=minute)
                            if window_start < next_due < now:
                                should_have_sent.append(next_due)
                    except:
                        pass
            
            elif frequency == "Monthly":
                if schedule_day:
                    # Check each month in window
                    check_date = window_start
                    while check_date < now:
                        valid_day = self.get_valid_day_for_month(
                            check_date.year, check_date.month, schedule_day
                        )
                        scheduled_dt = check_date.replace(
                            day=valid_day, hour=hour, minute=minute, second=0, microsecond=0
                        )
                        if window_start < scheduled_dt < now:
                            # Check if not already sent this month
                            if last_sent:
                                last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                                if (last_sent_dt.month != scheduled_dt.month or 
                                    last_sent_dt.year != scheduled_dt.year):
                                    should_have_sent.append(scheduled_dt)
                            else:
                                should_have_sent.append(scheduled_dt)
                        
                        # Move to next month
                        if check_date.month == 12:
                            check_date = check_date.replace(year=check_date.year + 1, month=1)
                        else:
                            check_date = check_date.replace(month=check_date.month + 1)
            
            elif frequency == "Yearly":
                if schedule_month and schedule_day:
                    # Check if the yearly date was in the window
                    for year in [window_start.year, now.year]:
                        if year < window_start.year:
                            continue
                        
                        valid_day = self.get_valid_day_for_month(year, schedule_month, schedule_day)
                        
                        try:
                            scheduled_dt = datetime(
                                year, schedule_month, valid_day, hour, minute
                            )
                            
                            if window_start < scheduled_dt < now:
                                # Check if not already sent this year
                                if last_sent:
                                    last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                                    if last_sent_dt.year != year:
                                        should_have_sent.append(scheduled_dt)
                                else:
                                    should_have_sent.append(scheduled_dt)
                        except ValueError:
                            pass  # Invalid date
            
            # Check if any scheduled time was missed
            for scheduled_dt in should_have_sent:
                if last_sent:
                    try:
                        last_sent_dt = datetime.strptime(last_sent, '%Y-%m-%d %H:%M:%S')
                        if last_sent_dt >= scheduled_dt:
                            continue  # Already sent
                    except:
                        pass
                
                # This is a missed reminder
                self.log(f"⚠️ Found missed reminder: {contact_name} at {scheduled_dt.strftime('%Y-%m-%d %H:%M')}")
                
                # Send with MISSED prefix
                missed_message = f"⚠️ MISSED REMINDER\n\n{message}"
                success, error = self.whatsapp.send_message_with_retry(phone, missed_message)
                
                if success:
                    self.db.update_last_sent(reminder_id)
                    missed_count += 1
                
                time.sleep(5)  # Wait between missed reminders
        
        if missed_count > 0:
            self.log(f"✅ Sent {missed_count} missed reminder(s)")
        else:
            self.log("✅ No missed reminders found")
    
    def run_scheduler_loop(self):
        """Main scheduler loop"""
        self.is_running = True
        self.log("🚀 Scheduler service started")
        
        # Check for missed reminders on startup
        if config.CHECK_MISSED_ON_STARTUP:
            try:
                self.check_missed_reminders()
            except Exception as e:
                self.log(f"Error checking missed reminders: {e}")
        
        # Main loop
        last_check = time.time()
        
        while self.is_running:
            try:
                # Check if it's time to check reminders
                if time.time() - last_check >= config.CHECK_INTERVAL:
                    self.check_due_reminders()
                    last_check = time.time()
                
                # Sleep to reduce CPU usage
                time.sleep(5)
                
            except Exception as e:
                self.log(f"Error in scheduler loop: {str(e)}")
                logger.exception("Scheduler loop error")
                time.sleep(10)
        
        self.log("ℹ️ Scheduler service stopped")
    
    def start(self):
        """Start scheduler in background thread"""
        if not self.is_running:
            self.scheduler_thread = threading.Thread(
                target=self.run_scheduler_loop,
                daemon=True
            )
            self.scheduler_thread.start()
            self.log("Scheduler thread started")
    
    def stop(self):
        """Stop scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        self.log("Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status"""
        return {
            'is_running': self.is_running,
            'whatsapp_status': self.whatsapp.get_status() if self.whatsapp else None,
        }

# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Test scheduler service
    print("Starting scheduler service test...")
    
    db = DatabaseManager()
    whatsapp = WhatsAppService()
    
    def log_callback(message):
        print(f"LOG: {message}")
    
    scheduler = SchedulerService(db, whatsapp, log_callback)
    
    # Start scheduler
    scheduler.start()
    
    print("Scheduler running... Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped")