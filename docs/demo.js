/* HAMO AI -- static demo for GitHub Pages.
 * No backend, no network call, no API key: every reply below is a fixed sample
 * written to show the real UI's layout, modes and Markdown rendering only.
 * The actual app talks to a real AI model through backend/main.py -- see the README. */
(() => {
    "use strict";

    const MODES = {
        chat:      { label: "",            tag: "" },
        explain:   { label: "اشرح",        tag: "شرح" },
        summarize: { label: "لخّص",        tag: "تلخيص" },
        simplify:  { label: "بسّط",        tag: "تبسيط" },
        examples:  { label: "أمثلة",       tag: "أمثلة" },
        quiz:      { label: "اختبرني",     tag: "اختبار" },
        steps:     { label: "خطوة بخطوة",  tag: "خطوة بخطوة" }
    };

    const SAMPLE_LESSON =
        "الفاعل هو الاسم المرفوع الذي يدل على من قام بالفعل أو اتّصف به، " +
        "ويأتي غالبًا بعد الفعل مباشرة، مثل: نجح الطالبُ في الامتحان.";

    const SAMPLE_REPLIES = {
        chat:
            "تمام، أنا هنا. الصق أي فقرة تدرسها واختر نوع المساعدة الذي تريده (اشرح، لخّص، بسّط...) من الشريط بالأعلى.\n\nهذا رد نموذجي ثابت لأن هذا عرض تجريبي بدون اتصال حقيقي بالذكاء الاصطناعي.",
        explain:
            "**الفاعل** هو الاسم المرفوع الذي يدل على مَن قام بالفعل.\n\n- يأتي بعد الفعل غالبًا: *نجح الطالبُ*.\n- علامة رفعه الأساسية هي **الضمة** الظاهرة أو المقدّرة.\n- قد يكون اسمًا ظاهرًا أو ضميرًا مستترًا.\n\nمثال: في جملة «نجح الطالبُ»، الفعل هو «نجح» والفاعل هو «الطالبُ» لأنه مَن قام بالنجاح.\n\n*(هذا شرح نموذجي ثابت لعرض التصميم فقط.)*",
        summarize:
            "- الفاعل: اسم مرفوع يدل على من قام بالفعل.\n- يأتي عادة بعد الفعل مباشرة.\n- علامته الأصلية: الضمة.\n\nباختصار: الفاعل يجيب عن سؤال «مَن فعل؟».\n\n*(تلخيص نموذجي ثابت لعرض التصميم فقط.)*",
        simplify:
            "تخيّل الجملة كأنها قصة قصيرة: فيها شخص **قام بالفعل**، وهذا الشخص هو الفاعل.\n\nفي «نجح الطالبُ»: مين اللي نجح؟ الطالب. إذن الطالب هو الفاعل، وبسيطة كده.\n\n*(تبسيط نموذجي ثابت لعرض التصميم فقط.)*",
        examples:
            "1. **نجح الطالبُ** -- الفاعل: الطالب.\n2. **طلعت الشمسُ** -- الفاعل: الشمس.\n3. **يلعب الأطفالُ** -- الفاعل: الأطفال (جمع).\n4. **سافرتْ سارةُ** -- الفاعل: سارة (مؤنث، فاء الفعل مربوطة بتاء التأنيث).\n\n*(أمثلة نموذجية ثابتة لعرض التصميم فقط.)*",
        quiz:
            "جاهز؟ أجب عن الأسئلة التالية ثم أرسل إجاباتك:\n\n1. حدّد الفاعل في: «كتب الطالبُ الدرسَ».\n2. صحّح الخطأ إن وجد: «نجح الطالبِ في الامتحان».\n3. هل الفاعل في «يلعب الولدان» مفرد أم مثنى؟\n\n*(اختبار نموذجي ثابت -- في النسخة الحقيقية يصحح الذكاء الاصطناعي إجاباتك في الرد التالي.)*",
        steps:
            "1. ابحث عن الفعل في الجملة: «نجح».\n2. اسأل: مَن الذي قام بهذا الفعل؟ الإجابة: «الطالبُ».\n3. تأكد أن الاسم مرفوع (ضمة في آخره).\n4. إذن: الفاعل هو «الطالبُ».\n\n**الناتج:** الفاعل = الطالبُ.\n\n*(حل نموذجي ثابت لعرض التصميم فقط.)*"
    };

    const $ = (id) => document.getElementById(id);
    const el = {
        chat: $("chat"), messages: $("messages"), welcome: $("welcome"),
        form: $("chat-form"), input: $("message-input"), send: $("send-button"),
        paste: $("paste-button"), modes: $("modes"), newChat: $("new-chat"), toast: $("toast")
    };

    let mode = "chat";
    let busy = false;
    const ICON_COPY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 9h10v11H9zM5 15V4h10"/></svg>';

    function toast(text) {
        el.toast.textContent = text;
        el.toast.hidden = false;
        clearTimeout(toast._t);
        toast._t = setTimeout(() => { el.toast.hidden = true; }, 2600);
    }

    function scrollToEnd() {
        el.chat.scrollTop = el.chat.scrollHeight;
    }

    function autoGrow() {
        el.input.style.height = "auto";
        el.input.style.height = Math.min(el.input.scrollHeight, 130) + "px";
    }

    function setMode(next) {
        mode = next === mode ? "chat" : next;
        for (const button of el.modes.children) {
            button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
        }
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
            button.addEventListener("click", () => setMode(key));
            el.modes.appendChild(button);
        }
    }

    function addUser(text, modeKey) {
        el.welcome.hidden = true;
        const box = document.createElement("div");
        box.className = "msg user";
        if (modeKey && modeKey !== "chat") {
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
        scrollToEnd();
    }

    function addAssistant(text) {
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
        copy.innerHTML = ICON_COPY + "<span>نسخ</span>";
        copy.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(text);
                toast("تم نسخ الإجابة");
            } catch (_) {
                toast("تعذر النسخ");
            }
        });
        actions.appendChild(copy);
        box.append(content, actions);
        el.messages.appendChild(box);
        scrollToEnd();
    }

    function showTyping() {
        const box = document.createElement("div");
        box.className = "typing";
        box.innerHTML = "<i></i><i></i><i></i>";
        el.messages.appendChild(box);
        scrollToEnd();
        return box;
    }

    function onSubmit(event) {
        event.preventDefault();
        const text = el.input.value.trim();
        if (!text || busy) return;
        busy = true;
        el.send.disabled = true;
        addUser(text, mode);
        const replyMode = mode;
        el.input.value = "";
        autoGrow();
        setMode("chat");
        const typing = showTyping();
        setTimeout(() => {
            typing.remove();
            addAssistant(SAMPLE_REPLIES[replyMode] || SAMPLE_REPLIES.chat);
            busy = false;
            el.send.disabled = false;
        }, 650 + Math.random() * 500);
    }

    buildModes();
    el.input.value = SAMPLE_LESSON;
    autoGrow();
    el.form.addEventListener("submit", onSubmit);
    el.input.addEventListener("input", autoGrow);
    el.paste.addEventListener("click", () => {
        el.input.value = SAMPLE_LESSON;
        autoGrow();
        el.input.focus();
        toast("هذا عرض تجريبي: تم إدراج نص جاهز بدل اللصق الفعلي");
    });
    el.newChat.addEventListener("click", () => {
        el.messages.textContent = "";
        el.welcome.hidden = false;
        setMode("chat");
        el.input.value = SAMPLE_LESSON;
        autoGrow();
    });
})();
