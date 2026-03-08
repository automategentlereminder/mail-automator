import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "mailer_state.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            subject TEXT,
            body TEXT,
            variants TEXT -- JSON array of variant strings
        )
    ''')
    
    # Campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            csv_path TEXT,
            template_id INTEGER,
            status TEXT, -- DRAFT, RUNNING, PAUSED, COMPLETED
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Queue / History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            email_address TEXT,
            row_data TEXT, -- JSON serialization of row data
            status TEXT, -- PENDING, SENT, FAILED
            error_message TEXT,
            sent_at TIMESTAMP,
            variant_used TEXT,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        )
    ''')
    
    # Contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            email TEXT,
            field_data TEXT, -- JSON representation of other CSV fields
            is_active INTEGER DEFAULT 1,
            UNIQUE(category, email)
        )
    ''')
    
    conn.commit()
    
    # Insert default settings if empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = {
            "daily_limit": "50",
            "pulse_min": "300",
            "pulse_max": "600",
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "skip_weekends": "1"
        }
        for k, v in default_settings.items():
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()

    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

