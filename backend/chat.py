"""Chat pipeline: validate the request, shape the conversation, call the provider."""

from providers import get_provider
from tutor import MODES, SYSTEM_INSTRUCTION, apply_mode

MAX_MESSAGE_CHARS = 12_000   # one message
MAX_HISTORY_ITEMS = 40       # accepted from the client
KEEP_TURNS = 12              # newest history turns sent to the model
MAX_CONTEXT_CHARS = 30_000   # hard cap on everything sent to the model


class ChatError(ValueError):
    """Invalid client request. The message is safe to show to the user."""


def parse_request(data):
    """Return (message, mode, history) or raise ChatError."""
    if not isinstance(data, dict):
        raise ChatError("صيغة الطلب غير صحيحة.")

    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ChatError("الرسالة مطلوبة.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise ChatError(f"الرسالة طويلة جدًا. الحد الأقصى {MAX_MESSAGE_CHARS} حرفًا.")

    mode = data.get("mode", "chat")
    if not isinstance(mode, str) or mode not in MODES:
        raise ChatError("نوع المساعدة المطلوب غير معروف.")

    raw_history = data.get("history")
    if raw_history is None:
        raw_history = []
    if not isinstance(raw_history, list) or len(raw_history) > MAX_HISTORY_ITEMS:
        raise ChatError("سجل المحادثة غير صالح.")

    history = []
    for item in raw_history:
        if not isinstance(item, dict):
            raise ChatError("سجل المحادثة غير صالح.")
        role, text = item.get("role"), item.get("text")
        if role not in ("user", "assistant") or not isinstance(text, str):
            raise ChatError("سجل المحادثة غير صالح.")
        if text.strip():
            history.append({"role": role, "text": text[:MAX_MESSAGE_CHARS]})

    return message.strip(), mode, history


def _normalize(turns):
    """Start with a user turn and merge consecutive turns of the same role."""
    merged = []
    for turn in turns:
        if merged and merged[-1]["role"] == turn["role"]:
            merged[-1] = {"role": turn["role"],
                          "text": merged[-1]["text"] + "\n\n" + turn["text"]}
        elif merged or turn["role"] == "user":
            merged.append(dict(turn))
    return merged


def build_turns(message, mode, history):
    turns = _normalize(history[-KEEP_TURNS:] + [{"role": "user", "text": apply_mode(mode, message)}])
    while len(turns) > 1 and sum(len(t["text"]) for t in turns) > MAX_CONTEXT_CHARS:
        turns = _normalize(turns[1:])
    return turns


def run_chat(message, mode, history):
    """Call the active AI provider and return the reply text."""
    return get_provider().generate(SYSTEM_INSTRUCTION, build_turns(message, mode, history))
