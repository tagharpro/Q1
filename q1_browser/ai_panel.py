"""Built-in AI assistant panel.

Uses an OpenAI-compatible chat completions endpoint (works with Ollama,
LM Studio, vLLM, Groq, OpenAI, etc.). Supports streaming responses.
"""
import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .settings import Settings


class AIPanel(QWidget):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.view = QTextEdit(self)
        self.view.setReadOnly(True)
        self.view.setPlaceholderText(
            "AI assistant.\n\nSend a message or ask it about the current page, "
            "text, code, or anything else."
        )
        self.view.setAcceptRichText(False)

        self.input = QPlainTextEdit(self)
        self.input.setPlaceholderText(
            "Ask the AI anything...  (Enter to send, Shift+Enter for a new line)"
        )
        self.input.setFixedHeight(72)
        self.input.installEventFilter(self)

        self.model_label = QLabel(self)
        self.model_label.setStyleSheet("color: #888; font-size: 11px;")
        self.model_label.setWordWrap(True)

        self.send_btn = QPushButton("Send", self)
        self.clear_btn = QPushButton("Clear", self)
        self.stop_btn = QPushButton("Stop", self)
        self.stop_btn.setEnabled(False)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for btn in (self.send_btn, self.clear_btn, self.stop_btn):
            btn_row.addWidget(btn)
        btn_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.model_label)
        layout.addWidget(self.input)
        layout.addLayout(btn_row)

        self.send_btn.clicked.connect(self.send)
        self.clear_btn.clicked.connect(self.clear_chat)
        self.stop_btn.clicked.connect(self.stop)

        self.manager = QNetworkAccessManager(self)
        self.reply = None
        self.messages = []
        self._stream_buffer = b""
        self._assistant_content = ""
        self.reset_conversation()
        self.refresh_model_label()

    # ---- UI helpers -----------------------------------------------------
    def refresh_model_label(self):
        base = self.settings.ai_base_url
        model = self.settings.ai_model
        self.model_label.setText(f"Model: {model}\nEndpoint: {base}")

    def append_message(self, role, text):
        prefix = "You" if role == "user" else "AI"
        color = "#1a73e8" if role == "user" else "#0f8a3d"
        self.view.append(f'<b style="color:{color}">{prefix}:</b>')
        self.view.append(text.replace("\n", "<br>"))
        self.view.append("")

    def append_assistant_chunk(self, text):
        cursor = self.view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.view.setTextCursor(cursor)
        self.view.ensureCursorVisible()

    def notify_status(self, text):
        self.view.append(f'<i style="color:#b00">{text}</i>')

    def reset_conversation(self):
        self.messages = [
            {"role": "system", "content": self.settings.ai_system_prompt}
        ]
        self._assistant_content = ""
        self.view.clear()
        self.view.append("<b>AI Assistant</b>")
        self.view.append(
            "Connected to an OpenAI-compatible endpoint. By default it points "
            "to Ollama at http://127.0.0.1:11434/v1. Change the endpoint or "
            "model in Settings -> AI."
        )
        self.view.append("")

    def clear_chat(self):
        self.reset_conversation()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self.send()
                return True
        return super().eventFilter(obj, event)

    # ---- sending --------------------------------------------------------
    def send(self):
        text = self.input.toPlainText().strip()
        if not text or self.reply is not None:
            return
        self.input.clear()
        self._assistant_content = ""
        self.messages.append({"role": "user", "content": text})
        self.append_message("user", text)

        base = self.settings.ai_base_url.rstrip("/")
        endpoint = f"{base}/chat/completions"

        stream = True
        body = {
            "model": self.settings.ai_model,
            "messages": self.messages,
            "stream": stream,
            "temperature": self.settings.ai_temperature,
        }
        max_tokens = self.settings.ai_max_tokens
        if max_tokens:
            body["max_tokens"] = max_tokens

        request = QNetworkRequest(QUrl(endpoint))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        api_key = self.settings.ai_api_key
        if api_key:
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())

        data = json.dumps(body).encode("utf-8")

        self.reply = self.manager.post(request, data)
        self.reply.errorOccurred.connect(self.on_error)
        self.reply.readyRead.connect(self.on_ready_read)
        self.reply.finished.connect(self.on_finished)

        self.view.append('<i style="color:#b00">…</i>')
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._stream_buffer = b""

    def stop(self):
        if self.reply is not None:
            self.reply.abort()

    def _feed_stream(self, line: str):
        line = line.strip()
        if not line.startswith("data:"):
            return
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            return
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        choices = data.get("choices") or []
        if not choices:
            return
        delta = choices[0].get("delta") or {}
        content = delta.get("content")
        if content:
            self._assistant_content += content
            self.append_assistant_chunk(content)

    def on_ready_read(self):
        if self.reply is None:
            return
        self._stream_buffer += self.reply.readAll().data()
        lines = self._stream_buffer.split(b"\n")
        self._stream_buffer = lines.pop()  # keep the last partial line
        for line in lines:
            self._feed_stream(line.decode("utf-8", errors="ignore"))

    def on_finished(self):
        if self.reply is None:
            return
        if self._stream_buffer:
            self._feed_stream(self._stream_buffer.decode("utf-8", errors="ignore"))
            self._stream_buffer = b""
        self.reply = None
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.view.append("")
        # Store the assistant reply for follow-up context.
        assistant_text = self._assistant_content.strip()
        self._assistant_content = ""
        if assistant_text:
            self.messages.append({"role": "assistant", "content": assistant_text})

    def on_error(self, error):
        if self.reply is None:
            return
        detail = self.reply.errorString() or str(error)
        if "Operation canceled" not in detail:
            self.notify_status(f"AI error: {detail}\n\nCheck Settings > AI "
                               f"(endpoint / model / API key).")
