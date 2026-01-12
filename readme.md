# WhatsApp Reminder Manager

**Never forget important messages again.** Automate your WhatsApp reminders with a lightweight, gaming-PC-optimized desktop application that runs silently in the background.

---

## 🌟 Why Use This?

### **Set It and Forget It**
Create reminders once, and they'll automatically send WhatsApp messages at exactly the right time - every day, every week, monthly, or yearly. No more manual reminders!

### **Perfect For:**
- 💊 **Medication reminders** - Daily pills, weekly vitamins
- 💰 **Payment reminders** - Monthly rent, bills, subscriptions
- 🎂 **Birthday wishes** - Never forget a birthday again (yearly reminders)
- 👪 **Family check-ins** - Daily "good morning" to loved ones
- 📅 **Event reminders** - Weekly team meetings, monthly reports
- 💼 **Client follow-ups** - Regular business touchpoints
- 🏋️ **Habit tracking** - Daily workout reminders, weekly meal prep
- 📚 **Study schedules** - Consistent learning reminders

### **Optimized for Gamers**
- Uses **< 1% CPU** when idle
- Only **~150-200 MB RAM** (headless browser)
- **Below Normal process priority** - won't affect your game performance
- Runs completely hidden in system tray
- No interruptions while gaming

---

## ✨ Key Features

### 🔄 **Flexible Scheduling**
- **Once** - Send a one-time reminder
- **Daily** - Every day at a specific time
- **Weekdays** - Monday through Friday only (great for work reminders)
- **Weekly** - Once per week
- **Monthly** - Specific day each month (e.g., 15th of every month)
- **Yearly** - Specific date each year (e.g., June 15 for birthdays)

### 📱 **Smart Contact Management**
- Store unlimited contacts with notes
- International phone number support (+country code)
- Easy-to-use interface
- Quick search and edit

### 🎯 **Reliable Delivery**
- **Missed reminder recovery** - Sends missed messages on startup
- **Auto-retry on failure** - Tries 3 times if sending fails
- **Persistent browser session** - Stays logged into WhatsApp Web
- **Activity logging** - Track all sent messages

### 🔒 **Privacy & Security**
- ✅ **100% local** - No cloud services, no external servers
- ✅ **Your WhatsApp account** - Uses your own WhatsApp Web session
- ✅ **No data collection** - All data stored in local SQLite database
- ✅ **Open source** - Review the code yourself

### 🎮 **Gaming-Optimized Performance**
- **Headless browser** - No visible window, minimal resources
- **Low CPU usage** - < 1% idle, ~5% when sending
- **Low memory footprint** - ~150-200 MB total
- **Adjustable priority** - Set to "low" for zero game impact
- **System tray operation** - Completely hidden while gaming

### 🛠️ **Easy to Use**
- **One-time QR setup** - Scan once, stays connected
- **Simple GUI** - No command line needed
- **Test before use** - Built-in connection testing
- **Visual feedback** - Activity log shows all operations
- **Windows .bat launcher** - Double-click to start

---

## 🎯 Real-World Use Cases

### **Healthcare Reminders**
```
Contact: Mom
Frequency: Daily at 09:00
Message: "Good morning Mom! Time for your morning medication 💊"
```

### **Rent Payment Reminder**
```
Contact: Landlord
Frequency: Monthly (day 1) at 08:00
Message: "Hi! Just confirming rent payment for this month. Will transfer today."
```

### **Birthday Wishes**
```
Contact: Best Friend
Frequency: Yearly (June 15) at 09:00
Message: "🎂 Happy Birthday! Wishing you an amazing year ahead! 🎉"
```

### **Weekly Team Check-in**
```
Contact: Team Lead
Frequency: Weekly (Mondays) at 10:00
Message: "Good morning! Ready for our weekly sync meeting at 11:00."
```

### **Daily Motivation**
```
Contact: Workout Buddy
Frequency: Weekdays at 06:00
Message: "🏋️ Rise and grind! Gym session at 7:00. You in?"
```

---

## 📁 File Structure

```
whatsapp_reminder_manager/
│
├── config.py                 # Configuration settings
├── database.py              # Database operations (SQLite)
├── whatsapp_service.py      # WhatsApp sending (Selenium)
├── scheduler_service.py     # Background scheduler
├── gui.py                   # GUI interface
├── main.py                  # Entry point (run this!)
├── requirements.txt         # Dependencies
├── START_APP.bat           # Windows launcher
│
├── whatsapp_reminders.db   # Database (auto-created)
├── browser_data/           # Browser session (auto-created)
└── whatsapp_manager.log    # Log file (auto-created)
```

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

**Installs:**
- `selenium` - Browser automation
- `webdriver-manager` - Auto Chrome driver management
- `schedule` - Task scheduling
- `pillow` - GUI icons & QR code display
- `pystray` - System tray support
- `psutil` - Process priority management

### **2. Run the Application**

**Windows:**
```bash
# Double-click START_APP.bat
# OR run:
python main.py
```

**Linux/Mac:**
```bash
python main.py
```

### **3. First Time Setup (One-Time Only)**

1. Application opens and shows setup wizard
2. Click "**Start Setup**"
3. QR code appears in the window
4. Open WhatsApp on your phone
5. Tap **Menu → Linked Devices → Link a Device**
6. Scan the QR code
7. Click "**Setup Complete**" when ready
8. ✅ Done! You're connected

### **4. Add Your First Contact**

1. Go to **Contacts** tab
2. Enter details:
   - **Name:** Mom
   - **Phone:** +27821234567 *(must include country code)*
   - **Notes:** Daily medication reminder
3. Click "**Save Contact**"

### **5. Create Your First Reminder**

1. Go to **Reminders** tab
2. Select contact from dropdown
3. Set time (e.g., **09:00** for 9 AM)
4. Choose frequency (e.g., **Daily**)
5. Type your message
6. Click "**Create Reminder**"

### **6. Test It Works**

1. Menu → **File → Test Connection**
2. Select a contact
3. Customize test message (optional)
4. Click "Send Test Message"
5. Check your phone! 📱

---

## ⚙️ Configuration

Edit `config.py` to customize behavior:

### **Performance Tuning**

```python
# Browser settings
HEADLESS_BROWSER = True          # No visible window (recommended)
BROWSER = 'chrome'               # chrome, firefox, or edge
PROCESS_PRIORITY = 'below_normal' # Won't affect game performance

# Scheduler settings
CHECK_INTERVAL = 30              # Check every 30 seconds
CHECK_MISSED_ON_STARTUP = True   # Send missed reminders on startup

# Performance
KEEP_BROWSER_ALIVE = True        # Faster subsequent sends
BROWSER_TIMEOUT = 300            # Close browser after 5 min idle
```

### **For Maximum Gaming Performance**

```python
HEADLESS_BROWSER = True
PROCESS_PRIORITY = 'low'         # Lowest possible priority
CHECK_INTERVAL = 60              # Check less frequently
KEEP_BROWSER_ALIVE = False       # Close browser between sends
```

### **For Fastest Message Sending**

```python
KEEP_BROWSER_ALIVE = True        # Browser stays open
CHECK_INTERVAL = 30              # Check frequently
PROCESS_PRIORITY = 'below_normal'
```

---

## 📊 Resource Usage

### **Typical Usage (Headless Mode)**
| Metric | Value | Impact |
|--------|-------|--------|
| CPU (Idle) | < 1% | None |
| CPU (Sending) | ~5% | Minimal |
| RAM | 150-200 MB | Low |
| Disk Space | ~50 MB | Minimal |
| Network | Minimal | Only when sending |

### **Process Priority**
- Default: **Below Normal** - Won't affect gaming or heavy tasks
- Optional: **Low** - Absolute minimum priority
- Adjustable in config.py

---

## 📱 Phone Number Format

**IMPORTANT:** Always include country code with `+` prefix

### ✅ Correct Format:
```
South Africa:  +27821234567
USA:           +12125551234
UK:            +447700900123
India:         +919876543210
Germany:       +491234567890
```

### ❌ Wrong Format:
```
0821234567        (missing country code)
27821234567       (missing + symbol)
+27 82 123 4567   (has spaces - remove them)
```

---

## 🎮 Gaming-Optimized Features

### **Run Silently in Background**
1. **Minimize to System Tray**
   - File → Minimize to Tray
   - App disappears completely
   - Right-click tray icon to access

2. **Low Resource Usage**
   - Configured for minimal CPU/RAM
   - Automatically closes browser when idle
   - Below normal process priority

3. **No Interruptions**
   - No popup notifications
   - No sound alerts
   - Completely silent operation

### **Performance Tips**
1. Set `PROCESS_PRIORITY = 'low'` for zero game impact
2. Increase `CHECK_INTERVAL = 60` to check less often
3. Use `HEADLESS_BROWSER = True` always
4. Minimize to tray while gaming

---

## 🔧 Advanced Features

### **Missed Reminder Recovery**
If your PC was off when a reminder was due:
- On startup, checks last 24 hours for missed reminders
- Automatically sends them with "⚠️ MISSED REMINDER" prefix
- Configurable time window in config.py

### **System Tray Integration**
Right-click tray icon for quick access:
- Show/Hide Window
- Test Connection
- Check Missed Reminders
- Exit Application

### **Activity Logging**
- Every action logged with timestamp
- See all sent messages in Activity Log tab
- Track success/failure rates
- Debug issues easily

### **Frequency Intelligence**

**Monthly Reminders:**
- Handles months with different days (31, 30, 28/29)
- Example: Reminder on 31st → sends on last day of February (28/29)

**Yearly Reminders:**
- Perfect for birthdays, anniversaries
- Handles leap years automatically
- Won't send on Feb 29 in non-leap years

---

## 🔍 Troubleshooting

### **QR Code Not Appearing**
```bash
# Set in config.py:
HEADLESS_BROWSER = False  # Shows browser window

# Or check Activity Log tab for debug info
```

### **Messages Not Sending**
1. Check Activity Log for errors
2. File → Test Connection
3. Verify WhatsApp Web is logged in
4. Check phone number format (+27...)
5. File → Reset WhatsApp Login (if needed)

### **High Resource Usage**
```python
# In config.py:
PROCESS_PRIORITY = 'low'
KEEP_BROWSER_ALIVE = False
CHECK_INTERVAL = 60
```

### **Browser Errors**
```bash
# Update Chrome driver:
pip install webdriver-manager --upgrade

# Clear browser data:
# Delete the 'browser_data' folder
# Run app and scan QR code again
```

### **Database Issues**
```bash
# Backup then recreate:
# Rename: whatsapp_reminders.db to whatsapp_reminders.db.backup
# Run app - creates fresh database
```

---

## 💡 Pro Tips

### **Effective Reminder Messages**
```
✅ Clear and specific:
"Hi Mom! Time for your 9am blood pressure medication 💊"

✅ Include context:
"Rent payment ($1200) due today. Transferring now!"

✅ Add emojis:
"🎂 Happy Birthday Sarah! Hope you have an amazing day! 🎉"

❌ Too vague:
"Don't forget"
```

### **Frequency Selection Guide**
- **Once** → One-time events (appointments, specific deadlines)
- **Daily** → Medications, morning routines, daily habits
- **Weekdays** → Work-related reminders, weekday routines
- **Weekly** → Weekly meetings, grocery shopping, meal prep
- **Monthly** → Bills, rent, monthly check-ins (with day selection)
- **Yearly** → Birthdays, anniversaries, annual renewals (with month + day)

### **Contact Organization**
Use the **Notes** field effectively:
```
Name: Dr. Smith
Phone: +27123456789
Notes: Monthly checkup appointment - 3rd Thursday
```

### **Testing Your Setup**
1. Create a "Once" reminder for 2 minutes from now
2. Monitor Activity Log
3. Check your phone when it triggers
4. Verify message sent successfully

---

## 🔒 Privacy & Security

### **What Data is Stored?**
- Contact names and phone numbers (encrypted in SQLite)
- Reminder messages and schedules
- Message send history (timestamps only)
- WhatsApp Web session cookies (local browser_data folder)

### **What's NOT Collected?**
- ❌ No cloud sync
- ❌ No external servers
- ❌ No analytics or tracking
- ❌ No message content uploaded anywhere
- ❌ No access to your WhatsApp messages

### **Data Location**
- `whatsapp_reminders.db` - SQLite database (local only)
- `browser_data/` - Chrome session data (local only)
- `whatsapp_manager.log` - Activity log (local only)

### **Backup Your Data**
```python
from database import DatabaseManager

db = DatabaseManager()
db.backup_database('my_backup.db')
```

---

## 🆘 Common Questions

### **Q: Does this send messages from my WhatsApp?**
**A:** Yes! It uses WhatsApp Web with your account. Recipients see messages from YOU.

### **Q: Do I need to keep my phone online?**
**A:** Yes, WhatsApp Web requires your phone to be connected to the internet.

### **Q: Can I use this on multiple computers?**
**A:** Yes, but each computer needs its own QR code scan and setup.

### **Q: Will this drain my PC resources while gaming?**
**A:** No! Uses <1% CPU and ~150MB RAM with "Below Normal" priority. Won't affect games.

### **Q: What happens if my PC is off when a reminder is due?**
**A:** Missed reminders are automatically sent when you start the app (within 24hr window).

### **Q: Can I edit a reminder after creating it?**
**A:** Currently no, but you can delete and recreate. Edit feature coming in future version!

### **Q: Does this work with WhatsApp Business?**
**A:** Yes! Scan the QR code with your WhatsApp Business account.

### **Q: Is this official WhatsApp software?**
**A:** No, this is an independent automation tool using WhatsApp Web.

---

## 🚧 Roadmap / Future Features

- [ ] Edit existing reminders
- [ ] Recurring reminders with custom intervals
- [ ] Import/export contacts and reminders
- [ ] Multiple WhatsApp accounts support
- [ ] Reminder templates library
- [ ] Statistics dashboard
- [ ] Message preview before sending
- [ ] Conditional reminders (if/then logic)
- [ ] Group message support

---

## 📝 Contributing

Found a bug? Want a feature? 
- Open an issue with detailed description
- Include Activity Log output for bugs
- Suggest improvements

---

## 📜 License

**Free for personal use.** No warranty provided.

---

## 🎯 Get Started Now!

1. ✅ Install: `pip install -r requirements.txt`
2. ✅ Run: `python main.py`
3. ✅ Scan QR code (one time)
4. ✅ Add contacts
5. ✅ Create reminders
6. ✅ Minimize and forget!

---

## 🙏 Acknowledgments

Built for personal use and optimized for gaming PCs. Uses:
- Selenium for browser automation
- WhatsApp Web for messaging
- SQLite for local data storage
- Tkinter for GUI

---

**Never miss an important message again. Start automating your WhatsApp reminders today!** 🚀📱

*Lightweight • Reliable • Privacy-First • Gaming-Optimized*