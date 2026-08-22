"""Windows floating side-panel UI for iGuru."""

from __future__ import annotations

import os
import json
import queue
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from dotenv import load_dotenv

from iguru import (
    ActivityState,
    FileChange,
    capture_screen,
    file_prompt,
    listen_for_help_hotkey,
    make_agent,
    screen_prompt,
    watch_files,
    watch_for_stuck,
)


BG = "#111827"
PANEL = "#1f2937"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
TEXT = "#f9fafb"
MUTED = "#9ca3af"
USER = "#93c5fd"
COACH = "#86efac"


class CoachApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("iGuru")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.collapse)

        self.app_dir = Path(__file__).resolve().parent
        self.window_state_file = self.app_dir / ".iguru_window.json"
        self.expanded_geometry = self._load_window_geometry()
        load_dotenv(self.app_dir / ".env")
        self.watch_root = self.app_dir.parent.resolve()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.agent_requests: queue.Queue[tuple[str, object]] = queue.Queue()
        self.activity = ActivityState()
        self.coach = None
        self.started = False
        self.expanded = False
        self.mode_var = tk.StringVar(value="Combined")

        self._build_launcher()
        self._build_panel()
        self.collapse()
        self.root.after(150, self._drain_events)
        threading.Thread(target=self._agent_worker, daemon=True).start()

    def _build_launcher(self) -> None:
        self.launcher = tk.Frame(self.root, bg=BG)
        self.launch_button = tk.Button(
            self.launcher,
            text="✦\niGuru",
            command=self.expand,
            width=8,
            height=3,
            bg=ACCENT,
            fg=TEXT,
            activebackground=ACCENT_HOVER,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 11),
        )
        self.launch_button.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_panel(self) -> None:
        self.panel = tk.Frame(self.root, bg=BG)
        header = tk.Frame(self.panel, bg=PANEL, height=56)
        header.pack(fill="x")
        tk.Label(
            header, text="✦  iGuru", bg=PANEL, fg=TEXT,
            font=("Segoe UI Semibold", 15),
        ).pack(side="left", padx=16, pady=14)
        tk.Button(
            header, text="×", command=self.collapse, bg=PANEL, fg=TEXT,
            activebackground="#374151", activeforeground=TEXT, relief="flat",
            font=("Segoe UI", 18), cursor="hand2",
        ).pack(side="right", padx=8)
        tk.Button(
            header, text="Quit", command=self.quit_app, bg="#7f1d1d", fg=TEXT,
            activebackground="#991b1b", activeforeground=TEXT, relief="flat",
            font=("Segoe UI", 9), cursor="hand2", padx=9, pady=5,
        ).pack(side="right", padx=(4, 0))

        controls = tk.Frame(self.panel, bg=BG)
        self.folder_controls = controls
        controls.pack(fill="x", padx=12, pady=(6, 6))
        self.folder_label = tk.Label(
            controls, text=self._short_path(self.watch_root), anchor="w",
            bg=BG, fg=MUTED, font=("Segoe UI", 9),
        )
        self.folder_label.pack(side="left", fill="x", expand=True)
        tk.Button(
            controls, text="Choose folder", command=self.choose_folder,
            bg=PANEL, fg=TEXT, activebackground="#374151", activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=8,
        ).pack(side="right")

        mode_controls = tk.Frame(self.panel, bg=BG)
        mode_controls.pack(fill="x", padx=12, pady=(12, 6), before=controls)
        tk.Label(
            mode_controls, text="Monitoring mode", bg=BG, fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.mode_picker = ttk.Combobox(
            mode_controls,
            textvariable=self.mode_var,
            values=("File", "Screen", "Combined"),
            state="readonly",
            width=11,
        )
        self.mode_picker.pack(side="left", padx=8)
        self.mode_picker.bind("<<ComboboxSelected>>", self._on_mode_changed)
        self.start_button = tk.Button(
            mode_controls, text="Start monitoring", command=self._ensure_started,
            bg=ACCENT, fg=TEXT, activebackground=ACCENT_HOVER, activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=9,
        )
        self.start_button.pack(side="right")

        self.transcript = ScrolledText(
            self.panel, wrap="word", bg="#0b1220", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10), padx=12, pady=12, state="disabled",
        )
        self.transcript.pack(fill="both", expand=True, padx=12, pady=6)
        self.transcript.tag_config("user", foreground=USER, spacing1=8)
        self.transcript.tag_config("coach", foreground=COACH, spacing1=8)
        self.transcript.tag_config("system", foreground=MUTED, spacing1=8)

        actions = tk.Frame(self.panel, bg=BG)
        actions.pack(fill="x", padx=12, pady=6)
        tk.Button(
            actions, text="See my screen", command=self.request_screen,
            bg=ACCENT, fg=TEXT, activebackground=ACCENT_HOVER, activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=12, pady=6,
        ).pack(side="left")
        tk.Button(
            actions, text="Small hint", command=lambda: self.ask("Give me one small additional hint."),
            bg=PANEL, fg=TEXT, activebackground="#374151", activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=12, pady=6,
        ).pack(side="left", padx=6)

        composer = tk.Frame(self.panel, bg=BG)
        composer.pack(fill="x", padx=12, pady=(4, 12))
        self.entry = tk.Entry(
            composer, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Segoe UI", 10),
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=9)
        self.entry.bind("<Return>", lambda _event: self.send_message())
        tk.Button(
            composer, text="Send", command=self.send_message, bg=ACCENT, fg=TEXT,
            activebackground=ACCENT_HOVER, activeforeground=TEXT, relief="flat",
            cursor="hand2", padx=14, pady=7,
        ).pack(side="right", padx=(8, 0))

    @staticmethod
    def _short_path(path: Path) -> str:
        value = str(path)
        return value if len(value) <= 45 else "…" + value[-44:]

    def _position(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 18
        y = max(18, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def expand(self) -> None:
        if self.expanded:
            self.root.deiconify()
            self.root.lift()
            self.entry.focus_set()
            return
        self.expanded = True
        self.launcher.pack_forget()
        self.panel.pack(fill="both", expand=True)
        if self.expanded_geometry:
            self.root.geometry(self.expanded_geometry)
        else:
            self._position(430, min(720, self.root.winfo_screenheight() - 70))
        self.root.deiconify()
        self.root.lift()
        self.entry.focus_set()

    def collapse(self) -> None:
        if self.expanded:
            self._remember_window_geometry()
        self.expanded = False
        self.panel.pack_forget()
        self.launcher.pack(fill="both", expand=True)
        self._position(88, 82)
        self.root.deiconify()

    def quit_app(self) -> None:
        """Fully stop iGuru; all worker threads are daemon threads."""
        if self.expanded:
            self._remember_window_geometry()
        self.root.destroy()

    def _remember_window_geometry(self) -> None:
        self.root.update_idletasks()
        self.expanded_geometry = self.root.geometry()
        try:
            self.window_state_file.write_text(
                json.dumps({"expanded_geometry": self.expanded_geometry}),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _load_window_geometry(self) -> str | None:
        try:
            value = json.loads(self.window_state_file.read_text(encoding="utf-8")).get(
                "expanded_geometry"
            )
        except (OSError, ValueError, AttributeError):
            return None
        if isinstance(value, str) and re.fullmatch(r"\d+x\d+[+-]\d+[+-]\d+", value):
            return value
        return None

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.watch_root, title="Choose practice folder")
        if not selected:
            return
        if self.started:
            messagebox.showinfo(
                "Restart required",
                "The watcher is already running. Restart iGuru to change folders.",
            )
            return
        self.watch_root = Path(selected).resolve()
        self.folder_label.configure(text=self._short_path(self.watch_root))

    def _on_mode_changed(self, _event: object | None = None) -> None:
        if self.mode_var.get().lower() == "screen":
            self.folder_controls.pack_forget()
        elif not self.folder_controls.winfo_manager():
            self.folder_controls.pack(
                fill="x",
                padx=12,
                pady=(6, 6),
                after=self.mode_picker.master,
            )

    def _ensure_started(self) -> bool:
        if self.started:
            return True
        if not os.getenv("GEMINI_API_KEY"):
            self._append("system", "Add GEMINI_API_KEY to helper-agent/.env, then restart the app.")
            return False
        self.started = True
        mode = self.mode_var.get().lower()
        self.mode_picker.configure(state="disabled")
        self.start_button.configure(text="Monitoring active", state="disabled")
        if mode in {"file", "combined"}:
            self._append("system", f"Watching files in {self.watch_root}")
            threading.Thread(
                target=watch_files, args=(self.watch_root, self.events, 1.0), daemon=True
            ).start()
        if mode in {"screen", "combined"}:
            self.activity.last_code_activity = time.monotonic()
            self._append("system", "Screen help is active. Ctrl+Alt+H requests help.")
            threading.Thread(
                target=watch_for_stuck, args=(self.events, self.activity, 120.0), daemon=True
            ).start()
            threading.Thread(target=listen_for_help_hotkey, args=(self.events,), daemon=True).start()
        self.agent_requests.put(("initialize", None))
        return True

    def send_message(self) -> None:
        message = self.entry.get().strip()
        if not message:
            return
        self.entry.delete(0, "end")
        self.ask(message)

    def ask(self, message: str) -> None:
        self.expand()
        if not self._ensure_started():
            return
        if self.mode_var.get().lower() in {"screen", "combined"}:
            self.activity.last_code_activity = time.monotonic()
            self.activity.idle_prompt_sent = False
        self._append("user", f"You: {message}")
        self.agent_requests.put(("text", message))

    def request_screen(self) -> None:
        self.expand()
        if not self._ensure_started():
            return
        if self.mode_var.get().lower() == "file":
            self._append(
                "system",
                "Screen help is disabled in File mode. Restart in Screen or Combined mode.",
            )
            return
        self.activity.last_code_activity = time.monotonic()
        self.activity.idle_prompt_sent = False
        self._append("system", "Capturing your primary screen…")
        self.agent_requests.put(("screen", "button or Ctrl+Alt+H request"))

    def _agent_worker(self) -> None:
        while True:
            kind, payload = self.agent_requests.get()
            try:
                if kind == "initialize":
                    self.coach = make_agent("desktop-practice", self.app_dir / ".coach_sessions")
                    self.events.put(("ready", None))
                    continue
                if self.coach is None:
                    self.coach = make_agent("desktop-practice", self.app_dir / ".coach_sessions")
                if kind == "screen":
                    image = capture_screen(1)
                    response = self.coach(screen_prompt(str(payload), image))
                else:
                    response = self.coach(payload)
                self.events.put(("response", str(response)))
            except Exception as exc:
                self.events.put(("error", str(exc)))

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "change":
                    change = payload
                    if isinstance(change, FileChange):
                        self.activity.last_code_activity = time.monotonic()
                        self.activity.idle_prompt_sent = False
                        self._append("system", f"Noticed a change in {change.path.name}…")
                        self.agent_requests.put(("text", file_prompt(change, self.watch_root)))
                elif kind == "screen":
                    self.expand()
                    self._append("system", f"Screen check: {payload}…")
                    self.agent_requests.put(("screen", payload))
                elif kind == "response":
                    self.expand()
                    self._append("coach", f"iGuru: {payload}")
                elif kind == "error":
                    self.expand()
                    self._append("system", f"iGuru error: {payload}")
                elif kind == "notice":
                    self._append("system", str(payload))
                elif kind == "ready":
                    self._append("system", "iGuru is ready.")
        except queue.Empty:
            pass
        self.root.after(150, self._drain_events)

    def _append(self, tag: str, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", text + "\n", tag)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")


def main() -> None:
    root = tk.Tk()
    CoachApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
