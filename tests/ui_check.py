"""Headless-browser check of the web UI against a running mock server (manual script)."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else "/tmp/shots"
errors, failures = [], []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 760}, device_scale_factor=2,
                        has_touch=True, is_mobile=True,
                        permissions=["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    # "Failed to load resource" lines come from the 429/abort cases this script triggers on purpose.
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and "Failed to load resource" not in m.text else None)
    page.add_init_script("Clipboard.prototype.writeText = async (t) => { window.__copied = t; }")
    page.add_init_script("Clipboard.prototype.readText = async () => 'الفاعل هو الاسم المرفوع الذي يدل على من قام بالفعل.'")
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_selector("#conn-text:has-text('متصل بالخادم')")
    check("health dot online", "on" in page.get_attribute("#dot", "class"))
    check("close button hidden outside the app", not page.is_visible("#close-panel"))
    check("6 mode chips", page.locator(".mode").count() == 6)
    page.screenshot(path=f"{SHOTS}/1_welcome.png")

    # mode toggle + paste via clipboard API fallback
    page.click(".mode[data-mode=explain]")
    check("chip pressed", page.get_attribute(".mode[data-mode=explain]", "aria-pressed") == "true")
    check("placeholder follows mode", "شرحه" in page.get_attribute("#message-input", "placeholder"))
    page.focus("#message-input")
    page.click("#paste-button")
    got = page.input_value("#message-input")
    check("paste fills textarea", "الفاعل هو الاسم" in got)
    if "الفاعل هو الاسم" not in got:
        print("   textarea was:", repr(got), "| toast:", page.inner_text("#toast"))
        page.fill("#message-input", "الفاعل هو الاسم المرفوع")
    page.click("#send-button")
    page.wait_for_selector(".msg.ai")
    ai = page.inner_text(".msg.ai")
    check("reply rendered", "نموذج تجريبي" in ai)
    check("bold rendered as <strong>", page.locator(".msg.ai strong").count() >= 1)
    check("list rendered", page.locator(".msg.ai ul li").count() == 2)
    check("mode directive reached server", "المطلوب: اشرح" in ai)
    check("mode tag on user bubble", page.inner_text(".msg.user .tag") == "شرح")
    check("mode reset after send", page.get_attribute(".mode[data-mode=explain]", "aria-pressed") == "false")

    # follow-up keeps context (history)
    page.fill("#message-input", "وضّح أكثر")
    page.click("#send-button")
    page.locator(".msg.ai").nth(1).wait_for()
    check("history sent with follow-up (3 turns)", "(3 في السياق)" in page.inner_text(".msg.ai:nth-of-type(2)") or "(3 في السياق)" in page.locator(".msg.ai").nth(1).inner_text())
    page.screenshot(path=f"{SHOTS}/2_conversation.png")

    # copy answer
    page.click(".msg.ai .copy")
    check("copy toast", page.is_visible("#toast"))
    clip = page.evaluate("window.__copied") or ""
    check("copied text is the answer", "نموذج تجريبي" in clip)

    # XSS
    page.fill("#message-input", '<img src=x onerror="window.__pwn=1"> <script>window.__pwn=2</script>')
    page.click("#send-button")
    page.locator(".msg.ai").nth(2).wait_for()
    check("no injected <img> in answer", page.locator(".msg.ai img").count() == 0)
    check("script did not run", page.evaluate("window.__pwn === undefined"))

    # server error -> specific Arabic message + retry
    page.fill("#message-input", "[fail:429]")
    page.click("#send-button")
    page.wait_for_selector(".msg.error")
    check("API error shows server message (not 'cannot connect')", "حد الاستخدام" in page.inner_text(".msg.error"))
    check("retry button exists", page.locator(".msg.error .retry").count() == 1)
    page.screenshot(path=f"{SHOTS}/3_error.png")

    # persistence
    page.reload()
    page.wait_for_selector(".msg.ai")
    check("history restored after reload", page.locator(".msg.ai").count() == 3)

    # new chat
    page.click("#new-chat")
    check("new chat clears and shows welcome", page.locator(".msg").count() == 0 and page.is_visible("#welcome"))

    # network down -> offline message
    page.route("**/api/chat", lambda r: r.abort())
    page.fill("#message-input", "اختبار الشبكة")
    page.click("#send-button")
    page.wait_for_selector(".msg.error")
    check("offline message mentions Termux", "Termux" in page.inner_text(".msg.error"))
    check("status dot offline", "off" in page.get_attribute("#dot", "class"))

    # native bridge simulation (Android WebView)
    ctx2 = b.new_context(viewport={"width": 360, "height": 500})
    ctx2.add_init_script("""
      window.__log = [];
      window.HamoNative = {
        getClipboardText: () => 'نص من الحافظة الأصلية',
        copyText: (t) => { window.__log.push('copy:' + t.slice(0, 5)); return true; },
        closePanel: () => window.__log.push('close')
      };""")
    n = ctx2.new_page()
    n.on("pageerror", lambda e: errors.append(str(e)))
    n.goto(BASE)
    check("close button visible in native mode", n.is_visible("#close-panel"))
    n.click("#paste-button")
    check("native paste used", n.input_value("#message-input") == "نص من الحافظة الأصلية")
    n.click("#send-button")
    n.wait_for_selector(".msg.ai")
    n.click(".msg.ai .copy")
    n.click("#close-panel")
    log = n.evaluate("window.__log")
    check("native copy + close called", any(x.startswith("copy:") for x in log) and "close" in log)
    n.screenshot(path=f"{SHOTS}/4_native_panel.png")
    b.close()

check("no console/page errors (CSP ok)", not errors)
if errors:
    print("ERRORS:", errors[:5])
print("\nRESULT:", "ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
