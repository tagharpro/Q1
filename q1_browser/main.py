"""Q1 Browser application entry point."""
import os
import sys

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEnginePage

from .browser_window import BrowserWindow
from .paths import app_version, resource_path
from .settings import Settings


class AppPage(QWebEnginePage):
    """Page that opens target=_blank / window.open links in new Q1 tabs."""

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.new_window_cb = None

    def createWindow(self, window_type):
        if self.new_window_cb:
            return self.new_window_cb(window_type)
        return super().createWindow(window_type)


def _setup_webengine():
    settings = QWebEngineSettings.globalSettings()
    # These help the Q1 new tab page and rich pages behave like a modern browser.
    try:
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
        )
    except Exception:
        pass

    profile = QWebEngineProfile.defaultProfile()
    try:
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    except Exception:
        pass


def main():
    QCoreApplication.setOrganizationName("tagharpro")
    QCoreApplication.setApplicationName("Q1Browser")
    QCoreApplication.setApplicationVersion(app_version())

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Q1 Browser")

    # Icon (SVG above, so only set if a PNG exists).
    for name in ("assets/icon.png", "assets/icon.ico"):
        path = resource_path(name)
        if os.path.exists(path):
            try:
                icon = QIcon(path)
                if not icon.isNull():
                    app.setWindowIcon(icon)
                    break
            except Exception:
                pass

    _setup_webengine()

    settings = Settings()
    window = BrowserWindow(settings)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
