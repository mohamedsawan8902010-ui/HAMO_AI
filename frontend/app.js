(() => {
    "use strict";

    const MODES = {
        chat:      { label: "",            tag: "",            placeholder: "اكتب سؤالك أو الصق النص هنا…" },
        explain:   { label: "اشرح",        tag: "شرح",         placeholder: "الصق النص الذي تريد شرحه…" },
        summarize: { label: "لخّص",        tag: "تلخيص",       placeholder: "الصق الفقرة التي تريد تلخيصها…" },
        simplify:  { label: "بسّط",        tag: "تبسيط",       placeholder: "الصق النص الصعب لأبسّطه لك…" },
        examples:  { label: "أمثلة",       tag: "أمثلة",       placeholder: "الصق القاعدة أو الفكرة لأعطيك أمثلة…" },
        quiz:      { label: "اختبرني",     tag: "اختبار",      placeholder: "الصق الدرس لأختبر فهمك…" },
        steps:     { label: "خطوة بخطوة",  tag: "خطوة بخطوة",  placeholder: "الصق المسألة أو النص لنحلّه خطوة بخطوة…" }
    };

    const STORE_KEY = "hamo.history.v1";
    const MAX_KEPT = 24;
    const NATIVE = typeof window.HamoNative !== "undefined";
    const COARSE_POINTER = !!(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
    const ICON_COPY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 9h10v11H9zM5 15V4h10"/></svg>';

    const $ = (id) => document.getElementById(id);
    const el = {
        chat: $("chat"), messages: $("messages"), welcome: $("welcome"),
        form: $("chat-form"), input: $("message-input"), send: $("send-button"),
        paste: $("paste-button"), modes: $("modes"), dot: $("dot"),
        connText: $("conn-text"), newChat: $("new-chat"), close: $("close-panel"),
        toast: $("toast")
    };

    let history = [];      // committed turns: { role, text, mode }
    let mode = "chat";
    let busy = false;
    let toastTimer = 0;

    class ApiError extends Error {}

    /* ---------- small UI helpers ---------- */

    function toast(text) {
        el.toast.textContent = text;
        el.toast.hidden = false;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => { el.toast.hidden = true; }, 3200);
    }

    function setOnline(online) {
        el.dot.className = "dot " + (online ? "on" : "off");
        el.connText.textContent = online ? "متصل بالخادم" : "الخادم غير متصل";
    }

    async function checkHealth() {
        try {
            const res = await fetch("/health", { cache: "no-store" });
            setOnline(res.ok);
        } catch (_) {
            setOnline(false);
        }
    }

    function scrollToEnd(instant) {
        el.chat.style.scrollBehavior = instant ? "auto" : "";
        el.chat.scrollTop = el.chat.scrollHeight;
    }

    function autoGrow() {
        el.input.style.height = "auto";
        el.input.style.height = Math.min(el.input.scrollHeight, 130) + "px";
    }

    function setBusy(value) {
        busy = value;
        el.send.disabled = value;
    }

    /* ---------- modes ---------- */

    function setMode(next) {
        mode = next === mode ? "chat" : next;
        for (const button of el.modes.children) {
            button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
        }
        el.input.placeholder = MODES[mode].placeholder;
    }

    function buildModes() {
        for (const key of Object.keys(MODES)) {
            if (key === "chat") continue;
            const button = document.createElement("button");
            button.type = "button";
            button.className = "mode";
            button.dataset.mode = key;
            button.textContent = MODES[key].label;
            button.setAttribute("aria-pressed", "false");
            button.addEventListener("click", () => {
                setMode(key);
                el.input.focus();
            });
            el.modes.appendChild(button);
        }
    }

    /* ---------- messages ---------- */

    function addUser(text, modeKey, instant) {
        el.welcome.hidden = true;
        const box = document.createElement("div");
        box.className = "msg user";
        if (modeKey && modeKey !== "chat" && MODES[modeKey]) {
            const tag = document.createElement("span");
            tag.className = "tag";
            tag.textContent = MODES[modeKey].tag;
            box.appendChild(tag);
        }
        const body = document.createElement("div");
        body.className = "body";
        body.dir = "auto";
        body.textContent = text;
        box.appendChild(body);
        el.messages.appendChild(box);
        scrollToEnd(instant);
    }

    function addAssistant(text, instant) {
        el.welcome.hidden = true;
        const box = document.createElement("div");
        box.className = "msg ai";
        const content = document.createElement("div");
        content.dir = "auto";
        content.innerHTML = window.HamoMarkdown.render(text);
        const actions = document.createElement("div");
        actions.className = "msg-actions";
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "copy";
        copy.setAttribute("aria-label", "نسخ الإجابة");
        copy.innerHTML = ICON_COPY + "<span>نسخ</span>";
        copy.addEventListener("click", async () => {
            toast((await copyText(text)) ? "تم نسخ الإجابة" : "تعذر النسخ");
        });
        actions.appendChild(copy);
        box.append(content, actions);
        el.messages.appendChild(box);
        scrollToEnd(instant);
    }

    function addError(message, payload) {
        const box = document.createElement("div");
        box.className = "msg error";
        box.setAttribute("role", "alert");
        const text = document.createElement("div");
        text.textContent = message;
        const retry = document.createElement("button");
        retry.type = "button";
        retry.className = "retry";
        retry.textContent = "إعادة المحاولة";
        retry.addEventListener("click", () => {
            if (busy) return;
            box.remove();
            request(payload);
        });
        box.append(text, retry);
        el.messages.appendChild(box);
        scrollToEnd();
    }

    function showTyping() {
        const box = document.createElement("div");
        box.className = "typing";
        box.setAttribute("role", "status");
        box.setAttribute("aria-label", "جارٍ كتابة الإجابة");
        box.innerHTML = "<i></i><i></i><i></i>";
        el.messages.appendChild(box);
        scrollToEnd();
        return box;
    }

    /* ---------- clipboard (native bridge first, web APIs as fallback) ---------- */

    async function copyText(text) {
        try {
            if (NATIVE && typeof window.HamoNative.copyText === "function") {
                return !!window.HamoNative.copyText(text);
            }
        } catch (_) { /* fall through */ }
        try {
            if (navigator.clipboard && window.isSecureContext) {
                const written = await Promise.race([
                    navigator.clipboard.writeText(text).then(() => true),
                    new Promise((resolve) => setTimeout(() => resolve(false), 1500))
                ]);
                if (written) return true;
            }
        } catch (_) { /* fall through */ }
        try {
            const area = document.createElement("textarea");
            area.value = text;
            area.setAttribute("readonly", "");
            area.className = "offscreen";
            document.body.appendChild(area);
            area.select();
            const ok = document.execCommand("copy");
            area.remove();
            return ok;
        } catch (_) {
            return false;
        }
    }

    async function pasteFromClipboard() {
        let text = "";
        try {
            if (NATIVE && typeof window.HamoNative.getClipboardText === "function") {
                text = window.HamoNative.getClipboardText() || "";
            } else if (navigator.clipboard && navigator.clipboard.readText) {
                // Some browsers leave this promise pending when permission is not granted.
                text = await Promise.race([
                    navigator.clipboard.readText(),
                    new Promise((resolve) => setTimeout(() => resolve(""), 1500))
                ]);
            }
        } catch (_) { /* handled below */ }

        text = (text || "").trim();
        if (!text) {
            toast("لم أستطع قراءة الحافظة. اضغط مطولًا داخل المربع ثم اختر «لصق».");
            el.input.focus();
            return;
        }
        const start = el.input.selectionStart;
        const end = el.input.selectionEnd;
        if (typeof start === "number" && typeof end === "number") {
            el.input.setRangeText(text, start, end, "end");
        } else {
            el.input.value += text;
        }
        autoGrow();
        el.input.focus();
        if (mode === "chat" && text.length > 200) {
            toast("اختر نوع المساعدة (اشرح، لخّص…) ثم أرسل.");
        }
    }

    /* ---------- history ---------- */

    function persist() {
        try {
            localStorage.setItem(STORE_KEY, JSON.stringify(history.slice(-MAX_KEPT)));
        } catch (_) { /* storage may be unavailable */ }
    }

    function restore() {
        try {
            const saved = JSON.parse(localStorage.getItem(STORE_KEY) || "[]");
            if (!Array.isArray(saved)) return;
            for (const item of saved) {
                if (!item || typeof item.text !== "string") continue;
                if (item.role !== "user" && item.role !== "assistant") continue;
                const entry = { role: item.role, text: item.text, mode: MODES[item.mode] ? item.mode : "chat" };
                history.push(entry);
                if (entry.role === "user") addUser(entry.text, entry.mode, true);
                else addAssistant(entry.text, true);
            }
        } catch (_) { /* ignore corrupt data */ }
    }

    function resetChat() {
        history = [];
        try { localStorage.removeItem(STORE_KEY); } catch (_) { /* ignore */ }
        el.messages.textContent = "";
        el.welcome.hidden = false;
        setMode("chat");
        el.input.value = "";
        autoGrow();
    }

    /* ---------- chat request ---------- */

    async function request(payload) {
        setBusy(true);
        const typing = showTyping();
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            let data = null;
            try { data = await res.json(); } catch (_) { /* non-JSON error page */ }
            if (!res.ok || !data || data.status !== "success") {
                throw new ApiError((data && data.error) || "حدث خطأ غير متوقع (" + res.status + ").");
            }
            typing.remove();
            history.push({ role: "user", text: payload.message, mode: payload.mode });
            history.push({ role: "assistant", text: data.reply, mode: "chat" });
            persist();
            addAssistant(data.reply);
            setOnline(true);
        } catch (err) {
            typing.remove();
            const unreachable = !(err instanceof ApiError);
            addError(
                unreachable
                    ? "تعذر الاتصال بالخادم. شغّل HAMO AI في Termux بالأمر bash start.sh ثم أعد المحاولة."
                    : err.message,
                payload
            );
            if (unreachable) setOnline(false);
        } finally {
            setBusy(false);
        }
    }

    function onSubmit(event) {
        event.preventDefault();
        const text = el.input.value.trim();
        if (!text || busy) return;
        const payload = {
            message: text,
            mode: mode,
            history: history.slice(-MAX_KEPT).map((m) => ({ role: m.role, text: m.text }))
        };
        addUser(text, mode);
        el.input.value = "";
        autoGrow();
        setMode("chat");
        request(payload);
    }

    /* ---------- wiring ---------- */

    buildModes();
    restore();
    checkHealth();

    el.form.addEventListener("submit", onSubmit);
    el.input.addEventListener("input", autoGrow);
    el.input.addEventListener("keydown", (event) => {
        // Phones: Enter adds a new line (the send button sends). Desktop: Enter sends.
        if (event.key === "Enter" && !event.shiftKey && !COARSE_POINTER) {
            event.preventDefault();
            el.form.requestSubmit();
        }
    });
    el.paste.addEventListener("click", pasteFromClipboard);
    el.newChat.addEventListener("click", resetChat);

    if (NATIVE) {
        el.close.hidden = false;
        el.close.addEventListener("click", () => window.HamoNative.closePanel());
    }
})();
