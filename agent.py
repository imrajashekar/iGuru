"""Command-line entry point for the iGuru learning assistant."""

from __future__ import annotations

import argparse
import queue
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

from iguru import (
    ActivityState,
    EventQueue,
    FileChange,
    capture_screen,
    file_prompt,
    listen_for_help_hotkey,
    make_agent,
    screen_prompt,
    watch_files,
    watch_for_stuck,
)
from iguru.config import COACHING_STYLES, DEFAULT_SCAN_INTERVAL, DEFAULT_STUCK_AFTER, MONITOR_MODES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A Strands-powered coding practice coach")
    parser.add_argument(
        "--watch", type=Path, default=Path.cwd(),
        help="practice directory to watch (default: current directory)",
    )
    parser.add_argument(
        "--session", default="coding-practice",
        help="name used to persist this coaching conversation",
    )
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_SCAN_INTERVAL,
        help="scan interval in seconds",
    )
    parser.add_argument(
        "--stuck-after", type=float, default=DEFAULT_STUCK_AFTER,
        help="capture the screen after this many seconds without a code change (0 disables)",
    )
    parser.add_argument(
        "--monitor", type=int, default=1,
        help="screen number to capture; 1 is normally the primary display",
    )
    parser.add_argument(
        "--mode", choices=MONITOR_MODES, default="combined",
        help="monitor saved files, screen triggers, or both (default: combined)",
    )
    parser.add_argument(
        "--coaching-style", choices=COACHING_STYLES, default="standard",
        help="standard Socratic coaching or a more engaging style (default: standard)",
    )
    parser.add_argument("--no-screen", action="store_true", help="disable all screen capture")
    return parser.parse_args()


def read_user_input(events: EventQueue) -> None:
    while True:
        try:
            message = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            message = "/quit"
        events.put(("input", message))
        if message.lower() in {"/quit", "quit", "exit"}:
            return


def run() -> None:
    load_dotenv(Path(__file__).with_name(".env"))
    args = parse_args()
    root = args.watch.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Watch path is not a directory: {root}")

    session_dir = Path(__file__).with_name(".coach_sessions")
    coach = make_agent(args.session, session_dir, args.coaching_style)
    events: EventQueue = queue.Queue()
    activity = ActivityState()

    mode = "file" if args.no_screen else args.mode
    if mode in {"file", "combined"}:
        threading.Thread(target=watch_files, args=(root, events, args.interval), daemon=True).start()
    threading.Thread(target=read_user_input, args=(events,), daemon=True).start()
    if mode in {"screen", "combined"}:
        threading.Thread(target=listen_for_help_hotkey, args=(events,), daemon=True).start()
        if args.stuck_after > 0:
            activity.last_code_activity = time.monotonic()
            threading.Thread(
                target=watch_for_stuck,
                args=(events, activity, args.stuck_after),
                daemon=True,
            ).start()

    print(f"iGuru mode: {mode}")
    print(f"iGuru coaching style: {args.coaching_style}")
    if mode in {"file", "combined"}:
        print(f"iGuru is watching: {root}")
    print("Edit a code file or ask a question. Commands: /screen, /hint, /status, /help, /quit")
    if mode in {"screen", "combined"}:
        print(
            f"Screen capture is ON: press Ctrl+Alt+H for help; possible-stuck check after "
            f"{args.stuck_after:g}s. Captures are sent to Gemini only when triggered."
        )

    while True:
        kind, payload = events.get()
        if kind == "change":
            change = payload
            assert isinstance(change, FileChange)
            activity.last_code_activity = time.monotonic()
            activity.idle_prompt_sent = False
            print(f"\niGuru noticed a change in {change.path.relative_to(root)}...")
            try:
                print(f"iGuru > {coach(file_prompt(change, root))}\n")
            except Exception as exc:
                print(f"iGuru error: {exc}\n")
        elif kind == "screen":
            if mode == "file":
                print("Screen capture is disabled in file mode. Use --mode screen or combined.")
                continue
            print(f"\niGuru is capturing monitor {args.monitor} ({payload})...")
            try:
                image_bytes = capture_screen(args.monitor)
                print(f"iGuru > {coach(screen_prompt(str(payload), image_bytes))}\n")
            except Exception as exc:
                print(f"iGuru screen error: {exc}\n")
        elif kind == "notice":
            print(f"\n{payload}\n")
        else:
            message = str(payload)
            command = message.lower()
            if command in {"/quit", "quit", "exit"}:
                print("iGuru > Nice work. See you next practice session!")
                return
            if command == "/help":
                print(
                    "/screen = capture now, /hint = smaller hint, /status = learning "
                    "checkpoint, /quit = stop"
                )
                continue
            if command == "/screen":
                events.put(("screen", "typed /screen request"))
                continue
            if command == "/hint":
                message = "Give me one additional small hint about my latest obstacle."
            elif command == "/status":
                message = "Briefly summarize my progress, current obstacle, and next checkpoint."
            if not message:
                continue
            try:
                print(f"iGuru > {coach(message)}\n")
            except Exception as exc:
                print(f"iGuru error: {exc}\n")


if __name__ == "__main__":
    run()
