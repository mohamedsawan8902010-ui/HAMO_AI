
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send-button");

const API_URL = "http://127.0.0.1:8000/api/chat";


function addMessage(text, type) {
    const message = document.createElement("div");

    message.classList.add("message");

    if (type === "user") {
        message.classList.add("user-message");
    } else {
        message.classList.add("ai-message");
    }

    message.textContent = text;

    messages.appendChild(message);

    message.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}


async function sendMessage(text) {
    try {
        sendButton.disabled = true;
        sendButton.textContent = "جاري الإرسال...";

        const response = await fetch(API_URL, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        addMessage(data.reply, "ai");

    } catch (error) {
        console.error("HAMO AI Error:", error);

        addMessage(
            "تعذر الاتصال بالخادم. تأكد من تشغيل HAMO AI Server.",
            "ai"
        );

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "إرسال";
        messageInput.focus();
    }
}


chatForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const text = messageInput.value.trim();

    if (!text) {
        return;
    }

    addMessage(text, "user");

    messageInput.value = "";

    await sendMessage(text);
});


messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

