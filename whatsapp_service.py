"""
WhatsApp Service - Lightweight message sender
Uses headless browser for minimal resource usage
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import urllib.parse
import config

class WhatsAppService:
    """Handles WhatsApp Web automation"""
    
    def __init__(self, log_callback=None):
        """Initialize WhatsApp service"""
        self.driver = None
        self.log_callback = log_callback
        self.is_logged_in = False
        self.last_activity = time.time()
    
    def log(self, message):
        """Log message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        if self.log_callback:
            self.log_callback(log_msg)
    
    def init_browser(self):
        """Initialize browser with optimized settings"""
        if self.driver is not None:
            return True
        
        try:
            self.log("Initializing headless browser...")
            
            # Get browser options from config
            options = config.get_browser_options()
            
            # Initialize Chrome with automatic driver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.log("Browser initialized successfully")
            return True
            
        except Exception as e:
            self.log(f"Error initializing browser: {str(e)}")
            return False
    
    def close_browser(self):
        """Close browser and free resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                self.log("Browser closed")
            except Exception as e:
                self.log(f"Error closing browser: {str(e)}")
    
    def check_browser_timeout(self):
        """Close browser if inactive for too long"""
        if not config.KEEP_BROWSER_ALIVE:
            return
        
        if self.driver and (time.time() - self.last_activity) > config.BROWSER_TIMEOUT:
            self.log("Browser timeout - closing to free resources")
            self.close_browser()
    
    def login_to_whatsapp(self):
        """Open WhatsApp Web and wait for login"""
        if not self.init_browser():
            return False
        
        try:
            self.log("Opening WhatsApp Web...")
            self.driver.get(config.WHATSAPP_WEB_URL)
            
            # Wait for either QR code or chat interface
            self.log("Waiting for WhatsApp Web to load...")
            self.log("If you see a QR code, scan it with your phone")
            
            # Wait for chat interface (indicates logged in)
            wait = WebDriverWait(self.driver, config.WHATSAPP_LOAD_TIME)
            
            try:
                # Look for the search box which appears when logged in
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                )
                self.is_logged_in = True
                self.log("✅ Logged in to WhatsApp Web successfully!")
                return True
            except TimeoutException:
                self.log("⚠️ Timeout waiting for login. Please scan QR code if visible.")
                # Don't close browser, let user scan QR code
                return False
            
        except Exception as e:
            self.log(f"Error logging in: {str(e)}")
            return False
    
    def send_message(self, phone, message):
        """
        Send WhatsApp message to phone number
        
        Args:
            phone: Phone number with country code (e.g., +27821234567)
            message: Message text to send
            
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        # Update last activity
        self.last_activity = time.time()
        
        # Initialize browser if needed
        if not self.driver:
            if not self.init_browser():
                return False, "Failed to initialize browser"
        
        # Check if logged in
        if not self.is_logged_in:
            self.log("Not logged in, attempting to login...")
            if not self.login_to_whatsapp():
                return False, "Not logged in to WhatsApp Web"
        
        try:
            # Remove spaces and format phone
            phone_clean = phone.replace(' ', '').replace('-', '')
            
            # Add prefix/suffix to message if configured
            full_message = f"{config.MESSAGE_PREFIX}{message}{config.MESSAGE_SUFFIX}"
            
            # URL encode the message
            encoded_message = urllib.parse.quote(full_message)
            
            # Construct WhatsApp Web URL
            url = f"{config.WHATSAPP_WEB_URL}/send?phone={phone_clean}&text={encoded_message}"
            
            self.log(f"Sending message to {phone}...")
            self.driver.get(url)
            
            # Wait for message box to appear
            wait = WebDriverWait(self.driver, 20)
            message_box = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            
            # Small delay to ensure page is fully loaded
            time.sleep(config.MESSAGE_SEND_DELAY)
            
            # Send the message by pressing Enter
            message_box.send_keys(Keys.ENTER)
            
            # Wait a moment to ensure message is sent
            time.sleep(2)
            
            self.log(f"✅ Message sent successfully to {phone}")
            return True, None
            
        except TimeoutException:
            error_msg = "Timeout waiting for WhatsApp interface"
            self.log(f"❌ {error_msg}")
            self.is_logged_in = False  # Might need to re-login
            return False, error_msg
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error sending message: {error_msg}")
            return False, error_msg
    
    def send_message_with_retry(self, phone, message, max_retries=None):
        """
        Send message with automatic retries
        
        Args:
            phone: Phone number
            message: Message text
            max_retries: Number of retries (default from config)
            
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        if max_retries is None:
            max_retries = config.MAX_SEND_RETRIES
        
        for attempt in range(max_retries):
            success, error = self.send_message(phone, message)
            
            if success:
                return True, None
            
            if attempt < max_retries - 1:
                self.log(f"Retry {attempt + 1}/{max_retries} in {config.RETRY_DELAY} seconds...")
                time.sleep(config.RETRY_DELAY)
            else:
                self.log(f"Failed after {max_retries} attempts")
        
        return False, error
    
    def test_connection(self, phone, message="Test message from WhatsApp Reminder Manager"):
        """Test WhatsApp connection"""
        self.log("=== Testing WhatsApp Connection ===")
        success, error = self.send_message(phone, message)
        
        if success:
            self.log("=== Connection Test: SUCCESS ===")
        else:
            self.log(f"=== Connection Test: FAILED - {error} ===")
        
        return success, error
    
    def get_status(self):
        """Get current status"""
        return {
            'browser_active': self.driver is not None,
            'logged_in': self.is_logged_in,
            'last_activity': self.last_activity,
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close_browser()

# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Test WhatsApp service
    service = WhatsAppService()
    
    # Login
    if service.login_to_whatsapp():
        # Send test message
        phone = "+27821234567"  # Replace with your number
        message = "This is a test message from WhatsApp Reminder Manager!"
        
        success, error = service.send_message(phone, message)
        
        if success:
            print("Test message sent successfully!")
        else:
            print(f"Failed to send test message: {error}")
    
    # Cleanup
    input("Press Enter to close browser...")
    service.close_browser()