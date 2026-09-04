"""Custom QWebEnginePage subclass used by browser tabs."""
from PyQt6.QtWebEngineWidgets import QWebEnginePage


class BrowserPage(QWebEnginePage):
    """Page that lets the browser open target=_blank / window.open in new tabs."""

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.new_window_cb = None

    def createWindow(self, window_type):
        page = BrowserPage(self.profile(), self)
        if self.new_window_cb:
            self.new_window_cb(page, window_type)
        return page
