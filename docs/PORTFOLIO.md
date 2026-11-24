# HAMO AI -- Project Case Study

*A one-page summary for applications, resumes and portfolios. For the full technical documentation see the [README](../README.md).*

## The problem

Students on Arabic educational platforms frequently hit a term, a grammar rule or a question they do not understand while studying on their phone, and have to leave the page to search for an explanation elsewhere. HAMO AI puts that explanation on top of the page they are already reading, through a floating button that works over any app, Chrome included.

## What I built

- **Backend** (Python, standard library only -- no dependencies to install): a hardened HTTP API with a provider-abstraction layer so the AI model (currently Google Gemini) can be swapped without touching the rest of the system.
- **Educational layer**: a system prompt and six structured study modes (explain, summarize, simplify, examples, quiz, step-by-step) with multi-turn conversation context.
- **Web UI**: an Arabic, RTL, mobile-first chat interface with a safe Markdown renderer written from scratch (escapes everything, builds only known tags -- no raw HTML or links can reach the page).
- **Android app** (Java, no external dependencies): a control screen, an in-app chat, and a system-overlay service that draws a draggable floating button and a resizable assistant panel over other apps, using Android's `SYSTEM_ALERT_WINDOW` and foreground-service APIs.
- **CI/CD**: a GitHub Actions workflow that builds and signs a debug APK on every push and publishes it as a downloadable release -- no local Android Studio needed, since the project was developed entirely from a phone (Termux).

## Engineering decisions worth highlighting

| Decision | Why |
|---|---|
| Backend serves the frontend itself (one origin, one port) | Removes a class of cross-origin bugs entirely instead of patching CORS headers. |
| No CORS headers at all, plus `Content-Type`, `Origin` and `Host` checks | An audit of the inherited prototype found `Access-Control-Allow-Origin: *`, which let any open web page spend the project's AI quota through `127.0.0.1:8000`. Reproduced it, then closed it at the protocol level instead of a UI-level fix. |
| Hand-written escaping Markdown renderer instead of a library | AI output is untrusted text rendered as HTML; the renderer only emits tags it explicitly builds, closing the XSS surface rather than trusting a sanitizer to catch every case. |
| Provider interface (`generate(system, turns) -> str`) | One function signature, three implementations (Gemini, OpenAI, Mock). Adding Anthropic Claude later means writing one file, not touching the chat pipeline. |
| Mock provider | Enables deterministic automated tests and a live public demo with no API key and no network dependency. |
| Same WebView/JS bundle for the website, the in-app screen and the floating panel | One UI to build and test; the Android layer is a thin native shell (overlay, permissions, clipboard bridge) around it. |

## Testing

- 26 backend unit and integration tests (`tests/test_tutor.py`, `tests/test_server.py`): request validation, conversation-history shaping and truncation, rate limiting, path-traversal protection, DNS-rebinding protection, and that provider error details never leak to the client.
- 27 headless-browser checks (`tests/ui_check.py`, Playwright, phone viewport): mode switching, clipboard paste/copy (including the Android native-bridge path), Markdown rendering, an XSS attempt against the renderer, error handling and retry, and conversation persistence across a reload.
- The Android code is verified with `javac` for compile correctness in CI on every push; on-device behavior (the overlay, drag gestures, permission flows) still needs manual testing on real hardware, and the README says so plainly rather than claiming it is verified.

## Scope and honesty

The project tracks what is *verified* separately from what is *implemented but untested* (see the status table in the README and `docs/PROJECT_PLAN.md`). The backend and web UI are tested; the Android overlay and the OpenAI provider are implemented but not yet confirmed on real devices or with a live key. Production concerns -- HTTPS hosting, user accounts, cost controls -- are explicitly listed as open, not glossed over.

## Stack

Python (stdlib only) -- HTML/CSS/JavaScript -- Java (Android, no dependencies) -- GitHub Actions -- Google Gemini API -- `unittest` + Playwright for testing.
