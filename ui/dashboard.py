import sqlite3
import datetime
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (TitleLabel, CardWidget, SubtitleLabel, BodyLabel, 
                            ProgressBar, PrimaryPushButton, PushButton,
                            FluentIcon as FIF, MessageBox, ImageLabel)
from core.database import get_setting, DB_PATH
from core.utils import get_resource_path

class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        # Header Layout with Guide Button
        headerLayout = QHBoxLayout()
        self.titleLabel = TitleLabel("Dashboard", self)
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        self.guideBtn = PushButton("📖 Guide", self)
        self.guideBtn.clicked.connect(self.show_guide)
        headerLayout.addWidget(self.guideBtn)
        
        self.vBoxLayout.addLayout(headerLayout)
        
        # Stats Grid
        self.statsLayout = QHBoxLayout()
        self.statsLayout.setSpacing(16)
        self.vBoxLayout.addLayout(self.statsLayout)
        
        self._setup_sent_card()
        self._setup_queue_card()
        self._setup_lifetime_card()
        # Reputation card removed as requested
        
        self.vBoxLayout.addSpacing(16)
        self._setup_tips_card()
        
        self.vBoxLayout.addStretch(1)
        
        # Socials & Logo
        self._setup_socials_and_logo()
        
    def _setup_sent_card(self):
        self.sentCard = CardWidget(self)
        layout = QVBoxLayout(self.sentCard)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.sentTitle = SubtitleLabel("Sent Today", self.sentCard)
        self.sentCount = BodyLabel("0 / 50", self.sentCard)
        self.sentCount.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.sentProgress = ProgressBar(self.sentCard)
        self.sentProgress.setValue(0)
        
        layout.addWidget(self.sentTitle)
        layout.addWidget(self.sentCount)
        layout.addWidget(self.sentProgress)
        
        self.statsLayout.addWidget(self.sentCard)

    def _setup_queue_card(self):
        self.queueCard = CardWidget(self)
        layout = QVBoxLayout(self.queueCard)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.queueTitle = SubtitleLabel("Pending Queue", self.queueCard)
        self.queueCount = BodyLabel("0 emails left", self.queueCard)
        self.queueCount.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078D4;")
        
        layout.addWidget(self.queueTitle)
        layout.addWidget(self.queueCount)
        layout.addStretch(1)
        
        self.statsLayout.addWidget(self.queueCard)

    def _setup_lifetime_card(self):
        self.lifetimeCard = CardWidget(self)
        layout = QVBoxLayout(self.lifetimeCard)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.ltTitle = SubtitleLabel("Lifetime Sent", self.lifetimeCard)
        self.ltCount = BodyLabel("0 emails", self.lifetimeCard)
        self.ltCount.setStyleSheet("font-size: 24px; font-weight: bold; color: #107C10;")
        
        layout.addWidget(self.ltTitle)
        layout.addWidget(self.ltCount)
        layout.addStretch(1)
        
        self.statsLayout.addWidget(self.lifetimeCard)

    def _setup_tips_card(self):
        self.tipsCard = CardWidget(self)
        layout = QVBoxLayout(self.tipsCard)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        header = SubtitleLabel("📬 Primary Inbox Blueprint", self.tipsCard)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        layout.addWidget(header)
        
        intro = BodyLabel("Our engine is built on the philosophy of deliverability over volume. Follow these tested rules to ensure your emails land in the <b>Primary</b> tab of your prospects.", self.tipsCard)
        intro.setWordWrap(True)
        layout.addWidget(intro)
        
        tips = [
            "🟢 <b>Be Less Greedy:</b> Keep daily volume between 40-60 emails. Burning through thousands of leads a day is the fastest way to get your domain blacklisted.",
            "🕒 <b>Trust the Pulse:</b> Maintain a 300-600s delay. Local Outlook sending mimics a real human typing—bulk sending triggers automated server alarms.",
            "📝 <b>Short & Personal:</b> Avoid long marketing 'salesy' copies. Keep emails brief (2-4 sentences) and highly relevant to the recipient's business.",
            "🚫 <b>Ditch the Extras:</b> Do NOT include tracking links, heavy HTML, or large attachments. Plain-text-style emails are physically indistinguishable from personal mail.",
            "💬 <b>The CTA Question:</b> Always end your mail with a simple, clear question (e.g. 'Are you open to a quick chat?') to maximize response rates."
        ]
        
        for tip in tips:
            lbl = BodyLabel(tip, self.tipsCard)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
            
        layout.addStretch(1)
        self.vBoxLayout.addWidget(self.tipsCard)

    def _setup_socials_and_logo(self):
        self.bottomLayout = QHBoxLayout()
        
        # Socials Layout (Horizontal)
        self.socialLayout = QHBoxLayout()
        self.socialLayout.setSpacing(16)
        
        self.githubBtn = PushButton("Love the tool? Star us on GitHub", self)
        self.githubBtn.setStyleSheet("QPushButton { padding: 6px 16px; color: #f0f6fc; background-color: #21262d; border: 1px solid #30363d; border-radius: 5px; } QPushButton:hover { background-color: #30363d; }")
        self.githubBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/automategentlereminder/mail-automator")))
        
        self.linkedinBtn = PushButton("Follow for automation tips on LinkedIn", self)
        self.linkedinBtn.setStyleSheet("QPushButton { padding: 6px 16px; color: white; background-color: #0A66C2; border: none; border-radius: 5px; } QPushButton:hover { background-color: #004182; }")
        self.linkedinBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.linkedin.com/company/gentle-reminder-in/")))
        
        self.webBtn = PushButton("Visit our website for more services", self)
        self.webBtn.setStyleSheet("QPushButton { padding: 6px 16px; color: white; background-color: #107C10; border: none; border-radius: 5px; } QPushButton:hover { background-color: #0c5e0c; }")
        self.webBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://gentlereminder.in/")))
        
        self.socialLayout.addWidget(self.githubBtn)
        self.socialLayout.addWidget(self.linkedinBtn)
        self.socialLayout.addWidget(self.webBtn)
        self.socialLayout.addStretch(1)
        
        self.bottomLayout.addLayout(self.socialLayout)
        
        # Brand Logo (Bottom Right)
        self.logoLabel = ImageLabel(get_resource_path("assets/logo.png"), self)
        self.logoLabel.setFixedSize(150, 150)
        # It will gracefully be invisible/empty if the file doesn't exist yet
        self.logoLabel.scaledToWidth(150)
        
        self.bottomLayout.addWidget(self.logoLabel, alignment=Qt.AlignBottom | Qt.AlignRight)
        
        self.vBoxLayout.addLayout(self.bottomLayout)
        
    def show_guide(self):
        content = (
            "<b>Welcome to Smart Mailer!</b><br><br>"
            "This Dashboard gives you a quick overview of your daily limits and current mail queue.<br><br>"
            "• <b>Sent Today:</b> Tracks how many emails have successfully hit your Outlook Outbox against your configured Daily Quota.<br>"
            "• <b>Pending Queue:</b> Shows how many emails are waiting to be processed across all active campaigns.<br>"
            "• Use the quick links at the bottom to stay updated with Gentle Reminder!"
        )
        msgBox = MessageBox("Dashboard Guide", content, self.window())
        msgBox.yesButton.setText("Got it!")
        msgBox.cancelButton.hide()
        msgBox.exec()
        
    def refresh_stats(self):
        # Called when dashboard is opened or via timer
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Daily limit
            limit = int(get_setting("daily_limit", "50"))
            
            # Sent today
            today_str = datetime.date.today().isoformat()
            cur.execute("SELECT COUNT(*) FROM queue WHERE status='SENT' AND date(sent_at)=?", (today_str,))
            sent_today = cur.fetchone()[0]
            
            # Pending queue
            cur.execute("SELECT COUNT(*) FROM queue WHERE status='PENDING'")
            pending = cur.fetchone()[0]
            
            # Lifetime sent
            cur.execute("SELECT COUNT(*) FROM queue WHERE status='SENT'")
            lifetime = cur.fetchone()[0]
            
            conn.close()
            
            self.sentCount.setText(f"{sent_today} / {limit}")
            pct = int((sent_today / limit) * 100) if limit > 0 else 0
            self.sentProgress.setValue(min(pct, 100))
            
            self.queueCount.setText(f"{pending} emails left")
            self.ltCount.setText(f"{lifetime} emails")
            
        except Exception as e:
            print(f"Error refreshing stats: {e}")
