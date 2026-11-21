# HAMO AI -- project plan and status

Legend: DONE = implemented and verified here | WRITTEN = code exists, not yet verified on a device | TODO

| Phase | Goal | Status |
|---|---|---|
| 0 | Project audit | DONE (`docs/AUDIT.md`) |
| 1 | Stabilize the web app (errors, loading, copy, RTL, hardening) | DONE -- 26 backend tests + 27 headless-browser checks pass (mock provider) |
| 2 | Educational assistant (system instruction, 6 study modes, conversation context) | DONE for the mechanics. Answer quality with live Gemini still needs your review |
| 3 | Android app foundation (control screen, in-app chat, server setting, connection test) | WRITTEN -- needs the first cloud build |
| 4 | Floating button + panel over Chrome | WRITTEN -- needs testing on your phone |
| 5 | Clipboard integration (paste button, native clipboard bridge) | WRITTEN -- Android may restrict clipboard reads; fallback is long-press paste |
| 6 | Image / screen understanding | TODO (after 3-5 are stable) |
| 7 | Multi-provider | Provider interface + manager DONE; Gemini live-tested by the owner; OpenAI EXPERIMENTAL/untested; Claude TODO |
| 8 | Branding (logo, watermark, final colors) | PARTIAL: "H" mark + palette exist; watermark TODO |
| 9 | Production (HTTPS hosting, accounts/auth, signed release APK, usage/cost limits) | TODO. README + tests started |

## Next steps
1. Cloud build of the APK -> install -> test the floating button over Chrome.
2. Review answer quality of each study mode with real lessons; tune `backend/tutor.py`.
3. Decide on hosting (HTTPS) so students do not need Termux.
