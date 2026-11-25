# Episode 3 project — the folder-organizing agent Claude Code built

This folder is the demo project from Local AI Lab Episode 3,
"Build Your First AI Agent with Claude Code — Beginner Tutorial".
Everything in it was written by Claude Code (Opus 5.5, Claude Pro) from one
plain-English assignment, in a single recorded terminal session. Nothing here
was hand-edited afterwards.

## What it is

`claude-agent-demo/organize_agent.py` — a small Python AI agent (standard
library only, just under 200 lines) that sorts a messy folder into subfolders by file
type and writes a Markdown report. The summary paragraph of the report is
written by a local Ollama model (`qwen2.5:3b`); the file tables in the report
come straight from the code.

## Run it

```bash
python3 organize_agent.py messy            # actually organize
python3 organize_agent.py messy --dry-run  # preview: shows the moves, moves nothing
python3 organize_agent.py messy --no-llm   # skip the Ollama summary
```

Ollama must be running on `localhost:11434` with `qwen2.5:3b` pulled for the
model-written summary; if Ollama is unavailable the agent writes a plain
summary itself and still works.

## The demo folder

`claude-agent-demo/messy/` is the folder from the video, shown here in its
organized state after the recorded run: 10 files moved into
`documents/` (4), `images/` (2), `spreadsheets/` (3), `code/` (1),
`other/` (1), plus the report `messy/organize_report.md`.

One file in the demo was a deliberate fixture, disclosed in the video: an old
January `budget.csv` was already sitting in `messy/spreadsheets/` before the
run, so the incoming `messy/budget.csv` had to be renamed to
`spreadsheets/budget (1).csv` instead of overwriting it. `messy-before/` is
a copy of the folder in its messy starting state (same 10 files + the same
duplicate fixture), so you can try the run yourself:
`python3 organize_agent.py messy-before`. (It can also be rebuilt from
scratch with `../build/setup_demo.sh` — note that script wipes and
recreates the whole demo folder, so only run it on a copy.)

## What happened in the recorded session

- Claude Code inspected the folder first, then showed its plan — and spotted
  the duplicate trap before writing any code.
- It wrote the agent, then tested it in a scratch copy before
  touching the real folder.
- Testing caught a real bug: the small local model miscounted (it said 9
  files moved, there were 10; 2 renamed, there was 1). The fix was to have
  the code compute the totals and tell the model to copy them exactly.
- The live run took 29 seconds: 10 files moved, 1 renamed, 1 skipped
  (the `spreadsheets/` folder itself), report written.
- The final summary's numbers were right, but the wording had two small
  flaws the video calls out: it never mentions the `other` category, and it
  says "moved from categories" where it means "moved into".

## Cost

Claude Code itself needs a Pro or Max subscription (Pro was $20/month at the
time of recording). The agent it built runs entirely on the free local Ollama
model — no API key, nothing leaves your computer.
