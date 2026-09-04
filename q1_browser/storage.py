"""Simple JSON backed storage used for bookmarks and history."""
import json
import os
import time

from PyQt6.QtCore import QStandardPaths


def data_dir():
    path = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    if not path:
        path = os.path.join(os.path.expanduser("~"), ".q1browser")
    os.makedirs(path, exist_ok=True)
    return path


class JsonStore:
    """Load/save a JSON object at $DATA_DIR/<name>.json."""

    def __init__(self, name):
        self.path = os.path.join(data_dir(), f"{name}.json")
        self._data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
        return self._default()

    def _default(self):
        return {}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    def raw(self):
        return self._data


class BookmarkStore(JsonStore):
    """Bookmarks organised by folder."""

    def _default(self):
        return {
            "folders": ["Bookmarks", "AI"],
            "items": [],
        }

    def _item(self, url):
        for it in self._data["items"]:
            if it["url"] == url:
                return it
        return None

    def add(self, title, url, folder="Bookmarks"):
        if self._item(url):
            return False
        if folder not in self._data["folders"]:
            self._data["folders"].append(folder)
        self._data["items"].append(
            {
                "title": title or url,
                "url": url,
                "folder": folder,
                "created": time.time(),
            }
        )
        self.save()
        return True

    def remove(self, url):
        before = len(self._data["items"])
        self._data["items"] = [it for it in self._data["items"] if it["url"] != url]
        if len(self._data["items"]) != before:
            self.save()
            return True
        return False

    def contains(self, url):
        return self._item(url) is not None

    def items(self):
        return list(self._data["items"])

    def folders(self):
        return list(self._data["folders"])


class HistoryStore(JsonStore):
    """Simple browser history."""

    MAX_ENTRIES = 2000

    def _default(self):
        return {"items": []}

    def add(self, title, url):
        if not url or url.startswith(("q1://", "about:blank")):
            return
        items = self._data["items"]
        for it in items:
            if it["url"] == url:
                it["title"] = title or it["title"]
                it["last_visit"] = time.time()
                it["visits"] = it.get("visits", 1) + 1
                self.save()
                return
        items.append(
            {
                "title": title or url,
                "url": url,
                "last_visit": time.time(),
                "visits": 1,
            }
        )
        # Keep the list bounded, sorted newest first.
        items.sort(key=lambda i: i.get("last_visit", 0), reverse=True)
        self._data["items"] = items[: self.MAX_ENTRIES]
        self.save()

    def items(self, limit=200):
        items = sorted(
            self._data["items"],
            key=lambda i: i.get("last_visit", 0),
            reverse=True,
        )
        return list(items[:limit])

    def clear(self):
        self._data = {"items": []}
        self.save()
