"""A single browser tab: one QWebEngineView + page / profile plumbing."""
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .pages import BrowserPage


class BrowserTab(QWidget):
    data_changed = pyqtSignal(QUrl, str, bool, bool)
    icon_changed = pyqtSignal(QIcon)
    progress_changed = pyqtSignal(int)
    load_finished = pyqtSignal(bool)
    crashed = pyqtSignal(object)
    new_window_needs = pyqtSignal(object, object)  # page, window type

    def __init__(self, profile, home_url, private=False, page=None, parent=None):
        super().__init__(parent)
        self.private = private
        self.home_url = home_url or "about:blank"

        self.view = QWebEngineView(self)
        self.browser_page = page or BrowserPage(profile, self)
        self.view.setPage(self.browser_page)
        self.browser_page.new_window_cb = self._create_new_window_page

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.view.urlChanged.connect(self._on_url_changed)
        self.view.titleChanged.connect(self._on_title_changed)
        self.view.iconChanged.connect(self._on_icon_changed)
        self.view.loadStarted.connect(self._on_load_started)
        self.view.loadProgress.connect(self._on_load_progress)
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.renderProcessTerminated.connect(self._on_crashed)

        self._url = QUrl()
        self._title = ""
        self._loading = False

    def _create_new_window_page(self, page, window_type):
        self.new_window_needs.emit(page, window_type)
        return page

    # Signals (used by BrowserWindow / tab manager) ------------------------
    def _on_url_changed(self, url):
        self._url = url
        self.data_changed.emit(url, self._title, False, self.private)

    def _on_title_changed(self, title):
        self._title = title
        self.data_changed.emit(self._url, title, False, self.private)

    def _on_icon_changed(self, icon):
        self.icon_changed.emit(icon)

    def _on_load_started(self):
        self._loading = True
        self.data_changed.emit(self._url, self._title, True, self.private)

    def _on_load_progress(self, progress):
        self.progress_changed.emit(progress)

    def _on_load_finished(self, ok):
        self._loading = False
        self.load_finished.emit(ok)

    def _on_crashed(self, reason):
        self.crashed.emit(reason)

    # Public API ----------------------------------------------------------
    def load(self, url):
        if isinstance(url, str):
            url = QUrl(url)
        self.view.load(url)

    def load_home(self):
        self.view.load(QUrl(self.home_url))

    def go_back(self):
        self.view.back()
        return self.view.history().canGoBack()

    def go_forward(self):
        self.view.forward()
        return self.view.history().canGoForward()

    def reload(self):
        self.view.reload()

    def stop(self):
        self.view.stop()

    def current_url(self):
        return self.view.url().toString()

    def current_title(self):
        return self._title or self.view.title() or ("" if self.private else "New Tab")

    def is_private(self):
        return self.private
