# HAMO AI

An Arabic educational AI assistant for Android students. Copy a paragraph from any study page, tap the floating **H** button over Chrome, paste it, and get an explanation, summary, examples or a quiz without leaving the page.

**Version 0.2.0** -- see [Status](#status) for exactly what is verified and what is not.

## The problem

While reading a lecture or a lesson, a student hits a rule, a term or a question they do not understand and has to leave the page to search for help. HAMO AI puts the explanation on top of the page they are studying.

## Status

| Area | State |
|---|---|
| Python backend (`/health`, `/api/chat`, serves the web UI) | Verified: 26 automated tests (mock provider) |
| Gemini provider | Live-tested by the project owner (`gemini-3.5-flash-lite`); not re-run in automated tests |
| Web UI (modes, history, Markdown, copy/paste, errors) | Verified in headless Chromium at phone size (mock provider) |
| Educational modes (explain, summarize, simplify, examples, quiz, step by step) | Implemented; answer quality with live Gemini needs human review |
| Android app: control screen, in-app chat, floating button + panel | **Written, not yet built or tested on a device** |
| OpenAI provider | Experimental, untested |
| Claude provider, image/screen understanding, hosting, accounts | Not implemented |

## Architecture

```
Android phone
 +-- HAMO AI app (Java, no dependencies)
 |    +-- OverlayService: floating "H" button  --tap-->  panel with a WebView
 |    +-- MainActivity / ChatActivity (same WebView)
 |                              |  http://127.0.0.1:8000
 +-- Termux                     v
      +-- backend/main.py  (serves frontend/ + /health + /api/chat)
            +-- chat.py     validation, history shaping
            +-- tutor.py    system instruction + study modes
            +-- providers/  gemini | openai (experimental) | mock
                               |
                          Google Gemini API
```

The same `frontend/` is the web app, the in-app chat and the floating panel. The Android part is a thin native shell: overlay, permission, clipboard bridge.

## Quick start (Termux)

```bash
cp .env.example .env        # then put your key in .env (nano .env)
bash start.sh               # serves http://127.0.0.1:8000/
```
Open `http://127.0.0.1:8000/` in Chrome. No `pip install` is needed.

Try it without a key or internet: `HAMO_PROVIDER=mock bash start.sh`.

## Android app

The APK is built in the cloud by GitHub Actions (`.github/workflows/build-apk.yml`) on every push that touches `android/`. Download `HAMO-AI.apk` from the repository's **Releases -> HAMO AI (latest build)** page and install it. Step by step (Arabic): [docs/SETUP_AR.md](docs/SETUP_AR.md).

Pinned toolchain: Android Gradle Plugin 8.7.3, Gradle 8.9, JDK 17, compileSdk/targetSdk 34, minSdk 26. The APK is signed with a fixed **debug** key (public password, committed on purpose so updates install over old builds). Create your own key before any store release.

Permissions: `INTERNET`, `SYSTEM_ALERT_WINDOW` (floating button), foreground service (keeps the button alive), `POST_NOTIFICATIONS` (shows the service notification with a Stop action). Plain HTTP is allowed only for `127.0.0.1`/`localhost`.

## API

`GET /health` -> `{"status":"ok","project":"HAMO AI","version":"0.2.0","provider":"gemini"}`

`POST /api/chat` (`Content-Type: application/json`, body up to 64 KB)

```json
{
  "message": "الفاعل هو الاسم المرفوع ...",
  "mode": "explain",
  "history": [{"role": "user", "text": "..."}, {"role": "assistant", "text": "..."}]
}
```
`mode`: `chat` (default), `explain`, `summarize`, `simplify`, `examples`, `quiz`, `steps`. `history` is optional (last 12 turns are used). `message` max 12,000 characters.

Success: `{"status":"success","project":"HAMO AI","reply":"...","provider":"gemini"}`
Error: `{"error":"<Arabic message safe to show>"}` with status 400 (bad input), 403 (host/origin), 413, 415, 429 (rate limit or provider quota), 500, 502/503/504 (provider problems).

## Security

- API keys live only in the backend `.env` (git-ignored); never in the web UI or the APK.
- The server binds to `127.0.0.1`. No CORS headers: only the page it serves can call the API. Requests need `Content-Type: application/json`, a matching `Host` (DNS-rebinding guard) and, if present, a matching `Origin`.
- Rate limit: 30 chat requests/minute (`HAMO_RATE_LIMIT_PER_MIN`).
- Provider errors are logged on the server; users get safe messages.
- The UI renders model output with an escaping Markdown renderer (no raw HTML, no links) under a strict Content-Security-Policy.
- The system prompt tells the model to treat pasted text as study material, not instructions.
- Chat history is stored locally in the WebView/browser storage (last 24 messages) until "new chat" is pressed.
- **Not production-ready:** no authentication, no HTTPS hosting, no usage/cost accounting. See the roadmap.

## Tests

```bash
bash tests/run_all.sh        # backend (unittest) + Markdown (Node, optional)
```
`tests/ui_check.py` is a manual headless-browser script (needs Playwright) used during development.

## Known limitations

- Android may restrict reading the clipboard from an overlay on some devices; the paste button then falls back to a hint (long-press in the input box).
- Some phone makers (Xiaomi, Oppo, Huawei, ...) add extra "pop-up/overlay" permissions that must be enabled manually.
- Termux must be running with the server for the app to work; Android can stop it in the background (`start.sh` takes a wake lock; also disable battery optimization for Termux).
- The panel is not re-laid-out on rotation until it is closed and reopened.

## Roadmap

See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
