"""
Database Manager - SQLite operations
Handles all database interactions
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import config

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path=None):
        """Initialize database manager"""
        self.db_path = db_path or config.DB_PATH
        self.init_database()
        self.migrate_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                message TEXT NOT NULL,
                schedule_time TEXT NOT NULL,
                frequency TEXT NOT NULL,
                schedule_day INTEGER,
                schedule_month INTEGER,
                is_active BOOLEAN DEFAULT 1,
                last_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)
        
        # Message log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER,
                phone TEXT,
                message TEXT,
                status TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE SET NULL
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def migrate_database(self):
        """Add new columns if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(reminders)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'schedule_day' not in columns:
                cursor.execute("ALTER TABLE reminders ADD COLUMN schedule_day INTEGER")
            
            if 'schedule_month' not in columns:
                cursor.execute("ALTER TABLE reminders ADD COLUMN schedule_month INTEGER")
            
            conn.commit()
        except Exception as e:
            print(f"Migration error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # =========================================================================
    # CONTACT OPERATIONS
    # =========================================================================
    
    def add_contact(self, name, phone, notes=""):
        """Add new contact"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO contacts (name, phone, notes) VALUES (?, ?, ?)",
                (name, phone, notes)
            )
            conn.commit()
            contact_id = cursor.lastrowid
            print(f"Contact added: {name} ({phone})")
            return contact_id
        except sqlite3.IntegrityError:
            print(f"Contact already exists: {phone}")
            return None
        finally:
            conn.close()
    
    def get_all_contacts(self):
        """Get all contacts"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, notes FROM contacts ORDER BY name")
        contacts = cursor.fetchall()
        conn.close()
        return contacts
    
    def get_contact(self, contact_id):
        """Get single contact by ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, notes FROM contacts WHERE id=?", (contact_id,))
        contact = cursor.fetchone()
        conn.close()
        return contact
    
    def update_contact(self, contact_id, name, phone, notes):
        """Update contact"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE contacts SET name=?, phone=?, notes=? WHERE id=?",
            (name, phone, notes, contact_id)
        )
        conn.commit()
        conn.close()
        print(f"Contact updated: {name}")
        return True
    
    def delete_contact(self, contact_id):
        """Delete contact and associated reminders"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE contact_id=?", (contact_id,))
        cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        conn.commit()
        conn.close()
        print(f"Contact deleted: ID {contact_id}")
        return True
    
    # =========================================================================
    # REMINDER OPERATIONS
    # =========================================================================
    
    def add_reminder(self, contact_id, message, schedule_time, frequency, schedule_day=None, schedule_month=None):
        """Add new reminder"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO reminders 
            (contact_id, message, schedule_time, frequency, schedule_day, schedule_month) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (contact_id, message, schedule_time, frequency, schedule_day, schedule_month)
        )
        conn.commit()
        reminder_id = cursor.lastrowid
        conn.close()
        print(f"Reminder added: ID {reminder_id}")
        return reminder_id
    
    def get_all_reminders(self):
        """Get all reminders with contact info"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, c.name as contact_name, c.phone, r.message, r.schedule_time, 
                   r.frequency, r.schedule_day, r.schedule_month, r.is_active, r.last_sent
            FROM reminders r
            JOIN contacts c ON r.contact_id = c.id
            ORDER BY r.schedule_time
        """)
        reminders = cursor.fetchall()
        conn.close()
        return reminders
    
    def get_active_reminders(self):
        """Get only active reminders"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, c.name as contact_name, c.phone, r.message, r.schedule_time, 
                   r.frequency, r.schedule_day, r.schedule_month, r.last_sent
            FROM reminders r
            JOIN contacts c ON r.contact_id = c.id
            WHERE r.is_active = 1
            ORDER BY r.schedule_time
        """)
        reminders = cursor.fetchall()
        conn.close()
        return [dict(row) for row in reminders]
    
    def update_reminder_status(self, reminder_id, is_active):
        """Enable/disable reminder"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reminders SET is_active=? WHERE id=?",
            (is_active, reminder_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def toggle_reminder(self, reminder_id, is_active):
        """Toggle reminder (alias for update_reminder_status)"""
        return self.update_reminder_status(reminder_id, is_active)
    
    def delete_reminder(self, reminder_id):
        """Delete reminder"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
        conn.commit()
        conn.close()
        print(f"Reminder deleted: ID {reminder_id}")
        return True
    
    def update_last_sent(self, reminder_id):
        """Update last sent timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "UPDATE reminders SET last_sent=? WHERE id=?",
            (now, reminder_id)
        )
        conn.commit()
        conn.close()
    
    # =========================================================================
    # MESSAGE LOG OPERATIONS
    # =========================================================================
    
    def log_message(self, reminder_id, phone, message, status, error_message=None):
        """Log sent message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO message_log 
            (reminder_id, phone, message, status, error_message) 
            VALUES (?, ?, ?, ?, ?)""",
            (reminder_id, phone, message, status, error_message)
        )
        conn.commit()
        conn.close()
    
    def get_message_log(self, limit=100):
        """Get recent message log"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, reminder_id, phone, message, status, sent_at, error_message
            FROM message_log
            ORDER BY sent_at DESC
            LIMIT ?
        """, (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    def cleanup_old_logs(self, days=30):
        """Delete logs older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM message_log 
            WHERE sent_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"Cleaned up {deleted} old log entries")
        return deleted
    
    # =========================================================================
    # SETTINGS OPERATIONS
    # =========================================================================
    
    def get_setting(self, key, default=None):
        """Get setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    def set_setting(self, key, value):
        """Set setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()
    
    # =========================================================================
    # UTILITY OPERATIONS
    # =========================================================================
    
    def get_stats(self):
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminders")
        total_reminders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE is_active=1")
        active_reminders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message_log")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message_log WHERE status='sent'")
        successful_messages = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_contacts': total_contacts,
            'total_reminders': total_reminders,
            'active_reminders': active_reminders,
            'total_messages': total_messages,
            'successful_messages': successful_messages,
        }
    
    def backup_database(self, backup_path=None):
        """Create database backup"""
        import shutil
        
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Path(self.db_path).parent / f"backup_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path