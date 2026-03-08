import sqlite3
import pandas as pd
import json
import datetime
import os
import math
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, 
                               QHeaderView, QTableWidgetItem, QScrollArea)
from qfluentwidgets import (TitleLabel, SubtitleLabel, ComboBox, PrimaryPushButton, 
                            PushButton, CardWidget, InfoBar, LineEdit, BodyLabel, 
                            ProgressBar, Dialog, MessageBox, SegmentedWidget,
                            TableWidget, CheckBox)
from core.database import DB_PATH
from core.worker import CampaignWorker
from core.scheduler import Scheduler

class CampaignsInterface(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("CampaignsInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        headerLayout = QHBoxLayout()
        self.titleLabel = TitleLabel("Campaigns", self)
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        
        # Segmented Control for Audience vs Launch
        self.segmentWidget = SegmentedWidget(self)
        self.segmentWidget.addItem('audience', 'Audience Manager')
        self.segmentWidget.addItem('launch', 'Launch Campaign')
        self.segmentWidget.currentItemChanged.connect(self.on_tab_changed)
        headerLayout.addWidget(self.segmentWidget)
        headerLayout.addStretch(1)
        
        self.guideBtn = PushButton("📖 Guide", self)
        self.guideBtn.clicked.connect(self.show_guide)
        headerLayout.addWidget(self.guideBtn)
        self.vBoxLayout.addLayout(headerLayout)
        
        self.worker = None
        
        self._setup_audience_manager()
        self._setup_launch_manager()
        self._setup_progress()
        
        self.vBoxLayout.addStretch(1)
        
        self.segmentWidget.setCurrentItem('launch')

    # --- TAB ROUTING ---
    def on_tab_changed(self, item_key):
        if item_key == 'audience':
            self.audienceCard.setVisible(True)
            self.launchCard.setVisible(False)
        else:
            self.refresh_audience_categories()
            self.refresh_templates() # Fix bug: ensure dropdown reloads
            self.update_status_tag()
            self.audienceCard.setVisible(False)
            self.launchCard.setVisible(True)

    # --- AUDIENCE MANAGER ---
    def _setup_audience_manager(self):
        self.audienceCard = CardWidget(self)
        layout = QVBoxLayout(self.audienceCard)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        layout.addWidget(SubtitleLabel("Import & Manage Audiences", self.audienceCard))
        
        # CSV
        cLayout = QHBoxLayout()
        cLayout.addWidget(BodyLabel("1. Contacts File (CSV):", self.audienceCard))
        self.csvPathEdit = LineEdit(self.audienceCard)
        self.csvPathEdit.setReadOnly(True)
        self.browseBtn = PushButton("Browse", self.audienceCard)
        self.browseBtn.clicked.connect(self.browse_csv)
        cLayout.addWidget(self.csvPathEdit)
        cLayout.addWidget(self.browseBtn)
        layout.addLayout(cLayout)
        
        # Column Map & Category
        optLayout = QHBoxLayout()
        optLayout.addWidget(BodyLabel("2. Map Email Column:", self.audienceCard))
        self.emailColumnCombo = ComboBox(self.audienceCard)
        optLayout.addWidget(self.emailColumnCombo)
        
        optLayout.addSpacing(16)
        optLayout.addWidget(BodyLabel("3. Category/Group Name:", self.audienceCard))
        self.categoryEdit = LineEdit(self.audienceCard)
        self.categoryEdit.setPlaceholderText("e.g. CEOs List Q3")
        optLayout.addWidget(self.categoryEdit)
        optLayout.addStretch(1)
        layout.addLayout(optLayout)
        
        # Action
        aLayout = QHBoxLayout()
        self.importBtn = PrimaryPushButton("Import Contacts to Database", self.audienceCard)
        self.importBtn.clicked.connect(self.import_contacts)
        aLayout.addWidget(self.importBtn)
        aLayout.addStretch(1)
        layout.addLayout(aLayout)
        
        # --- Manage Existing Categories ---
        layout.addSpacing(16)
        layout.addWidget(SubtitleLabel("Manage Existing Categories", self.audienceCard))
        
        mngLayout = QHBoxLayout()
        mngLayout.addWidget(BodyLabel("Select Category:", self.audienceCard))
        self.audienceCategoryCombo = ComboBox(self.audienceCard)
        self.audienceCategoryCombo.setMinimumWidth(200)
        self.audienceCategoryCombo.currentTextChanged.connect(self.on_category_selected)
        mngLayout.addWidget(self.audienceCategoryCombo)
        
        self.deleteCategoryBtn = PushButton("🗑 Delete Entire Category", self.audienceCard)
        self.deleteCategoryBtn.setStyleSheet("color: #d83b01;")
        self.deleteCategoryBtn.clicked.connect(self.delete_entire_category)
        mngLayout.addWidget(self.deleteCategoryBtn)
        mngLayout.addStretch(1)
        layout.addLayout(mngLayout)
        
        # Paginated Table
        layout.addWidget(BodyLabel("Unselect IDs to not use in campaigns (Selection persists automatically):", self.audienceCard))
        self.table = TableWidget(self.audienceCard)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Active", "Email", "Data Preview"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setMinimumHeight(400)
        layout.addWidget(self.table)
        
        # Pagination Controls
        pagLayout = QHBoxLayout()
        
        # Master checkbox for page check/uncheck
        self.pageCheckBtn = PushButton("Select / Deselect Page", self.audienceCard)
        self.pageCheckBtn.clicked.connect(self.toggle_page_checkboxes)
        pagLayout.addWidget(self.pageCheckBtn)
        pagLayout.addSpacing(16)
        
        self.prevBtn = PushButton("< Prev 100", self.audienceCard)
        self.prevBtn.clicked.connect(self.prev_page)
        self.pageLabel = BodyLabel("Page 1 / 1", self.audienceCard)
        self.nextBtn = PushButton("Next 100 >", self.audienceCard)
        self.nextBtn.clicked.connect(self.next_page)
        
        pagLayout.addStretch(1)
        pagLayout.addWidget(self.prevBtn)
        pagLayout.addWidget(self.pageLabel)
        pagLayout.addWidget(self.nextBtn)
        layout.addLayout(pagLayout)
        
        # Table Actions
        tblActLayout = QHBoxLayout()
        self.addContactBtn = PushButton("➕ Add Contact to Group", self.audienceCard)
        self.addContactBtn.clicked.connect(self.add_single_contact)
        
        self.deleteSelectedBtn = PushButton("🗑 Delete Selected from Group", self.audienceCard)
        self.deleteSelectedBtn.setStyleSheet("color: #d83b01;")
        self.deleteSelectedBtn.clicked.connect(self.delete_selected_contacts)
        
        tblActLayout.addWidget(self.addContactBtn)
        tblActLayout.addWidget(self.deleteSelectedBtn)
        tblActLayout.addStretch(1)
        layout.addLayout(tblActLayout)
        
        self.vBoxLayout.addWidget(self.audienceCard)

    def browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if path:
            self.csvPathEdit.setText(path)
            try:
                df = pd.read_csv(path)
                self.emailColumnCombo.clear()
                self.emailColumnCombo.addItems(list(df.columns))
            except Exception as e:
                InfoBar.error("Error", f"Could not read CSV: {e}", parent=self.window())

    def import_contacts(self):
        csv_path = self.csvPathEdit.text()
        email_col = self.emailColumnCombo.currentText()
        category = self.categoryEdit.text().strip()
        
        if not csv_path or not email_col or not category:
            InfoBar.error("Missing Info", "Please provide a valid CSV, mapping, and a category name.", parent=self.window())
            return
            
        try:
            df = pd.read_csv(csv_path)
            df = df.dropna(subset=[email_col]) # Remove blank emails
            
            # The rest of columns will be saved as JSON
            other_cols = [c for c in df.columns if c != email_col]
            
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Ask for default status
            msg = MessageBox("Import Options", "Should imported contacts be set to Active by default?\n(Inactive contacts are skipped during campaign launch)", self.window())
            msg.yesButton.setText("Active")
            msg.cancelButton.setText("Inactive")
            default_active = 1 if msg.exec() else 0
            
            inserted = 0
            for index, row in df.iterrows():
                email = str(row[email_col]).strip().lower()
                field_data_dict = {col: row[col] for col in other_cols}
                
                # We use INSERT OR REPLACE to update existing emails
                try:
                    cur.execute("INSERT OR REPLACE INTO contacts (category, email, field_data, is_active) VALUES (?, ?, ?, ?)",
                                (category, email, json.dumps(field_data_dict), default_active))
                    inserted += 1
                except:
                    pass
                    
            conn.commit()
            conn.close()
            InfoBar.success("Success", f"Imported/Updated {inserted} contacts in group '{category}'.", parent=self.window())
            self.categoryEdit.clear()
            self.csvPathEdit.clear()
            self.refresh_audience_categories() # Auto-refresh UI
        except Exception as e:
            InfoBar.error("Error", f"Failed to import: {e}", parent=self.window())


    # --- LAUNCH MANAGER ---
    def _setup_launch_manager(self):
        self.launchCard = CardWidget(self)
        layout = QVBoxLayout(self.launchCard)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        layout.addWidget(SubtitleLabel("Launch Campaign", self.launchCard))
        
        # Config Layer
        cfgLayout = QHBoxLayout()
        cfgLayout.addWidget(BodyLabel("1. Choose Template:", self.launchCard))
        self.templateCombo = ComboBox(self.launchCard)
        self.templateCombo.setMinimumWidth(200)
        cfgLayout.addWidget(self.templateCombo)
        cfgLayout.addStretch(1)
        layout.addLayout(cfgLayout)
        
        # Checkboxes for Target Categories
        layout.addWidget(BodyLabel("2. Target Categories (Multi-select):", self.launchCard))
        self.catScroll = QScrollArea(self.launchCard)
        self.catScroll.setWidgetResizable(True)
        self.catScroll.setMinimumHeight(150)
        self.catScroll.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; border-radius: 4px; background: transparent; }")
        
        self.catScrollWidget = QWidget()
        self.catScrollWidget.setStyleSheet("background: transparent;")
        self.catScrollLayout = QVBoxLayout(self.catScrollWidget)
        self.catScrollLayout.setAlignment(Qt.AlignTop)
        self.catScroll.setWidget(self.catScrollWidget)
        layout.addWidget(self.catScroll)
        
        self.category_checkboxes = [] # Tracks all checkable categories
        
        # Status
        self.statusTag = BodyLabel("", self.launchCard)
        font = self.statusTag.font()
        font.setPointSize(10)
        font.setBold(True)
        self.statusTag.setFont(font)
        layout.addWidget(self.statusTag)
        
        # Actions
        aLayout = QHBoxLayout()
        self.draftBtn = PushButton("Send Selected to Drafts (Sanity Check)", self.launchCard)
        self.draftBtn.clicked.connect(lambda: self.start_campaign("DRAFT"))
        
        self.sendBtn = PrimaryPushButton("Launch Campaign with Selected", self.launchCard)
        self.sendBtn.clicked.connect(lambda: self.start_campaign("SEND"))
        
        aLayout.addStretch(1)
        aLayout.addWidget(self.draftBtn)
        aLayout.addWidget(self.sendBtn)
        layout.addLayout(aLayout)
        
        self.vBoxLayout.addWidget(self.launchCard)
        
        # State vars used by Audience Manager
        self.current_page = 1
        self.page_size = 100
        self.total_pages = 1
        self.selected_emails = set() # Global set keeping track of selections across pages

    def update_status_tag(self):
        can_send, reason = Scheduler.can_send_now()
        if can_send:
            self.statusTag.setText("🟢 Engine active. Campaigns will launch immediately.")
            self.statusTag.setStyleSheet("color: #107C10;")
        else:
            self.statusTag.setText(f"🔴 Sending blocked by Humanizer Rules: {reason}")
            self.statusTag.setStyleSheet("color: #D83B01;")

    def refresh_templates(self):
        self.templateCombo.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM templates")
            for tid, name in cur.fetchall():
                self.templateCombo.addItem(name, userData=tid)
            conn.close()
        except:
            pass
            
    def refresh_audience_categories(self):
        current_selection = self.audienceCategoryCombo.currentText()
        self.audienceCategoryCombo.clear()
        
        for cb in self.category_checkboxes:
            self.catScrollLayout.removeWidget(cb)
            cb.deleteLater()
        self.category_checkboxes.clear()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT category FROM contacts")
            for row in cur.fetchall():
                cat = row[0]
                self.audienceCategoryCombo.addItem(cat)
                
                # Launch Checkbox
                cb = CheckBox(cat, self.catScrollWidget)
                # Check if group has any active contacts to pre-check the group
                cur_check = conn.cursor()
                cur_check.execute("SELECT COUNT(*) FROM contacts WHERE category=? AND is_active=1", (cat,))
                if cur_check.fetchone()[0] > 0:
                    cb.setChecked(True)
                
                self.category_checkboxes.append(cb)
                self.catScrollLayout.addWidget(cb)
            conn.close()
            
            if current_selection:
                self.audienceCategoryCombo.setCurrentText(current_selection)
        except:
            pass

    def on_category_selected(self, category):
        if not category:
            return
        self.selected_emails.clear()
        
        # Check all by default on group load
        self.check_all_in_category(category)
        
        self.current_page = 1
        self._load_table_page()
        
    def check_all_in_category(self, category):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT email FROM contacts WHERE category=? AND is_active=1", (category,))
            for row in cur.fetchall():
                self.selected_emails.add(row[0])
            conn.close()
        except:
            pass

    def _load_table_page(self):
        category = self.audienceCategoryCombo.currentText()
        if not category:
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM contacts WHERE category=?", (category,))
            total_records = cur.fetchone()[0]
            self.total_pages = max(1, math.ceil(total_records / self.page_size))
            
            offset = (self.current_page - 1) * self.page_size
            cur.execute("SELECT email, field_data, is_active FROM contacts WHERE category=? LIMIT ? OFFSET ?", 
                        (category, self.page_size, offset))
            rows = cur.fetchall()
            conn.close()
            
            self.table.setRowCount(0)
            
            for i, (email, field_data_str, is_active) in enumerate(rows):
                self.table.insertRow(i)
                
                # Checkbox
                cb = CheckBox()
                cb.setChecked(bool(is_active))
                cb.stateChanged.connect(lambda state, e=email: self.on_checkbox_changed(state, e))
                # Add centering
                cw = QWidget()
                chw = QHBoxLayout(cw)
                chw.setContentsMargins(8, 0, 0, 0)
                chw.addWidget(cb)
                self.table.setCellWidget(i, 0, cw)
                
                self.table.setItem(i, 1, QTableWidgetItem(email))
                
                # Format JSON slightly nicer for preview
                try:
                    data = json.loads(field_data_str)
                    preview = ", ".join([f"{k}: {v}" for k, v in data.items()])
                except:
                    preview = field_data_str
                self.table.setItem(i, 2, QTableWidgetItem(preview))
                
            self.pageLabel.setText(f"Page {self.current_page} / {self.total_pages}")
            self.prevBtn.setEnabled(self.current_page > 1)
            self.nextBtn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            print("Error loading page:", e)
            
    def on_checkbox_changed(self, state, email):
        category = self.audienceCategoryCombo.currentText()
        is_active = 1 if state == 2 else 0
        
        # Persist to database immediately
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("UPDATE contacts SET is_active=? WHERE category=? AND email=?", (is_active, category, email))
            conn.commit()
            conn.close()
            
            # Sync local set for current session logic
            if is_active:
                self.selected_emails.add(email)
            else:
                self.selected_emails.discard(email)
        except Exception as e:
            print("Database error on checkbox change:", e)

    def add_single_contact(self):
        category = self.audienceCategoryCombo.currentText()
        if not category:
            InfoBar.error("Error", "Select a Category first.", parent=self.window())
            return
            
        dialog = AddContactDialog(category, self.window())
        if dialog.exec():
            email, json_data = dialog.get_data()
            if not email:
                InfoBar.error("Error", "Email is required.", parent=self.window())
                return
            
            if not json_data:
                json_data = "{}"
            else:
                try:
                    # Validate JSON
                    json.loads(json_data)
                except:
                    InfoBar.error("Error", "Invalid JSON format. Expected format: {\"key\": \"value\"}", parent=self.window())
                    return
                    
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                # dialog.get_data now returns email, json, is_active
                email, json_data, is_active = dialog.get_data()
                cur.execute("INSERT OR REPLACE INTO contacts (category, email, field_data, is_active) VALUES (?, ?, ?, ?)",
                            (category, email.lower(), json_data, 1 if is_active else 0))
                conn.commit()
                conn.close()
                self._load_table_page() # Refresh table
                InfoBar.success("Success", f"Contact added to {category}", parent=self.window())
            except Exception as e:
                InfoBar.error("Error", f"Database error: {e}", parent=self.window())

    def delete_selected_contacts(self):
        category = self.audienceCategoryCombo.currentText()
        if not category:
            return
            
        if not self.selected_emails:
            InfoBar.error("Error", "No contacts selected to delete.", parent=self.window())
            return
            
        # Confirmation
        dialog = MessageBox("Delete Contacts?", f"Are you sure you want to permanently delete {len(self.selected_emails)} selected contacts from the '{category}' group?", self.window())
        if dialog.exec():
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                placeholders = ','.join(['?'] * len(self.selected_emails))
                params = [category] + list(self.selected_emails)
                cur.execute(f"DELETE FROM contacts WHERE category=? AND email IN ({placeholders})", params)
                conn.commit()
                conn.close()
                
                deleted_count = len(self.selected_emails)
                self.selected_emails.clear()
                self._load_table_page()
                InfoBar.success("Deleted", f"Successfully removed {deleted_count} contacts.", parent=self.window())
            except Exception as e:
                InfoBar.error("Error", f"Failed to delete: {e}", parent=self.window())

    def delete_entire_category(self):
        category = self.audienceCategoryCombo.currentText()
        if not category:
            return
            
        dialog = MessageBox("Delete Category?", f"Are you sure you want to permanently delete the entire '{category}' category and ALL its contacts?", self.window())
        if dialog.exec():
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("DELETE FROM contacts WHERE category=?", (category,))
                conn.commit()
                conn.close()
                self.refresh_audience_categories()
                InfoBar.success("Deleted", f"Category '{category}' deleted entirely.", parent=self.window())
            except Exception as e:
                InfoBar.error("Error", f"Failed to delete category: {e}", parent=self.window())

    def toggle_page_checkboxes(self):
        # Scan current table checkboxes. If all checked, uncheck all. Otherwise, check all.
        all_checked = True
        for i in range(self.table.rowCount()):
            cb_widget = self.table.cellWidget(i, 0)
            if cb_widget:
                cb = cb_widget.findChild(CheckBox)
                if cb and not cb.isChecked():
                    all_checked = False
                    break
                    
        new_state = False if all_checked else True
        
        for i in range(self.table.rowCount()):
            cb_widget = self.table.cellWidget(i, 0)
            if cb_widget:
                cb = cb_widget.findChild(CheckBox)
                if cb:
                    cb.setChecked(new_state) # This fires stateChanged and syncs globally
                    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_table_page()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_table_page()

    def start_campaign(self, mode):
        if self.templateCombo.currentIndex() < 0:
            InfoBar.error("Error", "Select a template.", parent=self.window())
            return
            
        selected_cats = [cb.text() for cb in self.category_checkboxes if cb.isChecked()]
        if not selected_cats:
            InfoBar.error("Error", "Select at least one category.", parent=self.window())
            return
            
        if mode == "SEND":
            can_send, reason = Scheduler.can_send_now()
            if not can_send:
                InfoBar.error("Blocked by Humanizer", f"Cannot Launch: {reason}", parent=self.window())
                return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            temp_id = self.templateCombo.currentData()
            camp_name = f"Campaign {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cat_str = ", ".join(selected_cats)
            cur.execute("INSERT INTO campaigns (name, csv_path, template_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (camp_name, f"Categories: {cat_str}", temp_id, "RUNNING", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))
            camp_id = cur.lastrowid
            
            # Fetch all contacts matching ANY of the selected categories AND are active
            placeholders = ','.join(['?'] * len(selected_cats))
            cur.execute(f"SELECT email, field_data FROM contacts WHERE is_active=1 AND category IN ({placeholders})", selected_cats)
            
            queued = 0
            for row in cur.fetchall():
                email = row[0]
                field_data = row[1]
                try:
                    parsed_fd = json.loads(field_data)
                except:
                    parsed_fd = {}
                
                row_data_str = json.dumps(parsed_fd)
                cur.execute("INSERT INTO queue (campaign_id, email_address, row_data, status) VALUES (?, ?, ?, ?)",
                            (camp_id, email, row_data_str, "PENDING"))
                queued += 1
                                
            conn.commit()
            conn.close()
            
            if queued == 0:
                InfoBar.error("Error", "No contacts found in selected categories.", parent=self.window())
                return
                
            self._start_worker(camp_id, mode)
            
        except Exception as e:
            InfoBar.error("Error", f"Failed to start: {e}", parent=self.window())

    # --- PROGRESS & WORKER (Existing Logic) ---
    def _setup_progress(self):
        self.progCard = CardWidget(self)
        layout = QVBoxLayout(self.progCard)
        layout.setContentsMargins(16, 16, 16, 16)
        
        layout.addWidget(SubtitleLabel("Active Job Progress", self.progCard))
        
        self.statusLabel = BodyLabel("Idle", self.progCard)
        layout.addWidget(self.statusLabel)
        
        self.progressBar = ProgressBar(self.progCard)
        self.progressBar.setValue(0)
        layout.addWidget(self.progressBar)
        
        ctrlLayout = QHBoxLayout()
        self.pauseBtn = PushButton("Pause", self.progCard)
        self.pauseBtn.clicked.connect(self.toggle_pause)
        self.pauseBtn.setEnabled(False)
        self.cancelBtn = PushButton("Cancel", self.progCard)
        self.cancelBtn.clicked.connect(self.cancel_job)
        self.cancelBtn.setEnabled(False)
        
        ctrlLayout.addWidget(self.pauseBtn)
        ctrlLayout.addWidget(self.cancelBtn)
        ctrlLayout.addStretch(1)
        layout.addLayout(ctrlLayout)
        
        self.vBoxLayout.addWidget(self.progCard)
        self.progCard.setVisible(False)

    def _start_worker(self, camp_id, mode):
        self.launchCard.setVisible(False)
        self.segmentWidget.setEnabled(False)
        self.progCard.setVisible(True)
        self.pauseBtn.setEnabled(True)
        self.cancelBtn.setEnabled(True)
        self.pauseBtn.setText("Pause")
        
        self.worker = CampaignWorker(camp_id, mode)
        self.worker.progress.connect(self._sync_progress)
        self.worker.status.connect(self._sync_status)
        self.worker.finished.connect(self._worker_finished)
        self.worker.error.connect(self._worker_error)
        self.worker.start()

    def _sync_progress(self, current, total):
        pct = int((current / total) * 100) if total > 0 else 0
        self.progressBar.setValue(pct)

    def _sync_status(self, text):
        self.statusLabel.setText(text)

    def _worker_finished(self, success, msg):
        self.pauseBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText("Finished: " + msg)
        self.launchCard.setVisible(True)
        self.segmentWidget.setEnabled(True)
        
        if success:
            InfoBar.success("Finished", msg, parent=self.window())
        else:
            InfoBar.warning("Interrupted", msg, parent=self.window())

    def _worker_error(self, msg):
        InfoBar.error("Worker Error", msg, duration=10000, parent=self.window())

    def toggle_pause(self):
        if not self.worker:
            return
            
        if self.worker.is_paused:
            self.worker.resume()
            self.pauseBtn.setText("Pause")
        else:
            self.worker.pause()
            self.pauseBtn.setText("Resume")

    def cancel_job(self):
        if self.worker:
            self.worker.cancel()
            self.statusLabel.setText("Cancelling... Please wait.")
            self.cancelBtn.setEnabled(False)
            self.pauseBtn.setEnabled(False)

    def show_guide(self):
        content = (
            "<b>Campaigns & Audience Manager</b><br><br>"
            "1. <b>Audience Manager Tab:</b> First, import your CSV here. Select the column representing the email address, and give the group a Category name (like 'Designers Sep24'). All other columns are saved as variables for your templates.<br><br>"
            "2. <b>Launch Campaign Tab:</b> Choose your Template and your newly saved Audience Category. By default, everyone is checked. You can page through 100 at a time, check or uncheck individuals, and then Send to Drafts or Launch!"
        )
        msgBox = MessageBox("Campaigns Guide", content, self.window())
        msgBox.yesButton.setText("Got it!")
        msgBox.cancelButton.hide()
        msgBox.exec()

class AddContactDialog(MessageBox):
    def __init__(self, category_name, parent=None):
        super().__init__("Add Single Contact", "", parent)
        self.category_name = category_name
        self.yesButton.setText("Add Contact")
        self.cancelButton.setText("Cancel")
        
        self.customWidget = QWidget()
        self.customWidget.setMinimumWidth(400)
        self.customLayout = QVBoxLayout(self.customWidget)
        self.customLayout.setContentsMargins(0, 16, 0, 0)
        self.customLayout.setSpacing(16)
        
        self.emailEdit = LineEdit()
        self.emailEdit.setPlaceholderText("Email Address (required)")
        self.customLayout.addWidget(self.emailEdit)
        
        self.jsonEdit = LineEdit()
        self.jsonEdit.setPlaceholderText('Extra Fields JSON (e.g. {"First Name": "John"})')
        self.customLayout.addWidget(self.jsonEdit)
        
        self.activeCb = CheckBox("Set as Active")
        self.activeCb.setChecked(True)
        self.customLayout.addWidget(self.activeCb)
        
        self.textLayout.addWidget(self.customWidget)

    def get_data(self):
        return self.emailEdit.text().strip(), self.jsonEdit.text().strip(), self.activeCb.isChecked()
