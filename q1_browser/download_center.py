"""Download manager for Q1 Browser."""
import os

from PyQt6.QtCore import QObject, QStandardPaths, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


def downloads_dir():
    d = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DownloadLocation
    )
    if not d:
        d = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(d, exist_ok=True)
    return d


class DownloadItem:
    """Small wrapper for a QWebEngineDownloadRequest."""

    def __init__(self, request: QWebEngineDownloadRequest):
        self.request = request
        self.name = request.downloadFileName() or "download"
        self.url = request.url().toString()
        self.path = ""

    def progress(self):
        try:
            total = self.request.totalBytes()
            received = self.request.receivedBytes()
        except AttributeError:
            return 0, 0
        return received, total

    def state(self):
        return self.request.state()

    def download_path(self):
        try:
            return self.request.downloadFileName()
        except AttributeError:
            return ""

    def accept(self, directory=None):
        directory = directory or downloads_dir()
        try:
            self.request.setDownloadDirectory(directory)
            path = os.path.join(directory, self.name)
            self.request.setDownloadFileName(self.name)
            self.path = path
            self.request.accept()
        except Exception:
            pass


class DownloadManager(QObject):
    new_download = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_states)
        self._timer.start(1000)
        self._installed = False

    def install(self, profiles):
        for profile in profiles:
            try:
                if profile is not None:
                    profile.downloadRequested.connect(self.on_download_requested)
            except Exception:
                pass
        self._installed = True

    def on_download_requested(self, request: QWebEngineDownloadRequest):
        item = DownloadItem(request)
        item.accept()
        self.items.append(item)
        self.new_download.emit(item)

    def _check_states(self):
        for item in self.items:
            try:
                item.request.receivedBytes()
            except Exception:
                pass
        self.state_changed.emit()

    state_changed = pyqtSignal()


class DownloadCenterDialog(QDialog):
    def __init__(self, manager: DownloadManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Downloads")
        self.resize(620, 420)

        self.list_widget = QListWidget(self)
        self.hint = QLabel("Downloads will appear here.", self)
        self.hint.setStyleSheet("color:#888;")

        buttons = QHBoxLayout()
        open_btn = QPushButton("Open selected folder", self)
        clear_btn = QPushButton("Clear finished", self)
        close_btn = QPushButton("Close", self)
        buttons.addWidget(open_btn)
        buttons.addWidget(clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.hint)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(buttons)

        open_btn.clicked.connect(self.open_selected_folder)
        clear_btn.clicked.connect(self.clear_finished)
        close_btn.clicked.connect(self.accept)
        self.manager.new_download.connect(lambda _: self.refresh())
        self.manager.state_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        rows = self.manager.items
        if not rows:
            self.hint.setText("Downloads will appear here.")
            return
        self.hint.setText(f"{len(rows)} download(s).")
        for idx, item in enumerate(rows):
            name = item.name
            received, total = item.progress()
            bar_text = f"{name}  ({received}/{total} bytes)"
            row = QListWidgetItem(bar_text)
            self.list_widget.addItem(row)
            bar = QProgressBar(self.list_widget)
            bar.setMaximum(100)
            if total > 0:
                bar.setValue(int(received * 100 / total))
            else:
                bar.setRange(0, 0)
            self.list_widget.setItemWidget(row, bar)

    def selected_item(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.manager.items):
            return self.manager.items[row]
        return None

    def clear_finished(self):
        finished = []
        for item in self.manager.items:
            try:
                if item.request.state() != QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                    continue
            except Exception:
                continue
            finished.append(item)
        for item in finished:
            self.manager.items.remove(item)
        self.refresh()

    def open_selected_folder(self):
        item = self.selected_item()
        if item is None:
            return
        directory = os.path.dirname(item.path) if item.path else downloads_dir()
        if not directory or not os.path.isdir(directory):
            directory = downloads_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory))
