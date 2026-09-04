"""Q1 Browser (WebView2 / pywebview edition).

A small, portable Windows browser powered by the installed Microsoft Edge
WebView2 runtime. The UI is a single HTML shell (see assets/index.html).
"""

import os
import sys
import traceback


def _log_error(message):
    try:
        base = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "Q1Browser",
        )
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "q1-error.log"), "a", encoding="utf-8") as fh:
            fh.write(message + "\n")
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Q1 Browser", 0x10)
    except Exception:
        pass


def _safe_main():
    try:
        import webview
    except Exception as exc:
        _log_error(
            "Q1 Browser could not load its rendering engine.\n\n"
            "Make sure Windows has .NET Framework 4.7.2+ and the Microsoft Edge "
            "WebView2 Runtime installed.\n\nError:\n" + traceback.format_exc()
        )
        sys.exit(1)
    return webview


def resource(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", name)


from q1_data import Data, ai_chat  # noqa: E402


class Api:
    def __init__(self):
        self.data = Data()

    # Config --------------------------------------------------------------
    def config_get(self):
        return self.data.get_settings()

    def config_set(self, settings):
        return self.data.set_settings(settings)

    # Bookmarks -----------------------------------------------------------
    def bookmarks_list(self):
        return self.data.bookmarks()

    def bookmarks_add(self, title, url):
        self.data.add_history(title, url, private=False)
        return self.data.add_bookmark(title, url)

    def bookmarks_remove(self, url):
        return self.data.remove_bookmark(url)

    # History -------------------------------------------------------------
    def history_list(self):
        return self.data.history()

    def history_add(self, title, url, private=False):
        self.data.add_history(title, url, private=bool(private))

    def history_clear(self):
        self.data.clear_history()
        return True

    # AI ------------------------------------------------------------------
    def ai_chat(self, message):
        return ai_chat(self.data.get_settings(), message or "")


def main():
    webview = _safe_main()
    index = resource("index.html")
    api = Api()

    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["ALLOW_FILE_URLS"] = True
    webview.settings["SHOW_DEFAULT_MENUS"] = False

    webview.create_window(
        "Q1 Browser",
        index,
        js_api=api,
        width=1280,
        height=860,
        min_size=(880, 600),
        text_select=True,
        confirm_close=True,
        background_color="#0b1e3f",
    )

    data_dir = api.data.dir
    try:
        webview.start(
            debug=False,
            http_server=True,
            private_mode=False,
            storage_path=data_dir,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36 Q1Browser/1.0"
            ),
        )
    except Exception:
        # Fallback: try without the HTTP server if bottle is unavailable.
        _log_error("First start attempt failed; retrying without HTTP server.\n" + traceback.format_exc())
        webview.start(
            debug=False,
            private_mode=False,
            storage_path=data_dir,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _log_error(traceback.format_exc())
        sys.exit(1)
