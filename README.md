# iGuru

A read-only Strands agent that watches a coding-practice directory and coaches you
after each saved change. It can inspect your screen when you request help or appear
idle, and gives progressive hints and guiding questions instead of finished solutions.

## Setup

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r .\helper-agent\requirements.txt
Copy-Item .\helper-agent\.env.example .\helper-agent\.env
```

Put your Gemini API key in `helper-agent/.env`, then run:

```powershell
python .\helper-agent\agent.py --watch .\my-first-agent
```

While it runs, press `Ctrl+Alt+H` anywhere or type `/screen` to capture your primary
display and ask for contextual coaching. After you start changing code, the default
automatic check triggers once if there are no more code changes for 300 seconds
(five minutes).
Saving code resets that timer.

Screen images are held in memory and sent to Gemini only on a help or idle trigger;
they are not saved by this program. Because the display can contain private data,
close unrelated windows before enabling this feature. Disable it with `--no-screen`,
change the idle threshold with `--stuck-after 300`, or select another display with
`--monitor 2`.

Use a different `--session my-problem-name` for each exercise. The coach persists
conversation context under `helper-agent/.coach_sessions`, so it remembers your
attempts after a restart. Type `/help` to see the available commands.

The watcher reads supported source files up to 80 KB. It ignores virtual
environments, Git metadata, editor settings, build output, and dependency folders.

## Windows floating app

Double-click `Launch iGuru.bat`. A small always-on-top **iGuru** button
appears near the right edge of the desktop. Click it once to open the coaching side
panel, then click **×** once to collapse it back to the button.

Click **Quit** in the panel header to stop iGuru completely. To restart it, quit and
then double-click `Launch iGuru.bat` again.

iGuru remembers the side panel's last expanded position and size when you collapse
or quit it. Sending messages and receiving responses will no longer reset the window.

The panel lets you choose a practice folder, ask questions, request a smaller hint,
or share the current screen. `Ctrl+Alt+H` also opens the panel and requests contextual
screen help. The selected folder must currently be chosen before the watcher starts;
restart the app to switch folders after coaching has begun.

Choose a monitoring mode before clicking **Start monitoring**:

- **File** watches saved source files and never captures the screen.
- **Screen** enables on-demand screen help, the global hotkey, and idle checks without
  reading project files.
- **Combined** enables both file and screen monitoring.

The folder selector is shown only for File and Combined modes because Screen mode
does not read local project files.

Screen monitoring is trigger-based. iGuru does not continuously upload the display.

Choose a teaching style before monitoring starts:

- **Standard** is the default calm, concise Socratic coach.
- **Engaging** adds relatable analogies, micro-checkpoints, learner choices,
  prediction questions, specific encouragement, and completion reflection while
  continuing to withhold complete solutions.

## Project structure

```text
helper-agent/
├── agent.py                 # Command-line entry point
├── desktop_app.pyw          # Windows UI entry point
└── iguru/
    ├── activity.py          # Possible-stuck detection
    ├── coach.py             # Strands agent and Gemini model
    ├── config.py            # Shared defaults and file filters
    ├── events.py            # Shared event types
    ├── file_monitor.py      # Read-only practice-file watcher
    ├── prompts.py           # Tutoring policy and contextual prompts
    ├── screen_monitor.py    # Screen capture and global hotkey
    └── tools/               # Controlled Strands tools and learning state
```

Both interfaces import the same reusable `iguru` package, so coaching behavior and
monitoring features can be tested or extended without duplicating implementation.

The Strands agent can call controlled tools for active-window metadata, compact
learner state, recent attempts, hint history, and intervention evaluation. These
tools do not expose arbitrary files, shell commands, or unrestricted screen capture.
