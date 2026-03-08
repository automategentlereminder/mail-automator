import sys
from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from qfluentwidgets import (TitleLabel, SubtitleLabel, SpinBox, SwitchButton, 
                            PrimaryPushButton, PushButton, CardWidget, BodyLabel, InfoBar, InfoBarPosition,
                            TimePicker, MessageBox)
from core.database import get_setting, set_setting
from core.outlook_engine import OutlookEngine
from core.scheduler import Scheduler
from PySide6.QtCore import QTime

class SettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingsInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        self.titleLabel = TitleLabel("Settings (The Humanizer)", self)
        
        # Header Layout with Guide Button
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        self.guideBtn = PushButton("📖 Guide", self)
        self.guideBtn.clicked.connect(self.show_guide)
        headerLayout.addWidget(self.guideBtn)
        
        self.vBoxLayout.addLayout(headerLayout)
        
        self._setup_humanizer_card()
        self._setup_connection_card()
        
        self.vBoxLayout.addStretch(1)
        self.load_settings()

    def _setup_humanizer_card(self):
        self.hCard = CardWidget(self)
        layout = QVBoxLayout(self.hCard)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        layout.addWidget(SubtitleLabel("The Humanizer Engine", self.hCard))
        layout.addWidget(BodyLabel("Makes your automated emails indistinguishable from manual sending.", self.hCard))
        
        # Live Status Tag
        self.statusTag = BodyLabel("Status: Unknown", self.hCard)
        # Use a nice font size
        font = self.statusTag.font()
        font.setPointSize(11)
        font.setBold(True)
        self.statusTag.setFont(font)
        layout.addWidget(self.statusTag)
        layout.addSpacing(4)
        
        # Quota
        qLayout = QHBoxLayout()
        qLayout.addWidget(BodyLabel("Daily Quota:", self.hCard))
        self.quotaSpin = SpinBox(self.hCard)
        self.quotaSpin.setRange(1, 10000)
        qLayout.addWidget(self.quotaSpin)
        qLayout.addStretch(1)
        layout.addLayout(qLayout)
        
        # Pulse
        pLayout = QHBoxLayout()
        pLayout.addWidget(BodyLabel("The Pulse (Seconds gap):", self.hCard))
        self.pulseMinSpin = SpinBox(self.hCard)
        self.pulseMinSpin.setRange(1, 3600)
        self.pulseMaxSpin = SpinBox(self.hCard)
        self.pulseMaxSpin.setRange(1, 3600)
        pLayout.addWidget(self.pulseMinSpin)
        pLayout.addWidget(BodyLabel("to", self.hCard))
        pLayout.addWidget(self.pulseMaxSpin)
        pLayout.addStretch(1)
        layout.addLayout(pLayout)
        
        # Working Hours
        wLayout = QHBoxLayout()
        wLayout.addWidget(BodyLabel("Working Hours:", self.hCard))
        self.timeStart = TimePicker(self.hCard)
        self.timeEnd = TimePicker(self.hCard)
        wLayout.addWidget(self.timeStart)
        wLayout.addWidget(BodyLabel("to", self.hCard))
        wLayout.addWidget(self.timeEnd)
        wLayout.addStretch(1)
        layout.addLayout(wLayout)
        
        # Weekends
        weLayout = QHBoxLayout()
        weLayout.addWidget(BodyLabel("Skip Weekends:", self.hCard))
        self.weekendSwitch = SwitchButton(self.hCard)
        weLayout.addWidget(self.weekendSwitch)
        weLayout.addStretch(1)
        layout.addLayout(weLayout)

        # Save
        self.saveBtn = PrimaryPushButton("Save Settings", self.hCard)
        self.saveBtn.clicked.connect(self.save_settings)
        hSaveLayout = QHBoxLayout()
        hSaveLayout.addWidget(self.saveBtn)
        hSaveLayout.addStretch(1)
        layout.addLayout(hSaveLayout)
        
        self.vBoxLayout.addWidget(self.hCard)

    def _setup_connection_card(self):
        self.cCard = CardWidget(self)
        layout = QVBoxLayout(self.cCard)
        layout.setContentsMargins(16, 16, 16, 16)
        
        layout.addWidget(SubtitleLabel("Outlook Bridge", self.cCard))
        
        self.testBtn = PrimaryPushButton("Test Connection", self.cCard)
        self.testBtn.clicked.connect(self.test_connection)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.testBtn)
        hLayout.addStretch(1)
        layout.addLayout(hLayout)
        
        self.vBoxLayout.addWidget(self.cCard)

    def load_settings(self):
        self.quotaSpin.setValue(int(get_setting("daily_limit", "50")))
        self.pulseMinSpin.setValue(int(get_setting("pulse_min", "300")))
        self.pulseMaxSpin.setValue(int(get_setting("pulse_max", "600")))
        
        start = get_setting("working_hours_start", "09:00").split(":")
        end = get_setting("working_hours_end", "18:00").split(":")
        self.timeStart.setTime(QTime(int(start[0]), int(start[1])))
        self.timeEnd.setTime(QTime(int(end[0]), int(end[1])))
        
        skip_weekends = str(get_setting("skip_weekends", "1")).lower()
        self.weekendSwitch.setChecked(skip_weekends in ["1", "true", "yes"])
        
        self.update_status_tag()

    def save_settings(self):
        set_setting("daily_limit", self.quotaSpin.value())
        set_setting("pulse_min", self.pulseMinSpin.value())
        set_setting("pulse_max", self.pulseMaxSpin.value())
        set_setting("working_hours_start", self.timeStart.time.toString("HH:mm"))
        set_setting("working_hours_end", self.timeEnd.time.toString("HH:mm"))
        set_setting("skip_weekends", "1" if self.weekendSwitch.isChecked() else "0")
        
        InfoBar.success(
            title='Success',
            content="Settings saved successfully.",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self.window()
        )
        self.update_status_tag()

    def update_status_tag(self):
        can_send, reason = Scheduler.can_send_now()
        if can_send:
            self.statusTag.setText("🟢 LIVE: Campaign sending is currently active.")
            self.statusTag.setStyleSheet("color: #107C10;") # Greenish
        else:
            self.statusTag.setText(f"🔴 PAUSED: {reason}")
            self.statusTag.setStyleSheet("color: #D83B01;") # Reddish

    def test_connection(self):
        engine = OutlookEngine()
        result = engine.test_connection()
        
        if result["success"]:
            InfoBar.success(
                title='Connection Successful',
                content=result["message"],
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
        else:
            InfoBar.error(
                title='Connection Failed',
                content=result["message"],
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self.window()
            )
            
    def show_guide(self):
        content = (
            "<b>The Humanizer Engine</b> ensures your emails look like they were typed by a human.<br><br>"
            "• <b>Daily Quota:</b> Maximum emails to send per day (to protect reputation).<br>"
            "• <b>The Pulse:</b> A random delay chosen between these two values after every email.<br>"
            "• <b>Working Hours:</b> The app will only send within this range. If it hits the end time, it waits until the start time the next day.<br>"
            "• <b>Outlook Bridge:</b> Connects to your logged-in Outlook session securely."
        )
        msgBox = MessageBox("Settings Guide", content, self.window())
        msgBox.yesButton.setText("Got it!")
        msgBox.cancelButton.hide()
        msgBox.exec()
