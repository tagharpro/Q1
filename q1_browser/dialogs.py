"""Settings, bookmarks, and history dialogs."""
import webbrowser

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, clear_history_cb=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.clear_history_cb = clear_history_cb
        self.setWindowTitle("Q1 Browser Settings")
        self.resize(560, 460)

        tabs = QTabWidget(self)

        # --- General ---
        general = QWidget()
        form = QFormLayout(general)
        self.homepage_edit = QLineEdit(settings.homepage, general)
        self.homepage_edit.setPlaceholderText("Leave empty to use the Q1 new tab page")
        self.search_edit = QLineEdit(settings.search_engine, general)
        self.search_edit.setPlaceholderText("https://duckduckgo.com/?q={}")
        self.restore_check = QCheckBox("Restore open tabs after last session", general)
        self.restore_check.setChecked(bool(settings.restore_last_session))
        form.addRow("Homepage:", self.homepage_edit)
        form.addRow("Search engine URL:", self.search_edit)
        form.addRow("", self.restore_check)
        tabs.addTab(general, "General")

        # --- AI ---
        ai = QWidget()
        aform = QFormLayout(ai)
        self.ai_enabled = QCheckBox("Enable built-in AI assistant", ai)
        self.ai_enabled.setChecked(bool(settings.ai_enabled))
        self.ai_base = QLineEdit(settings.ai_base_url, ai)
        self.ai_base.setPlaceholderText("http://127.0.0.1:11434/v1")
        self.ai_model = QLineEdit(settings.ai_model, ai)
        self.ai_model.setPlaceholderText("llama3.2")
        self.ai_key = QLineEdit(settings.ai_api_key, ai)
        self.ai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_prompt = QTextEdit(settings.ai_system_prompt, ai)
        self.ai_prompt.setFixedHeight(90)
        self.ai_temp = QDoubleSpinBox(ai)
        self.ai_temp.setRange(0, 2)
        self.ai_temp.setSingleStep(0.1)
        self.ai_temp.setValue(float(settings.ai_temperature))
        self.ai_max = QSpinBox(ai)
        self.ai_max.setRange(0, 128000)
        self.ai_max.setValue(int(settings.ai_max_tokens))
        aform.addRow("", self.ai_enabled)
        aform.addRow("OpenAI-compatible base URL:", self.ai_base)
        aform.addRow("Model:", self.ai_model)
        aform.addRow("API key (optional):", self.ai_key)
        aform.addRow("System prompt:", self.ai_prompt)
        aform.addRow("Temperature:", self.ai_temp)
        aform.addRow("Max tokens:", self.ai_max)
        hint = QLabel(
            "Works with Ollama, LM Studio, vLLM, Groq, OpenAI and any "
            "OpenAI-compatible /v1/chat/completions server.",
            ai,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888;")
        aform.addRow(hint)
        tabs.addTab(ai, "AI")

        # --- Privacy ---
        privacy = QWidget()
        pform = QFormLayout(privacy)
        self.clear_history_btn = QPushButton("Clear browsing history", privacy)
        self.clear_history_btn.clicked.connect(self._clear_history)
        self.clear_cookies_btn = QPushButton("Clear cookies & site data", privacy)
        self.clear_cookies_btn.clicked.connect(self._clear_cookies)
        pform.addRow(self.clear_history_btn)
        pform.addRow(self.clear_cookies_btn)
        tabs.addTab(privacy, "Privacy")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs, 1)
        layout.addWidget(buttons)

    def _clear_history(self):
        if self.clear_history_cb:
            self.clear_history_cb()

    def _clear_cookies(self):
        from PyQt6.QtWebEngineCore import QWebEngineProfile

        QWebEngineProfile.defaultProfile().clearAllVisitedLinks()
        try:
            QWebEngineProfile.defaultProfile().clearHttpCache()
        except Exception:
            pass

    def apply(self):
        self.settings.homepage = self.homepage_edit.text().strip()
        self.settings.search_engine = self.search_edit.text().strip() or \
            "https://duckduckgo.com/?q={}"
        self.settings.restore_last_session = self.restore_check.isChecked()
        self.settings.ai_enabled = self.ai_enabled.isChecked()
        self.settings.ai_base_url = self.ai_base.text().strip()
        self.settings.ai_model = self.ai_model.text().strip()
        self.settings.ai_api_key = self.ai_key.text().strip()
        self.settings.ai_system_prompt = self.ai_prompt.toPlainText().strip()
        self.settings.ai_temperature = self.ai_temp.value()
        self.settings.ai_max_tokens = self.ai_max.value()
        self.settings.sync()


class BookmarkDialog(QDialog):
    def __init__(self, bookmarks, add_current=None, open_url=None, parent=None):
        super().__init__(parent)
        self.bookmarks = bookmarks
        self.add_current = add_current
        self.open_url = open_url
        self.setWindowTitle("Bookmarks")
        self.resize(520, 400)

        self.list_widget = QListWidget(self)
        self.refresh()

        buttons = QHBoxLayout()
        add_btn = QPushButton("Add current page", self)
        open_btn = QPushButton("Open selected", self)
        remove_btn = QPushButton("Remove selected", self)
        close_btn = QPushButton("Close", self)
        for b in (add_btn, open_btn, remove_btn):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(buttons)

        add_btn.clicked.connect(self.add_current)
        open_btn.clicked.connect(self.open_selected)
        remove_btn.clicked.connect(self.remove_selected)
        close_btn.clicked.connect(self.accept)

    def refresh(self):
        self.list_widget.clear()
        for it in self.bookmarks.items():
            row = QListWidgetItem(f"{it['title']}\n{it['url']}")
            row.setData(Qt.ItemDataRole.UserRole, it["url"])
            self.list_widget.addItem(row)

    def add_current(self):
        if self.add_current:
            self.add_current()
            self.refresh()

    def open_selected(self):
        item = self.list_widget.currentItem()
        if item and self.open_url:
            self.open_url(item.data(Qt.ItemDataRole.UserRole))

    def remove_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.bookmarks.remove(item.data(Qt.ItemDataRole.UserRole))
            self.refresh()


class HistoryDialog(QDialog):
    def __init__(self, history, open_url=None, parent=None):
        super().__init__(parent)
        self.history = history
        self.open_url = open_url
        self.setWindowTitle("History")
        self.resize(600, 460)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search history...")
        self.search.textChanged.connect(self.refresh)
        self.list_widget = QListWidget(self)
        self.refresh()

        buttons = QHBoxLayout()
        open_btn = QPushButton("Open selected", self)
        clear_btn = QPushButton("Clear history", self)
        close_btn = QPushButton("Close", self)
        buttons.addWidget(open_btn)
        buttons.addWidget(clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(buttons)

        open_btn.clicked.connect(self.open_selected)
        clear_btn.clicked.connect(self.clear_history)
        close_btn.clicked.connect(self.accept)

    def refresh(self, *_):
        self.list_widget.clear()
        query = self.search.text().strip().lower()
        for it in self.history.items(limit=500):
            if query and query not in it["url"].lower() and query not in it["title"].lower():
                continue
            row = QListWidgetItem(f"{it['title']}\n{it['url']}")
            row.setData(Qt.ItemDataRole.UserRole, it["url"])
            self.list_widget.addItem(row)

    def open_selected(self):
        item = self.list_widget.currentItem()
        if item and self.open_url:
            self.open_url(item.data(Qt.ItemDataRole.UserRole))

    def clear_history(self):
        self.history.clear()
        self.refresh()
