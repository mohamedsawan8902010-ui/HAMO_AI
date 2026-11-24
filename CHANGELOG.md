# Changelog

All notable changes to HAMO AI are documented here.

## [1.0.0] -- 2026-11-24
### Added
- `LICENSE` (MIT), `CONTRIBUTING.md`, this changelog.
- `docs/PORTFOLIO.md`: a one-page case study of the project (problem, architecture, engineering decisions, testing) for applications and resumes.
- Static demo site (`docs/index.html`) for GitHub Pages: the real UI with sample canned replies, no backend or API key required, so anyone can try the interface from the README.
- Brand mark (`docs/assets/logo.svg`) used in the README header and reusable as a web favicon.
### Changed
- Version bumped to 1.0.0 across the backend, the Android app and the docs.
### Status
- No functional change to the backend or the Android app in this release: v0.2.1 is carried forward as-is once more files/docs are verified. See `docs/PROJECT_PLAN.md` for what is still open (hosting, accounts, Claude provider, image understanding).

## [0.2.1] -- 2026-11-21
### Added
- Floating-panel size control: a button in the panel header cycles small / medium / large and remembers the choice (`Prefs.panelSize`, `OverlayService.cyclePanelSize`).

## [0.2.0] -- 2026-11-20
Full rebuild of the v0.1.0 handover prototype after the Phase-0 audit (`docs/AUDIT.md`).
### Added
- Educational layer: system instruction + 6 study modes (explain, summarize, simplify, examples, quiz, step-by-step) with multi-turn context (`backend/tutor.py`, `backend/chat.py`).
- Provider manager supporting Gemini (live-tested), OpenAI (experimental/untested) and a Mock provider for offline development and tests.
- Backend now serves the web UI itself (one origin, one port) instead of two separate local servers.
- Hardening: no CORS, `Content-Type` and `Origin`/`Host` checks (blocks cross-site requests and DNS rebinding), per-minute rate limit, sanitized error messages, path-traversal-safe static file serving, security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy`).
- Rewritten web UI: RTL Arabic layout, mode chips, conversation history (local storage), a safe escaping Markdown renderer (no raw HTML/links), copy button, retry on error, auto-resizing input.
- Android app (Java, no external dependencies): control screen (`MainActivity`), in-app chat (`ChatActivity`), floating "H" button and resizable assistant panel over other apps (`OverlayService`), a small JS bridge for clipboard paste/copy (`HamoBridge`), same-origin `WebView` navigation guard (`HamoWebView`).
- GitHub Actions workflow building a signed debug APK on every push and publishing it to a rolling "latest" release.
- Automated tests: 26 backend unit/integration tests (`tests/test_tutor.py`, `tests/test_server.py`) and a 27-check headless-browser UI script (`tests/ui_check.py`).
### Fixed
- `Access-Control-Allow-Origin: *` let any open web page spend the Gemini quota through `127.0.0.1:8000` (reproduced during the audit).
- A JSON body that was not an object (e.g. `[1,2]`) crashed the request with no reply.
- `requirements.txt` claimed no dependencies while the code imported `python-dotenv`; replaced with a small built-in `.env` loader so the claim is now true.

## [0.1.0] -- initial handover
Termux-built prototype: Python stdlib backend (`/health`, `/api/chat`), a working Gemini provider, a plain HTML/CSS/JS frontend. Verified manually by the project owner (see the original handover documents). No tests, no hardening, no Android app yet.
