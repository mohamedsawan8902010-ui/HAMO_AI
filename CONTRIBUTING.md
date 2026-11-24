# Contributing to HAMO AI

Thanks for considering a contribution. The project favors small, well-tested changes over large rewrites.

## Setup
```bash
git clone https://github.com/<your-fork>/HAMO_AI.git
cd HAMO_AI
cp .env.example .env            # add a Gemini API key, or skip and use the mock provider
bash start.sh                   # http://127.0.0.1:8000
```
No `pip install` is required: the backend only uses the Python standard library.

## Running the tests
```bash
bash tests/run_all.sh           # backend unit/integration tests + Markdown renderer tests
HAMO_PROVIDER=mock python backend/main.py   # try the app with no API key / no internet
```
`tests/ui_check.py` is a headless-browser script (needs `pip install playwright --break-system-packages && playwright install chromium`); it is a development aid, not part of CI yet.

## Before opening a pull request
- Run `bash tests/run_all.sh` and make sure it is clean.
- Keep the system prompt (`backend/tutor.py`) and the Arabic UI strings consistent in tone with the rest of the app.
- Never commit `.env`, API keys, or the debug keystore's real-world replacement if you change signing.
- One focused change per pull request, with a short description of what you tested and how.

## Android changes
Changes under `android/` are built automatically by `.github/workflows/build-apk.yml`; a compile error there fails the Actions run. If you cannot build Android locally, describe what you changed and how you reasoned about it, and the CI build will confirm it compiles (it cannot confirm behavior on a real device).

## Reporting issues
Please include: what you expected, what happened, the backend log output, and whether you used the `gemini`, `openai` or `mock` provider.
