"""Local storage + AI logic for the Q1 Browser WebView2 edition."""
import json
import os
import time
import urllib.request


class Data:
    def __init__(self):
        base = os.environ.get("Q1_DATA_DIR")
        if not base:
            base = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                "Q1Browser",
            )
        self.dir = base
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "q1.json")
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        except Exception:
            self._data = {}
        self._data.setdefault("settings", {
            "homepage": "",
            "search_url": "https://duckduckgo.com/?q={}",
            "ai_base_url": "http://127.0.0.1:11434/v1",
            "ai_model": "llama3.2",
            "ai_api_key": "",
            "ai_temperature": 0.7,
        })
        self._data.setdefault("bookmarks", [])
        self._data.setdefault("history", [])

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    # Settings ------------------------------------------------------------
    def get_settings(self):
        return self._data.get("settings", {})

    def set_settings(self, settings):
        self._data["settings"].update(settings or {})
        self.save()
        return self._data["settings"]

    # Bookmarks -----------------------------------------------------------
    def bookmarks(self):
        return self._data.get("bookmarks", [])

    def add_bookmark(self, title, url):
        items = self._data.setdefault("bookmarks", [])
        if any(i.get("url") == url for i in items):
            return False
        items.insert(0, {"title": title or url, "url": url, "created": time.time()})
        self.save()
        return True

    def remove_bookmark(self, url):
        items = self._data.setdefault("bookmarks", [])
        before = len(items)
        self._data["bookmarks"] = [i for i in items if i.get("url") != url]
        self.save()
        return len(items) != before

    # History -------------------------------------------------------------
    def history(self, limit=300):
        items = sorted(
            self._data.get("history", []),
            key=lambda i: i.get("t", 0),
            reverse=True,
        )
        return items[:limit]

    def add_history(self, title, url, private=False):
        if not url or private or url.startswith(("about:", "q1:")):
            return
        items = self._data.setdefault("history", [])
        for item in items:
            if item.get("url") == url:
                item["title"] = title or item.get("title", url)
                item["t"] = time.time()
                item["v"] = item.get("v", 1) + 1
                self.save()
                return
        items.append({"title": title or url, "url": url, "t": time.time(), "v": 1})
        self._data["history"] = sorted(items, key=lambda i: i.get("t", 0), reverse=True)[:2000]
        self.save()

    def clear_history(self):
        self._data["history"] = []
        self.save()


def ai_chat(settings, message):
    """Call an OpenAI-compatible endpoint and return the reply text."""
    base = (settings.get("ai_base_url") or "").rstrip("/")
    model = settings.get("ai_model") or "llama3.2"
    api_key = settings.get("ai_api_key") or ""
    endpoint = f"{base}/chat/completions"

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are the built-in assistant of Q1 Browser. "
                           "Answer concisely and accurately.",
            },
            {"role": "user", "content": message},
        ],
        "stream": False,
        "temperature": float(settings.get("ai_temperature", 0.7)),
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
        choices = payload.get("choices") or []
        if not choices:
            return {"ok": False, "error": "No response from model."}
        return {"ok": True, "reply": (choices[0].get("message") or {}).get("content", "").strip()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
