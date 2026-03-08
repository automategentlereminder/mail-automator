import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import (TitleLabel, CardWidget, TableWidget, PrimaryPushButton, 
                            PushButton, InfoBar, MessageBox)
from core.database import DB_PATH
from core.worker import CampaignWorker

class HistoryInterface(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("HistoryInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        self.titleLabel = TitleLabel("History & Resilience", self)
        
        # Header Controls
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        self.guideBtn = PushButton("📖 Guide", self)
        self.guideBtn.clicked.connect(self.show_guide)
        headerLayout.addWidget(self.guideBtn)
        
        self.refreshBtn = PushButton("Refresh", self)
        self.refreshBtn.clicked.connect(self.refresh_table)
        headerLayout.addWidget(self.refreshBtn)
        self.vBoxLayout.addLayout(headerLayout)
        
        # Table
        self.tableCard = CardWidget(self)
        tLayout = QVBoxLayout(self.tableCard)
        tLayout.setContentsMargins(0, 0, 0, 0)
        
        self.table = TableWidget(self.tableCard)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Date", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().hide()
        
        tLayout.addWidget(self.table)
        self.vBoxLayout.addWidget(self.tableCard)
        
        # We need a reference to the main window to pass to the worker or campaign interface
        # For simplicity, we can spawn a worker here directly or use signals. We'll spawn here but in real 
        # life we might want a global queue manager.
        self.worker = None

    def refresh_table(self):
        self.table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name, status, created_at FROM campaigns ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            for i, (cid, name, status, created_at) in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(cid)))
                self.table.setItem(i, 1, QTableWidgetItem(name))
                self.table.setItem(i, 2, QTableWidgetItem(status))
                self.table.setItem(i, 3, QTableWidgetItem(str(created_at).split('.')[0]))
                
                # Action button
                if status in ["RUNNING", "PAUSED"]:
                    btn = PrimaryPushButton("Resume")
                    btn.clicked.connect(lambda checked, c=cid: self.resume_campaign(c))
                    # Setting widget
                    # PySide requires layout or setCellWidget
                    self.table.setCellWidget(i, 4, btn)
                else:
                    self.table.setItem(i, 4, QTableWidgetItem("N/A"))
                    
        except Exception as e:
            print(f"Error refreshing history: {e}")

    def resume_campaign(self, campaign_id):
        if self.worker and self.worker.isRunning():
            InfoBar.warning("Wait", "Another campaign is currently active.", parent=self.window())
            return
            
        InfoBar.info("Resuming...", f"Resuming Campaign {campaign_id}.", parent=self.window())
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("UPDATE campaigns SET status='RUNNING' WHERE id=?", (campaign_id,))
            conn.commit()
            conn.close()
        except:
            pass
            
        self.refresh_table()

        self.worker = CampaignWorker(campaign_id, "SEND")
        self.worker.finished.connect(self._on_resume_finished)
        self.worker.error.connect(lambda e: InfoBar.error("Error", e, parent=self.window()))
        self.worker.start()

    def _on_resume_finished(self, success, msg):
        if success:
            InfoBar.success("Finished", "Campaign Complete.", parent=self.window())
        else:
            InfoBar.warning("Stopped", msg, parent=self.window())
        self.refresh_table()

    def show_guide(self):
        content = (
            "<b>History & Resilience</b><br><br>"
            "This tab acts as your safety net.<br><br>"
            "• See a summary of your recent 50 campaigns.<br>"
            "• <b>The Resume Feature:</b> If your laptop sleeps, Outlook crashes, or you manually paused a run, it will sit here waiting. Just click <b>Resume</b>, and the background worker will pick up exactly where it left off without sending duplicates!"
        )
        msgBox = MessageBox("History Guide", content, self.window())
        msgBox.yesButton.setText("Got it!")
        msgBox.cancelButton.hide()
        msgBox.exec()

