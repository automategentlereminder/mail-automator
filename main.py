import sys
import os
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtWidgets import QApplication

from core.utils import get_resource_path

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme, setTheme, Theme, setThemeColor, qrouter)
from qfluentwidgets import FluentWindow, SplashScreen

from core.database import init_db

from ui.dashboard import DashboardInterface
from ui.settings import SettingsInterface
from ui.templates import TemplatesInterface
from ui.campaigns import CampaignsInterface
from ui.history import HistoryInterface
from qfluentwidgets import FluentIcon as FIF


class MailAutomatorWindow(FluentWindow):

    def __init__(self):
        super().__init__()

        # Setup database
        init_db()

        # Set greenish theme
        setThemeColor('#107C10')
        
        self.initWindow()

        self.dashboard_interface = DashboardInterface(self)
        self.settings_interface = SettingsInterface(self)
        self.templates_interface = TemplatesInterface(self)
        self.campaigns_interface = CampaignsInterface(self)
        self.history_interface = HistoryInterface(self)

        self.initNavigation()
        
    def initNavigation(self):
        self.addSubInterface(self.dashboard_interface, FIF.HOME, 'Dashboard')
        self.addSubInterface(self.campaigns_interface, FIF.SEND, 'Campaigns')
        self.addSubInterface(self.templates_interface, FIF.DOCUMENT, 'Templates')
        self.addSubInterface(self.history_interface, FIF.HISTORY, 'History')
        self.addSubInterface(self.settings_interface, FIF.SETTING, 'Settings')
        
        # Fixed Footer
        self.navigationInterface.addItem(
            routeKey='footer_link',
            icon=FIF.GLOBE,
            text='Developed by Gentlereminder.in',
            onClick=lambda: QDesktopServices.openUrl(QUrl("https://gentlereminder.in/")),
            position=NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.setCurrentItem(self.dashboard_interface.objectName())
        
        # Connect navigation change to force widget refreshes
        self.stackedWidget.currentChanged.connect(self.on_nav_changed)
        
        # Decrease sidebar collapsed/expanded width to 60% of default
        self.navigationInterface.panel.setExpandWidth(180) # Default is much wider

    def on_nav_changed(self, index):
        # Dynamically trigger refreshes when tab is clicked
        widget = self.stackedWidget.widget(index)
        if widget == self.campaigns_interface:
            self.campaigns_interface.update_status_tag()
            self.campaigns_interface.refresh_templates()
        elif widget == self.dashboard_interface:
            self.dashboard_interface.refresh_stats()

    def initWindow(self):
        self.resize(1000, 700)
        self.setWindowIcon(QIcon(get_resource_path('assets/icon.ico')))
        self.setWindowTitle('Smart Mailer')


if __name__ == '__main__':
    # Enable DPI scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_resource_path('assets/icon.ico'))) # Required for Taskbar icon in Windows
    
    # Initialize the main window
    w = MailAutomatorWindow()
    w.show()
    
    sys.exit(app.exec())
