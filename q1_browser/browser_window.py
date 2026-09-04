"""Main browser window: toolbar, tabs, AI dock, menus, and dialogs."""
import os

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QAction, QDesktopServices, QKeySequence
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QStyle,
    QTabWidget,
    QToolBar,
    QWidget,
)

from .ai_panel import AIPanel
from .browser_tab import BrowserTab
from .dialogs import BookmarkDialog, HistoryDialog, SettingsDialog
from .download_center import DownloadCenterDialog, DownloadManager
from .paths import resource_path
from .settings import Settings
from .storage import BookmarkStore, HistoryStore


class BrowserWindow(QMainWindow):
    def __init__(self, settings: Settings = None):
        super().__init__()
        self.settings = settings or Settings()
        self.bookmarks = BookmarkStore("bookmarks")
        self.history = HistoryStore("history")
        self.downloads = DownloadManager(self)
        self._newtab_qurl = QUrl.fromLocalFile(resource_path("assets/newtab.html"))
        self.newtab_url = self._newtab_qurl.toString()
        self.home_url = self.settings.homepage or self.newtab_url
        self.address_bar = QLineEdit(self)
        self._address_ignore = False
        self._exiting = False

        self.private_profile = QWebEngineProfile(self)

        self._build_ui()
        self._build_menus()
        self._build_ai_dock()
        self._connect_downloads()

        self.add_tab(self.home_url)
        self.resize(1280, 860)
        self.setWindowTitle("Q1 Browser")

    # ---- Build UI --------------------------------------------------------
    def _build_ui(self):
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_current_tab_changed)
        self.setCentralWidget(self.tabs)

        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready", self)
        self.status_bar.addPermanentWidget(self.status_label)

        tb = QToolBar("Navigation", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        sp = QStyle.StandardPixmap
        self.back_action = self._tool_button(tb, "Back", sp.SP_ArrowBack)
        self.forward_action = self._tool_button(tb, "Forward", sp.SP_ArrowForward)
        self.reload_action = self._tool_button(tb, "Reload", sp.SP_BrowserReload)
        self.stop_action = self._tool_button(tb, "Stop", sp.SP_DialogCancelButton)
        self.home_action = self._tool_button(tb, "Home", sp.SP_DirHomeIcon)

        self.back_action.triggered.connect(lambda: self._run_if_tab(lambda t: t.go_back()))
        self.forward_action.triggered.connect(lambda: self._run_if_tab(lambda t: t.go_forward()))
        self.reload_action.triggered.connect(lambda: self._run_if_tab(lambda t: t.reload()))
        self.stop_action.triggered.connect(lambda: self._run_if_tab(lambda t: t.stop()))
        self.home_action.triggered.connect(lambda: self.go_home())

        self.address_bar = QLineEdit(self)
        self.address_bar.setPlaceholderText("Search the web or enter an address")
        self.address_bar.returnPressed.connect(self.navigate_from_address_bar)
        tb.addSeparator()
        tb.addWidget(self.address_bar)
        tb.addSeparator()

        self.bookmark_action = QAction(self)
        self.bookmark_action.setText("Add bookmark")
        self.bookmark_action.setCheckable(True)
        self.bookmark_action.triggered.connect(self.toggle_bookmark)
        tb.addAction(self.bookmark_action)

        self.ai_action = QAction("AI Assistant", self)
        self.ai_action.setCheckable(True)
        self.ai_action.setChecked(bool(self.settings.ai_enabled))
        self.ai_action.triggered.connect(self.toggle_ai)
        tb.addAction(self.ai_action)

        self.private_action = QAction("New private tab", self)
        self.private_action.triggered.connect(lambda: self.add_tab(private=True))
        tb.addAction(self.private_action)

        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.open_settings)
        tb.addAction(self.settings_action)

    def _tool_button(self, toolbar, name, pixmap_enum):
        act = QAction(self)
        act.setText(name)
        icon = self.style().standardIcon(pixmap_enum)
        act.setIcon(icon)
        toolbar.addAction(act)
        return act

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._act("New tab", self.new_tab, QKeySequence.StandardKey.AddTab))
        file_menu.addAction(self._act("New private tab", lambda: self.add_tab(private=True)))
        file_menu.addAction(self._act("Close tab", self.close_current_tab, QKeySequence.StandardKey.Close))
        file_menu.addSeparator()
        file_menu.addAction(self._act("Exit", self.close, QKeySequence.StandardKey.Quit))

        nav_menu = self.menuBar().addMenu("&Go")
        nav_menu.addAction(self.back_action)
        nav_menu.addAction(self.forward_action)
        nav_menu.addAction(self.reload_action)
        nav_menu.addSeparator()
        nav_menu.addAction(self.home_action)

        bok_menu = self.menuBar().addMenu("&Bookmarks")
        bok_menu.addAction(self._act("Bookmark current page", self.toggle_bookmark))
        bok_menu.addAction(self._act("Manage bookmarks", self.open_bookmarks))

        hist_menu = self.menuBar().addMenu("&History")
        hist_menu.addAction(self._act("Show history", self.open_history))

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self._act("Downloads", self.open_downloads))
        tools_menu.addAction(self.ai_action)
        tools_menu.addAction(self.settings_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self._act("About Q1 Browser", self.about))

    def _act(self, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut:
            from PyQt6.QtGui import QKeySequence
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        return act

    def _build_ai_dock(self):
        self.ai_panel = AIPanel(self.settings, self)
        self.ai_dock = QDockWidget("AI Assistant", self)
        self.ai_dock.setObjectName("AIDock")
        self.ai_dock.setWidget(self.ai_panel)
        self.ai_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        self.ai_dock.setVisible(bool(self.settings.ai_enabled))

    def _connect_downloads(self):
        self.downloads.install(
            [QWebEngineProfile.defaultProfile(), self.private_profile]
        )
        self.downloads.new_download.connect(self._notify_download)

    # ---- Tabs ------------------------------------------------------------
    def current_tab(self):
        return self.tabs.currentWidget()

    def notify(self, message, timeout=3000):
        self.statusBar().showMessage(message, timeout)
        self.status_label.setText(message)

    def add_tab(self, url=None, private=False):
        profile = self.private_profile if private else QWebEngineProfile.defaultProfile()
        tab = BrowserTab(profile, self.newtab_url, private=private, parent=self.tabs)
        self._register_tab(tab)
        if url:
            tab.load(url)
        else:
            tab.load_home()
        return tab

    def _register_tab(self, tab, private=None):
        private = tab.is_private() if private is None else private
        tab.data_changed.connect(self._on_tab_data)
        tab.icon_changed.connect(self._on_tab_icon)
        tab.progress_changed.connect(self._on_tab_progress)
        tab.load_finished.connect(self._on_tab_loaded)
        tab.crashed.connect(self._on_tab_crashed)
        tab.new_window_needs.connect(self._on_new_window_needs)
        idx = self.tabs.addTab(tab, "Private tab" if private else "New tab")
        self.tabs.setCurrentIndex(idx)
        return tab

    def _on_new_window_needs(self, page, window_type):
        current = self.current_tab()
        private = current.is_private() if current else False
        profile = self.private_profile if private else QWebEngineProfile.defaultProfile()
        tab = BrowserTab(
            profile,
            self.newtab_url,
            private=private,
            page=page,
            parent=self.tabs,
        )
        page.new_window_cb = tab._create_new_window_page
        self._register_tab(tab, private=private)
        return tab

    def new_tab(self):
        self.add_tab()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if index < 0 or self.tabs.count() <= 1:
            return
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()
        if self.tabs.count() == 0:
            self.add_tab()

    def close_current_tab(self):
        self.close_tab(self.tabs.currentIndex())

    def _run_if_tab(self, fn):
        tab = self.current_tab()
        if tab:
            fn(tab)

    # ---- Navigation ------------------------------------------------------
    def go_home(self):
        tab = self.current_tab()
        if tab:
            tab.load(self.home_url)

    def navigate_to(self, raw):
        url = self._to_url(raw)
        tab = self.current_tab()
        if tab:
            tab.load(url)
        else:
            self.add_tab(url)

    def open_in_new_tab(self, raw):
        self.add_tab(self._to_url(raw))

    def _to_url(self, raw):
        raw = (raw or "").strip()
        if not raw:
            return QUrl(self.home_url)
        qurl = QUrl.fromUserInput(raw)
        if qurl.isValid() and qurl.scheme() in ("http", "https", "file", "about", "ftp"):
            return qurl
        # Looks like a URL but no scheme.
        if " " not in raw and "." in raw:
            return QUrl(f"https://{raw}")
        template = self.settings.search_engine or "https://duckduckgo.com/?q={}"
        return QUrl(template.replace("{}", QUrl.toPercentEncoding(raw).data().decode()))

    def navigate_from_address_bar(self):
        self.navigate_to(self.address_bar.text())
        self.address_bar.clearFocus()

    # ---- Tab signal handlers --------------------------------------------
    def _on_tab_data(self, url: QUrl, title: str, loading: bool, private: bool):
        tab = self.sender()
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            label = title if title else ("Private tab" if private else "New tab")
            self.tabs.setTabText(idx, label)
            if private:
                self.tabs.setTabToolTip(idx, "Private browsing")
        if self.current_tab() is tab:
            self._sync_address_bar(url)
            self._sync_nav_state(tab)
            self.setWindowTitle(f"{title or 'Q1 Browser'} - Q1 Browser")
            self.bookmark_action.setChecked(self.bookmarks.contains(url.toString()))

    def _sync_address_bar(self, url: QUrl):
        self._address_ignore = True
        try:
            scheme = url.scheme()
            if url == self._newtab_qurl:
                text = ""
            else:
                text = url.toString() if scheme in ("http", "https", "file", "ftp") else ""
            self.address_bar.setText(text)
        finally:
            self._address_ignore = False

    def _sync_nav_state(self, tab):
        try:
            history = tab.view.history()
            self.back_action.setEnabled(history.canGoBack())
            self.forward_action.setEnabled(history.canGoForward())
        except Exception:
            pass

    def _on_tab_icon(self, icon):
        tab = self.sender()
        idx = self.tabs.indexOf(tab)
        if idx >= 0 and not icon.isNull():
            self.tabs.setTabIcon(idx, icon)

    def _on_tab_progress(self, progress):
        tab = self.sender()
        if self.current_tab() is tab:
            self.statusBar().showMessage(f"Loading... {progress}%")

    def _on_tab_loaded(self, ok):
        tab = self.sender()
        if not tab.private and ok:
            url = tab.current_url()
            if (
                url
                and not url.startswith(("about:", "q1://"))
                and url != self.newtab_url
            ):
                self.history.add(tab.current_title(), url)
        if self.current_tab() is tab:
            self._sync_nav_state(tab)
            self.statusBar().showMessage("Done", 1500)

    def _on_tab_crashed(self, reason):
        self.notify(f"Page crashed ({reason}). Reloading...")
        tab = self.sender()
        if tab:
            QTimer.singleShot(400, lambda: tab.reload())

    def _on_current_tab_changed(self, index):
        tab = self.tabs.widget(index)
        if tab:
            self._sync_address_bar(QUrl(tab.current_url() or ""))
            self._sync_nav_state(tab)

    # ---- Bookmarks / history / downloads / settings ----------------------
    def toggle_bookmark(self):
        tab = self.current_tab()
        if tab is None:
            return
        url = tab.current_url()
        if not url:
            return
        if self.bookmarks.contains(url):
            self.bookmarks.remove(url)
            self.bookmark_action.setChecked(False)
            self.notify("Bookmark removed")
        else:
            self.bookmarks.add(tab.current_title(), url)
            self.bookmark_action.setChecked(True)
            self.notify("Bookmark added")

    def open_bookmarks(self):
        dlg = BookmarkDialog(
            self.bookmarks,
            add_current=self.toggle_bookmark,
            open_url=self.open_in_new_tab,
            parent=self,
        )
        dlg.exec()

    def open_history(self):
        dlg = HistoryDialog(self.history, open_url=self.open_in_new_tab, parent=self)
        dlg.exec()

    def open_downloads(self):
        dlg = DownloadCenterDialog(self.downloads, parent=self)
        dlg.exec()

    def open_settings(self):
        dlg = SettingsDialog(self.settings, clear_history_cb=self.history.clear, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply()
            self.home_url = self.settings.homepage or self.newtab_url
            self.ai_panel.refresh_model_label()
            self.ai_dock.setVisible(self.settings.ai_enabled)
            # Default profile HTTP cache cleared by settings dialog.
            self.notify("Settings saved")

    def toggle_ai(self, checked):
        self.ai_dock.setVisible(checked)

    def _notify_download(self, item):
        self.notify(f"Download started: {item.name}")

    def about(self):
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Q1 Browser",
            "<h3>Q1 Browser</h3>"
            "<p>A lightweight, Chromium-based desktop browser with tabs, "
            "bookmarks, history, downloads, private mode and a built-in AI "
            "assistant (OpenAI-compatible endpoints such as Ollama).</p>"
            "<p>Made with PyQt6 / QtWebEngine.</p>",
        )

    # ---- Lifecycle -------------------------------------------------------
    def closeEvent(self, event):
        try:
            if QWebEngineProfile.defaultProfile():
                pass
        except Exception:
            pass
        event.accept()

    def show_devtools_dialog_for(self, tab=None):
        tab = tab or self.current_tab()
        if tab:
            try:
                tab.view.page().setDevToolsPage(tab.view.page())
            except Exception:
                pass
