"""
GUI Launcher for free-claude-code proxy.
Edit .env settings and start the proxy server with a modern PySide6 interface.
Supports two server profiles: Server 1 (.env) and Server 2 (.env-2).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


# ── Config ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

PROFILES: dict[str, Path] = {
    "Server 1": BASE_DIR / ".env",
    "Server 2": BASE_DIR / ".env-2",
}

STYLESHEET = """
QWidget {
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #f5f5f5;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px;
    background: #fff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background: #fff;
    color: #222;
}
QLabel {
    color: #444;
}
QLineEdit {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 6px 10px;
    background: #fafafa;
    color: #222;
}
QLineEdit:focus {
    border-color: #0078d4;
    background: #fff;
}
QComboBox {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px 10px;
    background: #fafafa;
    color: #222;
    min-height: 22px;
}
QComboBox:focus {
    border-color: #0078d4;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 20px;
}
QPushButton#btnSave {
    background-color: #0078d4;
    color: #fff;
}
QPushButton#btnSave:hover {
    background-color: #106ebe;
}
QPushButton#btnStart {
    background-color: #107c10;
    color: #fff;
}
QPushButton#btnStart:hover {
    background-color: #0b6a0b;
}
QPushButton#btnStop {
    background-color: #d32f2f;
    color: #fff;
}
QPushButton#btnStop:hover {
    background-color: #b71c1c;
}
QStatusBar {
    background: #e8e8e8;
    color: #555;
    font-size: 12px;
}
QTextEdit {
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #1e1e1e;
    color: #d4d4d4;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}
"""


# ── Env helpers ──────────────────────────────────────────────────────────
def _parse_env(text: str) -> dict[str, str]:
    """Parse .env text into {key: value}."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([\w]+)="?(.*?)"?\s*(?:#.*)?$', line)
        if m:
            result[m.group(1)] = m.group(2).strip('"')
    return result


def _dump_env(data: dict[str, str], template: str) -> str:
    """Merge data back into the template, preserving comments and order."""
    lines = template.splitlines(keepends=True)

    def _replace(key: str, val: str) -> str:
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key}="{escaped}"'

    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        m = re.match(r'^([\w]+)=', line)
        if m and m.group(1) in data and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(_replace(m.group(1), data[m.group(1)]) + "\n")
        else:
            out.append(line)
    for k, v in data.items():
        if k not in seen:
            out.append(_replace(k, v) + "\n")
    return "".join(out)


# ── Field definition ─────────────────────────────────────────────────────
PROVIDER_CHOICES = ["nvidia_nim", "open_router", "deepseek", "lmstudio", "llamacpp"]
PLATFORM_CHOICES = ["telegram", "discord"]
WHISPER_DEVICE_CHOICES = ["cpu", "cuda", "nvidia_nim"]
BOOLEAN_CHOICES = ["true", "false"]

FIELD_DEFS: list[tuple] = [
    ("heading", "Provider & Model Settings"),
    ("PROVIDER_RATE_LIMIT", "Rate Limit", "line"),
    ("PROVIDER_RATE_WINDOW", "Rate Window (s)", "line"),
    ("PROVIDER_MAX_CONCURRENCY", "Max Concurrency", "line"),
    ("MODEL_OPUS", "Model (Opus)", "line"),
    ("MODEL_SONNET", "Model (Sonnet)", "line"),
    ("MODEL_HAIKU", "Model (Haiku)", "line"),
    ("MODEL", "Model (Fallback)", "line"),
    ("ENABLE_THINKING", "Enable Thinking", "combo", BOOLEAN_CHOICES),
    ("heading", "API Keys"),
    ("NVIDIA_NIM_API_KEY", "NVIDIA NIM API Key", "password"),
    ("OPENROUTER_API_KEY", "OpenRouter API Key", "password"),
    ("DEEPSEEK_API_KEY", "DeepSeek API Key", "password"),
    ("heading", "Proxy Settings"),
    ("NVIDIA_NIM_PROXY", "NVIDIA NIM Proxy", "line"),
    ("OPENROUTER_PROXY", "OpenRouter Proxy", "line"),
    ("LMSTUDIO_PROXY", "LM Studio Proxy", "line"),
    ("LLAMACPP_PROXY", "Llama.cpp Proxy", "line"),
    ("heading", "Messaging Platform"),
    ("MESSAGING_PLATFORM", "Platform", "combo", PLATFORM_CHOICES),
    ("MESSAGING_RATE_LIMIT", "Rate Limit", "line"),
    ("MESSAGING_RATE_WINDOW", "Rate Window (s)", "line"),
    ("DISCORD_BOT_TOKEN", "Discord Bot Token", "password"),
    ("ALLOWED_DISCORD_CHANNELS", "Allowed Discord Channels", "line"),
    ("TELEGRAM_BOT_TOKEN", "Telegram Bot Token", "password"),
    ("ALLOWED_TELEGRAM_USER_ID", "Allowed Telegram User ID", "line"),
    ("heading", "Voice Transcription"),
    ("VOICE_NOTE_ENABLED", "Voice Note Enabled", "combo", BOOLEAN_CHOICES),
    ("WHISPER_DEVICE", "Whisper Device", "combo", WHISPER_DEVICE_CHOICES),
    ("WHISPER_MODEL", "Whisper Model", "line"),
    ("HF_TOKEN", "HuggingFace Token", "password"),
    ("heading", "Server"),
    ("PORT", "Port", "line"),
    ("ANTHROPIC_AUTH_TOKEN", "Auth Token (optional)", "password"),
    ("heading", "Agent Config"),
    ("CLAUDE_WORKSPACE", "Workspace Path", "line"),
    ("ALLOWED_DIR", "Allowed Directory", "line"),
    ("FAST_PREFIX_DETECTION", "Fast Prefix Detection", "combo", BOOLEAN_CHOICES),
    ("ENABLE_NETWORK_PROBE_MOCK", "Mock Network Probe", "combo", BOOLEAN_CHOICES),
    ("ENABLE_TITLE_GENERATION_SKIP", "Skip Title Generation", "combo", BOOLEAN_CHOICES),
    ("ENABLE_SUGGESTION_MODE_SKIP", "Skip Suggestion Mode", "combo", BOOLEAN_CHOICES),
    ("ENABLE_FILEPATH_EXTRACTION_MOCK", "Mock Filepath Extraction", "combo", BOOLEAN_CHOICES),
    ("heading", "HTTP Timeouts"),
    ("HTTP_READ_TIMEOUT", "Read Timeout (s)", "line"),
    ("HTTP_WRITE_TIMEOUT", "Write Timeout (s)", "line"),
    ("HTTP_CONNECT_TIMEOUT", "Connect Timeout (s)", "line"),
]


# ── Main Window ──────────────────────────────────────────────────────────
class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("free-claude-code Launcher")
        self.setMinimumSize(820, 680)
        self.setStyleSheet(STYLESHEET)

        self.fields: dict[str, QtWidgets.QWidget] = {}
        self._current_profile: str = "Server 1"

        # QProcess for non-blocking subprocess management
        self.qprocess = QtCore.QProcess(self)
        self.qprocess.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        self.qprocess.readyReadStandardOutput.connect(self._on_stdout)
        self.qprocess.finished.connect(self._on_finished)

        self._build_ui()
        self._switch_profile("Server 1")

    # ── UI Construction ──────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # ── Profile selector ──
        profile_bar = QtWidgets.QHBoxLayout()
        profile_bar.setSpacing(10)

        lbl_profile = QtWidgets.QLabel("Profile:")
        lbl_profile.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.addItems(list(PROFILES.keys()))
        self.profile_combo.setMinimumWidth(200)
        self.profile_combo.currentTextChanged.connect(self._switch_profile)

        self.lbl_env_file = QtWidgets.QLabel("")
        self.lbl_env_file.setStyleSheet("color: #888; font-size: 12px;")

        profile_bar.addWidget(lbl_profile)
        profile_bar.addWidget(self.profile_combo)
        profile_bar.addWidget(self.lbl_env_file)
        profile_bar.addStretch()
        layout.addLayout(profile_bar)

        # ── Scrollable form area ──
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        layout.addWidget(scroll, stretch=1)

        form_container = QtWidgets.QWidget()
        scroll.setWidget(form_container)
        form_layout = QtWidgets.QVBoxLayout(form_container)
        form_layout.setSpacing(0)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self._rebuild_form(form_layout)

        # ── Buttons ──
        btn_bar = QtWidgets.QHBoxLayout()
        btn_bar.setSpacing(10)

        self.btn_save = QtWidgets.QPushButton("Save .env")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self._save_env)

        self.btn_start = QtWidgets.QPushButton("Start Proxy")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.clicked.connect(self._start_proxy)

        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_proxy)

        btn_bar.addWidget(self.btn_save)
        btn_bar.addWidget(self.btn_start)
        btn_bar.addWidget(self.btn_stop)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        # ── Log output ──
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        layout.addWidget(self.log)

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

    def _rebuild_form(self, form_layout: QtWidgets.QVBoxLayout) -> None:
        current_group: QtWidgets.QGroupBox | None = None
        current_group_layout: QtWidgets.QFormLayout | None = None

        for item in FIELD_DEFS:
            if item[0] == "heading":
                current_group = QtWidgets.QGroupBox(item[1])
                current_group_layout = QtWidgets.QFormLayout(current_group)
                current_group_layout.setSpacing(8)
                current_group_layout.setContentsMargins(10, 16, 10, 10)
                form_layout.addWidget(current_group)
                continue

            key, label, kind = item[0], item[1], item[2]
            extra = item[3] if len(item) > 3 else None

            if kind == "combo":
                w = QtWidgets.QComboBox()
                assert extra is not None
                w.addItems(extra)
                w.setEditable(True)
            elif kind == "password":
                w = QtWidgets.QLineEdit()
                w.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            else:
                w = QtWidgets.QLineEdit()

            self.fields[key] = w
            assert current_group_layout is not None
            current_group_layout.addRow(label + ":", w)

    # ── Profile switching ────────────────────────────────────────────
    def _switch_profile(self, profile: str) -> None:
        self._current_profile = profile
        env_path = PROFILES[profile]
        self.lbl_env_file.setText(str(env_path))
        self._load_env(env_path)

    # ── Env I/O ──────────────────────────────────────────────────────
    def _load_env(self, path: Path) -> None:
        if not path.exists():
            self.log.append(f"\u2139 {path.name} not found, starting empty")
            for key, w in self.fields.items():
                if isinstance(w, QtWidgets.QComboBox):
                    w.setEditText("")
                else:
                    w.setText("")
            return

        raw = path.read_text(encoding="utf-8")
        data = _parse_env(raw)
        for key, w in self.fields.items():
            val = data.get(key, "")
            if isinstance(w, QtWidgets.QComboBox):
                idx = w.findText(val, QtCore.Qt.MatchFlag.MatchFixedString)
                if idx >= 0:
                    w.setCurrentIndex(idx)
                else:
                    w.setEditText(val)
            else:
                w.setText(val)
        self.log.append(f"\U0001f4c4 Loaded {path.name} ({len(data)} keys)")
        self.status.showMessage(f"Loaded {path.name}", 3000)

    def _save_env(self) -> None:
        path = PROFILES[self._current_profile]

        if path.exists():
            template = path.read_text(encoding="utf-8")
        else:
            template = ""

        data: dict[str, str] = {}
        for key, w in self.fields.items():
            if isinstance(w, QtWidgets.QComboBox):
                data[key] = w.currentText().strip()
            else:
                data[key] = w.text().strip()

        merged = _dump_env(data, template)
        path.write_text(merged, encoding="utf-8")
        self.log.append(f"\u2705 {path.name} saved")
        self.status.showMessage(f"{path.name} saved", 3000)

    # ── Process control (non-blocking via QProcess) ──────────────────
    def _start_proxy(self) -> None:
        if self.qprocess.state() != QtCore.QProcess.ProcessState.NotRunning:
            self.log.append("\u26a0 Proxy is already running")
            return

        # Save before starting
        self._save_env()

        port = self.fields["PORT"].text().strip() if "PORT" in self.fields else "8083"
        if not port:
            port = "8083"

        uvicorn_path = str(Path(sys.executable).parent / "uvicorn.exe")
        args = [
            "server:app",
            "--host", "0.0.0.0",
            "--port", port,
            "--timeout-graceful-shutdown", "5",
        ]
        self.log.append(f"\U0001f680 Starting proxy server (profile: {self._current_profile})...")
        self.log.append(f"   {uvicorn_path} {' '.join(args)}")
        self.status.showMessage("Starting...")

        self.qprocess.setWorkingDirectory(str(BASE_DIR))
        self.qprocess.start(uvicorn_path, args)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _stop_proxy(self) -> None:
        if self.qprocess.state() == QtCore.QProcess.ProcessState.NotRunning:
            return
        self.log.append("\U0001f6d1 Stopping proxy server...")
        self.qprocess.terminate()
        if not self.qprocess.waitForFinished(5000):
            self.qprocess.kill()
            self.qprocess.waitForFinished(3000)
        # _on_finished handles button state

    def _on_stdout(self) -> None:
        data = self.qprocess.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        for line in text.splitlines():
            self.log.append(line.rstrip())
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_finished(self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus) -> None:
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        status_str = "crashed" if exit_status == QtCore.QProcess.ExitStatus.CrashExit else "exited"
        self.log.append(f"\u2705 Proxy {status_str} (code {exit_code})")
        self.status.showMessage(f"Proxy {status_str}", 5000)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.qprocess.state() != QtCore.QProcess.ProcessState.NotRunning:
            self.qprocess.terminate()
            self.qprocess.waitForFinished(3000)
        event.accept()


# ── Entry ────────────────────────────────────────────────────────────────
def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LauncherWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
