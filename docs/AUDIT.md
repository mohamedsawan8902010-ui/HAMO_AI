# Phase 0 audit (handover review)

Reviewed the delivered `HAMO_AI_Source.zip` (15 entries, 7.6 KB) on 2026-11-21.

## What was verified
| Check | Result |
|---|---|
| `py_compile` on `main.py`, `gemini_provider.py`, `openai_provider.py` | OK |
| `GET /health` | `{"status":"ok","project":"HAMO AI","version":"0.1.0"}` |
| Empty message | HTTP 400 |
| Secrets in the archive | No `.env`, no `.git` in the zip |
| Live Gemini call | Not re-run in the review sandbox (no internet). The owner's earlier `OK` test is the reference. |

## Findings (all addressed in v0.2.0)
| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | High | `Access-Control-Allow-Origin: *` and no `Content-Type` check: any web page open in Chrome could POST to `127.0.0.1:8000` and spend the Gemini quota (reproduced: the request reached the provider). | No CORS at all, same-origin UI served by the backend, `Content-Type: application/json` required, `Origin` and `Host` checks, rate limit. |
| 2 | Medium | A JSON body that is not an object (e.g. `[1,2]`) raised an unhandled exception and the connection dropped without a reply. | Strict validation, catch-all 500 handler. |
| 3 | Medium | Provider error bodies were returned to the client. | User-safe Arabic messages; details only in the server log. |
| 4 | Low | UI showed "cannot connect" for every error, no history, no educational mode, plain-text answers. | UI rewritten (modes, history, Markdown, retry, copy, paste). |
| 5 | Low | `requirements.txt` said "no dependencies" but the code needed `python-dotenv`. | Tiny built-in `.env` loader; truly no dependencies. |
| 6 | Info | `openai_provider.py` was unused and untested; its default model name was unverified. | Adapted to the provider interface, no default model, marked EXPERIMENTAL. |
| 7 | Info | `README.md` and `docs/PROJECT_PLAN.md` were empty; stray untracked `backend/requiremuvicorno` (fastapi/uvicorn, unused). | Docs written. The stray file is safe to delete (see `SETUP_AR.md`). |

## Not changed on purpose
Python stdlib server (no FastAPI), plain HTML/CSS/JS frontend, Gemini model name `gemini-3.5-flash-lite` (now overridable with `GEMINI_MODEL`).
