"""
GUI Interface - Simple and lightweight
Manages contacts and reminders
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import io
import config
from database import DatabaseManager
from whatsapp_service import WhatsAppService
from scheduler_service import SchedulerService

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed - QR code display disabled")

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("Warning: pystray not installed - system tray disabled")

class WhatsAppReminderGUI:
    """Main GUI application"""
    
    def __init__(self, root):
        """Initialize GUI"""
        self.root = root
        self.root.title(config.APP_NAME)
        self.root.geometry("800x600")
        
        # Initialize components
        self.db = DatabaseManager()
        self.whatsapp = WhatsAppService(self.log_message)
        self.scheduler = SchedulerService(self.db, self.whatsapp, self.log_message)
        
        # Initialize tray icon variable
        self.tray_icon = None
        
        # Create GUI
        self.create_menu()
        self.create_widgets()
        
        # Check if first time setup needed
        is_setup = self.db.get_setting("whatsapp_setup_complete", "false")
        if is_setup == "false":
            self.show_first_time_setup()
        else:
            # Start scheduler
            self.scheduler.start()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    # =========================================================================
    # SYSTEM TRAY METHODS
    # =========================================================================
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not PYSTRAY_AVAILABLE or not PIL_AVAILABLE:
            return None
        
        # Create a simple icon (you can replace with a custom image later)
        # Create a 64x64 icon with "WA" text
        image = Image.new('RGB', (64, 64), color='#25D366')  # WhatsApp green
        draw = ImageDraw.Draw(image)
        
        # Draw white text
        try:
            # Try to use a font if available
            from PIL import ImageFont
            try:
                font = ImageFont.truetype("arial.ttf", 36)
                draw.text((8, 10), "WA", fill='white', font=font)
            except:
                draw.text((8, 20), "WA", fill='white')
        except:
            draw.text((8, 20), "WA", fill='white')
        
        # Create tray icon menu
        menu = (
            item('Show Window', self.show_window),
            item('Hide Window', self.hide_window),
            pystray.Menu.SEPARATOR,
            item('Test Connection', self.test_connection_from_tray),
            item('Check Missed', self.check_missed_from_tray),
            pystray.Menu.SEPARATOR,
            item('Exit', self.quit_from_tray)
        )
        
        icon = pystray.Icon("whatsapp_reminder", image, config.APP_NAME, menu)
        return icon
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.after(0, self._show_window_safe)
    
    def _show_window_safe(self):
        """Show window in main thread"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self, icon=None, item=None):
        """Hide window to system tray"""
        if not PYSTRAY_AVAILABLE:
            messagebox.showwarning(
                "System Tray Not Available",
                "pystray not installed. Window will minimize to taskbar instead.\n\n"
                "Install with: pip install pystray"
            )
            self.root.iconify()
            return
        
        self.root.withdraw()  # Hide window
        self.log_message("Minimized to system tray")
        
        # Start tray icon if not already running
        if not self.tray_icon:
            self.tray_icon = self.create_tray_icon()
            if self.tray_icon:
                # Run tray icon in separate thread
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def test_connection_from_tray(self, icon=None, item=None):
        """Test connection from tray menu"""
        self.root.after(0, self.test_connection)
    
    def check_missed_from_tray(self, icon=None, item=None):
        """Check missed reminders from tray menu"""
        self.root.after(0, self.check_missed)
    
    def quit_from_tray(self, icon=None, item=None):
        """Quit application from tray"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.on_closing)
    
    # =========================================================================
    # FIRST TIME SETUP
    # =========================================================================
    
    def show_first_time_setup(self):
        """Show first-time setup wizard"""
        self.setup_window = tk.Toplevel(self.root)
        self.setup_window.title("First Time Setup")
        self.setup_window.geometry("800x900")
        self.setup_window.grab_set()  # Make it modal
        
        # Center the window
        self.setup_window.transient(self.root)
        
        # Make it resizable so user can expand if needed
        self.setup_window.resizable(True, True)
        
        main_frame = ttk.Frame(self.setup_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            main_frame,
            text="Welcome to WhatsApp Reminder Manager!",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Instructions
        instructions = """
FIRST TIME SETUP - WhatsApp Web Login

STEP 1: Click "Start Setup" below

STEP 2: Scan the QR Code that appears
   - Open WhatsApp on your phone
   - Tap Menu > Linked Devices > Link a Device
   - Point your camera at the QR code below

STEP 3: Wait for login confirmation

STEP 4: Click "Setup Complete" when ready
        """
        
        text_widget = tk.Text(
            main_frame,
            wrap=tk.WORD,
            height=8,
            width=70,
            font=("Arial", 10)
        )
        text_widget.pack(pady=5)
        text_widget.insert(1.0, instructions)
        text_widget.config(state=tk.DISABLED)
        
        # QR Code Frame - use pack with specific height
        qr_frame = ttk.LabelFrame(main_frame, text="WhatsApp QR Code", padding="10")
        qr_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Configure grid for better control
        qr_frame.grid_rowconfigure(0, weight=1)
        qr_frame.grid_columnconfigure(0, weight=1)
        
        # QR Code display area - fixed size with scrolling if needed
        self.qr_label = tk.Label(
            qr_frame,
            text="QR Code will appear here after clicking 'Start Setup'",
            bg="white",
            relief=tk.SUNKEN,
            font=("Arial", 10),
            compound=tk.CENTER
        )
        self.qr_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Status label - pack at bottom, won't be hidden
        self.setup_status = tk.Label(
            main_frame,
            text="Status: Ready to start",
            font=("Arial", 10, "bold"),
            fg="blue"
        )
        self.setup_status.pack(pady=10, side=tk.TOP)
        
        # Buttons - pack at very bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM)
        
        self.start_setup_btn = ttk.Button(
            button_frame,
            text="Start Setup",
            command=self.start_whatsapp_setup
        )
        self.start_setup_btn.pack(side=tk.LEFT, padx=5)
        
        self.complete_setup_btn = ttk.Button(
            button_frame,
            text="Setup Complete",
            command=self.complete_whatsapp_setup,
            state=tk.DISABLED
        )
        self.complete_setup_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Skip (Setup Later)",
            command=self.setup_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def start_whatsapp_setup(self):
        """Start WhatsApp setup process"""
        self.setup_status.config(text="Status: Opening browser and loading WhatsApp Web...", fg="orange")
        self.start_setup_btn.config(state=tk.DISABLED)
        self.qr_label.config(text="Loading WhatsApp Web...", bg="lightyellow")
        
        def setup_thread():
            try:
                self.log_message("Starting WhatsApp Web setup...")
                
                # Initialize browser
                if not self.scheduler.whatsapp.init_browser():
                    self.setup_status.config(
                        text="Status: Failed to start browser",
                        fg="red"
                    )
                    self.start_setup_btn.config(state=tk.NORMAL)
                    return
                
                # Open WhatsApp Web
                self.scheduler.whatsapp.driver.get(config.WHATSAPP_WEB_URL)
                self.setup_status.config(text="Status: Loading WhatsApp Web...", fg="orange")
                
                # Wait a moment for page to load
                time.sleep(3)
                
                # Try to capture QR code
                self.capture_and_display_qr()
                
                # Check if logged in (wait up to 60 seconds)
                self.setup_status.config(text="Status: Waiting for QR code scan...", fg="orange")
                
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                try:
                    # Wait for the search box (indicates logged in)
                    wait = WebDriverWait(self.scheduler.whatsapp.driver, 60)
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                    )
                    
                    # Success!
                    self.scheduler.whatsapp.is_logged_in = True
                    self.setup_status.config(
                        text="Status: Successfully logged in! Click 'Setup Complete' below",
                        fg="green"
                    )
                    self.qr_label.config(
                        text="✓ Login Successful!\n\nYou can now click 'Setup Complete'",
                        bg="lightgreen",
                        font=("Arial", 12, "bold")
                    )
                    self.complete_setup_btn.config(state=tk.NORMAL)
                    self.log_message("WhatsApp Web login successful!")
                    
                except Exception as e:
                    # Timeout or error
                    self.setup_status.config(
                        text="Status: Please scan QR code, then click 'Setup Complete'",
                        fg="orange"
                    )
                    self.complete_setup_btn.config(state=tk.NORMAL)
                    self.log_message("Waiting for QR code scan...")
                
            except Exception as e:
                self.setup_status.config(
                    text=f"Status: Error - {str(e)}",
                    fg="red"
                )
                self.qr_label.config(text=f"Error: {str(e)}", bg="pink")
                self.start_setup_btn.config(state=tk.NORMAL)
                self.log_message(f"Setup error: {str(e)}")
        
        threading.Thread(target=setup_thread, daemon=True).start()
    
    def capture_and_display_qr(self):
        """Capture QR code from WhatsApp Web and display it - IMPROVED VERSION"""
        if not PIL_AVAILABLE:
            self.qr_label.config(
                text="QR Code is displayed in the browser window\n(Pillow not installed for in-app display)",
                bg="lightyellow"
            )
            return
        
        try:
            from selenium.webdriver.common.by import By
            
            self.log_message("=== QR Code Capture Debug ===")
            
            # Wait longer for QR code to appear
            self.log_message("Waiting 7 seconds for QR code to load...")
            time.sleep(7)  # ✅ INCREASED: Give more time for WhatsApp to load
            
            # Check page status
            try:
                page_title = self.scheduler.whatsapp.driver.title
                self.log_message(f"Page title: {page_title}")
                current_url = self.scheduler.whatsapp.driver.current_url
                self.log_message(f"Current URL: {current_url}")
            except Exception as e:
                self.log_message(f"Could not get page info: {e}")
            
            # Look for ALL canvas elements first
            try:
                canvases = self.scheduler.whatsapp.driver.find_elements(By.TAG_NAME, "canvas")
                self.log_message(f"Found {len(canvases)} canvas elements on page")
                
                for i, canvas in enumerate(canvases):
                    try:
                        size = canvas.size
                        location = canvas.location
                        is_displayed = canvas.is_displayed()
                        self.log_message(f"Canvas {i}: {size['width']}x{size['height']} at ({location['x']}, {location['y']}) - Displayed: {is_displayed}")
                    except:
                        pass
            except Exception as e:
                self.log_message(f"Error checking canvases: {e}")
            
            # Try multiple selectors in priority order
            qr_element = None
            selectors = [
                ('//canvas[@aria-label="Scan this QR code to link a device!"]', "Official QR aria-label"),
                ('//canvas[@role="img"]', "Canvas with role=img"),
                ('//div[contains(@class, "landing-wrapper")]//canvas', "Landing wrapper canvas"),
                ('//div[@data-ref]//canvas', "Data-ref canvas"),
                ('//canvas[contains(@style, "cursor")]', "Canvas with cursor style"),
                ('//canvas', "Any canvas element")
            ]
            
            for xpath, description in selectors:
                try:
                    self.log_message(f"Trying selector: {description}")
                    elements = self.scheduler.whatsapp.driver.find_elements(By.XPATH, xpath)
                    
                    if elements:
                        self.log_message(f"  Found {len(elements)} element(s)")
                        # Use the first visible one
                        for elem in elements:
                            if elem.is_displayed() and elem.size['width'] > 0:
                                qr_element = elem
                                self.log_message(f"✓ SUCCESS: Using {description}")
                                break
                    
                    if qr_element:
                        break
                        
                except Exception as e:
                    self.log_message(f"  Failed: {str(e)}")
                    continue
            
            if not qr_element:
                self.log_message("❌ ERROR: Could not find QR code element with any selector")
                self.qr_label.config(
                    text="QR Code is in the browser window\n(Could not capture automatically)\n\nCheck Activity Log for details",
                    bg="lightyellow",
                    fg="red"
                )
                return
            
            # Take screenshot of the QR code element
            self.log_message("Capturing QR code screenshot...")
            qr_png = qr_element.screenshot_as_png
            
            # Convert to PIL Image
            qr_image = Image.open(io.BytesIO(qr_png))
            
            # Get original size
            original_width, original_height = qr_image.size
            self.log_message(f"Original QR code size: {original_width}x{original_height}")
            
            # Target size for scannable QR code - make it LARGE
            target_size = 500
            
            # Calculate scaling factor
            scale_factor = target_size / min(original_width, original_height)
            
            # Always scale to make QR code large and scannable
            if scale_factor != 1:
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                
                # Use NEAREST for QR codes (keeps sharp edges)
                qr_image = qr_image.resize((new_width, new_height), Image.Resampling.NEAREST)
                self.log_message(f"Scaled QR code to: {new_width}x{new_height}")
            
            # If still too small, scale up more
            if qr_image.size[0] < 400:
                scale_more = 500 / qr_image.size[0]
                new_width = int(qr_image.size[0] * scale_more)
                new_height = int(qr_image.size[1] * scale_more)
                qr_image = qr_image.resize((new_width, new_height), Image.Resampling.NEAREST)
                self.log_message(f"Scaled QR code AGAIN to: {new_width}x{new_height}")
            
            # Convert to PhotoImage
            qr_photo = ImageTk.PhotoImage(qr_image)
            
            # Display in label (clear text, show image only)
            self.qr_label.config(image=qr_photo, text="", bg="white")
            self.qr_label.image = qr_photo  # Keep a reference!
            
            final_width, final_height = qr_image.size
            self.log_message(f"QR code displayed at: {final_width}x{final_height} pixels")
            
            self.setup_status.config(text="Status: Scan the QR code with your phone", fg="orange")
            self.log_message("✓ QR code captured and displayed - should be scannable now!")
            self.log_message("=== QR Code Capture Complete ===")
            
        except Exception as e:
            self.log_message(f"❌ ERROR: Could not capture QR code: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
            self.qr_label.config(
                text=f"Could not capture QR code automatically.\n\nError: {str(e)}\n\nCheck Activity Log for details",
                bg="lightyellow",
                fg="red",
                font=("Arial", 10, "bold")
            )
    
    def complete_whatsapp_setup(self):
        """Complete WhatsApp setup"""
        # Mark setup as complete
        self.db.set_setting("whatsapp_setup_complete", "true")
        
        # Start scheduler
        self.scheduler.start()
        
        self.log_message("Setup complete! You can now use the application.")
        
        messagebox.showinfo(
            "Setup Complete",
            "WhatsApp Web is now connected!\n\n"
            "You can now:\n"
            "1. Add contacts in the Contacts tab\n"
            "2. Create reminders in the Reminders tab\n"
            "3. Test with File > Test Connection\n\n"
            "Keep this app running for reminders to work!"
        )
        
        self.setup_window.destroy()
    
    # =========================================================================
    # MENU BAR
    # =========================================================================
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Test Connection", command=self.test_connection)
        file_menu.add_command(label="Check Missed Reminders", command=self.check_missed)
        file_menu.add_separator()
        
        # Add minimize to tray option if available
        if PYSTRAY_AVAILABLE:
            file_menu.add_command(label="Minimize to Tray", command=self.hide_window)
            file_menu.add_separator()
        
        file_menu.add_command(label="Reset WhatsApp Login", command=self.reset_whatsapp)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        help_menu.add_command(label="About", command=self.show_about)
    
    def reset_whatsapp(self):
        """Reset WhatsApp login"""
        if messagebox.askyesno(
            "Reset WhatsApp",
            "This will log you out of WhatsApp Web and require you to scan QR code again.\n\nContinue?"
        ):
            # Stop scheduler
            self.scheduler.stop()
            
            # Clear browser data
            import shutil
            browser_data = config.BASE_DIR / "browser_data"
            if browser_data.exists():
                try:
                    shutil.rmtree(browser_data)
                    self.log_message("Browser data cleared")
                except Exception as e:
                    self.log_message(f"Error clearing browser data: {e}")
            
            # Reset setup flag
            self.db.set_setting("whatsapp_setup_complete", "false")
            
            # Restart scheduler
            self.whatsapp = WhatsAppService(self.log_message)
            self.scheduler = SchedulerService(self.db, self.whatsapp, self.log_message)
            
            # Show setup wizard
            self.show_first_time_setup()
    
    # =========================================================================
    # MAIN WIDGETS
    # =========================================================================
    
    def create_widgets(self):
        """Create main widgets"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_contacts_tab(notebook)
        self.create_reminders_tab(notebook)
        self.create_log_tab(notebook)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready | Scheduler: Starting...",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.log_message(f"{config.APP_NAME} started")
    
    def create_contacts_tab(self, notebook):
        """Create contacts tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Contacts")
        
        # Left: Contact list
        left = ttk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left, text="Contacts", font=("Arial", 12, "bold")).pack()
        
        # Listbox
        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.contacts_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.contacts_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.contacts_list.yview)
        self.contacts_list.bind('<<ListboxSelect>>', self.on_contact_select)
        
        # Dictionary to map listbox index to contact_id
        self.contact_id_map = {}
        
        # Buttons
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Refresh", command=self.load_contacts).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="New", command=self.clear_contact_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_contact).pack(side=tk.LEFT, padx=2)
        
        # Right: Contact form
        right = ttk.LabelFrame(frame, text="Contact Details")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.contact_name = ttk.Entry(right, width=30)
        self.contact_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(right, text="Phone:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.contact_phone = ttk.Entry(right, width=30)
        self.contact_phone.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(right, text="(+27821234567)", font=("Arial", 8)).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(right, text="Notes:").grid(row=3, column=0, sticky=tk.NW, padx=5, pady=5)
        self.contact_notes = tk.Text(right, width=30, height=4)
        self.contact_notes.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Button(right, text="Save Contact", command=self.save_contact).grid(row=4, column=1, pady=10)
        
        self.selected_contact_id = None
        self.load_contacts()
    
    def create_reminders_tab(self, notebook):
        """Create reminders tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Reminders")
        
        # Top: Reminder list
        top = ttk.Frame(frame)
        top.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(top, text="Scheduled Reminders", font=("Arial", 12, "bold")).pack()
        
        # Treeview
        columns = ("Contact", "Time", "Frequency", "Status")
        self.reminders_tree = ttk.Treeview(top, columns=columns, show="tree headings", height=8)
        
        self.reminders_tree.heading("#0", text="ID")
        self.reminders_tree.column("#0", width=50)
        
        for col in columns:
            self.reminders_tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(top, orient=tk.VERTICAL, command=self.reminders_tree.yview)
        self.reminders_tree.configure(yscrollcommand=scrollbar.set)
        self.reminders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_reminders).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Toggle Active", command=self.toggle_reminder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_reminder).pack(side=tk.LEFT, padx=2)
        
        # Bottom: New reminder form
        form = ttk.LabelFrame(frame, text="Create Reminder")
        form.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(form, text="Contact:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.reminder_contact = ttk.Combobox(form, width=25, state="readonly")
        self.reminder_contact.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form, text="Time:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        time_frame = ttk.Frame(form)
        time_frame.grid(row=0, column=3, padx=5, pady=5)
        
        self.hour = ttk.Spinbox(time_frame, from_=0, to=23, width=5, format="%02.0f")
        self.hour.set("09")
        self.hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute = ttk.Spinbox(time_frame, from_=0, to=59, width=5, format="%02.0f")
        self.minute.set("00")
        self.minute.pack(side=tk.LEFT)
        
        ttk.Label(form, text="Frequency:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.frequency = ttk.Combobox(form, values=config.FREQUENCIES, width=15, state="readonly")
        self.frequency.set("Daily")
        self.frequency.grid(row=1, column=1, padx=5, pady=5)
        self.frequency.bind('<<ComboboxSelected>>', self.on_frequency_change)
        
        # Date pickers for Monthly/Yearly (initially hidden)
        self.day_label = tk.Label(form, text="Day of Month:")
        self.day_spinbox = tk.Spinbox(form, from_=1, to=31, width=5)
        self.day_spinbox.delete(0, tk.END)
        self.day_spinbox.insert(0, "1")
        
        self.month_label = tk.Label(form, text="Month:")
        self.month_combo = ttk.Combobox(form, width=15, state='readonly',
                                       values=["January", "February", "March", "April", 
                                              "May", "June", "July", "August",
                                              "September", "October", "November", "December"])
        self.month_combo.current(0)
        
        self.year_day_label = tk.Label(form, text="Day:")
        self.year_day_spinbox = tk.Spinbox(form, from_=1, to=31, width=5)
        self.year_day_spinbox.delete(0, tk.END)
        self.year_day_spinbox.insert(0, "1")
        
        ttk.Label(form, text="Message:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.message = tk.Text(form, width=60, height=4)
        self.message.grid(row=2, column=1, columnspan=3, padx=5, pady=5)
        
        ttk.Button(form, text="Create Reminder", command=self.create_reminder).grid(row=3, column=1, pady=10)
        
        self.load_reminder_contacts()
        self.load_reminders()
    
    def create_log_tab(self, notebook):
        """Create log tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Activity Log")
        
        ttk.Label(frame, text="Activity Log", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(frame, text="Clear Log", command=self.clear_log).pack(pady=5)
    
    # =========================================================================
    # CONTACT OPERATIONS
    # =========================================================================
    
    def load_contacts(self):
        """Load contacts into list"""
        self.contacts_list.delete(0, tk.END)
        self.contact_id_map.clear()
        contacts = self.db.get_all_contacts()
        
        for idx, contact in enumerate(contacts):
            contact_id, name, phone, notes = contact
            self.contacts_list.insert(tk.END, f"{name} ({phone})")
            self.contact_id_map[idx] = contact_id
    
    def on_contact_select(self, event):
        """Handle contact selection"""
        selection = self.contacts_list.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx in self.contact_id_map:
            contact_id = self.contact_id_map[idx]
            contact = self.db.get_contact(contact_id)
            
            if contact:
                self.selected_contact_id = contact_id
                self.contact_name.delete(0, tk.END)
                self.contact_name.insert(0, contact[1])
                self.contact_phone.delete(0, tk.END)
                self.contact_phone.insert(0, contact[2])
                self.contact_notes.delete(1.0, tk.END)
                self.contact_notes.insert(1.0, contact[3] or "")
    
    def save_contact(self):
        """Save contact"""
        name = self.contact_name.get().strip()
        phone = self.contact_phone.get().strip()
        notes = self.contact_notes.get(1.0, tk.END).strip()
        
        if not name or not phone:
            messagebox.showerror("Error", "Name and phone required!")
            return
        
        valid, msg = config.validate_phone_number(phone)
        if not valid:
            messagebox.showerror("Error", msg)
            return
        
        if self.selected_contact_id:
            self.db.update_contact(self.selected_contact_id, name, phone, notes)
            messagebox.showinfo("Success", "Contact updated!")
        else:
            contact_id = self.db.add_contact(name, phone, notes)
            if contact_id:
                messagebox.showinfo("Success", "Contact added!")
            else:
                messagebox.showerror("Error", "Phone already exists!")
        
        self.clear_contact_form()
        self.load_contacts()
        self.load_reminder_contacts()
    
    def clear_contact_form(self):
        """Clear contact form"""
        self.selected_contact_id = None
        self.contact_name.delete(0, tk.END)
        self.contact_phone.delete(0, tk.END)
        self.contact_notes.delete(1.0, tk.END)
    
    def delete_contact(self):
        """Delete selected contact"""
        selection = self.contacts_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a contact!")
            return
        
        if messagebox.askyesno("Confirm", "Delete contact and reminders?"):
            idx = selection[0]
            if idx in self.contact_id_map:
                contact_id = self.contact_id_map[idx]
                self.db.delete_contact(contact_id)
                self.clear_contact_form()
                self.load_contacts()
                self.load_reminders()
                self.load_reminder_contacts()
                messagebox.showinfo("Success", "Contact deleted!")
    
    # =========================================================================
    # REMINDER OPERATIONS
    # =========================================================================
    
    def load_reminder_contacts(self):
        """Load contacts for reminder dropdown"""
        contacts = self.db.get_all_contacts()
        contact_list = [f"{c[1]} ({c[2]})" for c in contacts]
        self.reminder_contact['values'] = contact_list
        if contact_list:
            self.reminder_contact.current(0)
    
    def on_frequency_change(self, event=None):
        """Show/hide date pickers based on frequency selection"""
        freq = self.frequency.get()
        
        # Hide all date fields first
        self.day_label.grid_remove()
        self.day_spinbox.grid_remove()
        self.month_label.grid_remove()
        self.month_combo.grid_remove()
        self.year_day_label.grid_remove()
        self.year_day_spinbox.grid_remove()
        
        # Show appropriate fields based on frequency
        if freq == "Monthly":
            # Show day picker only
            self.day_label.grid(row=1, column=2, sticky='w', padx=5, pady=5)
            self.day_spinbox.grid(row=1, column=3, sticky='w', padx=5, pady=5)
        
        elif freq == "Yearly":
            # Show month picker on row 1
            self.month_label.grid(row=1, column=2, sticky='w', padx=5, pady=5)
            self.month_combo.grid(row=1, column=3, sticky='w', padx=5, pady=5)
            # Show day picker on same row
            self.year_day_label.grid(row=1, column=4, sticky='w', padx=5, pady=5)
            self.year_day_spinbox.grid(row=1, column=5, sticky='w', padx=5, pady=5)
    
    def create_reminder(self):
        """Create new reminder"""
        if not self.reminder_contact.get():
            messagebox.showerror("Error", "Select a contact!")
            return
        
        # Get contact ID
        contact_text = self.reminder_contact.get()
        contacts = self.db.get_all_contacts()
        contact_id = None
        for c in contacts:
            if f"{c[1]} ({c[2]})" == contact_text:
                contact_id = c[0]
                break
        
        if not contact_id:
            messagebox.showerror("Error", "Invalid contact!")
            return
        
        message_text = self.message.get(1.0, tk.END).strip()
        if not message_text:
            messagebox.showerror("Error", "Enter a message!")
            return
        
        h = int(self.hour.get())
        m = int(self.minute.get())
        schedule_time = f"{h:02d}:{m:02d}"
        freq = self.frequency.get()
        
        # Get date values for Monthly/Yearly
        schedule_day = None
        schedule_month = None
        
        if freq == "Monthly":
            try:
                schedule_day = int(self.day_spinbox.get())
            except:
                schedule_day = 1
        elif freq == "Yearly":
            try:
                month_name = self.month_combo.get()
                month_map = {"January": 1, "February": 2, "March": 3, "April": 4,
                           "May": 5, "June": 6, "July": 7, "August": 8,
                           "September": 9, "October": 10, "November": 11, "December": 12}
                schedule_month = month_map.get(month_name, 1)
                schedule_day = int(self.year_day_spinbox.get())
            except:
                schedule_month = 1
                schedule_day = 1
        
        self.db.add_reminder(contact_id, message_text, schedule_time, freq, schedule_day, schedule_month)
        self.message.delete(1.0, tk.END)
        self.load_reminders()
        
        messagebox.showinfo("Success", "Reminder created!")
        self.log_message(f"Created reminder for {contact_text} at {schedule_time}")
    
    def load_reminders(self):
        """Load reminders"""
        for item in self.reminders_tree.get_children():
            self.reminders_tree.delete(item)
        
        reminders = self.db.get_all_reminders()
        for reminder in reminders:
            # Handle both old format (8 items) and new format (10 items with date fields)
            if len(reminder) == 10:  # New format with schedule_day and schedule_month
                reminder_id, name, phone, msg, time, freq, sday, smonth, active, last = reminder
            else:  # Old format
                reminder_id, name, phone, msg, time, freq, active, last = reminder
                sday, smonth = None, None
            
            status = "[ON] Active" if active else "[OFF] Inactive"
            self.reminders_tree.insert(
                "", tk.END,
                text=str(reminder_id),
                values=(name, time, freq, status),
                tags=(str(reminder_id),)
            )
    
    def toggle_reminder(self):
        """Toggle reminder"""
        selection = self.reminders_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a reminder!")
            return
        
        item = selection[0]
        reminder_id = int(self.reminders_tree.item(item, "text"))
        values = self.reminders_tree.item(item, "values")
        is_active = "Active" in values[3]
        
        self.db.toggle_reminder(reminder_id, not is_active)
        self.load_reminders()
        messagebox.showinfo("Success", f"Reminder {'activated' if not is_active else 'deactivated'}!")
    
    def delete_reminder(self):
        """Delete reminder"""
        selection = self.reminders_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a reminder!")
            return
        
        if messagebox.askyesno("Confirm", "Delete reminder?"):
            item = selection[0]
            reminder_id = int(self.reminders_tree.item(item, "text"))
            self.db.delete_reminder(reminder_id)
            self.load_reminders()
            messagebox.showinfo("Success", "Reminder deleted!")
    
    # =========================================================================
    # UTILITY OPERATIONS
    # =========================================================================
    
    def log_message(self, message):
        """Add to log"""
        try:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        except:
            pass
    
    def clear_log(self):
        """Clear log"""
        self.log_text.delete(1.0, tk.END)
    
    def test_connection(self):
        """Test WhatsApp connection with contact selection"""
        contacts = self.db.get_all_contacts()
        if not contacts:
            messagebox.showerror("Error", "Add a contact first!")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Send Test Message")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (250)
        dialog.geometry(f"500x500+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            main_frame,
            text="Select Contact & Customize Message",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Contact selection
        ttk.Label(main_frame, text="Select Contact:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        contact_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        contact_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=contact_listbox.yview)
        
        # Populate contacts
        contact_map = {}
        for idx, contact in enumerate(contacts):
            contact_id, name, phone, notes = contact
            display_text = f"{name} ({phone})"
            contact_listbox.insert(tk.END, display_text)
            contact_map[idx] = contact
        
        # Select first contact by default
        contact_listbox.selection_set(0)
        
        # Message customization
        ttk.Label(main_frame, text="Test Message:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        message_text = tk.Text(main_frame, width=50, height=5, font=("Arial", 10))
        message_text.pack(fill=tk.X, pady=(0, 10))
        message_text.insert(1.0, f"Test from {config.APP_NAME}\n\nThis is a test message to verify WhatsApp connection.")
        
        # Variables to capture selections
        selected_data = {'contact': None, 'message': None}
        
        def send_test():
            selection = contact_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a contact!", parent=dialog)
                return
            
            # Get message text BEFORE destroying dialog
            message = message_text.get(1.0, tk.END).strip()
            
            if not message:
                messagebox.showwarning("Warning", "Message cannot be empty!", parent=dialog)
                return
            
            # Store both contact and message
            idx = selection[0]
            selected_data['contact'] = contact_map[idx]
            selected_data['message'] = message
            
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Send Test Message",
            command=send_test,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=cancel,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Allow double-click to select
        contact_listbox.bind('<Double-Button-1>', lambda e: send_test())
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # If contact and message were captured, send test message
        if selected_data['contact'] and selected_data['message']:
            contact = selected_data['contact']
            contact_id, name, phone, notes = contact
            message = selected_data['message']
            
            self.log_message(f"Testing with {name} ({phone})...")
            
            def send():
                success, error = self.scheduler.whatsapp.send_message(phone, message)
                if success:
                    self.log_message("[SUCCESS] Test message sent!")
                    messagebox.showinfo("Success", f"Test message sent successfully to {name}!")
                else:
                    self.log_message(f"[FAILED] Test error: {error}")
                    messagebox.showerror("Failed", f"Test failed: {error}")
            
            threading.Thread(target=send, daemon=True).start()
    
    def check_missed(self):
        """Check for missed reminders"""
        self.log_message("Checking for missed reminders...")
        threading.Thread(
            target=self.scheduler.check_missed_reminders,
            daemon=True
        ).start()
    
    def show_instructions(self):
        """Show instructions"""
        msg = f"""
{config.APP_NAME} - Quick Start Guide

STEP 1: ADD CONTACTS
   - Go to Contacts tab
   - Enter name and phone number
   - Phone MUST include country code (+27 for South Africa)
   - Example: +27821234567
   - Click "Save Contact"

STEP 2: CREATE REMINDERS
   - Go to Reminders tab
   - Select a contact from dropdown
   - Set the time (24-hour format)
   - Choose frequency:
     * Once - Send one time only
     * Daily - Every day at that time
     * Weekdays - Monday to Friday only
     * Weekly - Once per week
     * Monthly - Specific day each month (select day 1-31)
     * Yearly - Specific date each year (select month + day)
   - For Monthly/Yearly: Date fields appear automatically
   - Type your message
   - Click "Create Reminder"

STEP 3: TEST
   - Menu > File > Test Connection
   - Select which contact to test with
   - Customize the test message if desired
   - Check Activity Log to see if it worked

STEP 4: USE
   - Keep this application running
   - Messages will send automatically
   - Check Activity Log for sent messages
   - You can minimize the window

MONTHLY/YEARLY REMINDERS:
   - Select "Monthly" to choose day (1-31)
   - Select "Yearly" to choose month and day
   - Example: Monthly day 15 = 15th of every month
   - Example: Yearly June 15 = June 15 every year

MINIMIZE TO TRAY:
   - File > Minimize to Tray
   - App runs completely hidden
   - Right-click tray icon to access features

TIPS:
- Browser runs in background (headless mode)
- Uses minimal resources - won't affect gaming
- First time only: You scanned QR code during setup
- If WhatsApp disconnects: File > Reset WhatsApp Login
- If QR code is too small: Resize the setup window

PHONE NUMBER FORMAT:
   South Africa: +27821234567
   USA: +12125551234
   UK: +447700900123
        """
        
        window = tk.Toplevel(self.root)
        window.title("Instructions")
        window.geometry("600x700")
        
        text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, msg)
        text.config(state=tk.DISABLED)
        
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)
    
    def show_about(self):
        """Show about"""
        messagebox.showinfo(
            "About",
            f"{config.APP_NAME} v{config.VERSION}\n\n"
            "Lightweight WhatsApp reminder system\n"
            "Optimized for gaming PCs\n\n"
            "Features:\n"
            "- Headless browser (low resources)\n"
            "- Contact management\n"
            "- Flexible scheduling\n"
            "- Monthly/Yearly date selection\n"
            "- Activity logging\n"
            "- Missed reminder recovery\n"
            "- System tray support\n"
            "- Custom test messages\n\n"
            "Created for personal use\n"
            "Free and open source"
        )
    
    def on_closing(self):
        """Handle window close"""
        if messagebox.askyesno("Quit", "Stop service and exit?"):
            self.log_message("Shutting down...")
            self.status_bar.config(text="Stopping scheduler...")
            self.scheduler.stop()
            
            # Stop tray icon if running
            if self.tray_icon:
                self.tray_icon.stop()
            
            self.root.destroy()

# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppReminderGUI(root)
    root.mainloop()