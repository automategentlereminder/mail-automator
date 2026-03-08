import time
import json
import sqlite3
import datetime
import traceback
from PySide6.QtCore import QThread, Signal
from core.database import DB_PATH, get_setting
from core.scheduler import Scheduler
from core.outlook_engine import OutlookEngine
from core.template_parser import TemplateParser

class CampaignWorker(QThread):
    progress = Signal(int, int) # Current, Total
    status = Signal(str) # Status message
    finished = Signal(bool, str) # Success flag, message
    error = Signal(str) # Error message
    
    def __init__(self, campaign_id, mode="SEND"):
        super().__init__()
        self.campaign_id = campaign_id
        self.mode = mode # "SEND" or "DRAFT"
        self.is_paused = False
        self.is_cancelled = False
        self.outlook = OutlookEngine()

    def run(self):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 1. Fetch Campaign and Template Info
            cursor.execute("SELECT template_id FROM campaigns WHERE id=?", (self.campaign_id,))
            camp_row = cursor.fetchone()
            if not camp_row:
                self.finished.emit(False, "Campaign not found.")
                return
                
            template_id = camp_row[0]
            cursor.execute("SELECT subject, body, variants FROM templates WHERE id=?", (template_id,))
            temp_row = cursor.fetchone()
            if not temp_row:
                self.finished.emit(False, "Template not found.")
                return
                
            template_subject = temp_row[0]
            template_body = temp_row[1]
            variants_str = temp_row[2]
            
            # Optional variants overriding body
            if variants_str and variants_str != "[]":
                try:
                    variants_list = json.loads(variants_str)
                    if isinstance(variants_list, list) and len(variants_list) > 0:
                        template_body = variants_list # We will use round-robin
                except:
                    pass

            # 2. Fetch queue items
            cursor.execute("SELECT id, email_address, row_data FROM queue WHERE campaign_id=? AND status='PENDING'", (self.campaign_id,))
            pending_items = cursor.fetchall()
            
            if not pending_items:
                self.status.emit("No pending items found.")
                self.finished.emit(True, "Completed")
                return
                
            total_items = len(pending_items)
            self.progress.emit(0, total_items)
            
            # Start loop
            sent_today = 0 # In a real scenario, fetch count of emails sent today from DB
            today_str = datetime.date.today().isoformat()
            cursor.execute("SELECT COUNT(*) FROM queue WHERE status='SENT' AND date(sent_at)=?", (today_str,))
            sent_today = cursor.fetchone()[0]

            for i, (queue_id, email, row_data_str) in enumerate(pending_items):
                if self.is_cancelled:
                    self.status.emit("Worker cancelled.")
                    break
                    
                while self.is_paused:
                    time.sleep(1)
                    if self.is_cancelled:
                        break
                        
                if self.is_cancelled:
                    break

                # The Humanizer checks
                if self.mode == "SEND":
                    can_send, reason = Scheduler.can_send_now()
                    while not can_send:
                        self.status.emit(f"Waiting: {reason}")
                        for _ in range(10): # Smaller increments for responsiveness
                            time.sleep(1)
                            if self.is_paused or self.is_cancelled:
                                break
                                
                        if self.is_cancelled:
                            break
                        if not self.is_paused:
                            can_send, reason = Scheduler.can_send_now()
                            
                    if self.is_cancelled:
                        break
                    
                    under_limit, limit_reason = Scheduler.check_daily_limit(sent_today)
                    if not under_limit:
                        self.status.emit(limit_reason)
                        # Optionally we could pause here or break
                        # Since user wants 'allow sending over limit anyway', we just warn.
                        self.status.emit(f"Warning: {limit_reason}")
                
                # Render Email
                row_data = {}
                try:
                    row_data = json.loads(row_data_str)
                except:
                    pass
                
                # Handle variants
                current_body = template_body
                variant_used = "Default"
                if isinstance(template_body, list):
                    current_body = template_body[i % len(template_body)]
                    variant_used = f"Variant {i % len(template_body) + 1}"
                    
                subject = TemplateParser.render(template_subject, row_data, apply_spintax=True)
                body = TemplateParser.render(current_body, row_data, apply_spintax=True)
                
                self.status.emit(f"Processing {email} ({variant_used})...")
                
                # Send or Draft
                if self.mode == "DRAFT":
                    success, msg = self.outlook.create_draft(email, subject, body)
                else:
                    success, msg = self.outlook.send_email(email, subject, body)
                    
                now_str = datetime.datetime.now().isoformat()
                if success:
                    cursor.execute("UPDATE queue SET status=?, sent_at=?, variant_used=?, error_message=? WHERE id=?", 
                                  ("SENT" if self.mode == "SEND" else "DRAFTED", now_str, variant_used, msg, queue_id))
                    sent_today += 1
                else:
                    cursor.execute("UPDATE queue SET status=?, sent_at=?, variant_used=?, error_message=? WHERE id=?", 
                                  ("FAILED", now_str, variant_used, msg, queue_id))
                
                conn.commit()
                self.progress.emit(i+1, total_items)
                
                # The Pulse delay (only if SEND and not the last item)
                if self.mode == "SEND" and i < total_items - 1:
                    delay = Scheduler.get_pulse_delay()
                    for s in range(delay):
                        if self.is_cancelled:
                            break
                        # We use 1-second sleeps to keep thread responsive to pause/cancel
                        while self.is_paused:
                            time.sleep(1)
                            if self.is_cancelled:
                                break
                        self.status.emit(f"Pulse waiting... {delay - s}s remaining.")
                        time.sleep(1)

            # End of loop
            if self.is_cancelled:
                cursor.execute("UPDATE campaigns SET status='CANCELLED' WHERE id=?", (self.campaign_id,))
                cursor.execute("UPDATE queue SET status='CANCELLED' WHERE campaign_id=? AND status='PENDING'", (self.campaign_id,))
                conn.commit()
                self.finished.emit(False, "Worker was cancelled by user.")
            else:
                cursor.execute("UPDATE campaigns SET status='COMPLETED' WHERE id=?", (self.campaign_id,))
                conn.commit()
                self.finished.emit(True, "Finished Processing Queue")
            
        except Exception as e:
            err_msg = str(e) + "\n" + traceback.format_exc()
            self.error.emit(err_msg)
            self.finished.emit(False, "Error: " + str(e))
        finally:
            if conn:
                conn.close()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def cancel(self):
        self.is_cancelled = True
        self.is_paused = False
