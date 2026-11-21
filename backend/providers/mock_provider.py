"""Offline provider for tests and UI demos (HAMO_PROVIDER=mock). No network."""

from .base import ProviderError


def generate(system, turns):
    last = turns[-1]["text"]
    if "[fail:429]" in last:
        raise ProviderError(
            "تم تجاوز حد الاستخدام لدى مزوّد الذكاء الاصطناعي مؤقتًا. حاول بعد قليل.",
            429, "mock 429")
    if "[crash]" in last:
        raise RuntimeError("mock crash")
    preview = " ".join(last.split())[:120]
    return (
        f"**نموذج تجريبي بدون إنترنت.** وصلتني رسالتك ({len(turns)} في السياق).\n\n"
        f"- آخر رسالة: {preview}\n"
        f"- التعليمات التعليمية مفعّلة: {'نعم' if system else 'لا'}"
    )
