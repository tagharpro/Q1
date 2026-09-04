"""Persistent browser settings."""
from PyQt6.QtCore import QSettings


class Settings:
    """Small wrapper around QSettings with sensible defaults."""

    def __init__(self):
        self._s = QSettings("tagharpro", "Q1Browser")

    def get(self, key, default=None):
        return self._s.value(key, default)

    def set(self, key, value):
        self._s.setValue(key, value)

    def sync(self):
        self._s.sync()

    @property
    def homepage(self):
        return self.get("browser/homepage", "")

    @homepage.setter
    def homepage(self, value):
        self.set("browser/homepage", value)

    @property
    def search_engine(self):
        return self.get("browser/search_engine", "https://duckduckgo.com/?q={}")

    @search_engine.setter
    def search_engine(self, value):
        self.set("browser/search_engine", value)

    @property
    def restore_last_session(self):
        return self.get("browser/restore_last_session", True)

    @restore_last_session.setter
    def restore_last_session(self, value):
        self.set("browser/restore_last_session", bool(value))

    # AI settings ---------------------------------------------------------
    @property
    def ai_enabled(self):
        return self.get("ai/enabled", True)

    @ai_enabled.setter
    def ai_enabled(self, value):
        self.set("ai/enabled", bool(value))

    @property
    def ai_base_url(self):
        return self.get("ai/base_url", "http://127.0.0.1:11434/v1")

    @ai_base_url.setter
    def ai_base_url(self, value):
        self.set("ai/base_url", value.rstrip("/"))

    @property
    def ai_model(self):
        return self.get("ai/model", "llama3.2")

    @ai_model.setter
    def ai_model(self, value):
        self.set("ai/model", value)

    @property
    def ai_api_key(self):
        return self.get("ai/api_key", "")

    @ai_api_key.setter
    def ai_api_key(self, value):
        self.set("ai/api_key", value)

    @property
    def ai_system_prompt(self):
        return self.get(
            "ai/system_prompt",
            "You are a helpful AI assistant embedded inside a web browser. "
            "Answer clearly, accurately and concisely.",
        )

    @ai_system_prompt.setter
    def ai_system_prompt(self, value):
        self.set("ai/system_prompt", value)

    @property
    def ai_temperature(self):
        return float(self.get("ai/temperature", 0.7))

    @ai_temperature.setter
    def ai_temperature(self, value):
        self.set("ai/temperature", float(value))

    @property
    def ai_max_tokens(self):
        return int(self.get("ai/max_tokens", 2048))

    @ai_max_tokens.setter
    def ai_max_tokens(self, value):
        self.set("ai/max_tokens", int(value))
